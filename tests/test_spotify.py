import json
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest
import requests

from modules.api_models import SpotifyAlbum, SpotifyAlbumImage, SpotifyArtist, SpotifyExternalUrls, SpotifyTrack
from modules.spotify import SpotifyConfigurationError, SpotifyError, SpotifyRateLimitError, SpotifyService
from resources import strings
from tests.conftest import make_message

TRACK_ID = "A" * 22


def _response(payload, status_code=200, headers=None):
    response = MagicMock()
    response.status_code = status_code
    response.content = json.dumps(payload).encode()
    response.headers = headers or {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
    return response


def _track(with_image=True, explicit=False):
    images = [SpotifyAlbumImage(url="https://i.scdn.co/image/test", width=300, height=300)] if with_image else []
    return SpotifyTrack(
        id=TRACK_ID,
        name="좋은 <날>",
        artists=[SpotifyArtist(name="아이유")],
        album=SpotifyAlbum(name="REAL & TEST", release_date="2010-12-09", images=images),
        duration_ms=233_000,
        explicit=explicit,
        external_urls=SpotifyExternalUrls(spotify="https://open.spotify.com/track/test"),
    )


def _service(**kwargs):
    return SpotifyService(
        MagicMock(),
        client_id=kwargs.get("client_id", "client"),
        client_secret=kwargs.get("client_secret", "secret"),
    )


class TestTokenManagement:
    @patch("modules.spotify.requests.post")
    def test_token_is_cached(self, mock_post):
        mock_post.return_value = _response({"access_token": "token", "token_type": "Bearer", "expires_in": 3600})
        service = _service()

        assert service._ensure_token() == "token"
        assert service._ensure_token() == "token"
        mock_post.assert_called_once()

    def test_missing_credentials_shows_unavailable_message(self):
        service = _service(client_id="", client_secret="")
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_unavailable_error_msg)

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_concurrent_401_refreshes_token_once(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "new-token", "expires_in": 3600})
        service = _service()
        service._access_token = "old-token"
        service._token_expires_at = float("inf")
        barrier = threading.Barrier(2)

        def get_response(*args, **kwargs):
            if kwargs["headers"] == {"Authorization": "Bearer old-token"}:
                # 두 worker가 모두 구 토큰으로 401을 받은 뒤 token refresh 경쟁에 진입하게 한다.
                barrier.wait(timeout=2)
                return _response({}, status_code=401)
            return _response(_track().model_dump())

        mock_get.side_effect = get_response

        with ThreadPoolExecutor(max_workers=2) as executor:
            tracks = list(executor.map(lambda _: service.get_track(TRACK_ID), range(2)))

        assert [track.id for track in tracks] == [TRACK_ID, TRACK_ID]
        mock_post.assert_called_once()

    @patch("modules.spotify.requests.post")
    def test_token_lock_rechecks_cooldown_before_request(self, mock_post):
        service = _service()
        first_check_completed = threading.Event()
        original_check = service._raise_if_rate_limited
        check_count = 0

        def tracked_check():
            nonlocal check_count
            original_check()
            check_count += 1
            if check_count == 1:
                first_check_completed.set()

        service._raise_if_rate_limited = tracked_check

        with ThreadPoolExecutor(max_workers=1) as executor:
            with service._token_lock:
                future = executor.submit(service._ensure_token)
                assert first_check_completed.wait(timeout=5)
                with service._rate_limit_lock:
                    service._rate_limit_until = float("inf")

            with pytest.raises(SpotifyRateLimitError):
                future.result(timeout=5)

        mock_post.assert_not_called()

    @pytest.mark.parametrize(
        "payload",
        [
            {"access_token": "", "expires_in": 3600},
            {"access_token": "token", "expires_in": 0},
        ],
    )
    @patch("modules.spotify.requests.post")
    def test_invalid_token_response_is_rejected(self, mock_post, payload):
        mock_post.return_value = _response(payload)
        service = _service()

        with pytest.raises(SpotifyError):
            service._ensure_token()

        assert service._access_token is None


class TestSpotifyAPI:
    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_search_tracks(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "token", "expires_in": 3600})
        mock_get.return_value = _response({"tracks": {"items": [_track(explicit=True).model_dump()]}})
        service = _service()

        tracks = service.search_tracks("아이유 좋은 날")

        assert tracks[0].id == TRACK_ID
        assert tracks[0].explicit is True
        assert mock_get.call_args.kwargs["params"] == {
            "q": "아이유 좋은 날",
            "type": "track",
            "limit": 5,
            "market": "KR",
        }

    @patch("modules.spotify.requests.get")
    def test_get_track_uses_expected_endpoint_and_options(self, mock_get):
        mock_get.return_value = _response(_track().model_dump())
        service = _service()
        service._access_token = "token"
        service._token_expires_at = float("inf")

        track = service.get_track(TRACK_ID)

        assert track.id == TRACK_ID
        mock_get.assert_called_once_with(
            f"https://api.spotify.com/v1/tracks/{TRACK_ID}",
            headers={"Authorization": "Bearer token"},
            params={"market": "KR"},
            timeout=10,
        )

    @patch("modules.spotify.requests.get")
    def test_cooldown_started_after_token_lookup_blocks_api_request(self, mock_get):
        service = _service()

        def start_cooldown(rejected_token=None):
            with service._rate_limit_lock:
                service._rate_limit_until = float("inf")
            return "token"

        service._ensure_token = MagicMock(side_effect=start_cooldown)

        with pytest.raises(SpotifyRateLimitError):
            service.search_tracks("test")

        mock_get.assert_not_called()

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_401_refreshes_token_once(self, mock_post, mock_get):
        mock_post.side_effect = [
            _response({"access_token": "old-token", "expires_in": 3600}),
            _response({"access_token": "new-token", "expires_in": 3600}),
        ]
        mock_get.side_effect = [
            _response({}, status_code=401),
            _response(_track().model_dump()),
        ]
        service = _service()

        track = service.get_track(TRACK_ID)

        assert track.id == TRACK_ID
        assert mock_post.call_count == 2
        assert mock_get.call_args_list[1].kwargs["headers"] == {"Authorization": "Bearer new-token"}

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_second_401_stops_after_single_refresh(self, mock_post, mock_get):
        mock_post.side_effect = [
            _response({"access_token": "old-token", "expires_in": 3600}),
            _response({"access_token": "new-token", "expires_in": 3600}),
        ]
        mock_get.side_effect = [_response({}, status_code=401), _response({}, status_code=401)]
        service = _service()

        with pytest.raises(SpotifyError):
            service.get_track(TRACK_ID)

        assert mock_post.call_count == 2
        assert mock_get.call_count == 2

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    @patch("modules.spotify.time.monotonic")
    def test_rate_limit_honors_retry_after_and_resumes(self, mock_monotonic, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "token", "expires_in": 3600})
        mock_get.side_effect = [
            _response({}, status_code=429, headers={"Retry-After": "30"}),
            _response({"tracks": {"items": [_track().model_dump()]}}),
        ]
        mock_monotonic.return_value = 100
        service = _service()

        with pytest.raises(SpotifyRateLimitError):
            service.search_tracks("test")

        assert service._rate_limit_until == 130
        mock_monotonic.return_value = 129
        with pytest.raises(SpotifyRateLimitError):
            service.search_tracks("test")

        mock_monotonic.return_value = 130
        tracks = service.search_tracks("test")

        assert tracks[0].id == TRACK_ID
        assert mock_get.call_count == 2

    @pytest.mark.parametrize("headers", [{}, {"Retry-After": "invalid"}])
    @patch("modules.spotify.time.monotonic", return_value=100)
    def test_rate_limit_uses_default_for_missing_or_invalid_header(self, mock_monotonic, headers):
        service = _service()

        service._start_rate_limit_cooldown(_response({}, status_code=429, headers=headers))

        assert service._rate_limit_until == 101
        mock_monotonic.assert_called_once()

    @patch("modules.spotify.time.monotonic", return_value=200)
    @patch("modules.spotify.requests.post")
    def test_auth_rate_limit_starts_cooldown(self, mock_post, mock_monotonic):
        mock_post.return_value = _response({}, status_code=429, headers={"Retry-After": "15"})
        service = _service()

        with pytest.raises(SpotifyRateLimitError):
            service._ensure_token()
        with pytest.raises(SpotifyRateLimitError):
            service._ensure_token()

        assert service._rate_limit_until == 215
        mock_post.assert_called_once()


class TestSearchHandler:
    def test_empty_keyword_shows_help(self):
        service = _service()
        message = make_message("/spotify")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_help_msg)

    def test_no_results(self):
        service = _service()
        service.search_tracks = MagicMock(return_value=[])
        message = make_message("/spotify unknown")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_no_result_msg)

    def test_rate_limit_shows_rate_limit_error(self):
        service = _service()
        service.search_tracks = MagicMock(side_effect=SpotifyRateLimitError)
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_rate_limit_error_msg)

    def test_search_result_contains_links_and_callbacks(self):
        service = _service()
        service.search_tracks = MagicMock(return_value=[_track(explicit=True)])
        message = make_message("/spotify 아이유 <좋은 날>")

        service.search_handler(message)

        call = service.bot.reply_to.call_args
        text = call.args[1]
        assert "아이유 &lt;좋은 날&gt;" in text
        assert "좋은 &lt;날&gt;" in text
        assert strings.spotify_explicit_badge in text
        assert "https://open.spotify.com/track/test" in text
        assert "콘텐츠 제공: Spotify" not in text
        assert "상세 정보를 볼 곡을 선택해 주세요." in text
        assert call.kwargs["parse_mode"] == "HTML"
        buttons = [button for row in call.kwargs["reply_markup"].keyboard for button in row]
        assert strings.spotify_explicit_badge in buttons[0].text
        assert buttons[0].callback_data == f"spotify_track:{TRACK_ID}"

    def test_invalid_track_id_is_excluded(self):
        service = _service()
        track = _track()
        track.id = "A" * 51
        service.search_tracks = MagicMock(return_value=[track])
        message = make_message("/spotify invalid")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_no_result_msg)

    def test_long_button_label_is_truncated_without_changing_callback(self):
        service = _service()
        track = _track()
        track.name = "아주 긴 곡 제목" * 20
        service.search_tracks = MagicMock(return_value=[track])
        message = make_message("/spotify 긴 노래")

        service.search_handler(message)

        button = service.bot.reply_to.call_args.kwargs["reply_markup"].keyboard[0][0]
        assert len(button.text) == 60
        assert button.text.endswith("…")
        assert button.callback_data == f"spotify_track:{TRACK_ID}"

    @patch("modules.spotify.requests.post")
    def test_auth_http_error_shows_search_error(self, mock_post):
        mock_post.return_value = _response({}, status_code=500)
        service = _service()
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_error_msg)

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_search_http_error_shows_search_error(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "token", "expires_in": 3600})
        mock_get.return_value = _response({}, status_code=500)
        service = _service()
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_error_msg)

    @patch("modules.spotify.requests.get")
    @patch("modules.spotify.requests.post")
    def test_malformed_json_shows_search_error(self, mock_post, mock_get):
        mock_post.return_value = _response({"access_token": "token", "expires_in": 3600})
        mock_get.return_value = _response({})
        mock_get.return_value.content = b"not-json"
        service = _service()
        message = make_message("/spotify 아이유")

        service.search_handler(message)

        service.bot.reply_to.assert_called_once_with(message, strings.spotify_error_msg)


class TestTrackCallback:
    def test_detail_sends_original_artwork_and_open_link(self):
        service = _service()
        service.get_track = MagicMock(return_value=_track(explicit=True))
        call = MagicMock()
        call.data = f"spotify_track:{TRACK_ID}"
        call.message.chat.id = 123

        service.handle_spotify_callback(call)

        sent = service.bot.send_photo.call_args
        assert sent.args[:2] == (123, "https://i.scdn.co/image/test")
        assert "좋은 &lt;날&gt;" in sent.kwargs["caption"]
        assert strings.spotify_explicit_badge in sent.kwargs["caption"]
        assert "REAL &amp; TEST" in sent.kwargs["caption"]
        button = sent.kwargs["reply_markup"].keyboard[0][0]
        assert button.text == "Spotify에서 열기"
        assert button.url == "https://open.spotify.com/track/test"

    def test_artwork_send_failure_falls_back_to_text(self):
        service = _service()
        service.get_track = MagicMock(return_value=_track())
        service.bot.send_photo.side_effect = Exception("Telegram image fetch failed")
        call = MagicMock()
        call.data = f"spotify_track:{TRACK_ID}"
        call.message.chat.id = 123

        service.handle_spotify_callback(call)

        service.bot.send_message.assert_called_once()
        assert service.bot.send_message.call_args.args[0] == 123
        assert "콘텐츠 제공: Spotify" not in service.bot.send_message.call_args.args[1]

    def test_track_without_artwork_sends_text_detail(self):
        service = _service()
        service.get_track = MagicMock(return_value=_track(with_image=False))
        call = MagicMock()
        call.data = f"spotify_track:{TRACK_ID}"
        call.message.chat.id = 123

        service.handle_spotify_callback(call)

        service.bot.send_photo.assert_not_called()
        sent = service.bot.send_message.call_args
        assert sent.args[0] == 123
        assert "좋은 &lt;날&gt;" in sent.args[1]
        button = sent.kwargs["reply_markup"].keyboard[0][0]
        assert button.text == "Spotify에서 열기"
        assert button.url == "https://open.spotify.com/track/test"

    @pytest.mark.parametrize(
        ("error", "expected_message"),
        [
            (SpotifyConfigurationError(), strings.spotify_unavailable_error_msg),
            (SpotifyRateLimitError(), strings.spotify_rate_limit_error_msg),
            (SpotifyError(), strings.spotify_track_unavailable_error_msg),
        ],
    )
    def test_lookup_error_shows_expected_message(self, error, expected_message):
        service = _service()
        service.get_track = MagicMock(side_effect=error)
        call = MagicMock()
        call.data = f"spotify_track:{TRACK_ID}"
        call.message.chat.id = 123

        service.handle_spotify_callback(call)

        service.bot.send_message.assert_called_once_with(123, expected_message)
        service.bot.send_photo.assert_not_called()

    def test_track_without_spotify_url_shows_unavailable_message(self):
        service = _service()
        track = _track()
        track.external_urls.spotify = ""
        service.get_track = MagicMock(return_value=track)
        call = MagicMock()
        call.data = f"spotify_track:{TRACK_ID}"
        call.message.chat.id = 123

        service.handle_spotify_callback(call)

        service.bot.send_message.assert_called_once_with(123, strings.spotify_track_unavailable_error_msg)
        service.bot.send_photo.assert_not_called()

    def test_invalid_callback_is_ignored(self):
        service = _service()
        call = MagicMock()
        call.data = "spotify_track:not-valid"

        service.handle_spotify_callback(call)

        service.bot.send_photo.assert_not_called()
        service.bot.send_message.assert_not_called()


class TestCallbackDetection:
    @pytest.mark.parametrize("value", [f"spotify_track:{TRACK_ID}", "spotify_track:A", "spotify_track:" + "z" * 50])
    def test_spotify_callback(self, value):
        assert SpotifyService.is_spotify_callback(value) is True

    @pytest.mark.parametrize(
        "value",
        [None, "", "spotify", "spotify_track:", "spotify_track:" + "z" * 51, "spotify_track:invalid-id"],
    )
    def test_non_spotify_callback(self, value):
        assert SpotifyService.is_spotify_callback(value) is False
