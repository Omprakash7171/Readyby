"""Order services: placement and status transitions.

Both entry points validate, log and use the shared ready-by calculation. The API
layer is deliberately thin — all rules live here so they can be tested without
HTTP.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction

from cafes.hours import next_closing_at
from cafes.models import Cafe, Destination, MenuItem
from readyby.clock import format_clock, format_day_clock
from readyby.clock import now as clock_now
from readyby.ready_by import (
    SLOT_INTERVAL_MINUTES,
    basket_prep_time_minutes,
    build_ready_by_plan,
    ceil_to_slot,
    earliest_bookable_arrival,
    latest_bookable_arrival,
    minimum_lead_minutes,
    preparation_buffer_minutes,
    slot_end,
    slot_start,
)

from readyby_api.exceptions import InvalidTransitionException, OrderPlacementException

from ..models import Order, OrderItem, OrderStatus, OrderStatusEvent
from ..state import (
    can_transition,
    customer_may_cancel,
    merchant_may_cancel,
    merchant_may_reject,
)

logger = logging.getLogger("orders")

MAX_LINE_QUANTITY = 20
MAX_DISTINCT_LINES = 20

REASON_CAFE_INACTIVE = "cafe_inactive"
REASON_CAFE_CLOSED = "cafe_closed"
REASON_ARRIVAL_PAST = "arrival_unavailable"
REASON_ARRIVAL_TOO_SOON = "arrival_too_soon"
REASON_ARRIVAL_TOO_FAR = "arrival_too_far"
REASON_CLOSING = "cafe_closes_before_ready"
REASON_ITEM_UNAVAILABLE = "item_unavailable"
REASON_SLOT_FULL = "slot_full"
REASON_EMPTY_CART = "empty_cart"
REASON_INVALID_QUANTITY = "invalid_quantity"

MESSAGES = {
    REASON_CAFE_INACTIVE: "This café is not taking orders right now.",
    REASON_CAFE_CLOSED: "This café is currently closed.",
    REASON_ARRIVAL_PAST: "The selected arrival time is no longer available.",
    REASON_ARRIVAL_TOO_SOON: "",  # built per café: names the real minimum
    REASON_ARRIVAL_TOO_FAR: "You can only book an arrival within the next 24 hours.",
    REASON_CLOSING: "This café closes before your order would be ready.",
    REASON_ITEM_UNAVAILABLE: "This item is currently unavailable.",
    REASON_SLOT_FULL: "That arrival slot is fully booked. Please choose another time.",
    REASON_EMPTY_CART: "Your order is empty.",
    REASON_INVALID_QUANTITY: "Each item needs a quantity of at least 1.",
}


def _too_soon_message(minimum_minutes: int) -> str:
    """Name the real minimum rather than a vague 'too soon'."""
    return (
        f"Please choose an arrival time at least {minimum_minutes} minutes "
        "from now."
    )


@dataclass(frozen=True)
class OrderLineInput:
    menu_item_id: int
    quantity: int


@dataclass(frozen=True)
class PlaceOrderResult:
    order: Order
    created: bool


def _fail(reason: str, field: str | None = None):
    message = MESSAGES[reason]
    raise OrderPlacementException(
        message,
        code=reason,
        field_errors={field: [message]} if field else None,
    )


def _validate_closing(
    cafe: Cafe, arrival_time: datetime, prep_time_minutes: int
) -> None:
    plan = build_ready_by_plan(arrival_time, prep_time_minutes)
    closing = next_closing_at(cafe.opening_hours, plan.estimated_ready_at)
    if closing is None or plan.estimated_ready_at >= closing:
        _fail(REASON_CLOSING, "arrival_time")


def _validate_arrival(
    cafe: Cafe, arrival_time: datetime, moment: datetime, prep_time_minutes: int
) -> None:
    """Reject arrival times the cafǸ could not realistically honour."""
    if arrival_time < moment:
        _fail(REASON_ARRIVAL_PAST, "arrival_time")

    if arrival_time < earliest_bookable_arrival(prep_time_minutes, moment=moment):
        message = _too_soon_message(minimum_lead_minutes(prep_time_minutes))
        raise OrderPlacementException(
            message,
            code=REASON_ARRIVAL_TOO_SOON,
            field_errors={"arrival_time": [message]},
        )

    if arrival_time > latest_bookable_arrival(moment):
        _fail(REASON_ARRIVAL_TOO_FAR, "arrival_time")

    _validate_closing(cafe, arrival_time, prep_time_minutes)


def slot_order_count(
    cafe: Cafe, arrival_time: datetime, *, exclude_order_id: int | None = None
) -> int:
    """Orders already booked into the same 15-minute arrival slot."""
    queryset = Order.objects.filter(
        cafe=cafe,
        status__in=(
            OrderStatus.PLACED,
            OrderStatus.ACCEPTED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
        ),
        arrival_time__gte=slot_start(arrival_time),
        arrival_time__lt=slot_end(arrival_time),
    )
    if exclude_order_id is not None:
        queryset = queryset.exclude(pk=exclude_order_id)
    return queryset.count()


def slot_remaining(
    cafe: Cafe, arrival_time: datetime, *, exclude_order_id: int | None = None
) -> int:
    used = slot_order_count(cafe, arrival_time, exclude_order_id=exclude_order_id)
    return max(0, cafe.slot_capacity - used)


def _validate_slot_capacity(cafe: Cafe, arrival_time: datetime) -> None:
    if slot_remaining(cafe, arrival_time) <= 0:
        _fail(REASON_SLOT_FULL, "arrival_time")


def _slot_payload(cafe: Cafe, arrival_time: datetime) -> dict:
    start = slot_start(arrival_time)
    return {
        "arrival_time": start.isoformat(),
        "time_label": format_clock(start),
        "day_label": format_day_clock(start),
        "label": format_day_clock(start),
        "remaining": slot_remaining(cafe, start),
        "capacity": cafe.slot_capacity,
    }


def _requested_slot_problem(
    cafe: Cafe, arrival_time: datetime, moment: datetime, prep_time_minutes: int
) -> str | None:
    if arrival_time < moment:
        return MESSAGES[REASON_ARRIVAL_PAST]
    if arrival_time < earliest_bookable_arrival(prep_time_minutes, moment=moment):
        return _too_soon_message(minimum_lead_minutes(prep_time_minutes))
    if arrival_time > latest_bookable_arrival(moment):
        return MESSAGES[REASON_ARRIVAL_TOO_FAR]

    closing = next_closing_at(cafe.opening_hours, arrival_time)
    if closing is None or arrival_time >= closing:
        return MESSAGES[REASON_CLOSING]
    if slot_remaining(cafe, arrival_time) <= 0:
        return MESSAGES[REASON_SLOT_FULL]
    return None


def quote_pickup(
    cafe: Cafe,
    lines: list[OrderLineInput],
    *,
    requested_arrival: datetime | None = None,
) -> dict:
    """Live preparation estimate and the next bookable 15-minute slots."""
    moment = clock_now()
    quantities: dict[int, int] = {}
    for line in lines:
        if line.quantity < 1:
            continue
        quantities[line.menu_item_id] = min(
            MAX_LINE_QUANTITY,
            quantities.get(line.menu_item_id, 0) + line.quantity,
        )

    found = {
        item.id: item
        for item in MenuItem.objects.filter(cafe=cafe, id__in=quantities)
    }
    available = [found[item_id] for item_id in quantities if item_id in found]
    unavailable = [
        found[item_id].name
        for item_id in quantities
        if item_id in found and not found[item_id].is_available
    ]
    missing = [item_id for item_id in quantities if item_id not in found]

    usable = [item for item in available if item.is_available]
    prep_time_minutes = basket_prep_time_minutes(
        [(item.prep_time_minutes, quantities[item.id]) for item in usable],
        kitchen_capacity=cafe.kitchen_capacity,
        fallback_minutes=cafe.prep_time_minutes,
    )
    earliest = earliest_bookable_arrival(prep_time_minutes, moment=moment)
    latest = latest_bookable_arrival(moment)

    slots: list[dict] = []
    candidate = ceil_to_slot(earliest)
    while candidate <= latest and len(slots) < 8:
        closing = next_closing_at(cafe.opening_hours, candidate)
        if closing is not None and candidate < closing:
            payload = _slot_payload(cafe, candidate)
            if payload["remaining"] > 0:
                slots.append(payload)
        candidate += timedelta(minutes=SLOT_INTERVAL_MINUTES)

    requested_slot = None
    if requested_arrival is not None:
        requested_slot = _slot_payload(cafe, requested_arrival)
        requested_slot["problem"] = _requested_slot_problem(
            cafe, requested_arrival, moment, prep_time_minutes
        )
        requested_slot["is_available"] = requested_slot["problem"] is None

    return {
        "cafe": cafe.slug,
        "prep_time_minutes": prep_time_minutes,
        "kitchen_capacity": cafe.kitchen_capacity,
        "slot_capacity": cafe.slot_capacity,
        "slot_interval_minutes": SLOT_INTERVAL_MINUTES,
        "earliest_arrival_time": earliest.isoformat(),
        "earliest_arrival_label": format_day_clock(earliest),
        "latest_arrival_time": latest.isoformat(),
        "latest_arrival_label": format_day_clock(latest),
        "slots": slots,
        "requested_slot": requested_slot,
        "unavailable_items": unavailable,
        "missing_item_ids": missing,
        "is_accepting_orders": cafe.is_active,
    }


def _resolve_lines(cafe: Cafe, lines: list[OrderLineInput]) -> list[MenuItem]:
    """Re-read every item from the database and confirm it can be sold.

    Prices and availability always come from the database; the client only ever
    sends item ids and quantities.
    """
    if not lines:
        _fail(REASON_EMPTY_CART)

    if len(lines) > MAX_DISTINCT_LINES:
        raise OrderPlacementException(
            "That's too many different items for one order.", code="too_many_items"
        )

    quantities: dict[int, int] = {}
    for line in lines:
        if line.quantity < 1:
            _fail(REASON_INVALID_QUANTITY, "items")
        quantities[line.menu_item_id] = quantities.get(line.menu_item_id, 0) + line.quantity

    if any(total > MAX_LINE_QUANTITY for total in quantities.values()):
        raise OrderPlacementException(
            f"Maximum {MAX_LINE_QUANTITY} of one item per order.",
            code="quantity_too_high",
            field_errors={"items": [f"Maximum {MAX_LINE_QUANTITY} of one item per order."]},
        )

    found = {
        item.id: item
        for item in MenuItem.objects.filter(cafe=cafe, id__in=quantities)
    }

    problems = _line_problems(quantities, found)
    if problems:
        raise OrderPlacementException(
            MESSAGES[REASON_ITEM_UNAVAILABLE],
            code=REASON_ITEM_UNAVAILABLE,
            field_errors={"items": problems},
        )

    return [found[item_id] for item_id in quantities]


def _line_problems(
    quantities: dict[int, int], found: dict[int, MenuItem]
) -> list[str]:
    """Human-readable reasons a requested line cannot be ordered."""
    problems: list[str] = []
    for item_id in quantities:
        item = found.get(item_id)
        if item is None:
            problems.append("An item on your order is no longer on this café's menu.")
        elif not item.is_available:
            problems.append(f"{item.name} is currently unavailable.")
    return problems


@transaction.atomic
def place_order(
    *,
    customer,
    cafe: Cafe,
    destination: Destination | None,
    arrival_time: datetime,
    lines: list[OrderLineInput],
    notes: str = "",
    idempotency_key: str = "",
) -> PlaceOrderResult:
    """Create a real order in the database.

    Runs inside one transaction and re-reads the café and menu rows, so two
    customers pressing "Place order" at the same moment can never book past a
    closing time or use a stale price.
    """
    moment = clock_now()
    key = (idempotency_key or "").strip()[:64]

    if key:
        existing = (
            Order.objects.filter(customer=customer, idempotency_key=key)
            .select_related("cafe")
            .first()
        )
        if existing is not None:
            logger.info(
                "order.replayed customer_id=%s order=%s",
                customer.pk,
                existing.public_id,
            )
            return PlaceOrderResult(order=existing, created=False)

    cafe = Cafe.objects.select_for_update().get(pk=cafe.pk)

    if not cafe.is_active:
        _fail(REASON_CAFE_INACTIVE, "cafe")

    # Check closing before resolving lines so a cafe that cannot honour the
    # arrival reports that clearly even if the basket is stale.
    _validate_closing(cafe, arrival_time, cafe.prep_time_minutes)

    menu_items = _resolve_lines(cafe, lines)

    quantity_by_item: dict[int, int] = {}
    for line in lines:
        quantity_by_item[line.menu_item_id] = (
            quantity_by_item.get(line.menu_item_id, 0) + line.quantity
        )

    prep_time_minutes = basket_prep_time_minutes(
        [
            (menu_item.prep_time_minutes, quantity_by_item[menu_item.id])
            for menu_item in menu_items
        ],
        kitchen_capacity=cafe.kitchen_capacity,
        fallback_minutes=cafe.prep_time_minutes,
    )
    _validate_arrival(cafe, arrival_time, moment, prep_time_minutes)
    _validate_slot_capacity(cafe, arrival_time)

    plan = build_ready_by_plan(arrival_time, prep_time_minutes)

    subtotal = Decimal("0.00")
    priced_lines: list[dict] = []
    for menu_item in menu_items:
        quantity = quantity_by_item[menu_item.id]
        line_total = (menu_item.price * quantity).quantize(Decimal("0.01"))
        subtotal += line_total
        priced_lines.append(
            {
                "menu_item": menu_item,
                "name": menu_item.name,
                "unit_price": menu_item.price,
                "quantity": quantity,
                "line_total": line_total,
                "art": menu_item.art,
            }
        )

    if subtotal <= Decimal("0.00"):
        _fail(REASON_EMPTY_CART)

    order = Order.objects.create(
        customer=customer,
        customer_name=customer.display_name,
        customer_email=customer.email,
        cafe=cafe,
        status=OrderStatus.PLACED,
        destination=destination,
        destination_label=_destination_label(destination, notes),
        arrival_time=plan.arrival_time,
        prep_time_minutes=plan.prep_time_minutes,
        start_preparing_time=plan.start_preparing_at,
        estimated_ready_time=plan.estimated_ready_at,
        subtotal=subtotal,
        notes=(notes or "").strip()[:280],
        idempotency_key=key,
    )

    # Snapshot the priced lines onto the order now that it exists.
    OrderItem.objects.bulk_create(
        OrderItem(order=order, **line) for line in priced_lines
    )

    OrderStatusEvent.objects.create(
        order=order,
        status=OrderStatus.PLACED,
        actor=customer,
        actor_role=customer.role,
        note="Order sent to the café.",
    )

    logger.info(
        "order.created order=%s cafe=%s customer_id=%s lines=%d subtotal=%s "
        "arrival=%s start_preparing=%s ready_by=%s buffer_minutes=%s",
        order.public_id,
        cafe.slug,
        customer.pk,
        len(priced_lines),
        subtotal,
        plan.arrival_time.isoformat(),
        plan.start_preparing_at.isoformat(),
        plan.estimated_ready_at.isoformat(),
        preparation_buffer_minutes(),
    )

    return PlaceOrderResult(order=order, created=True)


def _destination_label(destination: Destination | None, notes: str) -> str:
    if destination is not None:
        return destination.name
    return (notes or "").strip()[:120] or "Not specified"


@transaction.atomic
def transition_order(
    order: Order,
    *,
    to_status: str,
    actor=None,
    note: str = "",
    as_merchant: bool = False,
    as_customer: bool = False,
) -> Order:
    """Move an order to ``to_status``, refusing anything the machine forbids."""
    previous_status = order.status

    if to_status not in OrderStatus.values:
        raise InvalidTransitionException(
            "That status change is not allowed.", code="invalid_status"
        )

    if to_status == OrderStatus.REJECTED:
        # Only the café can reject, and only before it has accepted. Checked
        # before the generic rule so the message is specific.
        if not as_merchant or not merchant_may_reject(order):
            raise InvalidTransitionException(
                "This order can no longer be rejected.",
                code="rejection_closed",
                field_errors={"status": ["This order can no longer be rejected."]},
            )

    if to_status == OrderStatus.CANCELLED:
        # Check who is asking before the generic rule, so the customer is told
        # "it is too late to cancel" rather than a bare "not allowed".
        allowed = (
            customer_may_cancel(order)
            if as_customer
            else merchant_may_cancel(order) if as_merchant else False
        )
        if not allowed:
            raise InvalidTransitionException(
                "This order can no longer be cancelled.",
                code="cancellation_closed",
                field_errors={"status": ["This order can no longer be cancelled."]},
            )

    if not can_transition(previous_status, to_status):
        raise InvalidTransitionException(
            "That status change is not allowed.",
            code="invalid_transition",
            field_errors={
                "status": ["That status change is not allowed for this order."]
            },
        )

    moment = clock_now()
    order.status = to_status

    if to_status == OrderStatus.ACCEPTED:
        order.accepted_at = moment
    elif to_status == OrderStatus.PREPARING:
        order.preparing_at = moment
    elif to_status == OrderStatus.READY:
        order.ready_at = moment
    elif to_status == OrderStatus.COLLECTED:
        order.collected_at = moment
    elif to_status == OrderStatus.REJECTED:
        order.rejected_at = moment
        order.rejected_reason = (note or "").strip()[:140]
    elif to_status == OrderStatus.CANCELLED:
        order.cancelled_at = moment
        order.cancel_reason = (note or "").strip()[:140]

    order.save(
        update_fields=[
            "status",
            "accepted_at",
            "preparing_at",
            "ready_at",
            "collected_at",
            "rejected_at",
            "rejected_reason",
            "cancelled_at",
            "cancel_reason",
            "updated_at",
        ]
    )

    OrderStatusEvent.objects.create(
        order=order,
        status=to_status,
        actor=actor,
        actor_role=getattr(actor, "role", "") if actor else "",
        note=(note or "").strip()[:140],
    )

    logger.info(
        "order.status_changed order=%s from=%s to=%s actor_id=%s",
        order.public_id,
        previous_status,
        to_status,
        getattr(actor, "pk", None),
    )

    return order
