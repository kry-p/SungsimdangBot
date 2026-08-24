from modules.database import CommuteSchedule, db
from resources import strings

MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
MINUTES_PER_DAY = HOURS_PER_DAY * MINUTES_PER_HOUR
MINUTES_PER_WEEK = DAYS_PER_WEEK * MINUTES_PER_DAY
END_OF_DAY_TIME = "24:00"
VALIDATION_ERROR_MESSAGES = {
    "hour_out_of_range": "hour must be between 0 and 23",
    "minute_out_of_range": "minute must be between 0 and 59",
    "invalid_weekday": "invalid weekday",
    "empty_weekday": "weekday cannot be empty",
    "same_start_and_end": "start and end time must be different",
    "negative_minutes": "minutes cannot be negative",
}

WEEKDAY_MAP = {name: index for index, name in enumerate(strings.commute_weekday_names)}


def parse_time_to_minutes(time_text):
    hour_text, minute_text = time_text.split(":")
    hour = int(hour_text)
    minute = int(minute_text)

    if not 0 <= hour < HOURS_PER_DAY:
        raise ValueError(VALIDATION_ERROR_MESSAGES["hour_out_of_range"])

    if not 0 <= minute < MINUTES_PER_HOUR:
        raise ValueError(VALIDATION_ERROR_MESSAGES["minute_out_of_range"])

    return hour * MINUTES_PER_HOUR + minute


def parse_end_time_to_minutes(time_text):
    if time_text == END_OF_DAY_TIME:
        return MINUTES_PER_DAY

    return parse_time_to_minutes(time_text)


def parse_weekdays(value):
    weekdays = []

    for weekday_text in value:
        if weekday_text not in WEEKDAY_MAP:
            raise ValueError(VALIDATION_ERROR_MESSAGES["invalid_weekday"])

        weekday = WEEKDAY_MAP[weekday_text]

        if weekday not in weekdays:
            weekdays.append(weekday)

    if not weekdays:
        raise ValueError(VALIDATION_ERROR_MESSAGES["empty_weekday"])

    return weekdays


def save_schedule(user_id, weekday_text, start_time_text, end_time_text):
    weekdays = parse_weekdays(weekday_text)
    start_time_minutes = parse_time_to_minutes(start_time_text)
    end_time_minutes = parse_end_time_to_minutes(end_time_text)

    if start_time_minutes == end_time_minutes:
        raise ValueError(VALIDATION_ERROR_MESSAGES["same_start_and_end"])

    with db.atomic():
        for weekday in weekdays:
            CommuteSchedule.replace(
                user_id=user_id,
                weekday=weekday,
                start_time_minutes=start_time_minutes,
                end_time_minutes=end_time_minutes,
            ).execute()

    return len(weekdays)


def minutes_until_end(current_time_minutes, start_time_minutes, end_time_minutes):
    if start_time_minutes < end_time_minutes:
        if start_time_minutes <= current_time_minutes < end_time_minutes:
            return end_time_minutes - current_time_minutes

        return None

    if current_time_minutes >= start_time_minutes:
        return MINUTES_PER_DAY - current_time_minutes + end_time_minutes

    if current_time_minutes < end_time_minutes:
        return end_time_minutes - current_time_minutes

    return None


def minutes_until_start(current_weekday, current_time_minutes, target_weekday, start_time_minutes):
    days_until = (target_weekday - current_weekday) % DAYS_PER_WEEK
    minutes = days_until * MINUTES_PER_DAY + start_time_minutes - current_time_minutes

    if minutes <= 0:
        minutes += MINUTES_PER_WEEK

    return minutes


def format_minutes(minutes):
    if minutes < 0:
        raise ValueError(VALIDATION_ERROR_MESSAGES["negative_minutes"])

    hours, remaining_minutes = divmod(minutes, MINUTES_PER_HOUR)

    if hours and remaining_minutes:
        return strings.commute_duration_hours_minutes.format(
            hours=hours,
            minutes=remaining_minutes,
        )

    if hours:
        return strings.commute_duration_hours.format(hours=hours)

    return strings.commute_duration_minutes.format(minutes=remaining_minutes)


def get_schedules(user_id):
    query = CommuteSchedule.select().where(CommuteSchedule.user_id == user_id).order_by(CommuteSchedule.weekday)

    return list(query)


def find_next_schedule(user_id, current_weekday, current_time_minutes):
    schedules = get_schedules(user_id)

    if not schedules:
        return None, None

    next_schedule = None
    shortest_minutes = None

    for schedule in schedules:
        remaining_minutes = minutes_until_start(
            current_weekday,
            current_time_minutes,
            schedule.weekday,
            schedule.start_time_minutes,
        )

        if shortest_minutes is None or remaining_minutes < shortest_minutes:
            next_schedule = schedule
            shortest_minutes = remaining_minutes

    return next_schedule, shortest_minutes


def find_active_schedule(user_id, current_weekday, current_time_minutes):
    schedules = get_schedules(user_id)
    # 자정 이후에도 전날 시작한 야간 근무를 찾기 위해 전날 요일을 계산한다.
    previous_weekday = (current_weekday - 1) % DAYS_PER_WEEK

    for schedule in schedules:
        starts_today = schedule.weekday == current_weekday
        started_previous_day = schedule.weekday == previous_weekday
        is_day_shift = schedule.start_time_minutes < schedule.end_time_minutes
        is_overnight_shift = schedule.start_time_minutes > schedule.end_time_minutes

        is_today_day_shift = (
            starts_today
            and is_day_shift
            and schedule.start_time_minutes <= current_time_minutes < schedule.end_time_minutes
        )

        is_today_night_shift = (
            starts_today and is_overnight_shift and current_time_minutes >= schedule.start_time_minutes
        )

        is_previous_night_shift = (
            started_previous_day and is_overnight_shift and current_time_minutes < schedule.end_time_minutes
        )

        if is_today_day_shift or is_today_night_shift or is_previous_night_shift:
            remaining_minutes = minutes_until_end(
                current_time_minutes,
                schedule.start_time_minutes,
                schedule.end_time_minutes,
            )

            return schedule, remaining_minutes

    return None, None


def delete_schedules(user_id, weekday_text):
    weekdays = parse_weekdays(weekday_text)

    query = CommuteSchedule.delete().where(
        (CommuteSchedule.user_id == user_id) & (CommuteSchedule.weekday.in_(weekdays))
    )

    return query.execute()


def delete_all_schedules(user_id):
    query = CommuteSchedule.delete().where(CommuteSchedule.user_id == user_id)

    return query.execute()
