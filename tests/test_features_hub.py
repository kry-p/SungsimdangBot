import datetime
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from modules.database import PendingAction
from modules.features_hub import BotFeaturesHub
from resources import strings


@pytest.fixture
def hub():
    bot = MagicMock()
    with patch("modules.features_hub.WebManager"), patch("modules.features_hub.GeminiChat"):
        h = BotFeaturesHub(bot)
    return h


def make_message(text, chat_id=1, user_id=1):
    msg = MagicMock()
    msg.text = text
    msg.chat.id = chat_id
    msg.from_user.id = user_id
    return msg


class TestDDay:
    def test_future_date(self, hub):
        future = datetime.date.today() + datetime.timedelta(days=10)
        msg = make_message(f"/dday {future.year} {future.month} {future.day}")
        hub.d_day(msg)
        hub.bot.reply_to.assert_called_once_with(msg, "10" + strings.day_left_msg)

    def test_past_date(self, hub):
        past = datetime.date.today() - datetime.timedelta(days=5)
        msg = make_message(f"/dday {past.year} {past.month} {past.day}")
        hub.d_day(msg)
        hub.bot.reply_to.assert_called_once_with(msg, "5" + strings.day_passed_msg)

    def test_today(self, hub):
        today = datetime.date.today()
        msg = make_message(f"/dday {today.year} {today.month} {today.day}")
        hub.d_day(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.day_dest_msg)

    def test_invalid_input_non_numeric(self, hub):
        msg = make_message("/dday abc")
        hub.d_day(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.day_out_of_range_msg)

    def test_invalid_input_out_of_range(self, hub):
        msg = make_message("/dday 2020 13 32")
        hub.d_day(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.day_out_of_range_msg)

    def test_missing_args(self, hub):
        msg = make_message("/dday")
        hub.d_day(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.day_out_of_range_msg)


class TestGetTemp:
    def test_normal_temperature(self, hub):
        hub.web_manager.provide_suon_v2.return_value = "23.5"
        result = hub.get_temp()
        assert result == strings.suon_result_msg.format("23.5")

    def test_maintenance(self, hub):
        hub.web_manager.provide_suon_v2.return_value = "점검중"
        result = hub.get_temp()
        assert result == strings.suon_unavailable_msg


class TestCalculatorHandler:
    def test_normal_calculation(self, hub):
        msg = make_message("/calc 2 + 3")
        hub.calculator_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, 5)

    def test_syntax_error(self, hub):
        msg = make_message("/calc abc")
        hub.calculator_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.calc_syntax_error_msg)

    def test_division_by_zero(self, hub):
        msg = make_message("/calc 1 / 0")
        hub.calculator_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.calc_division_by_zero_error_msg)

    def test_no_expression(self, hub):
        msg = make_message("/calc")
        hub.calculator_handler(msg)
        hub.bot.reply_to.assert_not_called()


class TestOrdinaryMessage:
    def test_suon_keyword_triggers_temp(self, hub):
        hub.web_manager.provide_suon_v2.return_value = "20.0"
        msg = make_message("오늘 수온 어때?")
        hub.ordinary_message(msg)
        hub.bot.reply_to.assert_called_once()
        assert "수온" in hub.bot.reply_to.call_args[0][1]

    def test_magic_conch_keyword(self, hub):
        msg = make_message("마법의 소라고동아 알려줘")
        hub.ordinary_message(msg)
        hub.bot.reply_to.assert_called_once()
        all_sentences = [s for group in strings.magic_conch_sentence for s in group]
        assert hub.bot.reply_to.call_args[0][1] in all_sentences

    def test_normal_message_no_action(self, hub):
        msg = make_message("안녕하세요")
        hub.ordinary_message(msg)
        hub.bot.reply_to.assert_not_called()
        hub.bot.send_message.assert_not_called()


class TestGeolocationInfo:
    @patch("modules.features_hub.config.WEATHER_TOKEN", "test_weather")
    @patch("modules.features_hub.config.KAKAO_TOKEN", "test_kakao")
    @patch("modules.features_hub.requests.get")
    def test_success(self, mock_get, hub):
        map_response = MagicMock()
        map_response.text = json.dumps({"documents": [{"address": {"address_name": "서울특별시 중구"}}]})

        weather_response = MagicMock()
        weather_response.text = json.dumps(
            {
                "weather": [{"description": "맑음"}],
                "main": {"temp": 293.15, "feels_like": 291.15, "humidity": 50},
            }
        )

        mock_get.side_effect = [map_response, weather_response]
        msg = make_message("location")
        hub.geolocation_info(msg, 37.5, 127.0)

        hub.bot.reply_to.assert_called_once()
        result = hub.bot.reply_to.call_args[0][1]
        assert "서울특별시 중구" in result
        assert "맑음" in result

    @patch("modules.features_hub.requests.get")
    def test_api_error(self, mock_get, hub):
        mock_get.side_effect = Exception("connection error")
        msg = make_message("location")
        hub.geolocation_info(msg, 37.5, 127.0)

        hub.bot.reply_to.assert_called_once_with(msg, strings.geolocation_error_msg)


class TestAskHandler:
    def test_empty_question(self, hub):
        msg = make_message("/ask")
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_empty_msg)

    def test_normal_question(self, hub):
        hub.gemini_chat.ask.return_value = ["답변입니다"]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.gemini_chat.ask.assert_called_once_with(1, 1, "질문", "ko")
        hub.bot.reply_to.assert_called_once_with(msg, "답변입니다")

    def test_split_response(self, hub):
        hub.gemini_chat.ask.return_value = ["part1", "part2"]
        msg = make_message("/ask 긴 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        assert hub.bot.reply_to.call_count == 2

    def test_not_allowed(self, hub):
        hub.gemini_chat.ask.return_value = [strings.ask_not_allowed_msg]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_not_allowed_msg)


class TestClearChatHandler:
    def test_clear(self, hub):
        msg = make_message("/clear_chat")
        hub.clear_chat_handler(msg)
        hub.gemini_chat.clear_session.assert_called_once_with(1, 1)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_clear_msg)


class TestAllowChatHandler:
    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_admin_allow_shows_confirmation(self, hub):
        msg = make_message("/allow_chat", chat_id=42, user_id=100)
        msg.chat.title = "테스트 채널"
        msg.chat.first_name = None
        hub.bot.reply_to.return_value.message_id = 999
        hub.bot.reply_to.return_value.chat.id = 42
        hub.allow_chat_handler(msg)
        hub.gemini_chat.allow_chat.assert_not_called()
        row = PendingAction.get_or_none(PendingAction.msg_id == 999)
        assert row is not None
        assert row.action == "allow"
        assert row.chat_id == 42

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_non_admin_rejected(self, hub):
        msg = make_message("/allow_chat", user_id=999)
        hub.allow_chat_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_only_msg)

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_invalid_argument(self, hub):
        msg = make_message("/allow_chat abc", user_id=100)
        hub.allow_chat_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_allow_usage_msg)


class TestDenyChatHandler:
    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_admin_deny_shows_confirmation(self, hub):
        hub.gemini_chat.is_chat_allowed.return_value = True
        hub.gemini_chat.get_chat_name.return_value = "테스트"
        msg = make_message("/deny_chat 42", user_id=100)
        hub.bot.reply_to.return_value.message_id = 888
        hub.bot.reply_to.return_value.chat.id = 1
        hub.deny_chat_handler(msg)
        hub.gemini_chat.deny_chat.assert_not_called()
        row = PendingAction.get_or_none(PendingAction.msg_id == 888)
        assert row is not None
        assert row.action == "deny"

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_deny_not_in_list(self, hub):
        hub.gemini_chat.is_chat_allowed.return_value = False
        msg = make_message("/deny_chat 42", user_id=100)
        hub.deny_chat_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_deny_chat_not_found_msg.format(chat_id=42))

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_non_admin_rejected(self, hub):
        msg = make_message("/deny_chat 42", user_id=999)
        hub.deny_chat_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_only_msg)


class TestAdminCallback:
    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_allow_confirm(self, hub):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="테스트", timestamp=time.time())
        call = MagicMock()
        call.from_user.id = 100
        call.data = "allow_confirm:999"
        hub.handle_admin_callback(call)
        hub.gemini_chat.allow_chat.assert_called_once_with(42, "테스트")
        hub.bot.edit_message_text.assert_called_once()
        assert PendingAction.get_or_none(PendingAction.msg_id == 999) is None

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_deny_confirm(self, hub):
        PendingAction.create(msg_id=888, action="deny", chat_id=42, name="테스트", timestamp=time.time())
        call = MagicMock()
        call.from_user.id = 100
        call.data = "deny_confirm:888"
        hub.handle_admin_callback(call)
        hub.gemini_chat.deny_chat.assert_called_once_with(42)
        hub.bot.edit_message_text.assert_called_once()

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_cancel(self, hub):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="테스트", timestamp=time.time())
        call = MagicMock()
        call.from_user.id = 100
        call.data = "allow_cancel:999"
        hub.handle_admin_callback(call)
        hub.gemini_chat.allow_chat.assert_not_called()
        hub.bot.edit_message_text.assert_called_once()
        assert PendingAction.get_or_none(PendingAction.msg_id == 999) is None

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_non_admin_ignored(self, hub):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="테스트", timestamp=time.time())
        call = MagicMock()
        call.from_user.id = 999
        call.data = "allow_confirm:999"
        hub.handle_admin_callback(call)
        hub.gemini_chat.allow_chat.assert_not_called()
        assert PendingAction.get_or_none(PendingAction.msg_id == 999) is not None

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_set_model_callback(self, hub):
        call = MagicMock()
        call.from_user.id = 100
        call.data = "set_model:gemini-2.5-pro"
        hub.handle_admin_callback(call)
        hub.gemini_chat.set_model.assert_called_once_with("gemini-2.5-pro")
        hub.bot.edit_message_text.assert_called_once()


class TestPendingExpiry:
    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_expired_entries_cleaned(self, hub):
        PendingAction.create(msg_id=1, action="allow", chat_id=10, name="old", timestamp=time.time() - 301)
        PendingAction.create(msg_id=2, action="deny", chat_id=20, name="fresh", timestamp=time.time())
        hub._cleanup_expired_pending()
        assert PendingAction.get_or_none(PendingAction.msg_id == 1) is None
        assert PendingAction.get_or_none(PendingAction.msg_id == 2) is not None

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_all_expired(self, hub):
        PendingAction.create(msg_id=1, action="allow", chat_id=10, name="a", timestamp=time.time() - 400)
        PendingAction.create(msg_id=2, action="deny", chat_id=20, name="b", timestamp=time.time() - 500)
        hub._cleanup_expired_pending()
        assert PendingAction.select().count() == 0

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_expired_callback_ignored(self, hub):
        PendingAction.create(msg_id=999, action="allow", chat_id=42, name="expired", timestamp=time.time() - 301)
        call = MagicMock()
        call.from_user.id = 100
        call.data = "allow_confirm:999"
        hub.handle_admin_callback(call)
        hub.gemini_chat.allow_chat.assert_not_called()


class TestCallbackDataLength:
    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_long_model_name_skipped(self, hub):
        long_name = "gemini-" + "x" * 60
        hub.gemini_chat.list_models.return_value = [long_name, "gemini-2.5-flash"]
        msg = make_message("/set_model", user_id=100)
        hub.set_model_handler(msg)
        call_kwargs = hub.bot.reply_to.call_args
        keyboard = call_kwargs.kwargs["reply_markup"]
        button_texts = [btn.text for row in keyboard.keyboard for btn in row]
        assert long_name not in button_texts
        assert "gemini-2.5-flash" in button_texts

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_all_models_too_long(self, hub):
        long_name = "gemini-" + "x" * 60
        hub.gemini_chat.list_models.return_value = [long_name]
        msg = make_message("/set_model", user_id=100)
        hub.set_model_handler(msg)
        hub.bot.reply_to.assert_called_with(msg, strings.set_model_error_msg)


class TestSetModelHandler:
    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_shows_model_list(self, hub):
        hub.gemini_chat.list_models.return_value = ["gemini-2.5-flash", "gemini-2.5-pro"]
        msg = make_message("/set_model", user_id=100)
        hub.set_model_handler(msg)
        call_kwargs = hub.bot.reply_to.call_args
        assert "reply_markup" in call_kwargs.kwargs

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_empty_model_list(self, hub):
        hub.gemini_chat.list_models.return_value = []
        msg = make_message("/set_model", user_id=100)
        hub.set_model_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.set_model_error_msg)

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_non_admin_rejected(self, hub):
        msg = make_message("/set_model", user_id=999)
        hub.set_model_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_only_msg)


class TestCurrentModelHandler:
    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_shows_current_model(self, hub):
        hub.gemini_chat.model = "gemini-2.5-flash"
        msg = make_message("/current_model", user_id=100)
        hub.current_model_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.current_model_msg.format(model="gemini-2.5-flash"))

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_non_admin_rejected(self, hub):
        msg = make_message("/current_model", user_id=999)
        hub.current_model_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_only_msg)


class TestListChatsHandler:
    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_admin_with_chats(self, hub):
        hub.gemini_chat.list_allowed_chats.return_value = [
            {"id": 1, "name": "A"},
            {"id": 2, "name": ""},
            {"id": 3, "name": "C"},
        ]
        msg = make_message("/list_chats", user_id=100)
        hub.list_chats_handler(msg)
        expected = "1 (A)\n2\n3 (C)"
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_list_chats_msg.format(expected))

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_admin_empty(self, hub):
        hub.gemini_chat.list_allowed_chats.return_value = []
        msg = make_message("/list_chats", user_id=100)
        hub.list_chats_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_list_chats_empty_msg)

    @patch("modules.features_hub.config.ADMIN_USER_ID", 100)
    def test_non_admin_rejected(self, hub):
        msg = make_message("/list_chats", user_id=999)
        hub.list_chats_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.admin_only_msg)
