import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest

from modules.commute import save_schedule
from modules.commute_manager import CommuteManager
from resources import strings
from tests.conftest import make_message


class TestCommuteMenu:
    def test_shows_empty_schedule_and_menu_buttons(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message("/commute", user_id=123)

        manager.show_menu(message)

        bot.reply_to.assert_called_once()
        args, kwargs = bot.reply_to.call_args
        assert args == (
            message,
            strings.commute_menu_msg.format(
                schedule=strings.commute_schedule_empty_msg,
            ),
        )

        callback_data = [button.callback_data for row in kwargs["reply_markup"].keyboard for button in row]
        assert callback_data == [
            "commute:set",
            "commute:delete",
            "commute:clear",
            "commute:cancel",
        ]

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
                "월 09:00~18:00",
                "화 09:00~18:00",
                "금 22:00~07:00",
            )
        )
        bot.reply_to.assert_called_once_with(
            message,
            strings.commute_menu_msg.format(schedule=expected_schedule),
            reply_markup=bot.reply_to.call_args.kwargs["reply_markup"],
        )


class TestCommuteCallbacks:
    @staticmethod
    def make_callback(data, user_id=123, chat_id=1, message_id=10):
        call = MagicMock()
        call.data = data
        call.from_user.id = user_id
        call.message.chat.id = chat_id
        call.message.message_id = message_id
        return call

    def test_set_button_requests_input_and_saves_reply(self):
        bot = MagicMock()
        prompt_message = MagicMock()
        prompt_message.message_id = 99
        bot.send_message.return_value = prompt_message
        manager = CommuteManager(bot)
        call = self.make_callback("commute:set")

        manager.handle_commute_callback(call)

        bot.send_message.assert_called_once()
        assert bot.send_message.call_args.args[:2] == (
            call.message.chat.id,
            strings.commute_set_input_msg,
        )

        reply = make_message("월화 09:00 18:00", user_id=123)
        reply.reply_to_message = prompt_message
        manager.handle_input_reply(reply)

        schedules = manager._build_schedule_text(123)
        assert schedules == "월 09:00~18:00\n화 09:00~18:00"
        bot.reply_to.assert_called_once_with(
            reply,
            strings.commute_set_success_msg.format(count=2),
        )

    def test_delete_button_requests_input_and_deletes_reply(self):
        save_schedule(123, "월화", "09:00", "18:00")
        bot = MagicMock()
        prompt_message = MagicMock()
        prompt_message.message_id = 99
        bot.send_message.return_value = prompt_message
        manager = CommuteManager(bot)
        call = self.make_callback("commute:delete")

        manager.handle_commute_callback(call)

        assert bot.send_message.call_args.args[:2] == (
            call.message.chat.id,
            strings.commute_delete_input_msg,
        )

        reply = make_message("월", user_id=123)
        reply.reply_to_message = prompt_message
        manager.handle_input_reply(reply)

        assert manager._build_schedule_text(123) == "화 09:00~18:00"
        bot.reply_to.assert_called_once_with(
            reply,
            strings.commute_delete_success_msg.format(count=1),
        )

    @pytest.mark.parametrize(
        "text",
        (
            "월 09:00",
            "월 잘못된시간 18:00",
        ),
    )
    def test_invalid_set_reply_shows_set_error(self, text):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message(text, user_id=123)

        manager._save_schedule_from_reply(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_set_error_msg)

    @pytest.mark.parametrize(
        "text",
        (
            "월 화",
            "잘못된요일",
        ),
    )
    def test_invalid_delete_reply_shows_delete_error(self, text):
        bot = MagicMock()
        manager = CommuteManager(bot)
        message = make_message(text, user_id=123)

        manager._delete_schedules_from_reply(message)

        bot.reply_to.assert_called_once_with(message, strings.commute_delete_error_msg)

    def test_clear_button_asks_for_confirmation_and_clears_schedule(self):
        save_schedule(123, "월화", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        call = self.make_callback("commute:clear")

        manager.handle_commute_callback(call)

        args, kwargs = bot.edit_message_text.call_args
        assert args == (
            strings.commute_clear_confirm_msg,
            call.message.chat.id,
            call.message.message_id,
        )
        callback_data = [button.callback_data for row in kwargs["reply_markup"].keyboard for button in row]
        assert callback_data == [
            "commute_clear:confirm",
            "commute_clear:cancel",
        ]

        confirm_call = self.make_callback("commute_clear:confirm")
        manager.handle_commute_callback(confirm_call)

        assert manager._build_schedule_text(123) == strings.commute_schedule_empty_msg
        bot.edit_message_text.assert_called_with(
            strings.commute_clear_success_msg,
            confirm_call.message.chat.id,
            confirm_call.message.message_id,
        )

    def test_clear_cancel_keeps_schedule(self):
        save_schedule(123, "월", "09:00", "18:00")
        bot = MagicMock()
        manager = CommuteManager(bot)
        call = self.make_callback("commute_clear:cancel")

        manager.handle_commute_callback(call)

        assert manager._build_schedule_text(123) == "월 09:00~18:00"
        bot.edit_message_text.assert_called_once_with(
            strings.commute_clear_cancelled_msg,
            call.message.chat.id,
            call.message.message_id,
        )

    def test_close_button_closes_menu(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        call = self.make_callback("commute:cancel")

        manager.handle_commute_callback(call)

        bot.edit_message_text.assert_called_once_with(
            strings.commute_menu_cancelled_msg,
            call.message.chat.id,
            call.message.message_id,
        )

    def test_other_user_cannot_consume_pending_input(self):
        bot = MagicMock()
        prompt_message = MagicMock()
        prompt_message.message_id = 99
        bot.send_message.return_value = prompt_message
        manager = CommuteManager(bot)
        manager.handle_commute_callback(self.make_callback("commute:set", user_id=123))

        other_user_reply = make_message("월 09:00 18:00", user_id=456)
        other_user_reply.reply_to_message = prompt_message
        manager.handle_input_reply(other_user_reply)

        assert manager._build_schedule_text(456) == strings.commute_schedule_empty_msg
        assert (1, 99) in manager._pending_inputs

    def test_pending_input_is_consumed_once_by_concurrent_replies(self):
        bot = MagicMock()
        manager = CommuteManager(bot)
        manager._save_schedule_from_reply = MagicMock()
        manager._pending_inputs[(1, 99)] = (123, "set", time.time())

        replies = [
            make_message("월 09:00 18:00", user_id=123),
            make_message("월 09:00 18:00", user_id=123),
        ]
        prompt_message = MagicMock()
        prompt_message.message_id = 99
        for reply in replies:
            reply.reply_to_message = prompt_message

        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(manager.handle_input_reply, replies))

        manager._save_schedule_from_reply.assert_called_once()
        assert (1, 99) not in manager._pending_inputs

    def test_same_message_id_is_handled_separately_per_chat(self):
        bot = MagicMock()
        prompt_message = MagicMock()
        prompt_message.message_id = 99
        bot.send_message.return_value = prompt_message
        manager = CommuteManager(bot)

        manager.handle_commute_callback(self.make_callback("commute:set", user_id=123, chat_id=1))
        manager.handle_commute_callback(self.make_callback("commute:set", user_id=456, chat_id=2))

        assert (1, 99) in manager._pending_inputs
        assert (2, 99) in manager._pending_inputs

        first_reply = make_message("월 09:00 18:00", user_id=123, chat_id=1)
        first_reply.reply_to_message = prompt_message
        second_reply = make_message("화 10:00 19:00", user_id=456, chat_id=2)
        second_reply.reply_to_message = prompt_message

        manager.handle_input_reply(first_reply)
        manager.handle_input_reply(second_reply)

        assert manager._build_schedule_text(123) == "월 09:00~18:00"
        assert manager._build_schedule_text(456) == "화 10:00~19:00"
        assert manager._pending_inputs == {}


class TestCommuteKeywords:
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
