"""Order status copy.

Kept server-side so the customer app and the merchant board cannot disagree, and
so the same wording is available to tests and the API docs.
"""

from __future__ import annotations

from .models import OrderStatus

STATUS_LABEL: dict[str, str] = {
    OrderStatus.PLACED: "New order",
    OrderStatus.ACCEPTED: "Accepted",
    OrderStatus.PREPARING: "Preparing",
    OrderStatus.READY: "Ready for pickup",
    OrderStatus.COLLECTED: "Collected",
    OrderStatus.REJECTED: "Declined",
    OrderStatus.CANCELLED: "Cancelled",
}

STATUS_HEADLINE: dict[str, str] = {
    OrderStatus.PLACED: "Order received",
    OrderStatus.ACCEPTED: "Your café has accepted the order",
    OrderStatus.PREPARING: "Your order is being prepared",
    OrderStatus.READY: "Your order is ready",
    OrderStatus.COLLECTED: "Order collected",
    OrderStatus.REJECTED: "The café declined this order",
    OrderStatus.CANCELLED: "Order cancelled",
}

STATUS_MESSAGE: dict[str, str] = {
    OrderStatus.PLACED: "Your café has the order and will confirm it shortly.",
    OrderStatus.ACCEPTED: "The café has confirmed your order and will time it for your arrival.",
    OrderStatus.PREPARING: "Your order is being made now, timed for when you arrive.",
    OrderStatus.READY: "Walk in and show your order number — no queue required.",
    OrderStatus.COLLECTED: "Thanks for using ReadyBy. Enjoy it!",
    OrderStatus.REJECTED: "The café could not take this order. Nothing was charged.",
    OrderStatus.CANCELLED: "This order was cancelled. Nothing was charged.",
}

MERCHANT_HINT: dict[str, str] = {
    OrderStatus.PLACED: "Accept when you can start for this arrival time.",
    OrderStatus.ACCEPTED: "Start the order when you're ready to begin.",
    OrderStatus.PREPARING: "Being made now, ready before the customer arrives.",
    OrderStatus.READY: "Waiting at the counter for the customer.",
    OrderStatus.COLLECTED: "Handed over. Nothing else to do.",
    OrderStatus.REJECTED: "Declined by the café.",
    OrderStatus.CANCELLED: "Cancelled.",
}

TRACKING_STEPS: tuple[dict[str, str], ...] = (
    {"status": OrderStatus.PLACED, "label": "Order placed"},
    {"status": OrderStatus.ACCEPTED, "label": "Café accepted"},
    {"status": OrderStatus.PREPARING, "label": "Preparing"},
    {"status": OrderStatus.READY, "label": "Ready"},
    {"status": OrderStatus.COLLECTED, "label": "Collected"},
)

#: Order of the statuses used to work out how far a customer has got.
PROGRESS_ORDER: tuple[str, ...] = (
    OrderStatus.PLACED,
    OrderStatus.ACCEPTED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.COLLECTED,
)


def progress_rank(status: str) -> int:
    try:
        return PROGRESS_ORDER.index(status)
    except ValueError:
        return -1