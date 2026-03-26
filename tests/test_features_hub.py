import datetime
from unittest.mock import MagicMock, patch

import pytest

from modules.features_hub import BotFeaturesHub
from resources import strings
from tests.conftest import make_message


@pytest.fixture
def hub():
    bot = MagicMock()
    with (
        patch("modules.features_hub.WebManager"),
        patch("modules.features_hub.GeminiChat"),
        patch("modules.features_hub.AdminManager"),
    ):
        h = BotFeaturesHub(bot)
    return h


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
    def test_success(self, hub):
        hub.web_manager.geolocation_info.return_value = "위도 : 37.5, 경도 : 127.0\n서울특별시 중구\n\n날씨 맑음"
        msg = make_message("location")
        hub.geolocation_info(msg, 37.5, 127.0)
        hub.web_manager.geolocation_info.assert_called_once_with(37.5, 127.0)
        hub.bot.reply_to.assert_called_once_with(msg, hub.web_manager.geolocation_info.return_value)

    def test_api_error(self, hub):
        hub.web_manager.geolocation_info.side_effect = Exception("connection error")
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
        hub.gemini_chat.ask.assert_called_once_with(1, 1, "질문", "ko", None, None)
        hub.bot.reply_to.assert_called_once()
        call_kwargs = hub.bot.reply_to.call_args
        assert call_kwargs[0][1] == "답변입니다"
        assert "entities" in call_kwargs.kwargs

    def test_reply_with_context(self, hub):
        hub.gemini_chat.ask.return_value = ["요약입니다"]
        msg = make_message("/ask 이거 요약해줘", user_id=1)
        msg.from_user.language_code = "ko"
        msg.reply_to_message = MagicMock()
        msg.reply_to_message.text = "원본 메시지 내용"
        msg.reply_to_message.photo = None
        msg.reply_to_message.caption = None
        hub.ask_handler(msg)
        hub.gemini_chat.ask.assert_called_once_with(1, 1, "이거 요약해줘", "ko", "원본 메시지 내용", None)

    def test_reply_without_text(self, hub):
        hub.gemini_chat.ask.return_value = ["답변입니다"]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        msg.reply_to_message = MagicMock()
        msg.reply_to_message.text = None
        msg.reply_to_message.photo = None
        msg.reply_to_message.caption = None
        hub.ask_handler(msg)
        hub.gemini_chat.ask.assert_called_once_with(1, 1, "질문", "ko", None, None)

    def test_photo_caption(self, hub):
        hub.gemini_chat.ask.return_value = ["이미지 설명"]
        msg = make_message(None, user_id=1)
        msg.text = None
        msg.caption = "/ask 이게 뭐야"
        msg.from_user.language_code = "ko"
        photo = MagicMock()
        photo.file_id = "photo_123"
        msg.photo = [photo]
        hub.bot.get_file.return_value.file_path = "photos/file.jpg"
        hub.bot.download_file.return_value = b"fake_image_data"
        hub.ask_handler(msg)
        hub.bot.get_file.assert_called_once_with("photo_123")
        hub.gemini_chat.ask.assert_called_once_with(1, 1, "이게 뭐야", "ko", None, b"fake_image_data")

    def test_reply_to_photo(self, hub):
        hub.gemini_chat.ask.return_value = ["사진 분석"]
        msg = make_message("/ask 이 사진 설명해줘", user_id=1)
        msg.from_user.language_code = "ko"
        reply_photo = MagicMock()
        reply_photo.file_id = "reply_photo_123"
        msg.reply_to_message = MagicMock()
        msg.reply_to_message.text = None
        msg.reply_to_message.photo = [reply_photo]
        msg.reply_to_message.caption = "원본 캡션"
        hub.bot.get_file.return_value.file_path = "photos/reply.jpg"
        hub.bot.download_file.return_value = b"reply_image_data"
        hub.ask_handler(msg)
        hub.bot.get_file.assert_called_once_with("reply_photo_123")
        hub.gemini_chat.ask.assert_called_once_with(1, 1, "이 사진 설명해줘", "ko", "원본 캡션", b"reply_image_data")

    def test_photo_download_failure(self, hub):
        msg = make_message(None, user_id=1)
        msg.text = None
        msg.caption = "/ask 이게 뭐야"
        msg.from_user.language_code = "ko"
        photo = MagicMock()
        photo.file_id = "photo_123"
        msg.photo = [photo]
        hub.bot.get_file.side_effect = Exception("download error")
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_photo_download_error_msg)
        hub.gemini_chat.ask.assert_not_called()

    def test_reply_photo_download_failure(self, hub):
        msg = make_message("/ask 설명해줘", user_id=1)
        msg.from_user.language_code = "ko"
        reply_photo = MagicMock()
        reply_photo.file_id = "reply_photo_123"
        msg.reply_to_message = MagicMock()
        msg.reply_to_message.text = None
        msg.reply_to_message.photo = [reply_photo]
        msg.reply_to_message.caption = None
        hub.bot.get_file.side_effect = Exception("download error")
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_photo_download_error_msg)
        hub.gemini_chat.ask.assert_not_called()

    def test_reply_empty_question_rejected(self, hub):
        msg = make_message("/ask")
        msg.reply_to_message = MagicMock()
        msg.reply_to_message.text = "원본 메시지"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_empty_msg)
        hub.gemini_chat.ask.assert_not_called()

    def test_markdown_response(self, hub):
        hub.gemini_chat.ask.return_value = ["**bold** and `code`"]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once()
        call_kwargs = hub.bot.reply_to.call_args
        assert "entities" in call_kwargs.kwargs
        entities = call_kwargs.kwargs["entities"]
        assert len(entities) > 0

    def test_not_allowed(self, hub):
        hub.gemini_chat.ask.return_value = [strings.ask_not_allowed_msg]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once()

    @patch("modules.features_hub.convert", side_effect=Exception("parse error"))
    def test_convert_failure_fallback(self, mock_convert, hub):
        hub.gemini_chat.ask.return_value = ["plain text response"]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, "plain text response")


class TestClearChatHandler:
    def test_clear(self, hub):
        msg = make_message("/clear_chat")
        hub.clear_chat_handler(msg)
        hub.gemini_chat.clear_session.assert_called_once_with(1, 1)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_clear_msg)
