"""Response schemas for the generated OpenAPI document.

The views return plain dictionaries built by the app's payload functions (those
are unit tested). These ``inline_serializer`` definitions describe those same
payloads so ``/api/docs/`` is readable and the frontend team can see the exact
contract without reading the view code.
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import inline_serializer

Money = OpenApiTypes.STR


def many(serializer):
    """``inline_serializer`` returns an instance, so wrap it for lists."""
    return serializer.__class__(many=True)


def describe(serializer, text: str):
    """Attach prose to a component schema (``inline_serializer`` has no kwarg)."""
    serializer.description = text
    return serializer


ERROR_RESPONSE = describe(
    inline_serializer(
        name="Error",
        fields={
            "code": OpenApiTypes.STR,
            "message": OpenApiTypes.STR,
            "field_errors": OpenApiTypes.OBJECT,
        },
    ),
    "Every failure uses this shape. The frontend maps `code` to copy and never "
    "renders a raw backend error.",
)

DESTINATION_RESPONSE = inline_serializer(
    name="Destination",
    fields={
        "id": OpenApiTypes.INT,
        "key": OpenApiTypes.STR,
        "name": OpenApiTypes.STR,
        "kind": OpenApiTypes.STR,
        "area": OpenApiTypes.STR,
        "icon": OpenApiTypes.STR,
        "note": OpenApiTypes.STR,
    },
)

MENU_ITEM_RESPONSE = describe(
    inline_serializer(
        name="MenuItem",
        fields={
            "id": OpenApiTypes.INT,
            "name": OpenApiTypes.STR,
            "description": OpenApiTypes.STR,
            "price": Money,
            "category": OpenApiTypes.STR,
            "art": OpenApiTypes.STR,
            "is_available": OpenApiTypes.BOOL,
            "is_popular": OpenApiTypes.BOOL,
            "tag": OpenApiTypes.STR,
        },
    ),
    "Money is a decimal string so the client never rounds it as a float.",
)

CAFE_RESPONSE = describe(
    inline_serializer(
        name="Cafe",
        fields={
            "id": OpenApiTypes.INT,
            "slug": OpenApiTypes.STR,
            "name": OpenApiTypes.STR,
            "tagline": OpenApiTypes.STR,
            "category": OpenApiTypes.STR,
            "description": OpenApiTypes.STR,
            "address": OpenApiTypes.STR,
            "postcode": OpenApiTypes.STR,
            "rating": Money,
            "review_count": OpenApiTypes.INT,
            "prep_time_minutes": OpenApiTypes.INT,
            "opening_hours": OpenApiTypes.OBJECT,
            "opening_hours_summary": OpenApiTypes.STR,
            "open_state": OpenApiTypes.STR,
            "open_state_label": OpenApiTypes.STR,
            "is_active": OpenApiTypes.BOOL,
            "is_demo": OpenApiTypes.BOOL,
            "distance_metres": OpenApiTypes.INT,
            "distance_label": OpenApiTypes.STR,
            "walk_minutes": OpenApiTypes.INT,
            "arrival_time": OpenApiTypes.DATETIME,
            "start_preparing_time": OpenApiTypes.DATETIME,
            "start_preparing_time_label": OpenApiTypes.STR,
            "estimated_ready_time": OpenApiTypes.DATETIME,
            "estimated_ready_time_label": OpenApiTypes.STR,
            "available_pickup_time": OpenApiTypes.DATETIME,
            "available_pickup_time_label": OpenApiTypes.STR,
            "can_order": OpenApiTypes.BOOL,
            "unavailable_reason": OpenApiTypes.STR,
            "checked_at": OpenApiTypes.DATETIME,
        },
    ),
    "`can_order` and `unavailable_reason` are server decisions. `distance_metres` "
    "comes from the database, never from the browser.",
)

DESTINATION_LIST_RESPONSE = inline_serializer(
    name="DestinationList",
    fields={
        "count": OpenApiTypes.INT,
        "results": many(DESTINATION_RESPONSE),
    },
)

CAFE_LIST_RESPONSE = describe(
    inline_serializer(
        name="CafeList",
        fields={
            "count": OpenApiTypes.INT,
            "destination": DESTINATION_RESPONSE,
            "arrival_time": OpenApiTypes.DATETIME,
            "results": many(CAFE_RESPONSE),
        },
    ),
    "Bookable cafÃ©s first, then nearest, then alphabetical.",
)

CAFE_MENU_RESPONSE = inline_serializer(
    name="CafeMenu",
    fields={
        "cafe": CAFE_RESPONSE,
        "categories": OpenApiTypes.STR,
        "items": many(MENU_ITEM_RESPONSE),
    },
)

MERCHANT_CAFE_RESPONSE = inline_serializer(
    name="MerchantCafe",
    fields={
        "slug": OpenApiTypes.STR,
        "name": OpenApiTypes.STR,
        "tagline": OpenApiTypes.STR,
        "category": OpenApiTypes.STR,
        "address": OpenApiTypes.STR,
        "postcode": OpenApiTypes.STR,
        "prep_time_minutes": OpenApiTypes.INT,
        "is_active": OpenApiTypes.BOOL,
        "is_demo": OpenApiTypes.BOOL,
    },
)

ORDER_ITEM_RESPONSE = inline_serializer(
    name="OrderItem",
    fields={
        "id": OpenApiTypes.INT,
        "menu_item": OpenApiTypes.INT,
        "name": OpenApiTypes.STR,
        "unit_price": Money,
        "quantity": OpenApiTypes.INT,
        "line_total": Money,
        "art": OpenApiTypes.STR,
    },
)

ORDER_EVENT_RESPONSE = inline_serializer(
    name="OrderStatusEvent",
    fields={
        "status": OpenApiTypes.STR,
        "status_label": OpenApiTypes.STR,
        "note": OpenApiTypes.STR,
        "created_at": OpenApiTypes.DATETIME,
        "created_at_label": OpenApiTypes.STR,
    },
)

TRACKING_STEP_RESPONSE = inline_serializer(
    name="TrackingStep",
    fields={"status": OpenApiTypes.STR, "label": OpenApiTypes.STR},
)

ORDER_RESPONSE = describe(
    inline_serializer(
        name="Order",
        fields={
            "id": OpenApiTypes.INT,
            "public_id": OpenApiTypes.STR,
            "status": OpenApiTypes.STR,
            "status_label": OpenApiTypes.STR,
            "status_headline": OpenApiTypes.STR,
            "status_message": OpenApiTypes.STR,
            "progress_rank": OpenApiTypes.INT,
            "tracking_steps": many(TRACKING_STEP_RESPONSE),
            "customer": OpenApiTypes.OBJECT,
            "cafe": OpenApiTypes.OBJECT,
            "destination": OpenApiTypes.OBJECT,
            "destination_label": OpenApiTypes.STR,
            "items": many(ORDER_ITEM_RESPONSE),
            "item_count": OpenApiTypes.INT,
            "subtotal": Money,
            "payment_method": OpenApiTypes.STR,
            "payment_method_label": OpenApiTypes.STR,
            "notes": OpenApiTypes.STR,
            "arrival_time": OpenApiTypes.DATETIME,
            "arrival_time_label": OpenApiTypes.STR,
            "arrival_day_label": OpenApiTypes.STR,
            "prep_time_minutes": OpenApiTypes.INT,
            "start_preparing_time": OpenApiTypes.DATETIME,
            "start_preparing_time_label": OpenApiTypes.STR,
            "estimated_ready_time": OpenApiTypes.DATETIME,
            "estimated_ready_time_label": OpenApiTypes.STR,
            "minutes_until_arrival": OpenApiTypes.INT,
            "merchant_hint": OpenApiTypes.STR,
            "created_at": OpenApiTypes.DATETIME,
            "updated_at": OpenApiTypes.DATETIME,
            "accepted_at": OpenApiTypes.DATETIME,
            "ready_at": OpenApiTypes.DATETIME,
            "collected_at": OpenApiTypes.DATETIME,
            "rejected_at": OpenApiTypes.DATETIME,
            "rejected_reason": OpenApiTypes.STR,
            "cancelled_at": OpenApiTypes.DATETIME,
            "cancel_reason": OpenApiTypes.STR,
            "events": many(ORDER_EVENT_RESPONSE),
        },
    ),
    "All timing, prices and status wording are server-owned. The client renders "
    "these values and never recomputes them.",
)

ORDER_ROW_RESPONSE = inline_serializer(
    name="OrderSummary",
    fields={
        "public_id": OpenApiTypes.STR,
        "status": OpenApiTypes.STR,
        "status_label": OpenApiTypes.STR,
        "customer_name": OpenApiTypes.STR,
        "cafe": OpenApiTypes.OBJECT,
        "items": OpenApiTypes.STR,
        "items_detailed": many(ORDER_ITEM_RESPONSE),
        "subtotal": Money,
        "destination_label": OpenApiTypes.STR,
        "arrival_time": OpenApiTypes.DATETIME,
        "arrival_time_label": OpenApiTypes.STR,
        "start_preparing_time": OpenApiTypes.DATETIME,
        "start_preparing_time_label": OpenApiTypes.STR,
        "estimated_ready_time": OpenApiTypes.DATETIME,
        "estimated_ready_time_label": OpenApiTypes.STR,
        "prep_time_minutes": OpenApiTypes.INT,
        "minutes_until_arrival": OpenApiTypes.INT,
        "merchant_hint": OpenApiTypes.STR,
        "created_at": OpenApiTypes.DATETIME,
        "is_demo": OpenApiTypes.BOOL,
    },
)

ORDER_LIST_RESPONSE = inline_serializer(
    name="OrderSummaryList",
    fields={
        "count": OpenApiTypes.INT,
        "results": many(ORDER_ROW_RESPONSE),
    },
)

ORDER_STATUS_RESPONSE = describe(
    inline_serializer(
        name="OrderStatus",
        fields={
            "public_id": OpenApiTypes.STR,
            "status": OpenApiTypes.STR,
            "status_label": OpenApiTypes.STR,
            "status_headline": OpenApiTypes.STR,
            "status_message": OpenApiTypes.STR,
            "progress_rank": OpenApiTypes.INT,
            "estimated_ready_time": OpenApiTypes.DATETIME,
            "estimated_ready_time_label": OpenApiTypes.STR,
            "arrival_time_label": OpenApiTypes.STR,
            "minutes_until_arrival": OpenApiTypes.INT,
            "updated_at": OpenApiTypes.DATETIME,
        },
    ),
    "The small payload a customer app polls while tracking an order.",
)

BOARD_SUMMARY_RESPONSE = describe(
    inline_serializer(
        name="BoardSummary",
        fields={
            "orders_today": OpenApiTypes.INT,
            "dropped_today": OpenApiTypes.INT,
            "revenue_today": Money,
            "pending": OpenApiTypes.INT,
            "new": OpenApiTypes.INT,
            "accepted": OpenApiTypes.INT,
            "preparing": OpenApiTypes.INT,
            "ready": OpenApiTypes.INT,
            "collected": OpenApiTypes.INT,
            "rejected": OpenApiTypes.INT,
            "cancelled": OpenApiTypes.INT,
            "generated_at": OpenApiTypes.DATETIME,
        },
    ),
    "Only this café's orders are counted.",
)

NEXT_ACTION_RESPONSE = inline_serializer(
    name="NextAction",
    fields={
        "public_id": OpenApiTypes.STR,
        "status": OpenApiTypes.STR,
        "next_status": OpenApiTypes.STR,
        "next_action_label": OpenApiTypes.STR,
        "suggested_next_status": OpenApiTypes.STR,
    },
)

MERCHANT_MENU_RESPONSE = describe(
    inline_serializer(
        name="MerchantMenuItem",
        fields={
            "id": OpenApiTypes.INT,
            "name": OpenApiTypes.STR,
            "description": OpenApiTypes.STR,
            "price": Money,
            "category": OpenApiTypes.STR,
            "art": OpenApiTypes.STR,
            "is_available": OpenApiTypes.BOOL,
            "is_popular": OpenApiTypes.BOOL,
            "tag": OpenApiTypes.STR,
        },
    ),
    "Only the signed-in merchant's own café is reachable. Prices are decimal "
    "strings in both directions.",
)

USER_RESPONSE = describe(
    inline_serializer(
        name="User",
        fields={
            "id": OpenApiTypes.INT,
            "email": OpenApiTypes.STR,
            "first_name": OpenApiTypes.STR,
            "last_name": OpenApiTypes.STR,
            "full_name": OpenApiTypes.STR,
            "display_name": OpenApiTypes.STR,
            "initials": OpenApiTypes.STR,
            "role": OpenApiTypes.STR,
            "phone": OpenApiTypes.STR,
            "status": OpenApiTypes.STR,
            "is_active": OpenApiTypes.BOOL,
            "created_at": OpenApiTypes.DATETIME,
            "cafe": OpenApiTypes.OBJECT,
        },
    ),
    "The signed-in person's own account. `full_name` and `display_name` are "
    "derived from the stored first and last name, never a second copy of them. "
    "`status` and `is_active` are kept in step: SUSPENDED always means "
    "`is_active` is false.",
)

AUTH_RESPONSE = describe(
    inline_serializer(
        name="Credentials",
        fields={
            "token": OpenApiTypes.STR,
            "access": OpenApiTypes.STR,
            "refresh": OpenApiTypes.STR,
            "user": USER_RESPONSE,
        },
    ),
    "Both credential schemes are returned. `token` is the opaque DRF token the "
    "web client sends as `Authorization: Token <key>`; `access`/`refresh` are "
    "the JWT pair sent as `Authorization: Bearer <access>`.",
)

CUSTOMER_PAYLOAD_RESPONSE = describe(
    inline_serializer(
        name="CustomerContact",
        fields={
            "display_name": OpenApiTypes.STR,
            "phone": OpenApiTypes.STR,
        },
    ),
    "The safe subset of a customer shown on the café's order ticket: enough to "
    "hand the order over, and nothing about the account itself.",
)

JWT_RESPONSE = describe(
    inline_serializer(
        name="JwtAccess",
        fields={"access": OpenApiTypes.STR},
    ),
    "A fresh access token, obtained by posting the `refresh` token.",
)