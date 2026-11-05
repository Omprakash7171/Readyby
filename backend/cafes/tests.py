"""Opening-hours evaluation, including split shifts and overnight closing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone as dt_timezone

from django.test import SimpleTestCase

from cafes.hours import (
    format_hours_summary,
    is_open_at,
    next_closing_at,
    open_state_at,
    parse_opening_hours,
)

LONDON = dt_timezone(timedelta(hours=1))

# 2026-05-04 is a Monday.
SPLIT_SHIFT = {"mon": [["07:30", "11:30"], ["14:00", "18:00"]], "tue": [["07:30", "18:00"]]}
WEEKDAYS_ONLY = {
    "mon": [["09:00", "17:00"]],
    "tue": [["09:00", "17:00"]],
    "wed": [["09:00", "17:00"]],
    "thu": [["09:00", "17:00"]],
    "fri": [["09:00", "17:00"]],
}
OVERNIGHT = {"fri": [["22:00", "02:00"]]}


def at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 5, day, hour, minute, tzinfo=LONDON)


class ParseOpeningHoursTests(SimpleTestCase):
    def test_missing_and_malformed_days_are_ignored_not_fatal(self):
        parsed = parse_opening_hours(
            {
                "mon": [["07:00", "17:00"]],
                "nonsense": [["07:00", "17:00"]],
                "tue": "not a list",
                "wed": [["only-one"]],
                "thu": [["25:99", "17:00"]],
            }
        )
        self.assertEqual(len(parsed[0]), 1)
        self.assertEqual(parsed[1], [])
        self.assertEqual(parsed[2], [])
        self.assertEqual(parsed[3], [])

    def test_a_non_dict_is_treated_as_closed(self):
        self.assertFalse(any(parse_opening_hours("not a dict").values()))


class OpenStateTests(SimpleTestCase):
    def test_open_inside_a_normal_window(self):
        self.assertTrue(is_open_at(SPLIT_SHIFT, at(4, 9)))
        self.assertEqual(open_state_at(SPLIT_SHIFT, at(4, 9)).key, "open")

    def test_closed_between_split_shifts(self):
        self.assertFalse(is_open_at(SPLIT_SHIFT, at(4, 12, 30)))
        self.assertEqual(open_state_at(SPLIT_SHIFT, at(4, 12, 30)).key, "closed")

    def test_reopens_for_the_afternoon_shift(self):
        self.assertTrue(is_open_at(SPLIT_SHIFT, at(4, 15)))

    def test_days_hours_are_not_applied_to_every_day(self):
        """Saturday must not inherit Monday's hours."""
        # 2026-05-09 is a Saturday.
        self.assertFalse(is_open_at(WEEKDAYS_ONLY, at(9, 12)))
        # 2026-05-08 is a Friday.
        self.assertTrue(is_open_at(WEEKDAYS_ONLY, at(8, 12)))

    def test_closing_soon_is_flagged_before_shutting_time(self):
        state = open_state_at(SPLIT_SHIFT, at(4, 17, 45), closing_soon_minutes=30)
        self.assertEqual(state.key, "closing-soon")
        self.assertTrue(state.can_order)

    def test_closing_soon_threshold_is_respected(self):
        # Closes at 18:00: 40 minutes left is "open", 20 minutes left is "soon".
        self.assertEqual(open_state_at(SPLIT_SHIFT, at(4, 17, 20), 30).key, "open")
        self.assertEqual(open_state_at(SPLIT_SHIFT, at(4, 17, 40), 30).key, "closing-soon")

    def test_closed_at_the_exact_closing_time(self):
        self.assertFalse(is_open_at(SPLIT_SHIFT, at(4, 18, 0)))


class OvernightShiftTests(SimpleTestCase):
    def test_a_shift_running_past_midnight_covers_the_next_day(self):
        # Friday opens at 22:00 and closes at 02:00 on Saturday.
        self.assertTrue(is_open_at(OVERNIGHT, at(8, 23)))
        self.assertTrue(is_open_at(OVERNIGHT, at(9, 0, 30)))
        self.assertFalse(is_open_at(OVERNIGHT, at(9, 2, 30)))

    def test_saturday_is_not_open_before_its_shift_starts(self):
        self.assertFalse(is_open_at(OVERNIGHT, at(9, 12)))


class NextClosingAtTests(SimpleTestCase):
    def test_returns_todays_closing_time(self):
        self.assertEqual(next_closing_at(SPLIT_SHIFT, at(4, 9)), at(4, 11, 30))

    def test_returns_none_when_already_closed(self):
        self.assertIsNone(next_closing_at(SPLIT_SHIFT, at(4, 13)))

    def test_returns_the_closing_time_of_the_later_split_shift(self):
        self.assertEqual(next_closing_at(SPLIT_SHIFT, at(4, 15)), at(4, 18))

    def test_handles_a_window_running_across_midnight(self):
        closing = next_closing_at(OVERNIGHT, at(8, 23))
        self.assertEqual(closing, at(9, 2))


class HoursSummaryTests(SimpleTestCase):
    def test_unset_hours_say_so(self):
        self.assertEqual(format_hours_summary({}), "Hours not set")

    def test_a_single_day_is_named(self):
        self.assertIn("Mon", format_hours_summary({"mon": [["07:00", "17:00"]]}))
        self.assertIn("07:00", format_hours_summary({"mon": [["07:00", "17:00"]]}))