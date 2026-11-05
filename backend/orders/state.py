"""Order lifecycle.

The status machine is declared once, here. Nothing else in the codebase is
allowed to decide what may follow what.

    PLACED ──▶ ACCEPTED ──▶ PREPARING ──▶ READY ──▶ COLLECTED
       │  │          │
       │  │          └──────────▶ CANCELLED
       │  └─────────────────────▶ CANCELLED
       └────────────────────────▶ REJECTED

``REJECTED`` is the café declining ("we can't do this one") and is only
reachable from ``PLACED``. ``CANCELLED`` is a change of plan from either side
and is reachable from ``PLACED`` or ``ACCEPTED``.
"""

from __future__ import annotations

from .models import Order, OrderStatus

#: Every legal forward step. Anything not listed here is rejected.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.PLACED: frozenset(
        {OrderStatus.ACCEPTED, OrderStatus.REJECTED, OrderStatus.CANCELLED}
    ),
    OrderStatus.ACCEPTED: frozenset({OrderStatus.PREPARING, OrderStatus.CANCELLED}),
    OrderStatus.PREPARING: frozenset({OrderStatus.READY}),
    OrderStatus.READY: frozenset({OrderStatus.COLLECTED}),
    OrderStatus.COLLECTED: frozenset(),
    OrderStatus.REJECTED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}

#: Statuses the merchant board groups into columns.
BOARD_COLUMNS: dict[str, tuple[str, ...]] = {
    "new": (OrderStatus.PLACED,),
    "accepted": (OrderStatus.ACCEPTED,),
    "preparing": (OrderStatus.PREPARING,),
    "ready": (OrderStatus.READY,),
    "collected": (OrderStatus.COLLECTED,),
    "rejected": (OrderStatus.REJECTED,),
    "cancelled": (OrderStatus.CANCELLED,),
}

#: The single action each status offers the café, in order.
MERCHANT_ACTIONS: dict[str, tuple[str, str] | None] = {
    OrderStatus.PLACED: (OrderStatus.ACCEPTED, "Accept"),
    OrderStatus.ACCEPTED: (OrderStatus.PREPARING, "Start preparing"),
    OrderStatus.PREPARING: (OrderStatus.READY, "Mark ready"),
    OrderStatus.READY: (OrderStatus.COLLECTED, "Mark collected"),
    OrderStatus.COLLECTED: None,
    OrderStatus.REJECTED: None,
    OrderStatus.CANCELLED: None,
}


def can_transition(current: str, target: str) -> bool:
    """True when ``target`` may directly follow ``current``."""
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def next_status(current: str) -> str | None:
    """The status the happy path moves to next, or None at the end."""
    for candidate in (OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.COLLECTED):
        if can_transition(current, candidate):
            return candidate
    return None


def is_terminal(status: str) -> bool:
    return not ALLOWED_TRANSITIONS.get(status)


def customer_may_cancel(order: Order) -> bool:
    """A customer can walk away while the café has not started making it."""
    return order.status in {OrderStatus.PLACED, OrderStatus.ACCEPTED}


def merchant_may_reject(order: Order) -> bool:
    """A café can decline an order it has not started making.

    ``REJECTED`` is deliberately narrower than ``CANCELLED``: it is the café
    saying "we cannot do this one", and it only exists while the order is still
    ``PLACED``. Once the café accepts, a change of plan is a cancellation, not a
    rejection.
    """
    return order.status == OrderStatus.PLACED


def merchant_may_cancel(order: Order) -> bool:
    """A café can decline right up to the moment the drink goes on the bar.

    Once preparation has started the order must be finished and handed over:
    a customer standing at the counter is owed a drink, not a refund.
    """
    return order.status in {OrderStatus.PLACED, OrderStatus.ACCEPTED}