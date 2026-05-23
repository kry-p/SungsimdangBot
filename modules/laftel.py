import datetime
import time
import urllib.parse

import requests
import telebot
from pydantic import TypeAdapter

from modules import log
from modules.api_models import LaftelAnime, LaftelSearchResponse
from resources import strings

logger = log.Logger()

LAFTEL_BASE_URL = "https://laftel.net/api/"
LAFTEL_HEADERS = {"laftel": "TeJava"}
CACHE_INTERVAL = 3600
MAX_MESSAGE_LENGTH = 4096
SEARCH_INPUT_TIMEOUT = 300

SETTINGS_MODULE_PATH = "modules.laftel"

CALLBACK_PREFIXES = frozenset({"laftel_menu", "laftel_schedule", "laftel_ranking"})

RANKING_TYPES = {
    "week": "주간",
    "quarter": "분기",
    "history": "역대",
}

DAYS_OF_WEEK = ("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일")
DAY_CODES = {
    "mon": "월요일",
    "tue": "화요일",
    "wed": "수요일",
    "thu": "목요일",
    "fri": "금요일",
    "sat": "토요일",
    "sun": "일요일",
}
RATING_LABELS = {
    "전체 이용가": "ALL",
    "7세 이용가": "7+",
    "12세 이용가": "12+",
    "15세 이용가": "15+",
    "성인 이용가": "19+",
}
DAY_SHORT_LABELS = ("월", "화", "수", "목", "금", "토", "일")
DAY_CODE_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _escape_markdown(text):
    for ch in ("*", "_", "`", "["):
        text = text.replace(ch, "\\" + ch)
    return text


def _format_entry(item, rank=None):
    """LaftelAnime 항목을 포맷팅된 엔트리 문자열로 변환한다."""
    genres = _escape_markdown(", ".join(item.genres or []))
    rating = RATING_LABELS.get(item.content_rating or "", item.content_rating or "")

    tags = []
    if item.is_laftel_only or item.is_exclusive:
        tags.append("[독점]")
    if item.is_dubbed:
        tags.append("[더빙]")
    if item.is_ending:
        tags.append("[완결]")
    tags_str = _escape_markdown(" ".join(tags))

    if rank is not None:
        return strings.laftel_ranking_entry_msg.format(
            rank=rank,
            name=_escape_markdown(item.name or ""),
            genres=genres,
            rating=rating,
            tags=tags_str,
            item_id=item.id,
        )
    return strings.laftel_schedule_entry_msg.format(
        name=_escape_markdown(item.name or ""),
        genres=genres,
        rating=rating,
        tags=tags_str,
        item_id=item.id,
    )


class LaftelService:
    def __init__(self, bot):
        self.bot = bot
        # 캐시: GIL이 참조 할당의 원자성을 보장하므로 별도 락 불필요 (WebManager 동일 패턴)
        self._schedule_cache = None
        self._last_fetch_time = None
        self._ranking_cache = {}
        self._ranking_fetch_time = {}
        self._pending_search = None

    # --- 콜백 라우팅 ---

    @staticmethod
    def is_laftel_callback(data):
        return bool(data and ":" in data and data.split(":")[0] in CALLBACK_PREFIXES)

    def handle_laftel_callback(self, call):
        action, value = call.data.split(":", 1)
        if action == "laftel_menu":
            self._handle_menu(call, value)
        elif action == "laftel_schedule":
            self._handle_schedule(call, value)
        elif action == "laftel_ranking":
            self._handle_ranking(call, value)

    def _handle_menu(self, call, value):
        if value == "portal":
            self.bot.edit_message_text(
                strings.laftel_portal_msg,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=self._build_portal_keyboard(),
            )
        elif value == "schedule":
            today_code = DAY_CODE_KEYS[datetime.datetime.now().weekday()]
            today_name = DAY_CODES[today_code]
            result = self._get_schedule_by_day(today_name)
            self.bot.edit_message_text(
                result,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=self._build_day_selection_keyboard(),
            )
        elif value == "ranking":
            result = self._get_ranking("week")
            self.bot.edit_message_text(
                result,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown",
                reply_markup=self._build_ranking_type_keyboard(),
            )
        elif value == "search":
            self._pending_search = (call.from_user.id, call.message.chat.id, time.time())
            self.bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            self.bot.send_message(
                call.message.chat.id,
                strings.laftel_search_input_msg,
                reply_markup=telebot.types.ForceReply(selective=True),
            )

    def _handle_schedule(self, call, value):
        day = value
        if day == "today":
            day = DAY_CODE_KEYS[datetime.datetime.now().weekday()]
        day_name = DAY_CODES.get(day)
        if not day_name:
            return
        result = self._get_schedule_by_day(day_name)
        self.bot.edit_message_text(
            result,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=self._build_day_selection_keyboard(),
        )

    def _handle_ranking(self, call, value):
        if value not in RANKING_TYPES:
            return
        result = self._get_ranking(value)
        self.bot.edit_message_text(
            result,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=self._build_ranking_type_keyboard(),
        )

    # --- 포털 ---

    def show_portal(self, chat_id):
        self.bot.send_message(
            chat_id,
            strings.laftel_portal_msg,
            reply_markup=self._build_portal_keyboard(),
        )

    # --- 유틸리티 ---

    @staticmethod
    def _truncate_message(header, entries, footer):
        """메시지가 MAX_MESSAGE_LENGTH를 초과하면 항목을 잘라서 반환한다."""
        text = header + "".join(entries) + footer
        if len(text) > MAX_MESSAGE_LENGTH:
            truncated = header
            for entry in entries:
                remaining = len(footer) + len(strings.laftel_schedule_truncated_msg)
                if len(truncated) + len(entry) + remaining > MAX_MESSAGE_LENGTH:
                    break
                truncated += entry
            text = truncated + strings.laftel_schedule_truncated_msg + "\n" + footer
        return text

    # --- 키보드 ---

    @staticmethod
    def _build_portal_keyboard():
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.laftel_schedule_btn, callback_data="laftel_menu:schedule"),
            telebot.types.InlineKeyboardButton(strings.laftel_ranking_btn, callback_data="laftel_menu:ranking"),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.laftel_search_btn, callback_data="laftel_menu:search"),
        )
        return keyboard

    @staticmethod
    def _build_day_selection_keyboard():
        today_idx = datetime.datetime.now().weekday()
        keyboard = telebot.types.InlineKeyboardMarkup()
        buttons = []
        for i, (label, code) in enumerate(zip(DAY_SHORT_LABELS, DAY_CODE_KEYS, strict=True)):
            text = f"[{label}]" if i == today_idx else label
            buttons.append(telebot.types.InlineKeyboardButton(text, callback_data=f"laftel_schedule:{code}"))
        keyboard.row(*buttons)
        return keyboard

    # --- 편성표 데이터 ---

    def _fetch_daily_schedule(self):
        now = datetime.datetime.now()
        if self._schedule_cache is not None and self._last_fetch_time:
            elapsed = (now - self._last_fetch_time).total_seconds()
            if elapsed < CACHE_INTERVAL:
                return

        try:
            response = requests.get(
                LAFTEL_BASE_URL + "search/v2/daily/",
                headers=LAFTEL_HEADERS,
                timeout=10,
            )
            anime_list = TypeAdapter(list[LaftelAnime]).validate_json(response.content)
            grouped = {}
            for item in anime_list:
                day = item.distributed_air_time or ""
                if day not in grouped:
                    grouped[day] = []
                grouped[day].append(item)
            self._schedule_cache = grouped
            self._last_fetch_time = now
        except Exception:
            logger.log_error("Failed to fetch Laftel daily schedule.")
            if self._schedule_cache is None:
                self._schedule_cache = {}

    def _get_schedule_by_day(self, day_name):
        self._fetch_daily_schedule()

        items = self._schedule_cache.get(day_name, [])
        if not items:
            return strings.laftel_schedule_empty_msg.format(day_name)

        header = strings.laftel_schedule_header_msg.format(day_name)
        entries = [_format_entry(item) for item in items]
        footer = strings.laftel_schedule_footer_msg.format(len(items))

        return self._truncate_message(header, entries, footer)

    # --- 랭킹 데이터 ---

    def _fetch_ranking(self, ranking_type):
        now = datetime.datetime.now()
        fetch_time = self._ranking_fetch_time.get(ranking_type)
        if ranking_type in self._ranking_cache and fetch_time:
            elapsed = (now - fetch_time).total_seconds()
            if elapsed < CACHE_INTERVAL:
                return

        try:
            response = requests.get(
                LAFTEL_BASE_URL + f"home/v1/recommend/ranking?type={ranking_type}",
                headers=LAFTEL_HEADERS,
                timeout=10,
            )
            anime_list = TypeAdapter(list[LaftelAnime]).validate_json(response.content)
            self._ranking_cache[ranking_type] = anime_list
            self._ranking_fetch_time[ranking_type] = now
        except Exception:
            logger.log_error(f"Failed to fetch Laftel ranking (type={ranking_type}).")
            if ranking_type not in self._ranking_cache:
                self._ranking_cache[ranking_type] = []

    def _get_ranking(self, ranking_type):
        self._fetch_ranking(ranking_type)

        items = self._ranking_cache.get(ranking_type, [])
        type_label = RANKING_TYPES.get(ranking_type, ranking_type)
        if not items:
            return strings.laftel_ranking_empty_msg

        header = strings.laftel_ranking_header_msg.format(type_label)
        entries = [_format_entry(item, rank=rank) for rank, item in enumerate(items, 1)]
        footer = strings.laftel_ranking_footer_msg.format(len(items))

        return self._truncate_message(header, entries, footer)

    @staticmethod
    def _build_ranking_type_keyboard():
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            *[
                telebot.types.InlineKeyboardButton(label, callback_data=f"laftel_ranking:{code}")
                for code, label in RANKING_TYPES.items()
            ]
        )
        return keyboard

    @staticmethod
    def _build_search_result_keyboard():
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(strings.laftel_search_again_btn, callback_data="laftel_menu:search"),
            telebot.types.InlineKeyboardButton(strings.laftel_portal_btn, callback_data="laftel_menu:portal"),
        )
        return keyboard

    # --- 검색 ---

    def handle_search_reply(self, message):
        if not self._pending_search:
            return
        user_id, chat_id, timestamp = self._pending_search
        if message.from_user.id != user_id or message.chat.id != chat_id:
            return
        if time.time() - timestamp > SEARCH_INPUT_TIMEOUT:
            self._pending_search = None
            return
        self._pending_search = None
        keyword = message.text.strip()
        if not keyword:
            self.bot.reply_to(message, strings.laftel_search_empty_input_msg)
            return
        result = self._search(keyword)
        self.bot.reply_to(message, result, parse_mode="Markdown", reply_markup=self._build_search_result_keyboard())

    def _search(self, keyword):
        try:
            url = LAFTEL_BASE_URL + "search/v3/keyword/?" + urllib.parse.urlencode({"keyword": keyword})
            response = requests.get(url, headers=LAFTEL_HEADERS, timeout=10)
            parsed = LaftelSearchResponse.model_validate_json(response.content)
        except Exception:
            logger.log_error(f"Failed to search Laftel (keyword={keyword}).")
            return strings.laftel_error_msg

        items = parsed.results
        if not items:
            return strings.laftel_search_empty_msg.format(_escape_markdown(keyword))

        header = strings.laftel_search_header_msg.format(_escape_markdown(keyword))
        entries = [_format_entry(item, rank=rank) for rank, item in enumerate(items, 1)]
        footer = strings.laftel_search_footer_msg.format(len(items))

        return self._truncate_message(header, entries, footer)
