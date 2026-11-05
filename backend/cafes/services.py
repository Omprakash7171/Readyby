"""Café discovery: what a customer can order, and when.

Used by the café list endpoint so the explore screen never has to re-derive
open/closed state or the ready-by maths.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from readyby.clock import format_clock
from readyby.ready_by import (
    ReadyByPlan,
    build_ready_by_plan,
    is_arrival_bookable,
)

from .hours import OpenState, next_closing_at, open_state_at
from .models import Cafe, Destination

REASON_CLOSED = "cafe_closed"
REASON_INACTIVE = "cafe_inactive"
REASON_ARRIVAL = "arrival_unavailable"
REASON_NO_DISTANCE = "distance_unavailable"


@dataclass(frozen=True)
class CafeAvailability:
    cafe: Cafe
    open_state: OpenState
    open_state_label: str
    distance_metres: int | None
    walk_minutes: int | None
    plan: ReadyByPlan | None
    can_order: bool
    unavailable_reason: str | None

    @property
    def available_pickup_time(self) -> datetime | None:
        """When the café can hand the order over — the customer's arrival time."""
        return self.plan.estimated_ready_at if self.plan else None

    @property
    def start_preparing_time(self) -> datetime | None:
        return self.plan.start_preparing_at if self.plan else None


def opening_label(cafe: Cafe, moment: datetime, state: OpenState) -> str:
    """``Open until 6:00 PM`` / ``Closing soon · closes 3:00 PM`` / ``Closed``."""
    if state.key == "closed":
        return "Closed"

    closing = next_closing_at(cafe.opening_hours, moment)
    if closing is None:
        return state.label
    if state.key == "closing-soon":
        return f"Closing soon · closes {format_clock(closing)}"
    return f"Open until {format_clock(closing)}"


def cafe_availability(
    cafe: Cafe,
    *,
    destination: Destination | None,
    arrival_time: datetime | None,
    moment: datetime,
) -> CafeAvailability:
    """Work out one café's state for the customer's chosen arrival time."""
    state = open_state_at(cafe.opening_hours, moment, cafe.closing_soon_minutes)
    label = opening_label(cafe, moment, state)

    distance = cafe.distance_to(destination)
    walk = cafe.walk_minutes(distance) if distance is not None else None

    plan: ReadyByPlan | None = None
    reason: str | None = None

    if not cafe.is_active:
        reason = REASON_INACTIVE
    elif not state.can_order:
        reason = REASON_CLOSED
    elif arrival_time is None:
        reason = REASON_ARRIVAL
    elif not is_arrival_bookable(arrival_time, cafe.prep_time_minutes, moment=moment):
        reason = REASON_ARRIVAL
    else:
        plan = build_ready_by_plan(arrival_time, cafe.prep_time_minutes)
        closing = next_closing_at(cafe.opening_hours, plan.estimated_ready_at)
        if closing is None:
            reason = REASON_ARRIVAL
        elif plan.estimated_ready_at > closing - timedelta(minutes=1):
            # The café would be shutting before the order is finished.
            reason = REASON_ARRIVAL

    return CafeAvailability(
        cafe=cafe,
        open_state=state,
        open_state_label=label,
        distance_metres=distance,
        walk_minutes=walk,
        plan=plan,
        can_order=reason is None,
        unavailable_reason=reason,
    )


def sort_key(availability: CafeAvailability) -> tuple[int, int, str]:
    """Closed cafés sink, then nearest first, then alphabetical."""
    return (
        0 if availability.can_order else 1,
        availability.distance_metres if availability.distance_metres is not None else 10_000,
        availability.cafe.name.lower(),
    )


def format_distance(metres: int | None) -> str:
    if metres is None:
        return "Distance unavailable"
    if metres < 1000:
        return f"{metres} m"
    return f"{metres / 1000:.1f} km"