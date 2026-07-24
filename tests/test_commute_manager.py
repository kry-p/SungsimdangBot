from unittest.mock import MagicMock

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
        assert 99 in manager._pending_inputs
