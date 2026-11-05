"""The ReadyBy calculation.

This is the whole product in one function.

    arrival 10:30, café prep 8 minutes
      -> start preparing 10:22
      -> ready by 10:30

Rules, in order:

* **Ready by == the arrival time.** The customer is told the order will be
  finished at the moment they said they would walk in. That is the promise.
* **Start preparing == arrival − the café's preparation time.** The café starts
  exactly one preparation window before the customer arrives.
* **A small operational buffer guards booking, not the promise.** An arrival is
  only bookable if it leaves the café at least
  ``prep + PREPARATION_BUFFER_MINUTES`` of runway from now, so a customer
  cannot order a drink for "now". Keeping the buffer out of the start-time maths
  is what makes ``arrival 10:30 / prep 8 -> 10:22`` hold exactly.
* **Opening hours cap the booking window.** The café must still be open when the
  order is ready.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

# Defaults. Each one can be overridden per environment through Django settings
# (see ``readyby_api.settings.READYBY_RULES``) so a café with a slower kitchen
# can widen the lead time without a code change. The constants stay the
# documented defaults and the fallback when settings are unavailable.
DEFAULT_PREPARATION_BUFFER_MINUTES = 2
DEFAULT_MINIMUM_LEAD_MINUTES = 5
DEFAULT_MAX_BOOKING_HORIZON_HOURS = 24
DEFAULT_COLLECTION_GRACE_MINUTES = 30
SLOT_INTERVAL_MINUTES = 15


def _rule(name: str, default: int) -> int:
    """Read a pilot rule from Django settings, falling back to the default."""
    try:
        from django.conf import settings

        configured = getattr(settings, "READYBY_RULES", {}).get(name, default)
        return max(0, int(configured))
    except Exception:
        return default


def preparation_buffer_minutes() -> int:
    return _rule("PREPARATION_BUFFER_MINUTES", DEFAULT_PREPARATION_BUFFER_MINUTES)


def minimum_lead() -> int:
    return _rule("MINIMUM_LEAD_MINUTES", DEFAULT_MINIMUM_LEAD_MINUTES)


def collection_grace_minutes() -> int:
    return _rule("COLLECTION_GRACE_MINUTES", DEFAULT_COLLECTION_GRACE_MINUTES)


def max_booking_horizon() -> timedelta:
    return timedelta(hours=_rule("MAX_BOOKING_HORIZON_HOURS", DEFAULT_MAX_BOOKING_HORIZON_HOURS))


# Kept as module constants for readability at the call sites and for tests that
# assert the documented defaults.
PREPARATION_BUFFER_MINUTES = DEFAULT_PREPARATION_BUFFER_MINUTES
MINIMUM_LEAD_MINUTES = DEFAULT_MINIMUM_LEAD_MINUTES
COLLECTION_GRACE_MINUTES = DEFAULT_COLLECTION_GRACE_MINUTES
MAX_BOOKING_HORIZON = timedelta(hours=DEFAULT_MAX_BOOKING_HORIZON_HOURS)


@dataclass(frozen=True)
class ReadyByPlan:
    """Everything the customer and the café need to know about one order's timing."""

    arrival_time: datetime
    prep_time_minutes: int
    start_preparing_at: datetime
    estimated_ready_at: datetime

    @property
    def buffer_minutes(self) -> int:
        return preparation_buffer_minutes()


def build_ready_by_plan(arrival_time: datetime, prep_time_minutes: int) -> ReadyByPlan:
    """Derive the start and ready-by times for a given arrival.

    ``arrival_time`` must be timezone aware. ``prep_time_minutes`` is coerced to a
    positive integer so a mis-configured café can never produce a backwards plan.
    """
    if arrival_time.tzinfo is None:
        raise ValueError("arrival_time must be timezone aware")

    prep = max(1, int(prep_time_minutes))
    return ReadyByPlan(
        arrival_time=arrival_time,
        prep_time_minutes=prep,
        start_preparing_at=arrival_time - timedelta(minutes=prep),
        estimated_ready_at=arrival_time,
    )


def basket_prep_time_minutes(
    lines: list[tuple[int, int]], *, kitchen_capacity: int = 1, fallback_minutes: int = 1
) -> int:
    """Estimate one basket's preparation time without adding every item blindly.

    ``lines`` is ``[(item_prep_minutes, quantity), ...]``. A kitchen prepares up
    to ``kitchen_capacity`` items at once, so total work is spread across those
    parallel stations. The basket can never finish faster than its slowest
    single item, and a real kitchen never gets to zero minutes.
    """
    work = [(max(1, int(prep)), max(1, int(quantity))) for prep, quantity in lines]
    if not work:
        return max(1, int(fallback_minutes))

    capacity = max(1, int(kitchen_capacity))
    total_work = sum(prep * quantity for prep, quantity in work)
    longest_item = max(prep for prep, _quantity in work)
    parallel_time = (total_work + capacity - 1) // capacity
    return max(1, longest_item, parallel_time)


def slot_start(arrival_time: datetime) -> datetime:
    """The start of the 15-minute arrival slot containing ``arrival_time``."""
    minute = arrival_time.minute - (arrival_time.minute % SLOT_INTERVAL_MINUTES)
    return arrival_time.replace(minute=minute, second=0, microsecond=0)


def slot_end(arrival_time: datetime) -> datetime:
    return slot_start(arrival_time) + timedelta(minutes=SLOT_INTERVAL_MINUTES)


def ceil_to_slot(moment: datetime) -> datetime:
    """The first slot boundary at or after ``moment``."""
    start = slot_start(moment)
    if start == moment:
        return start
    return start + timedelta(minutes=SLOT_INTERVAL_MINUTES)


def minimum_lead_minutes(prep_time_minutes: int) -> int:
    """How far ahead a customer must book for a given preparation time."""
    return max(1, int(prep_time_minutes)) + preparation_buffer_minutes()


def earliest_bookable_arrival(
    prep_time_minutes: int, *, moment: datetime
) -> datetime:
    """The soonest arrival a café can realistically accept right now."""
    lead = max(minimum_lead_minutes(prep_time_minutes), minimum_lead())
    return moment + timedelta(minutes=lead)


def latest_bookable_arrival(moment: datetime) -> datetime:
    """The furthest ahead a customer may book."""
    return moment + max_booking_horizon()


def is_arrival_bookable(
    arrival_time: datetime,
    prep_time_minutes: int,
    *,
    moment: datetime,
) -> bool:
    """Whether the arrival is far enough ahead for the café to commit to it."""
    return (
        earliest_bookable_arrival(prep_time_minutes, moment=moment)
        <= arrival_time
        <= latest_bookable_arrival(moment)
    )


def minutes_until_arrival(arrival_time: datetime, *, moment: datetime) -> int:
    """Whole minutes until the customer is due. Never negative."""
    delta = (arrival_time - moment).total_seconds() / 60
    return max(0, int(round(delta)))


def collection_window_closed(
    arrival_time: datetime, *, moment: datetime
) -> bool:
    """True once the customer has had their collection window and gone."""
    return moment > arrival_time + timedelta(minutes=collection_grace_minutes())