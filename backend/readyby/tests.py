"""The ReadyBy calculation is the product; these tests pin it down."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase, override_settings

from readyby.clock import format_clock, format_date, format_day_clock
from readyby.ready_by import (
    MAX_BOOKING_HORIZON,
    MINIMUM_LEAD_MINUTES,
    PREPARATION_BUFFER_MINUTES,
    build_ready_by_plan,
    collection_window_closed,
    earliest_bookable_arrival,
    is_arrival_bookable,
    latest_bookable_arrival,
    minimum_lead,
    minimum_lead_minutes,
    minutes_until_arrival,
)

LONDON = ZoneInfo("Europe/London")


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 5, 4, hour, minute, tzinfo=LONDON)


class BuildReadyByPlanTests(SimpleTestCase):
    def test_arrival_1030_with_eight_minute_prep_starts_1022(self):
        """The headline promise, exactly as the product describes it."""
        plan = build_ready_by_plan(at(10, 30), 8)

        self.assertEqual(plan.arrival_time, at(10, 30))
        self.assertEqual(plan.prep_time_minutes, 8)
        self.assertEqual(plan.start_preparing_at, at(10, 22))
        self.assertEqual(plan.estimated_ready_at, at(10, 30))

    def test_ready_time_is_always_the_arrival_time(self):
        for prep in (1, 5, 8, 12, 25):
            with self.subTest(prep=prep):
                plan = build_ready_by_plan(at(14, 5), prep)
                self.assertEqual(plan.estimated_ready_at, at(14, 5))

    def test_prep_time_is_coerced_to_at_least_one_minute(self):
        plan = build_ready_by_plan(at(9, 0), 0)
        self.assertEqual(plan.prep_time_minutes, 1)
        self.assertEqual(plan.start_preparing_at, at(8, 59))

    def test_buffer_never_shrinks_the_visible_start_time(self):
        """The buffer is operational, so the customer still sees 10:22."""
        plan = build_ready_by_plan(at(10, 30), 8)
        self.assertEqual(plan.start_preparing_at, at(10, 22))
        self.assertEqual(
            plan.estimated_ready_at - plan.start_preparing_at, timedelta(minutes=8)
        )

    def test_naive_datetime_is_rejected(self):
        with self.assertRaises(ValueError):
            build_ready_by_plan(datetime(2026, 5, 4, 10, 30), 8)


class BookingWindowTests(SimpleTestCase):
    def test_lead_time_is_prep_plus_buffer(self):
        self.assertEqual(minimum_lead_minutes(8), 8 + PREPARATION_BUFFER_MINUTES)
        self.assertEqual(minimum_lead_minutes(8), 10)

    def test_short_prep_still_respects_the_absolute_minimum_lead(self):
        self.assertEqual(minimum_lead_minutes(1), 3)
        moment = at(9, 0)
        self.assertEqual(
            earliest_bookable_arrival(1, moment=moment),
            moment + timedelta(minutes=MINIMUM_LEAD_MINUTES),
        )

    def test_booking_horizon_is_24_hours(self):
        self.assertEqual(MAX_BOOKING_HORIZON, timedelta(days=1))
        self.assertEqual(
            latest_bookable_arrival(at(9, 0)), at(9, 0) + timedelta(days=1)
        )

    def test_arrival_at_the_exact_earliest_moment_is_bookable(self):
        moment = at(9, 0)
        arrival = earliest_bookable_arrival(8, moment=moment)
        self.assertTrue(is_arrival_bookable(arrival, 8, moment=moment))

    def test_one_minute_too_soon_is_rejected(self):
        moment = at(9, 0)
        arrival = earliest_bookable_arrival(8, moment=moment) - timedelta(minutes=1)
        self.assertFalse(is_arrival_bookable(arrival, 8, moment=moment))

    def test_beyond_the_horizon_is_rejected(self):
        moment = at(9, 0)
        arrival = latest_bookable_arrival(moment) + timedelta(minutes=1)
        self.assertFalse(is_arrival_bookable(arrival, 8, moment=moment))

    def test_a_slow_cafe_needs_more_lead_time_than_a_fast_one(self):
        moment = at(9, 0)
        arrival = moment + timedelta(minutes=12)
        self.assertTrue(is_arrival_bookable(arrival, 8, moment=moment))
        self.assertFalse(is_arrival_bookable(arrival, 20, moment=moment))


class ConfigurableRuleTests(SimpleTestCase):
    """The booking window is tunable per environment, not hardcoded."""

    @override_settings(READYBY_RULES={"PREPARATION_BUFFER_MINUTES": 7})
    def test_a_wider_buffer_demands_more_lead_time(self):
        self.assertEqual(minimum_lead_minutes(8), 15)
        moment = at(9, 0)
        self.assertEqual(
            earliest_bookable_arrival(8, moment=moment), moment + timedelta(minutes=15)
        )

    @override_settings(READYBY_RULES={"MINIMUM_LEAD_MINUTES": 20})
    def test_a_slower_kitchen_can_widen_the_absolute_minimum(self):
        moment = at(9, 0)
        # An 8 minute prep only asked for 10 minutes by default; the café's
        # rule now insists on 20.
        self.assertFalse(
            is_arrival_bookable(moment + timedelta(minutes=12), 8, moment=moment)
        )
        self.assertTrue(
            is_arrival_bookable(moment + timedelta(minutes=21), 8, moment=moment)
        )

    @override_settings(READYBY_RULES={"MAX_BOOKING_HORIZON_HOURS": 2})
    def test_the_horizon_can_be_shortened(self):
        moment = at(9, 0)
        self.assertEqual(
            latest_bookable_arrival(moment), moment + timedelta(hours=2)
        )
        self.assertFalse(
            is_arrival_bookable(moment + timedelta(hours=3), 8, moment=moment)
        )

    @override_settings(READYBY_RULES={})
    def test_unset_rules_fall_back_to_the_documented_defaults(self):
        self.assertEqual(minimum_lead(), MINIMUM_LEAD_MINUTES)
        self.assertEqual(minimum_lead_minutes(8), 8 + PREPARATION_BUFFER_MINUTES)

    def test_the_start_time_is_never_moved_by_the_buffer(self):
        """The buffer guards booking; it must not change the visible promise."""
        with override_settings(READYBY_RULES={"PREPARATION_BUFFER_MINUTES": 30}):
            plan = build_ready_by_plan(at(10, 30), 8)
        self.assertEqual(plan.start_preparing_at, at(10, 22))
        self.assertEqual(plan.estimated_ready_at, at(10, 30))


class MinutesUntilArrivalTests(SimpleTestCase):
    def test_counts_down_and_never_goes_negative(self):
        arrival = at(10, 0)
        self.assertEqual(minutes_until_arrival(arrival, moment=at(9, 30)), 30)
        self.assertEqual(minutes_until_arrival(arrival, moment=at(10, 20)), 0)

    def test_collection_window_closes_after_the_grace_period(self):
        arrival = at(10, 0)
        self.assertFalse(collection_window_closed(arrival, moment=at(10, 10)))
        self.assertTrue(collection_window_closed(arrival, moment=at(10, 31)))


class ClockFormattingTests(SimpleTestCase):
    """These must work on Windows, where glibc ``strftime`` flags are missing."""

    def test_format_clock_uses_a_12_hour_clock_without_leading_zero(self):
        self.assertEqual(format_clock(at(10, 30)), "10:30 AM")
        self.assertEqual(format_clock(at(9, 5)), "9:05 AM")
        self.assertEqual(format_clock(at(13, 0)), "1:00 PM")
        self.assertEqual(format_clock(at(0, 15)), "12:15 AM")
        self.assertEqual(format_clock(at(12, 0)), "12:00 PM")

    def test_format_day_clock_names_today_and_tomorrow(self):
        today = datetime.now(tz=LONDON).replace(hour=10, minute=30)
        tomorrow = today + timedelta(days=1)
        self.assertEqual(format_day_clock(today), "Today 10:30 AM")
        self.assertEqual(format_day_clock(tomorrow), "Tomorrow 10:30 AM")

    def test_format_date_does_not_lead_with_zero(self):
        self.assertEqual(format_date(at(10, 30)), "4 May 2026")