import pytest

from modules.commute import (
    delete_all_schedules,
    delete_schedules,
    find_active_schedule,
    find_next_schedule,
    format_minutes,
    get_schedules,
    minutes_until_end,
    minutes_until_start,
    parse_time_to_minutes,
    parse_weekdays,
    save_schedule,
)
from modules.database import CommuteSchedule


class TestParseTime:
    def test_valid_time(self):
        assert parse_time_to_minutes("09:00") == 540
        assert parse_time_to_minutes("18:30") == 1110

    def test_invalid_hour(self):
        with pytest.raises(ValueError):
            parse_time_to_minutes("24:00")

    def test_invalid_minute(self):
        with pytest.raises(ValueError):
            parse_time_to_minutes("09:60")


class TestParseWeekdays:
    def test_valid_weekdays(self):
        assert parse_weekdays("월화금") == [0, 1, 4]

    def test_duplicate_weekdays(self):
        assert parse_weekdays("월화월") == [0, 1]

    def test_invalid_weekday(self):
        with pytest.raises(ValueError):
            parse_weekdays("월엄")


class TestSaveSchedule:
    def test_save_multiple_weekdays(self):
        saved_count = save_schedule(123, "월화", "09:00", "18:00")

        monday = CommuteSchedule.get((CommuteSchedule.user_id == 123) & (CommuteSchedule.weekday == 0))
        tuesday = CommuteSchedule.get((CommuteSchedule.user_id == 123) & (CommuteSchedule.weekday == 1))

        assert saved_count == 2
        assert monday.start_time_minutes == 540
        assert monday.end_time_minutes == 1080
        assert tuesday.start_time_minutes == 540
        assert tuesday.end_time_minutes == 1080

    def test_replace_existing_schedule(self):
        save_schedule(123, "월", "09:00", "18:00")
        save_schedule(123, "월", "10:00", "19:00")

        schedule = CommuteSchedule.get((CommuteSchedule.user_id == 123) & (CommuteSchedule.weekday == 0))

        assert schedule.start_time_minutes == 600
        assert schedule.end_time_minutes == 1140
        assert CommuteSchedule.select().count() == 1

    def test_reject_same_start_and_end_time(self):
        with pytest.raises(ValueError):
            save_schedule(123, "월", "09:00", "09:00")

        assert CommuteSchedule.select().count() == 0


class TestGetSchedules:
    def test_get_user_schedules_in_weekday_order(self):
        save_schedule(123, "화월", "09:00", "18:00")

        schedules = get_schedules(123)

        assert [schedule.weekday for schedule in schedules] == [0, 1]

    def test_excludes_other_user_schedules(self):
        save_schedule(123, "월", "09:00", "18:00")
        save_schedule(456, "화", "10:00", "19:00")

        schedules = get_schedules(123)

        assert len(schedules) == 1
        assert schedules[0].user_id == 123
        assert schedules[0].weekday == 0

    def test_returns_empty_list_when_schedule_is_missing(self):
        schedules = get_schedules(999)

        assert schedules == []


class TestDeleteSchedules:
    def test_delete_selected_weekdays(self):
        save_schedule(123, "월화수", "09:00", "18:00")

        deleted_count = delete_schedules(123, "월화")
        schedules = get_schedules(123)

        assert deleted_count == 2
        assert [schedule.weekday for schedule in schedules] == [2]

    def test_does_not_delete_other_user_schedules(self):
        save_schedule(123, "월", "09:00", "18:00")
        save_schedule(456, "월", "10:00", "19:00")

        delete_schedules(123, "월")

        assert get_schedules(123) == []
        assert len(get_schedules(456)) == 1

    def test_returns_zero_when_schedule_is_missing(self):
        save_schedule(123, "월", "09:00", "18:00")

        deleted_count = delete_schedules(123, "화")

        assert deleted_count == 0
        assert len(get_schedules(123)) == 1

    def test_delete_all_user_schedules(self):
        save_schedule(123, "월화", "09:00", "18:00")
        save_schedule(456, "금", "10:00", "19:00")

        deleted_count = delete_all_schedules(123)

        assert deleted_count == 2
        assert get_schedules(123) == []
        assert len(get_schedules(456)) == 1


class TestFindNextSchedule:
    def test_finds_next_schedule_across_weekend(self):
        save_schedule(123, "금", "09:00", "18:00")
        save_schedule(123, "월", "09:00", "18:00")
        save_schedule(123, "수", "08:00", "17:00")

        schedule, remaining_minutes = find_next_schedule(
            user_id=123,
            current_weekday=4,
            current_time_minutes=20 * 60,
        )

        assert schedule.weekday == 0
        assert schedule.start_time_minutes == 540
        assert remaining_minutes == 3660


class TestFindActiveSchedule:
    def test_finds_active_day_shift(self):
        save_schedule(123, "수", "09:00", "18:00")

        schedule, remaining_minutes = find_active_schedule(
            user_id=123,
            current_weekday=2,
            current_time_minutes=15 * 60,
        )

        assert schedule.weekday == 2
        assert remaining_minutes == 180

    def test_returns_none_outside_day_shift(self):
        save_schedule(123, "수", "09:00", "18:00")

        schedule, remaining_minutes = find_active_schedule(
            user_id=123,
            current_weekday=2,
            current_time_minutes=20 * 60,
        )

        assert schedule is None
        assert remaining_minutes is None

    def test_finds_night_shift_before_midnight(self):
        save_schedule(123, "월", "22:00", "06:00")

        schedule, remaining_minutes = find_active_schedule(
            user_id=123,
            current_weekday=0,
            current_time_minutes=23 * 60,
        )

        assert schedule.weekday == 0
        assert remaining_minutes == 420

    def test_finds_previous_day_night_shift_after_midnight(self):
        save_schedule(123, "월", "22:00", "06:00")

        schedule, remaining_minutes = find_active_schedule(
            user_id=123,
            current_weekday=1,
            current_time_minutes=2 * 60,
        )

        assert schedule.weekday == 0
        assert remaining_minutes == 240

    def test_does_not_start_todays_night_shift_early(self):
        save_schedule(123, "화", "22:00", "06:00")

        schedule, remaining_minutes = find_active_schedule(
            user_id=123,
            current_weekday=1,
            current_time_minutes=2 * 60,
        )

        assert schedule is None
        assert remaining_minutes is None


class TestMinutesUntilEnd:
    def test_day_shift(self):
        result = minutes_until_end(
            current_time_minutes=15 * 60,
            start_time_minutes=9 * 60,
            end_time_minutes=18 * 60,
        )

        assert result == 180

    def test_outside_day_shift(self):
        result = minutes_until_end(
            current_time_minutes=20 * 60,
            start_time_minutes=9 * 60,
            end_time_minutes=18 * 60,
        )

        assert result is None

    def test_night_shift_before_midnight(self):
        result = minutes_until_end(
            current_time_minutes=23 * 60,
            start_time_minutes=22 * 60,
            end_time_minutes=6 * 60,
        )

        assert result == 420

    def test_night_shift_after_midnight(self):
        result = minutes_until_end(
            current_time_minutes=2 * 60,
            start_time_minutes=22 * 60,
            end_time_minutes=6 * 60,
        )

        assert result == 240

    def test_outside_night_shift(self):
        result = minutes_until_end(
            current_time_minutes=12 * 60,
            start_time_minutes=22 * 60,
            end_time_minutes=6 * 60,
        )

        assert result is None


class TestMinutesUntilStart:
    def test_same_day(self):
        result = minutes_until_start(
            current_weekday=0,
            current_time_minutes=8 * 60,
            target_weekday=0,
            start_time_minutes=9 * 60,
        )

        assert result == 60

    def test_across_weekend(self):
        result = minutes_until_start(
            current_weekday=4,
            current_time_minutes=20 * 60,
            target_weekday=0,
            start_time_minutes=9 * 60,
        )

        assert result == 3660


class TestFormatMinutes:
    def test_minutes_only(self):
        assert format_minutes(30) == "30분"

    def test_hours_only(self):
        assert format_minutes(120) == "2시간"

    def test_hours_and_minutes(self):
        assert format_minutes(150) == "2시간 30분"

    def test_zero_minutes(self):
        assert format_minutes(0) == "0분"

    def test_rejects_negative_minutes(self):
        with pytest.raises(ValueError):
            format_minutes(-1)
