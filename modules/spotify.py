import html
import re
import threading
import time

import requests
import telebot

from config import config
from modules import log
from modules.api_models import SpotifySearchResponse, SpotifyTokenResponse, SpotifyTrack
from resources import strings

logger = log.Logger()

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
SPOTIFY_MARKET = "KR"
SEARCH_LIMIT = 5
REQUEST_TIMEOUT = 10
TOKEN_REFRESH_MARGIN = 60
DEFAULT_RATE_LIMIT_COOLDOWN = 1
MAX_BUTTON_TEXT_LENGTH = 60
CALLBACK_PREFIX = "spotify_track"
# Telegram callback_data는 최대 64 bytes이고 Spotify ID는 base-62 ASCII이므로 prefix와 구분자 길이를 제외한다.
MAX_TRACK_ID_LENGTH = 64 - len(CALLBACK_PREFIX) - 1
TRACK_ID_PATTERN = re.compile(rf"^[A-Za-z0-9]{{1,{MAX_TRACK_ID_LENGTH}}}$")


class SpotifyError(Exception):
    """Spotify 요청을 처리하지 못했을 때 발생하는 공통 예외."""


class SpotifyConfigurationError(SpotifyError):
    """Spotify API credential이 설정되지 않은 경우."""


class SpotifyRateLimitError(SpotifyError):
    """Spotify API rate limit에 도달한 경우."""


class SpotifyService:
    def __init__(self, bot, client_id=None, client_secret=None):
        self.bot = bot
        self.client_id = config.SPOTIFY_CLIENT_ID if client_id is None else client_id
        self.client_secret = config.SPOTIFY_CLIENT_SECRET if client_secret is None else client_secret
        self._access_token = None
        self._token_expires_at = 0.0
        self._token_lock = threading.Lock()
        self._rate_limit_until = 0.0
        self._rate_limit_lock = threading.Lock()

    # --- Telegram routing ---

    @staticmethod
    def is_spotify_callback(data):
        prefix, separator, track_id = (data or "").partition(":")
        return prefix == CALLBACK_PREFIX and bool(separator) and bool(TRACK_ID_PATTERN.fullmatch(track_id))

    def search_handler(self, message):
        keyword = self._extract_keyword(getattr(message, "text", None))
        if not keyword:
            self.bot.reply_to(message, strings.spotify_help_msg)
            return

        self.bot.send_chat_action(message.chat.id, "typing")
        try:
            tracks = self.search_tracks(keyword)
        except SpotifyConfigurationError:
            self.bot.reply_to(message, strings.spotify_unavailable_error_msg)
            return
        except SpotifyRateLimitError:
            self.bot.reply_to(message, strings.spotify_rate_limit_error_msg)
            return
        except SpotifyError:
            logger.log_error("Failed to search Spotify tracks.")
            self.bot.reply_to(message, strings.spotify_error_msg)
            return

        tracks = [track for track in tracks if TRACK_ID_PATTERN.fullmatch(track.id) and track.external_urls.spotify]
        if not tracks:
            self.bot.reply_to(message, strings.spotify_no_result_msg)
            return

        text = self._build_search_message(keyword, tracks)
        keyboard = self._build_search_keyboard(tracks)
        self.bot.reply_to(
            message,
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )

    def handle_spotify_callback(self, call):
        _, _, track_id = (call.data or "").partition(":")
        if not TRACK_ID_PATTERN.fullmatch(track_id):
            return

        try:
            track = self.get_track(track_id)
        except SpotifyConfigurationError:
            self.bot.send_message(call.message.chat.id, strings.spotify_unavailable_error_msg)
            return
        except SpotifyRateLimitError:
            self.bot.send_message(call.message.chat.id, strings.spotify_rate_limit_error_msg)
            return
        except SpotifyError:
            logger.log_error("Failed to fetch a Spotify track.")
            self.bot.send_message(call.message.chat.id, strings.spotify_track_unavailable_error_msg)
            return

        if not track.external_urls.spotify:
            self.bot.send_message(call.message.chat.id, strings.spotify_track_unavailable_error_msg)
            return

        caption = self._build_detail_message(track)
        keyboard = self._build_open_keyboard(track.external_urls.spotify)
        image_url = next((image.url for image in track.album.images if image.url), None)

        if image_url:
            try:
                # Spotify 정책에 따라 앨범 아트를 가공하지 않고 API가 제공한 원본 URL로 전달한다.
                self.bot.send_photo(
                    call.message.chat.id,
                    image_url,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
                return
            except Exception:
                logger.log_error("Failed to send Spotify album artwork, falling back to text.")

        self.bot.send_message(
            call.message.chat.id,
            caption,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )

    # --- Spotify Web API ---

    def search_tracks(self, keyword):
        parsed = self._get_json(
            "/search",
            SpotifySearchResponse,
            params={"q": keyword, "type": "track", "limit": SEARCH_LIMIT, "market": SPOTIFY_MARKET},
        )
        return parsed.tracks.items

    def get_track(self, track_id):
        return self._get_json(f"/tracks/{track_id}", SpotifyTrack, params={"market": SPOTIFY_MARKET})

    def _ensure_token(self, rejected_token=None):
        if not self.client_id or not self.client_secret:
            raise SpotifyConfigurationError

        self._raise_if_rate_limited()
        now = time.monotonic()
        if rejected_token is None and self._access_token and now < self._token_expires_at:
            return self._access_token

        with self._token_lock:
            now = time.monotonic()
            token_is_valid = self._access_token and now < self._token_expires_at
            # lock 대기 중 다른 thread가 401을 받은 토큰을 교체했다면 새 토큰을 그대로 재사용한다.
            token_was_replaced = rejected_token is not None and self._access_token != rejected_token
            if token_is_valid and (rejected_token is None or token_was_replaced):
                return self._access_token

            # lock 대기 중 다른 thread가 cooldown을 시작했을 수 있으므로 token 요청 직전에 다시 확인한다.
            self._raise_if_rate_limited()
            try:
                response = requests.post(
                    SPOTIFY_AUTH_URL,
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"},
                    timeout=REQUEST_TIMEOUT,
                )
                if response.status_code == 429:
                    self._start_rate_limit_cooldown(response)
                    raise SpotifyRateLimitError
                response.raise_for_status()
                parsed = SpotifyTokenResponse.model_validate_json(response.content)
            except SpotifyRateLimitError:
                raise
            except (requests.RequestException, ValueError) as exc:
                raise SpotifyError from exc

            if not parsed.access_token or parsed.expires_in <= 0:
                raise SpotifyError

            self._access_token = parsed.access_token
            lifetime = max(1, parsed.expires_in - TOKEN_REFRESH_MARGIN)
            self._token_expires_at = now + lifetime
            return self._access_token

    def _get_json(self, path, model_cls, params):
        rejected_token = None
        for attempt in range(2):
            token = self._ensure_token(rejected_token=rejected_token)
            try:
                # token 조회 직후 다른 thread가 cooldown을 시작했을 수 있으므로 API 요청 직전에 다시 확인한다.
                self._raise_if_rate_limited()
                response = requests.get(
                    SPOTIFY_API_BASE_URL + path,
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )
                if response.status_code == 401 and attempt == 0:
                    # 인증 실패는 한 번만 재시도하며, 동시 요청은 rejected_token 비교로 갱신 결과를 공유한다.
                    rejected_token = token
                    continue
                if response.status_code == 429:
                    self._start_rate_limit_cooldown(response)
                    raise SpotifyRateLimitError
                response.raise_for_status()
                return model_cls.model_validate_json(response.content)
            except SpotifyRateLimitError:
                raise
            except (requests.RequestException, ValueError) as exc:
                raise SpotifyError from exc
        raise SpotifyError

    def _raise_if_rate_limited(self):
        with self._rate_limit_lock:
            if time.monotonic() < self._rate_limit_until:
                raise SpotifyRateLimitError

    def _start_rate_limit_cooldown(self, response):
        try:
            retry_after = max(DEFAULT_RATE_LIMIT_COOLDOWN, float(response.headers.get("Retry-After")))
        except (TypeError, ValueError):
            retry_after = DEFAULT_RATE_LIMIT_COOLDOWN

        with self._rate_limit_lock:
            self._rate_limit_until = max(self._rate_limit_until, time.monotonic() + retry_after)

    # --- Formatting and keyboards ---

    @staticmethod
    def _extract_keyword(text):
        parts = (text or "").split(maxsplit=1)
        return parts[1].strip() if len(parts) == 2 else ""

    @staticmethod
    def _artist_names(track):
        names = [artist.name for artist in track.artists if artist.name]
        return ", ".join(names) or strings.spotify_unknown_artist_msg

    @staticmethod
    def _track_name(track):
        name = track.name or strings.spotify_unknown_value_msg
        return f"{name} {strings.spotify_explicit_badge}" if track.explicit else name

    @staticmethod
    def _release_year(track):
        return track.album.release_date[:4] or strings.spotify_unknown_value_msg

    @staticmethod
    def _duration(duration_ms):
        minutes, seconds = divmod(max(0, duration_ms) // 1000, 60)
        return f"{minutes}:{seconds:02d}"

    @classmethod
    def _build_search_message(cls, keyword, tracks):
        entries = []
        for rank, track in enumerate(tracks, 1):
            label = f"{cls._track_name(track)} — {cls._artist_names(track)} · {cls._release_year(track)}"
            entries.append(
                strings.spotify_search_entry_msg.format(
                    rank=rank,
                    url=html.escape(track.external_urls.spotify, quote=True),
                    label=html.escape(label),
                )
            )
        header = strings.spotify_search_header_msg.format(keyword=html.escape(keyword))
        return header + "\n".join(entries) + strings.spotify_search_footer_msg

    @classmethod
    def _build_search_keyboard(cls, tracks):
        keyboard = telebot.types.InlineKeyboardMarkup()
        for rank, track in enumerate(tracks, 1):
            label = f"{rank}. {cls._track_name(track)} — {cls._artist_names(track)}"
            if len(label) > MAX_BUTTON_TEXT_LENGTH:
                label = label[: MAX_BUTTON_TEXT_LENGTH - 1] + "…"
            keyboard.row(telebot.types.InlineKeyboardButton(label, callback_data=f"{CALLBACK_PREFIX}:{track.id}"))
        return keyboard

    @classmethod
    def _build_detail_message(cls, track):
        return strings.spotify_detail_msg.format(
            name=html.escape(cls._track_name(track)),
            artists=html.escape(cls._artist_names(track)),
            album=html.escape(track.album.name or strings.spotify_unknown_value_msg),
            release_date=html.escape(track.album.release_date or strings.spotify_unknown_value_msg),
            duration=cls._duration(track.duration_ms),
        )

    @staticmethod
    def _build_open_keyboard(url):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(telebot.types.InlineKeyboardButton(strings.spotify_open_btn, url=url))
        return keyboard
