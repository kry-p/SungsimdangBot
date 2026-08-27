from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from config import config
from modules.commute import save_schedule
from modules.commute_manager import CommuteManager
from resources import strings
from tests.conftest import make_message


class TestCommuteMenu:
    def test_shows_empty_schedule_without_menu_buttons(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute", user_id=123)

        manager.show_menu(message)

        bot.reply_to.assert_called_once_with(
            message,
            strings.commute_menu_msg.format(
                schedule=strings.commute_schedule_empty_msg,
            ),
        )

    def test_shows_user_schedules_in_readable_format(self):
        save_schedule(123, "월화", "09:00", "18:00")
        save_schedule(123, "금", "22:00", "07:00")
        save_schedule(456, "수", "10:00", "19:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute", user_id=123)

        manager.show_menu(message)

        expected_schedule = "\n".join(
            (
                "• 월 09:00~18:00",
                "• 화 09:00~18:00",
                "• 금 22:00~07:00",
            )
        )
        bot.reply_to.assert_called_once_with(
            message,
            strings.commute_menu_msg.format(schedule=expected_schedule),
        )


class TestCommuteCommands:
    def test_command_without_action_shows_menu(self):
        manager = CommuteManager(MagicMock())
        manager.show_menu = MagicMock()
        message = make_message("/commute", user_id=123)

        manager.handle_command(message)

        manager.show_menu.assert_called_once_with(message)

    def test_registers_schedule(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute 등록 월화 9:00 18:00", user_id=123)

        manager.handle_command(message)

        assert manager._build_schedule_text(123) == "• 월 09:00~18:00\n• 화 09:00~18:00"
        bot.reply_to.assert_called_once_with(message, strings.commute_set_success_msg.format(count=2))

    @pytest.mark.parametrize(
        "text",
        (
            "/commute 등록",
            "/commute 등록 월 09:00",
            "/commute 등록 월 잘못된시간 18:00",
            "/commute 등록 잘못된요일 09:00 18:00",
            "/commute 등록 월 09:00 09:00",
        ),
    )
    def test_invalid_register_command_shows_error(self, text):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message(text, user_id=123)

        manager.handle_command(message)

        assert manager._build_schedule_text(123) == strings.commute_schedule_empty_msg
        bot.reply_to.assert_called_once_with(message, strings.commute_set_error_msg)

    def test_deletes_selected_schedules(self):
        save_schedule(123, "월화수", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute 삭제 월화", user_id=123)

        manager.handle_command(message)

        assert manager._build_schedule_text(123) == "• 수 09:00~18:00"
        bot.reply_to.assert_called_once_with(message, strings.commute_delete_success_msg.format(count=2))

    @pytest.mark.parametrize(
        "text",
        (
            "/commute 삭제",
            "/commute 삭제 잘못된요일",
        ),
    )
    def test_invalid_delete_command_shows_error(self, text):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message(text, user_id=123)

        manager.handle_command(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_delete_error_msg)

    def test_delete_missing_schedule_shows_error(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute 삭제 월", user_id=123)

        manager.handle_command(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_delete_missing_msg)

    def test_deletes_all_schedules(self):
        save_schedule(123, "월화", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute 전체삭제", user_id=123)

        manager.handle_command(message)

        assert manager._build_schedule_text(123) == strings.commute_schedule_empty_msg
        bot.reply_to.assert_called_once_with(message, strings.commute_delete_all_success_msg)

    def test_delete_all_without_schedules_shows_error(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute 전체삭제", user_id=123)

        manager.handle_command(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_delete_missing_msg)

    def test_delete_all_with_extra_argument_does_not_delete(self):
        save_schedule(123, "월", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute 전체삭제 월", user_id=123)

        manager.handle_command(message)

        assert manager._build_schedule_text(123) == "• 월 09:00~18:00"
        bot.reply_to.assert_called_once_with(message, strings.commute_command_error_msg)

    def test_unknown_action_shows_error(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute 알수없음", user_id=123)

        manager.handle_command(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_command_error_msg)


class TestCommuteKeywords:
    @patch("modules.commute_manager.datetime.datetime")
    def test_current_time_uses_configured_timezone(self, datetime_mock):
        datetime_mock.now.return_value = datetime(2026, 8, 5, 16, 31)

        weekday, minutes = CommuteManager.get_current_commute_time()

        datetime_mock.now.assert_called_once_with(config.TIMEZONE)
        assert weekday == 2
        assert minutes == 16 * 60 + 31

    def test_start_keyword(self):
        save_schedule(123, "월", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        manager.get_current_commute_time = MagicMock(return_value=(0, 8 * 60))
        message = make_message("출근", user_id=123)

        manager.handle_start_keyword(message)

        bot.reply_to.assert_called_once_with(
            message,
            strings.commute_until_start_msg.format(remaining="1시간"),
        )

    def test_start_keyword_during_working_hours(self):
        save_schedule(123, "월", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        manager.get_current_commute_time = MagicMock(return_value=(0, 12 * 60))
        message = make_message("출근", user_id=123)

        manager.handle_start_keyword(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_working_msg)

    def test_start_keyword_without_schedule(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        manager.get_current_commute_time = MagicMock(return_value=(0, 8 * 60))
        message = make_message("출근")

        manager.handle_start_keyword(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_schedule_missing_msg)

    def test_end_keyword(self):
        save_schedule(123, "월", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        manager.get_current_commute_time = MagicMock(return_value=(0, 12 * 60))
        message = make_message("퇴근", user_id=123)

        manager.handle_end_keyword(message)

        bot.reply_to.assert_called_once_with(
            message,
            strings.commute_until_end_msg.format(remaining="6시간"),
        )

    def test_end_keyword_outside_working_hours(self):
        save_schedule(123, "월", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        manager.get_current_commute_time = MagicMock(return_value=(0, 20 * 60))
        message = make_message("퇴근", user_id=123)

        manager.handle_end_keyword(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_not_working_msg)

    def test_end_keyword_without_schedule(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("퇴근")

        manager.handle_end_keyword(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_schedule_missing_msg)
