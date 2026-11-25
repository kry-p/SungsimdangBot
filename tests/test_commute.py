from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from modules.commute import (
    ScheduleOverlapError,
    delete_all_schedules,
    delete_schedules,
    find_active_schedule,
    find_next_schedule,
    format_minutes,
    get_schedules,
    minutes_until_end,
    minutes_until_start,
    parse_end_time_to_minutes,
    parse_time_to_minutes,
    parse_weekdays,
    save_schedule,
)
from modules.database import CommuteSchedule, db


class TestParseTime:
    def test_valid_time(self):
        assert parse_time_to_minutes("9:00") == 540
        assert parse_time_to_minutes("09:00") == 540
        assert parse_time_to_minutes("18:30") == 1110

    @pytest.mark.parametrize(
        "time_text",
        ("9:0", "9:5", "009:00", "09:000", "+9:00", "09:+00"),
    )
    def test_invalid_time_format(self, time_text):
        with pytest.raises(ValueError):
            parse_time_to_minutes(time_text)

    def test_invalid_hour(self):
        with pytest.raises(ValueError):
            parse_time_to_minutes("24:00")

    def test_invalid_minute(self):
        with pytest.raises(ValueError):
            parse_time_to_minutes("09:60")

    def test_end_time_accepts_end_of_day(self):
        assert parse_end_time_to_minutes("24:00") == 24 * 60

    def test_end_time_rejects_minutes_after_end_of_day(self):
        with pytest.raises(ValueError):
            parse_end_time_to_minutes("24:01")


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

    def test_accept_end_of_day_only_as_end_time(self):
        save_schedule(123, "월", "00:01", "24:00")

        schedule = CommuteSchedule.get()
        assert schedule.start_time_minutes == 1
        assert schedule.end_time_minutes == 24 * 60

    def test_reject_end_of_day_as_start_time(self):
        with pytest.raises(ValueError):
            save_schedule(123, "월", "24:00", "00:01")

        assert CommuteSchedule.select().count() == 0

    def test_rolls_back_all_weekdays_when_save_fails(self, monkeypatch):
        save_schedule(123, "월", "09:00", "18:00")
        original_replace = CommuteSchedule.replace
        call_count = 0

        def replace_with_failure(**kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 2:
                raise RuntimeError("simulated database failure")

            return original_replace(**kwargs)

        monkeypatch.setattr(CommuteSchedule, "replace", replace_with_failure)

        with pytest.raises(RuntimeError, match="simulated database failure"):
            save_schedule(123, "월화", "10:00", "19:00")

        schedules = list(CommuteSchedule.select())
        assert len(schedules) == 1
        assert schedules[0].weekday == 0
        assert schedules[0].start_time_minutes == 9 * 60
        assert schedules[0].end_time_minutes == 18 * 60


class TestScheduleOverlap:
    @pytest.mark.parametrize("reverse_order", (False, True))
    @pytest.mark.parametrize(
        "first, second",
        (
            (("월", "22:00", "06:00"), ("화", "05:00", "14:00")),
            (("일", "22:00", "06:00"), ("월", "05:00", "14:00")),
            (("월", "09:00", "18:00"), ("일", "22:00", "10:00")),
            (("월", "23:00", "02:00"), ("화", "01:00", "00:00")),
            (("월", "00:00", "24:00"), ("일", "23:00", "01:00")),
        ),
    )
    def test_rejects_overlap_in_either_registration_order(self, first, second, reverse_order):
        if reverse_order:
            first, second = second, first
        save_schedule(123, *first)

        with pytest.raises(ScheduleOverlapError):
            save_schedule(123, *second)

        assert len(get_schedules(123)) == 1

    @pytest.mark.parametrize("reverse_order", (False, True))
    @pytest.mark.parametrize(
        "first, second",
        (
            (("월", "22:00", "06:00"), ("화", "06:00", "14:00")),
            (("일", "22:00", "06:00"), ("월", "06:00", "14:00")),
            (("월", "20:00", "00:00"), ("화", "00:00", "09:00")),
            (("일", "20:00", "00:00"), ("월", "00:00", "09:00")),
            (("월", "00:00", "24:00"), ("화", "00:00", "24:00")),
            (("일", "00:00", "24:00"), ("월", "00:00", "24:00")),
        ),
    )
    def test_allows_touching_boundaries(self, first, second, reverse_order):
        if reverse_order:
            first, second = second, first

        save_schedule(123, *first)
        save_schedule(123, *second)

        assert len(get_schedules(123)) == 2

    def test_ignores_other_users_schedules(self):
        save_schedule(123, "일", "22:00", "06:00")

        assert save_schedule(456, "월", "05:00", "14:00") == 1

    def test_rejected_update_preserves_existing_schedule(self):
        save_schedule(123, "월", "22:00", "06:00")
        save_schedule(123, "화", "06:00", "14:00")

        with pytest.raises(ScheduleOverlapError):
            save_schedule(123, "화", "05:00", "14:00")

        assert get_schedules(123)[1].start_time_minutes == 6 * 60

    def test_rejects_entire_batch_without_replacing_or_adding_schedules(self):
        save_schedule(123, "월", "09:00", "18:00")
        save_schedule(123, "수", "00:00", "09:00")

        with pytest.raises(ScheduleOverlapError):
            save_schedule(123, "월화", "22:00", "06:00")

        schedules = get_schedules(123)
        assert [(s.weekday, s.start_time_minutes, s.end_time_minutes) for s in schedules] == [
            (0, 9 * 60, 18 * 60),
            (2, 0, 9 * 60),
        ]

    @pytest.mark.parametrize("weekdays", ("월화", "화월"))
    def test_excludes_all_replaced_weekdays_before_validating_batch(self, weekdays):
        save_schedule(123, "월", "22:00", "06:00")
        save_schedule(123, "화", "06:00", "14:00")

        assert save_schedule(123, weekdays, "05:00", "14:00") == 2

        assert [(s.start_time_minutes, s.end_time_minutes) for s in get_schedules(123)] == [
            (5 * 60, 14 * 60),
            (5 * 60, 14 * 60),
        ]

    @pytest.mark.parametrize("start, end", (("22:00", "06:00"), ("00:00", "24:00")))
    def test_accepts_full_week_batch(self, start, end):
        assert save_schedule(123, "월화수목금토일", start, end) == 7
        assert len(get_schedules(123)) == 7

    def test_leaves_unrelated_legacy_overlaps_unchanged(self):
        CommuteSchedule.create(user_id=123, weekday=0, start_time_minutes=22 * 60, end_time_minutes=6 * 60)
        CommuteSchedule.create(user_id=123, weekday=1, start_time_minutes=5 * 60, end_time_minutes=14 * 60)

        assert save_schedule(123, "금", "09:00", "18:00") == 1

        assert [(s.weekday, s.start_time_minutes, s.end_time_minutes) for s in get_schedules(123)] == [
            (0, 22 * 60, 6 * 60),
            (1, 5 * 60, 14 * 60),
            (4, 9 * 60, 18 * 60),
        ]

    @pytest.mark.parametrize("journal_mode", ("delete", "wal"))
    def test_concurrent_conflicting_registrations_only_save_one_schedule(self, journal_mode):
        db.pragma("journal_mode", journal_mode)
        ready = Barrier(2, timeout=5)

        def register(weekday, start, end):
            with db.connection_context():
                ready.wait()
                try:
                    save_schedule(123, weekday, start, end)
                except ScheduleOverlapError:
                    return "overlap"
                return "saved"

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(register, "일", "22:00", "06:00")
            second = executor.submit(register, "월", "05:00", "14:00")
            results = [first.result(timeout=10), second.result(timeout=10)]

        assert sorted(results) == ["overlap", "saved"]
        assert len(get_schedules(123)) == 1


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

    def test_finds_shift_ending_at_end_of_day(self):
        save_schedule(123, "월", "00:01", "24:00")

        schedule, remaining_minutes = find_active_schedule(
            user_id=123,
            current_weekday=0,
            current_time_minutes=23 * 60 + 59,
        )

        assert schedule.weekday == 0
        assert remaining_minutes == 1


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

    def test_end_of_day(self):
        result = minutes_until_end(
            current_time_minutes=23 * 60 + 59,
            start_time_minutes=1,
            end_time_minutes=24 * 60,
        )

        assert result == 1

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
