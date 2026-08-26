import datetime

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


class CommuteManager:
    def __init__(self, bot):
        self.bot = bot

    def handle_command(self, message):
        parts = (message.text or "").split()
        arguments = parts[1:]

        if not arguments:
            self.show_menu(message)
            return

        action = arguments[0]
        action_arguments = arguments[1:]

        if action == strings.commute_register_action:
            self._save_schedule_from_arguments(message, action_arguments)
        elif action == strings.commute_delete_action:
            self._delete_schedules_from_arguments(message, action_arguments)
        elif action == strings.commute_delete_all_action:
            self._delete_all_schedules_from_arguments(message, action_arguments)
        else:
            self.bot.reply_to(message, strings.commute_command_error_msg)

    def show_menu(self, message):
        schedule_text = self._build_schedule_text(message.from_user.id)
        menu_text = strings.commute_menu_msg.format(schedule=schedule_text)

        self.bot.reply_to(message, menu_text)

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

    def _save_schedule_from_arguments(self, message, arguments):
        if len(arguments) != 3:
            self.bot.reply_to(message, strings.commute_set_error_msg)
            return

        weekday_text, start_time_text, end_time_text = arguments
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

    def _delete_schedules_from_arguments(self, message, arguments):
        if len(arguments) != 1:
            self.bot.reply_to(message, strings.commute_delete_error_msg)
            return

        try:
            count = delete_schedules(message.from_user.id, arguments[0])
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

    def _delete_all_schedules_from_arguments(self, message, arguments):
        if arguments:
            self.bot.reply_to(message, strings.commute_command_error_msg)
            return

        count = delete_all_schedules(message.from_user.id)
        result = strings.commute_delete_all_success_msg if count else strings.commute_delete_missing_msg
        self.bot.reply_to(message, result)

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
