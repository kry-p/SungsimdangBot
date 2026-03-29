import datetime
from unittest.mock import MagicMock, patch

from modules.api_models import LaftelAnime
from modules.laftel import CACHE_INTERVAL, DAY_CODES, DAYS_OF_WEEK, LaftelService
from resources import strings

SAMPLE_SCHEDULE = [
    {
        "id": 1,
        "name": "테스트 애니 A",
        "distributed_air_time": "월요일",
        "genres": ["액션", "판타지"],
        "content_rating": "15세 이용가",
    },
    {
        "id": 2,
        "name": "테스트 애니 B",
        "distributed_air_time": "월요일",
        "genres": ["로맨스"],
        "content_rating": "12세 이용가",
    },
    {
        "id": 3,
        "name": "테스트 애니 C",
        "distributed_air_time": "금요일",
        "genres": ["스릴러"],
        "content_rating": "성인 이용가",
    },
]


def _make_service(**overrides):
    with patch.object(LaftelService, "__init__", lambda self, *a: None):
        svc = LaftelService()
        svc.bot = MagicMock()
        svc._schedule_cache = None
        svc._last_fetch_time = None
        for k, v in overrides.items():
            setattr(svc, k, v)
        return svc


class TestFetchDailySchedule:
    @patch("modules.laftel.requests.get")
    def test_success_groups_by_day(self, mock_get):
        import json

        response = MagicMock()
        response.content = json.dumps(SAMPLE_SCHEDULE).encode()
        mock_get.return_value = response

        svc = _make_service()
        svc._fetch_daily_schedule()

        assert "월요일" in svc._schedule_cache
        assert len(svc._schedule_cache["월요일"]) == 2
        assert "금요일" in svc._schedule_cache
        assert len(svc._schedule_cache["금요일"]) == 1
        assert svc._last_fetch_time is not None

    @patch("modules.laftel.requests.get")
    def test_api_failure_sets_empty_cache(self, mock_get):
        mock_get.side_effect = Exception("connection error")

        svc = _make_service()
        svc._fetch_daily_schedule()

        assert svc._schedule_cache == {}

    @patch("modules.laftel.requests.get")
    def test_stale_cache_preserved_on_error(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        old_cache = {"월요일": [{"name": "old"}]}

        svc = _make_service(_schedule_cache=old_cache, _last_fetch_time=datetime.datetime(2020, 1, 1))
        svc._fetch_daily_schedule()

        assert svc._schedule_cache is old_cache

    @patch("modules.laftel.requests.get")
    def test_cache_not_expired_skips_fetch(self, mock_get):
        svc = _make_service(
            _schedule_cache={"월요일": []},
            _last_fetch_time=datetime.datetime.now() - datetime.timedelta(seconds=100),
        )
        svc._fetch_daily_schedule()

        mock_get.assert_not_called()

    @patch("modules.laftel.requests.get")
    def test_cache_expired_refetches(self, mock_get):
        response = MagicMock()
        response.content = b"[]"
        mock_get.return_value = response

        svc = _make_service(
            _schedule_cache={"월요일": []},
            _last_fetch_time=datetime.datetime.now() - datetime.timedelta(seconds=CACHE_INTERVAL + 1),
        )
        svc._fetch_daily_schedule()

        mock_get.assert_called_once()


class TestGetScheduleByDay:
    def test_normal_output(self):
        cache = {
            "월요일": [
                LaftelAnime(
                    id=1, name="애니A", genres=["액션", "판타지"], content_rating="15세 이용가", is_laftel_only=True
                ),
                LaftelAnime(
                    id=2, name="애니B", genres=["로맨스"], content_rating="성인 이용가", is_ending=True, is_dubbed=True
                ),
            ]
        }
        svc = _make_service(_schedule_cache=cache, _last_fetch_time=datetime.datetime.now())
        result = svc._get_schedule_by_day("월요일")

        assert "월요일 신작 편성표" in result
        assert "애니A" in result
        assert "애니B" in result
        assert "액션, 판타지" in result
        assert "15+" in result
        assert "19+" in result
        assert "독점" in result
        assert "완결" in result
        assert "더빙" in result
        assert "총 2개" in result
        assert "laftel.net/item/1" in result

    def test_empty_day(self):
        svc = _make_service(_schedule_cache={}, _last_fetch_time=datetime.datetime.now())
        result = svc._get_schedule_by_day("월요일")

        assert strings.laftel_schedule_empty_msg.format("월요일") == result

    def test_truncation_on_long_list(self):
        items = [
            LaftelAnime(
                id=i,
                name=f"매우 긴 제목의 애니메이션 {i}",
                genres=["장르A", "장르B", "장르C"],
                content_rating="15세 이용가",
            )
            for i in range(200)
        ]
        svc = _make_service(_schedule_cache={"월요일": items}, _last_fetch_time=datetime.datetime.now())
        result = svc._get_schedule_by_day("월요일")

        assert len(result) <= 4096
        assert strings.laftel_schedule_truncated_msg in result


class TestTodayResolution:
    def test_each_weekday(self):
        from modules.laftel import DAY_CODE_KEYS

        for i, day in enumerate(DAYS_OF_WEEK):
            code = DAY_CODE_KEYS[i]
            assert DAY_CODES[code] == day

    @patch("modules.laftel.datetime")
    def test_today_resolves_correct_day(self, mock_dt):
        mock_dt.datetime.now.return_value.weekday.return_value = 4  # Friday

        svc = _make_service()
        svc._get_schedule_by_day = MagicMock(return_value="금요일 편성표")

        call = MagicMock()
        call.data = "laftel_schedule:today"
        call.message.chat.id = 1
        call.message.message_id = 1

        svc._handle_schedule(call, "today")
        svc._get_schedule_by_day.assert_called_once_with("금요일")


class TestBuildKeyboards:
    def test_portal_keyboard_has_schedule_button(self):
        keyboard = LaftelService._build_portal_keyboard()
        buttons = [btn for row in keyboard.keyboard for btn in row]
        assert any(btn.callback_data == "laftel_menu:schedule" for btn in buttons)
        assert any(btn.text == strings.laftel_schedule_btn for btn in buttons)

    def test_day_selection_has_all_days(self):
        keyboard = LaftelService._build_day_selection_keyboard()
        buttons = [btn for row in keyboard.keyboard for btn in row]
        callback_data_set = {btn.callback_data for btn in buttons}

        for code in DAY_CODES:
            assert f"laftel_schedule:{code}" in callback_data_set
        assert len(buttons) == 7

    @patch("modules.laftel.datetime")
    def test_today_is_highlighted(self, mock_dt):
        mock_dt.datetime.now.return_value.weekday.return_value = 2  # Wednesday
        keyboard = LaftelService._build_day_selection_keyboard()
        buttons = [btn for row in keyboard.keyboard for btn in row]
        assert buttons[2].text == "[수]"
        assert buttons[0].text == "월"


class TestIsLaftelCallback:
    def test_valid_prefixes(self):
        assert LaftelService.is_laftel_callback("laftel_menu:portal") is True
        assert LaftelService.is_laftel_callback("laftel_menu:schedule") is True
        assert LaftelService.is_laftel_callback("laftel_schedule:mon") is True

    def test_invalid_data(self):
        assert LaftelService.is_laftel_callback("admin_confirm:123") is False
        assert LaftelService.is_laftel_callback("random_string") is False
        assert LaftelService.is_laftel_callback("") is False
        assert LaftelService.is_laftel_callback(None) is False


class TestHandleLaftelCallback:
    @patch("modules.laftel.datetime")
    def test_menu_schedule_shows_today_schedule(self, mock_dt):
        mock_dt.datetime.now.return_value.weekday.return_value = 4  # Friday

        svc = _make_service()
        svc._get_schedule_by_day = MagicMock(return_value="금요일 편성표")

        call = MagicMock()
        call.data = "laftel_menu:schedule"
        call.message.chat.id = 1
        call.message.message_id = 1

        svc.handle_laftel_callback(call)

        svc._get_schedule_by_day.assert_called_once_with("금요일")
        svc.bot.edit_message_text.assert_called_once()
        assert svc.bot.edit_message_text.call_args[1]["reply_markup"] is not None

    def test_schedule_day_shows_formatted_text(self):
        cache = {"월요일": [LaftelAnime(id=1, name="테스트", genres=["액션"], content_rating="15세 이용가")]}
        svc = _make_service(_schedule_cache=cache, _last_fetch_time=datetime.datetime.now())

        call = MagicMock()
        call.data = "laftel_schedule:mon"
        call.message.chat.id = 1
        call.message.message_id = 1

        svc.handle_laftel_callback(call)

        args = svc.bot.edit_message_text.call_args
        assert "테스트" in args[0][0]
        assert "월요일" in args[0][0]

    def test_portal_callback_shows_portal(self):
        svc = _make_service()
        call = MagicMock()
        call.data = "laftel_menu:portal"
        call.message.chat.id = 1
        call.message.message_id = 1

        svc.handle_laftel_callback(call)

        args = svc.bot.edit_message_text.call_args
        assert args[0][0] == strings.laftel_portal_msg

    def test_show_portal_sends_message(self):
        svc = _make_service()
        svc.show_portal(123)

        svc.bot.send_message.assert_called_once()
        args = svc.bot.send_message.call_args
        assert args[0][0] == 123
        assert args[0][1] == strings.laftel_portal_msg
