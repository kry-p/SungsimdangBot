import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import ValidationError

from modules.api_models import CodexResetForecastResponse, CodexResetTimelineResponse
from modules.features_hub import BotFeaturesHub
from resources import strings
from tests.conftest import make_message


@pytest.fixture
def hub():
    bot = MagicMock()
    with (
        patch("modules.features_hub.WebManager"),
        patch("modules.features_hub.AIChatManager"),
        patch("modules.features_hub.AdminManager"),
        patch("modules.features_hub.SpotifyService"),
        patch("modules.features_hub.CodexResetService"),
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


class TestSpotifyDelegation:
    def test_search_handler(self, hub):
        message = make_message("/spotify 아이유")
        hub.spotify_search_handler(message)
        hub.spotify.search_handler.assert_called_once_with(message)

    def test_callback_handler(self, hub):
        call = MagicMock()
        hub.handle_spotify_callback(call)
        hub.spotify.handle_spotify_callback.assert_called_once_with(call)


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

    def test_calculation_limit_error(self, hub):
        msg = make_message("/calc 9^9^9^9^9")
        hub.calculator_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.calc_limit_error_msg)

    def test_no_expression(self, hub):
        msg = make_message("/calc")
        hub.calculator_handler(msg)
        hub.bot.reply_to.assert_not_called()


class TestCommuteHandler:
    def test_delegates_to_commute_manager(self, hub):
        hub.commute.handle_command = MagicMock()
        msg = make_message("/commute")

        hub.commute_handler(msg)

        hub.commute.handle_command.assert_called_once_with(msg)


class TestCodexHandler:
    def test_success_replies_with_forecast_and_banked_announcement(self, hub):
        forecast = MagicMock()
        timeline = MagicMock()
        announcement = MagicMock()
        hub.codex_reset.fetch_forecast.return_value = forecast
        hub.codex_reset.build_forecast_message.return_value = "Codex forecast"
        hub.codex_reset.fetch_timeline.return_value = timeline
        hub.codex_reset.find_latest_banked_announcement.return_value = announcement
        hub.codex_reset.build_banked_announcement_message.return_value = "\n\nBanked announcement"
        msg = make_message("/codex")

        hub.codex_handler(msg)

        hub.codex_reset.fetch_forecast.assert_called_once_with()
        hub.codex_reset.build_forecast_message.assert_called_once_with(forecast)
        hub.codex_reset.fetch_timeline.assert_called_once_with()
        hub.codex_reset.find_latest_banked_announcement.assert_called_once_with(timeline)
        hub.codex_reset.build_banked_announcement_message.assert_called_once_with(announcement)
        hub.bot.reply_to.assert_called_once_with(
            msg,
            f"Codex forecast\n\nBanked announcement{strings.codex_reset_disclaimer_msg}",
            disable_web_page_preview=True,
        )
        reply_text = hub.bot.reply_to.call_args.args[1]
        assert "공식 정보가 아니므로 참고용으로만 이용해 주세요." in reply_text
        assert "codex-reset.com" not in reply_text

    @patch("modules.features_hub.logger")
    def test_timeline_error_replies_with_forecast_and_unavailable_announcement(self, mock_logger, hub):
        forecast = MagicMock()
        hub.codex_reset.fetch_forecast.return_value = forecast
        hub.codex_reset.build_forecast_message.return_value = "Codex forecast"
        hub.codex_reset.fetch_timeline.side_effect = requests.Timeout("timed out")
        hub.codex_reset.build_banked_announcement_message.return_value = "\n\nUnavailable"
        msg = make_message("/codex")

        hub.codex_handler(msg)

        hub.codex_reset.find_latest_banked_announcement.assert_not_called()
        hub.codex_reset.build_banked_announcement_message.assert_called_once_with(None)
        mock_logger.log_error.assert_called_once_with("Failed to fetch Codex banked reset timeline.")
        hub.bot.reply_to.assert_called_once_with(
            msg,
            f"Codex forecast\n\nUnavailable{strings.codex_reset_disclaimer_msg}",
            disable_web_page_preview=True,
        )

    @patch("modules.features_hub.logger")
    def test_timeline_validation_error_keeps_forecast_response(self, mock_logger, hub):
        with pytest.raises(ValidationError) as error_info:
            CodexResetTimelineResponse.model_validate({})
        hub.codex_reset.build_forecast_message.return_value = "Codex forecast"
        hub.codex_reset.fetch_timeline.side_effect = error_info.value
        hub.codex_reset.build_banked_announcement_message.return_value = "\n\nUnavailable"
        msg = make_message("/codex")

        hub.codex_handler(msg)

        hub.codex_reset.find_latest_banked_announcement.assert_not_called()
        hub.codex_reset.build_banked_announcement_message.assert_called_once_with(None)
        mock_logger.log_error.assert_called_once_with("Failed to fetch Codex banked reset timeline.")
        hub.bot.reply_to.assert_called_once_with(
            msg,
            f"Codex forecast\n\nUnavailable{strings.codex_reset_disclaimer_msg}",
            disable_web_page_preview=True,
        )

    @patch("modules.features_hub.logger")
    def test_request_error_replies_with_codex_error(self, mock_logger, hub):
        hub.codex_reset.fetch_forecast.side_effect = requests.Timeout("timed out")
        msg = make_message("/codex")

        hub.codex_handler(msg)

        hub.codex_reset.build_forecast_message.assert_not_called()
        hub.codex_reset.fetch_timeline.assert_not_called()
        mock_logger.log_error.assert_called_once_with("Failed to fetch Codex reset forecast.")
        hub.bot.reply_to.assert_called_once_with(msg, strings.codex_reset_error_msg)

    @patch("modules.features_hub.logger")
    def test_validation_error_replies_with_codex_error(self, mock_logger, hub):
        with pytest.raises(ValidationError) as error_info:
            CodexResetForecastResponse.model_validate({})
        hub.codex_reset.fetch_forecast.side_effect = error_info.value
        msg = make_message("/codex")

        hub.codex_handler(msg)

        hub.codex_reset.build_forecast_message.assert_not_called()
        hub.codex_reset.fetch_timeline.assert_not_called()
        mock_logger.log_error.assert_called_once_with("Failed to fetch Codex reset forecast.")
        hub.bot.reply_to.assert_called_once_with(msg, strings.codex_reset_error_msg)


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

    @pytest.mark.parametrize("text", ["출근 시간", "출근시간 알려줘", "오늘 출근 시간이 몇 시야?"])
    def test_commute_start_keyword(self, hub, text):
        hub.commute.handle_start_keyword = MagicMock()
        msg = make_message(text)

        hub.ordinary_message(msg)

        hub.commute.handle_start_keyword.assert_called_once_with(msg)

    @pytest.mark.parametrize("text", ["퇴근 시간", "퇴근시간 알려줘", "퇴근 시간 얼마나 남았어?"])
    def test_commute_end_keyword(self, hub, text):
        hub.commute.handle_end_keyword = MagicMock()
        msg = make_message(text)

        hub.ordinary_message(msg)

        hub.commute.handle_end_keyword.assert_called_once_with(msg)

    @pytest.mark.parametrize("text", ["출근", "퇴근", "출근을 안 찍었으니까", "퇴근하고 밥 먹자"])
    def test_commute_keyword_without_time_does_not_trigger(self, hub, text):
        hub.commute.handle_start_keyword = MagicMock()
        hub.commute.handle_end_keyword = MagicMock()

        hub.ordinary_message(make_message(text))

        hub.commute.handle_start_keyword.assert_not_called()
        hub.commute.handle_end_keyword.assert_not_called()

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
        hub.ai_chat.ask.return_value = ["답변입니다"]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.ai_chat.ask.assert_called_once_with(1, 1, "질문", "ko", None, None)
        hub.bot.reply_to.assert_called_once()
        call_kwargs = hub.bot.reply_to.call_args
        assert call_kwargs[0][1] == "답변입니다"
        assert "entities" in call_kwargs.kwargs

    def test_reply_with_context(self, hub):
        hub.ai_chat.ask.return_value = ["요약입니다"]
        msg = make_message("/ask 이거 요약해줘", user_id=1)
        msg.from_user.language_code = "ko"
        msg.reply_to_message = MagicMock()
        msg.reply_to_message.text = "원본 메시지 내용"
        msg.reply_to_message.photo = None
        msg.reply_to_message.caption = None
        hub.ask_handler(msg)
        hub.ai_chat.ask.assert_called_once_with(1, 1, "이거 요약해줘", "ko", "원본 메시지 내용", None)

    def test_reply_without_text(self, hub):
        hub.ai_chat.ask.return_value = ["답변입니다"]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        msg.reply_to_message = MagicMock()
        msg.reply_to_message.text = None
        msg.reply_to_message.photo = None
        msg.reply_to_message.caption = None
        hub.ask_handler(msg)
        hub.ai_chat.ask.assert_called_once_with(1, 1, "질문", "ko", None, None)

    def test_photo_caption(self, hub):
        hub.ai_chat.ask.return_value = ["이미지 설명"]
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
        hub.ai_chat.ask.assert_called_once_with(1, 1, "이게 뭐야", "ko", None, b"fake_image_data")

    def test_reply_to_photo(self, hub):
        hub.ai_chat.ask.return_value = ["사진 분석"]
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
        hub.ai_chat.ask.assert_called_once_with(1, 1, "이 사진 설명해줘", "ko", "원본 캡션", b"reply_image_data")

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
        hub.ai_chat.ask.assert_not_called()

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
        hub.ai_chat.ask.assert_not_called()

    def test_reply_empty_question_rejected(self, hub):
        msg = make_message("/ask")
        msg.reply_to_message = MagicMock()
        msg.reply_to_message.text = "원본 메시지"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_empty_msg)
        hub.ai_chat.ask.assert_not_called()

    def test_markdown_response(self, hub):
        hub.ai_chat.ask.return_value = ["**bold** and `code`"]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once()
        call_kwargs = hub.bot.reply_to.call_args
        assert "entities" in call_kwargs.kwargs
        entities = call_kwargs.kwargs["entities"]
        assert len(entities) > 0

    def test_not_allowed(self, hub):
        hub.ai_chat.ask.return_value = [strings.ask_not_allowed_msg]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once()

    @patch("modules.features_hub.convert", side_effect=Exception("parse error"))
    def test_convert_failure_fallback(self, mock_convert, hub):
        hub.ai_chat.ask.return_value = ["plain text response"]
        msg = make_message("/ask 질문", user_id=1)
        msg.from_user.language_code = "ko"
        hub.ask_handler(msg)
        hub.bot.reply_to.assert_called_once_with(msg, "plain text response")


class TestParseBfrssArgs:
    def test_no_args(self):
        slug, date, error = BotFeaturesHub._parse_bfrss_args("/bfrss")
        assert slug == "hn"
        assert date == ""
        assert error is None

    def test_valid_slug(self):
        slug, date, error = BotFeaturesHub._parse_bfrss_args("/bfrss -lob")
        assert slug == "lob"
        assert date == ""
        assert error is None

    def test_uppercase_slug(self):
        slug, date, error = BotFeaturesHub._parse_bfrss_args("/bfrss -LOB")
        assert slug == "lob"
        assert error is None

    def test_invalid_slug_format(self):
        _, _, error = BotFeaturesHub._parse_bfrss_args("/bfrss abc")
        assert error == "invalid_slug"

    def test_valid_slug_and_date(self):
        slug, date, error = BotFeaturesHub._parse_bfrss_args("/bfrss -lob 260507")
        assert slug == "lob"
        assert date == "20260507"
        assert error is None

    def test_invalid_date_short(self):
        _, _, error = BotFeaturesHub._parse_bfrss_args("/bfrss -lob 2605")
        assert error == "invalid_date"

    def test_invalid_date_non_numeric(self):
        _, _, error = BotFeaturesHub._parse_bfrss_args("/bfrss -lob 26050a")
        assert error == "invalid_date"


class TestClearChatHandler:
    def test_clear(self, hub):
        msg = make_message("/clear_chat")
        hub.clear_chat_handler(msg)
        hub.ai_chat.clear_session.assert_called_once_with(1, 1)
        hub.bot.reply_to.assert_called_once_with(msg, strings.ask_clear_msg)
