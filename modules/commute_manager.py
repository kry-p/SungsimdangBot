import datetime
import threading
import time

import telebot

from config import config
from modules.commute import (
    MINUTES_PER_HOUR,
    delete_all_schedules,
    delete_schedules,
    find_active_schedule,
    find_next_schedule,
    format_minutes,
    get_schedules,
    save_schedule,
)
from resources import strings

CALLBACK_PREFIXES = frozenset({"commute", "commute_clear"})
INPUT_TIMEOUT_SECONDS = 300


class CommuteManager:
    def __init__(self, bot):
        self.bot = bot
        self._pending_inputs = {}
        self._pending_inputs_lock = threading.Lock()

    @staticmethod
    def is_commute_callback(data):
        return bool(data and ":" in data and data.split(":", 1)[0] in CALLBACK_PREFIXES)

    def handle_commute_callback(self, call):
        parts = call.data.split(":")
        if len(parts) != 3:
            return

        action, value, owner_id_text = parts
        try:
            owner_id = int(owner_id_text)
        except ValueError:
            return

        if call.from_user.id != owner_id:
            return

        if action == "commute":
            if value in {"set", "delete"}:
                self._request_input(call, value)
            elif value == "clear":
                self._show_clear_confirmation(call, owner_id)
            elif value == "cancel":
                self.bot.edit_message_text(
                    strings.commute_menu_cancelled_msg,
                    call.message.chat.id,
                    call.message.message_id,
                )
            return

        if action == "commute_clear":
            if value == "confirm":
                self._clear_schedules(call)
            elif value == "cancel":
                self.bot.edit_message_text(
                    strings.commute_clear_cancelled_msg,
                    call.message.chat.id,
                    call.message.message_id,
                )

    def show_menu(self, message):
        schedule_text = self._build_schedule_text(message.from_user.id)
        menu_text = strings.commute_menu_msg.format(schedule=schedule_text)

        self.bot.reply_to(
            message,
            menu_text,
            reply_markup=self._build_menu_keyboard(message.from_user.id),
        )

    @staticmethod
    def get_current_commute_time():
        now = datetime.datetime.now(config.TIMEZONE)

        return now.weekday(), now.hour * MINUTES_PER_HOUR + now.minute

    def handle_start_keyword(self, message):
        current_weekday, current_time_minutes = self.get_current_commute_time()
        _schedule, remaining_minutes = find_active_schedule(
            message.from_user.id,
            current_weekday,
            current_time_minutes,
        )

        if remaining_minutes is not None:
            self.bot.reply_to(message, strings.commute_working_msg)
            return

        _schedule, remaining_minutes = find_next_schedule(
            message.from_user.id,
            current_weekday,
            current_time_minutes,
        )

        if remaining_minutes is None:
            self.bot.reply_to(message, strings.commute_schedule_missing_msg)
            return

        self.bot.reply_to(
            message,
            strings.commute_until_start_msg.format(
                remaining=format_minutes(remaining_minutes),
            ),
        )

    def handle_end_keyword(self, message):
        if not get_schedules(message.from_user.id):
            self.bot.reply_to(message, strings.commute_schedule_missing_msg)
            return

        current_weekday, current_time_minutes = self.get_current_commute_time()
        _schedule, remaining_minutes = find_active_schedule(
            message.from_user.id,
            current_weekday,
            current_time_minutes,
        )

        if remaining_minutes is None:
            self.bot.reply_to(message, strings.commute_not_working_msg)
            return

        self.bot.reply_to(
            message,
            strings.commute_until_end_msg.format(
                remaining=format_minutes(remaining_minutes),
            ),
        )

    def handle_input_reply(self, message):
        reply_to = message.reply_to_message
        if not reply_to:
            return

        pending_key = (message.chat.id, reply_to.message_id)
        with self._pending_inputs_lock:
            pending = self._pending_inputs.get(pending_key)
            if pending is None:
                return

            user_id, action, created_at = pending
            if message.from_user.id != user_id:
                return

            del self._pending_inputs[pending_key]

        if time.time() - created_at > INPUT_TIMEOUT_SECONDS:
            self.bot.reply_to(message, strings.commute_input_expired_msg)
            return

        if action == "set":
            self._save_schedule_from_reply(message)
        elif action == "delete":
            self._delete_schedules_from_reply(message)

    def _request_input(self, call, action):
        self._cleanup_expired_inputs()
        prompt = strings.commute_set_input_msg if action == "set" else strings.commute_delete_input_msg
        original_message = getattr(call.message, "reply_to_message", None)
        original_message_id = getattr(original_message, "message_id", None)
        self.bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None,
        )
        sent = self.bot.send_message(
            call.message.chat.id,
            prompt,
            reply_to_message_id=original_message_id,
            reply_markup=telebot.types.ForceReply(
                selective=original_message_id is not None,
            ),
        )
        pending_key = (call.message.chat.id, sent.message_id)
        with self._pending_inputs_lock:
            self._pending_inputs[pending_key] = (
                call.from_user.id,
                action,
                time.time(),
            )

    def _save_schedule_from_reply(self, message):
        parts = (message.text or "").split()
        if len(parts) != 3:
            self.bot.reply_to(message, strings.commute_set_error_msg)
            return

        weekday_text, start_time_text, end_time_text = parts
        try:
            count = save_schedule(
                message.from_user.id,
                weekday_text,
                start_time_text,
                end_time_text,
            )
        except ValueError:
            self.bot.reply_to(message, strings.commute_set_error_msg)
            return

        self.bot.reply_to(
            message,
            strings.commute_set_success_msg.format(count=count),
        )

    def _delete_schedules_from_reply(self, message):
        parts = (message.text or "").split()
        if len(parts) != 1:
            self.bot.reply_to(message, strings.commute_delete_error_msg)
            return

        try:
            count = delete_schedules(message.from_user.id, parts[0])
        except ValueError:
            self.bot.reply_to(message, strings.commute_delete_error_msg)
            return

        if count == 0:
            self.bot.reply_to(message, strings.commute_delete_missing_msg)
            return

        self.bot.reply_to(
            message,
            strings.commute_delete_success_msg.format(count=count),
        )

    def _show_clear_confirmation(self, call, owner_id):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                strings.commute_confirm_btn,
                callback_data=f"commute_clear:confirm:{owner_id}",
            ),
            telebot.types.InlineKeyboardButton(
                strings.commute_cancel_btn,
                callback_data=f"commute_clear:cancel:{owner_id}",
            ),
        )
        self.bot.edit_message_text(
            strings.commute_clear_confirm_msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
        )

    def _clear_schedules(self, call):
        count = delete_all_schedules(call.from_user.id)
        result = strings.commute_clear_success_msg if count else strings.commute_delete_missing_msg
        self.bot.edit_message_text(
            result,
            call.message.chat.id,
            call.message.message_id,
        )

    def _cleanup_expired_inputs(self):
        now = time.time()
        with self._pending_inputs_lock:
            self._pending_inputs = {
                pending_key: pending
                for pending_key, pending in self._pending_inputs.items()
                if now - pending[2] <= INPUT_TIMEOUT_SECONDS
            }

    @staticmethod
    def _build_schedule_text(user_id):
        schedules = get_schedules(user_id)

        if not schedules:
            return strings.commute_schedule_empty_msg

        return "\n".join(
            strings.commute_schedule_item_msg.format(
                weekday=strings.commute_weekday_names[schedule.weekday],
                start_time=CommuteManager._format_time_from_minutes(schedule.start_time_minutes),
                end_time=CommuteManager._format_time_from_minutes(schedule.end_time_minutes),
            )
            for schedule in schedules
        )

    @staticmethod
    def _format_time_from_minutes(total_minutes):
        hour, minute = divmod(total_minutes, MINUTES_PER_HOUR)

        return f"{hour:02d}:{minute:02d}"

    @staticmethod
    def _build_menu_keyboard(owner_id):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                strings.commute_set_btn,
                callback_data=f"commute:set:{owner_id}",
            ),
            telebot.types.InlineKeyboardButton(
                strings.commute_delete_btn,
                callback_data=f"commute:delete:{owner_id}",
            ),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                strings.commute_clear_btn,
                callback_data=f"commute:clear:{owner_id}",
            ),
            telebot.types.InlineKeyboardButton(
                strings.commute_close_btn,
                callback_data=f"commute:cancel:{owner_id}",
            ),
        )

        return keyboard
