import datetime
import json
from unittest.mock import MagicMock, patch

import pytest

from modules.features_hub import BotFeaturesHub
from resources import strings


@pytest.fixture
def hub():
    bot = MagicMock()
    with patch("modules.features_hub.WebManager"):
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
        hub.webManager.provide_suon_v2.return_value = "23.5"
        result = hub.get_temp(1)
        assert result == "현재 한강 수온은 23.5 도입니다."

    def test_maintenance(self, hub):
        hub.webManager.provide_suon_v2.return_value = "점검중"
        result = hub.get_temp(1)
        assert "가져올 수 없습니다" in result


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
        hub.webManager.provide_suon_v2.return_value = "20.0"
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
