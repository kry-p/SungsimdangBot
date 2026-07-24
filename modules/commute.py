from modules.database import CommuteSchedule

WEEKDAY_MAP = {
    "월": 0,
    "화": 1,
    "수": 2,
    "목": 3,
    "금": 4,
    "토": 5,
    "일": 6,
}


def parse_time(value):
    hour_text, minute_text = value.split(":")
    hour = int(hour_text)
    minute = int(minute_text)

    if not 0 <= hour <= 23:
        raise ValueError("hour must be between 0 and 23")

    if not 0 <= minute <= 59:
        raise ValueError("minute must be between 0 and 59")

    return hour * 60 + minute


def parse_weekdays(value):
    weekdays = []

    for weekday_text in value:
        if weekday_text not in WEEKDAY_MAP:
            raise ValueError("invalid weekday")

        weekday = WEEKDAY_MAP[weekday_text]

        if weekday not in weekdays:
            weekdays.append(weekday)

    if not weekdays:
        raise ValueError("weekday must not be empty")

    return weekdays


def save_schedule(user_id, weekday_text, start_time, end_time):
    weekdays = parse_weekdays(weekday_text)
    start_minute = parse_time(start_time)
    end_minute = parse_time(end_time)

    if start_minute == end_minute:
        raise ValueError("start and end time must be different")

    for weekday in weekdays:
        CommuteSchedule.replace(
            user_id=user_id,
            weekday=weekday,
            start_minute=start_minute,
            end_minute=end_minute,
        ).execute()

    return len(weekdays)


def minutes_until_end(current_minute, start_minute, end_minute):
    if start_minute < end_minute:
        if start_minute <= current_minute < end_minute:
            return end_minute - current_minute

        return None

    if current_minute >= start_minute:
        return 24 * 60 - current_minute + end_minute

    if current_minute < end_minute:
        return end_minute - current_minute

    return None


def minutes_until_start(current_weekday, current_minute, target_weekday, start_minute):
    days_until = (target_weekday - current_weekday) % 7
    minutes = days_until * 24 * 60 + start_minute - current_minute

    if minutes <= 0:
        minutes += 7 * 24 * 60

    return minutes


def format_minutes(minutes):
    if minutes < 0:
        raise ValueError("minutes must not be negative")

    hours, remaining_minutes = divmod(minutes, 60)

    if hours and remaining_minutes:
        return f"{hours}시간 {remaining_minutes}분"

    if hours:
        return f"{hours}시간"

    return f"{remaining_minutes}분"


def get_schedules(user_id):
    query = CommuteSchedule.select().where(CommuteSchedule.user_id == user_id).order_by(CommuteSchedule.weekday)

    return list(query)


def find_next_schedule(user_id, current_weekday, current_minute):
    schedules = get_schedules(user_id)

    if not schedules:
        return None, None

    next_schedule = None
    shortest_minutes = None

    for schedule in schedules:
        remaining = minutes_until_start(
            current_weekday,
            current_minute,
            schedule.weekday,
            schedule.start_minute,
        )

        if shortest_minutes is None or remaining < shortest_minutes:
            next_schedule = schedule
            shortest_minutes = remaining

    return next_schedule, shortest_minutes


def find_active_schedule(user_id, current_weekday, current_minute):
    schedules = get_schedules(user_id)
    # 자정 이후에도 전날 시작한 야간 근무를 찾기 위해 전날 요일을 계산한다.
    previous_weekday = (current_weekday - 1) % 7

    for schedule in schedules:
        is_today_day_shift = (
            schedule.weekday == current_weekday
            and schedule.start_minute < schedule.end_minute
            and schedule.start_minute <= current_minute < schedule.end_minute
        )

        is_today_night_shift = (
            schedule.weekday == current_weekday
            and schedule.start_minute > schedule.end_minute
            and current_minute >= schedule.start_minute
        )

        is_previous_night_shift = (
            schedule.weekday == previous_weekday
            and schedule.start_minute > schedule.end_minute
            and current_minute < schedule.end_minute
        )

        if is_today_day_shift or is_today_night_shift or is_previous_night_shift:
            remaining = minutes_until_end(
                current_minute,
                schedule.start_minute,
                schedule.end_minute,
            )

            return schedule, remaining

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
