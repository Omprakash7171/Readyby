"""Order input validation and output shaping."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from rest_framework import serializers

from readyby.clock import format_clock, format_day_clock
from readyby.ready_by import minutes_until_arrival

from .models import Order, OrderItem, OrderStatus, PaymentMethod
from .presentation import (
    MERCHANT_HINT,
    STATUS_HEADLINE,
    STATUS_LABEL,
    STATUS_MESSAGE,
    TRACKING_STEPS,
    progress_rank,
)
from .services import MAX_LINE_QUANTITY


class OrderItemInputSerializer(serializers.Serializer):
    menu_item = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_LINE_QUANTITY)


class CreateOrderSerializer(serializers.Serializer):
    """Body for ``POST /api/orders/``.

    Deliberately contains no prices, totals or status: the server computes all
    of those. ``idempotency_key`` doubles as the duplicate-submission guard.
    """

    cafe = serializers.SlugField(max_length=80)
    destination = serializers.SlugField(max_length=64, required=False, allow_blank=True)
    arrival_time = serializers.DateTimeField()
    items = OrderItemInputSerializer(many=True, allow_empty=False)
    notes = serializers.CharField(
        max_length=280, required=False, allow_blank=True, default=""
    )
    idempotency_key = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default="", write_only=True
    )

    def validate_arrival_time(self, value: datetime) -> datetime:
        # A client clock is never trusted for "is this in the future"; the
        # service re-checks against server time. This only rejects nonsense.
        if value.year < 2020:
            raise serializers.ValidationError(
                "The selected arrival time is no longer available."
            )
        return value

    def validate_items(self, value: list[dict]) -> list[dict]:
        seen: set[int] = set()
        for line in value:
            item_id = line["menu_item"]
            if item_id in seen:
                raise serializers.ValidationError(
                    "The same item was listed twice. Adjust the quantity instead."
                )
            seen.add(item_id)
        return value


class UpdateStatusSerializer(serializers.Serializer):
    """Body for ``PATCH /api/merchant/orders/{id}/status/``."""

    status = serializers.ChoiceField(choices=OrderStatus.choices)
    note = serializers.CharField(
        max_length=140, required=False, allow_blank=True, default=""
    )


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(
        max_length=140, required=False, allow_blank=True, default=""
    )


# --------------------------------------------------------------------------- #
#  Output
# --------------------------------------------------------------------------- #


def order_item_payload(item: OrderItem) -> dict:
    return {
        "id": item.id,
        "menu_item": item.menu_item_id,
        "name": item.name,
        "unit_price": str(item.unit_price),
        "quantity": item.quantity,
        "line_total": str(item.line_total),
        "art": item.art,
    }


def order_event_payload(event) -> dict:
    return {
        "status": event.status,
        "status_label": STATUS_LABEL.get(event.status, event.status),
        "note": event.note,
        "created_at": event.created_at.isoformat(),
        "created_at_label": format_day_clock(event.created_at),
    }


def order_payload(order: Order, *, moment: datetime | None = None) -> dict:
    """Full order representation shared by the customer and merchant apps."""
    items = list(order.items.all())
    events = list(order.events.all())
    arrival = order.arrival_time

    return {
        "id": order.pk,
        "public_id": order.public_id,
        "status": order.status,
        "status_label": STATUS_LABEL.get(order.status, order.status),
        "status_headline": STATUS_HEADLINE.get(order.status, order.status),
        "status_message": STATUS_MESSAGE.get(order.status, ""),
        "progress_rank": progress_rank(order.status),
        "tracking_steps": list(TRACKING_STEPS),
        "customer": {
            "name": order.customer_name,
            "email": order.customer_email,
        },
        "cafe": {
            "slug": order.cafe.slug,
            "name": order.cafe.name,
            "address": order.cafe.address,
            "postcode": order.cafe.postcode,
            "image_url": order.cafe.image_url,
        },
        "destination": (
            {"key": order.destination.key, "name": order.destination.name}
            if order.destination_id
            else None
        ),
        "destination_label": order.destination_label,
        "items": [order_item_payload(item) for item in items],
        "item_count": sum(item.quantity for item in items),
        "subtotal": str(order.subtotal),
        "payment_method": order.payment_method,
        "payment_method_label": PaymentMethod(order.payment_method).label,
        "notes": order.notes,
        "arrival_time": arrival.isoformat(),
        "arrival_time_label": format_clock(arrival),
        "arrival_day_label": format_day_clock(arrival),
        "prep_time_minutes": order.prep_time_minutes,
        "start_preparing_time": order.start_preparing_time.isoformat(),
        "start_preparing_time_label": format_clock(order.start_preparing_time),
        "estimated_ready_time": order.estimated_ready_time.isoformat(),
        "estimated_ready_time_label": format_clock(order.estimated_ready_time),
        "minutes_until_arrival": (
            minutes_until_arrival(arrival, moment=moment) if moment else None
        ),
        "merchant_hint": MERCHANT_HINT.get(order.status, ""),
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "accepted_at": order.accepted_at.isoformat() if order.accepted_at else None,
        "ready_at": order.ready_at.isoformat() if order.ready_at else None,
        "collected_at": order.collected_at.isoformat() if order.collected_at else None,
        "rejected_at": order.rejected_at.isoformat() if order.rejected_at else None,
        "rejected_reason": order.rejected_reason,
        "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
        "cancel_reason": order.cancel_reason,
        "events": [order_event_payload(event) for event in events],
    }


def order_status_payload(order: Order, *, moment: datetime | None = None) -> dict:
    """The lightweight payload used for polling."""
    return {
        "public_id": order.public_id,
        "status": order.status,
        "status_label": STATUS_LABEL.get(order.status, order.status),
        "status_headline": STATUS_HEADLINE.get(order.status, order.status),
        "status_message": STATUS_MESSAGE.get(order.status, ""),
        "progress_rank": progress_rank(order.status),
        "estimated_ready_time": order.estimated_ready_time.isoformat(),
        "estimated_ready_time_label": format_clock(order.estimated_ready_time),
        "arrival_time_label": format_clock(order.arrival_time),
        "minutes_until_arrival": (
            minutes_until_arrival(order.arrival_time, moment=moment)
            if moment
            else None
        ),
        "updated_at": order.updated_at.isoformat(),
    }


def order_summary_payload(orders, *, moment: datetime | None = None) -> dict:
    """Compact rows for the merchant board and the customer's order list."""
    payload = []
    for order in orders:
        items = list(order.items.all())
        payload.append(
            {
                "public_id": order.public_id,
                "status": order.status,
                "status_label": STATUS_LABEL.get(order.status, order.status),
                "customer_name": order.customer_name,
                "cafe": {
                    "slug": order.cafe.slug,
                    "name": order.cafe.name,
                },
                "items": [
                    f"{item.quantity} × {item.name}" for item in items
                ],
                "items_detailed": [order_item_payload(item) for item in items],
                "subtotal": str(order.subtotal),
                "destination_label": order.destination_label,
                "arrival_time": order.arrival_time.isoformat(),
                "arrival_time_label": format_clock(order.arrival_time),
                "start_preparing_time": order.start_preparing_time.isoformat(),
                "start_preparing_time_label": format_clock(order.start_preparing_time),
                "estimated_ready_time": order.estimated_ready_time.isoformat(),
                "estimated_ready_time_label": format_clock(order.estimated_ready_time),
                "prep_time_minutes": order.prep_time_minutes,
                "minutes_until_arrival": (
                    minutes_until_arrival(order.arrival_time, moment=moment)
                    if moment
                    else None
                ),
                "merchant_hint": MERCHANT_HINT.get(order.status, ""),
                "created_at": order.created_at.isoformat(),
                "is_demo": order.cafe.is_demo,
            }
        )
    return {"count": len(payload), "results": payload}


def board_summary_payload(orders, *, moment: datetime, window_start: datetime) -> dict:
    """Headline counts for the merchant board.

    ``window_start`` bounds "today" so the numbers are honest: only orders placed
    inside the window are counted. No invented historic revenue.
    """
    in_window = [
        order
        for order in orders
        if window_start <= order.created_at
        and order.status
        not in {OrderStatus.REJECTED, OrderStatus.CANCELLED}
    ]
    dropped_today = [
        order
        for order in orders
        if window_start <= order.created_at
        and order.status in {OrderStatus.REJECTED, OrderStatus.CANCELLED}
    ]

    counts = {status: 0 for status in OrderStatus.values}
    for order in orders:
        counts[order.status] = counts.get(order.status, 0) + 1

    revenue = sum((order.subtotal for order in in_window), Decimal("0.00"))
    return {
        "orders_today": len(in_window),
        "dropped_today": len(dropped_today),
        "revenue_today": str(revenue),
        "pending": counts[OrderStatus.PLACED]
        + counts[OrderStatus.ACCEPTED]
        + counts[OrderStatus.PREPARING],
        "new": counts[OrderStatus.PLACED],
        "accepted": counts[OrderStatus.ACCEPTED],
        "preparing": counts[OrderStatus.PREPARING],
        "ready": counts[OrderStatus.READY],
        "collected": counts[OrderStatus.COLLECTED],
        "rejected": counts[OrderStatus.REJECTED],
        "cancelled": counts[OrderStatus.CANCELLED],
        "generated_at": moment.isoformat(),
    }