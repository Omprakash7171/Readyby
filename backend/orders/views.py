"""Order and merchant API endpoints."""

from __future__ import annotations

from datetime import timedelta

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.permissions import IsMerchant
from cafes.models import Cafe, Destination
from readyby.clock import now as clock_now

from readyby_api.exceptions import PilotAPIException
from readyby_api.schema import (
    BOARD_SUMMARY_RESPONSE,
    ERROR_RESPONSE,
    MERCHANT_CAFE_RESPONSE,
    NEXT_ACTION_RESPONSE,
    ORDER_LIST_RESPONSE,
    ORDER_RESPONSE,
    ORDER_STATUS_RESPONSE,
)

from .models import Order, OrderStatus
from .serializers import (
    CancelOrderSerializer,
    CreateOrderSerializer,
    UpdateStatusSerializer,
    board_summary_payload,
    order_payload,
    order_status_payload,
    order_summary_payload,
)
from .services import OrderLineInput, place_order, transition_order
from .state import BOARD_COLUMNS, MERCHANT_ACTIONS, next_status

FILTER_KEYS = tuple(BOARD_COLUMNS.keys())


def _arrival_query_parameter():
    return OpenApiParameter(
        name="arrival_time",
        type=str,
        location=OpenApiParameter.QUERY,
        required=False,
        description="ISO-8601 arrival time, e.g. 2026-05-01T10:30:00+01:00.",
    )


@extend_schema(
    tags=["orders"],
    summary="List the signed-in customer's orders, newest first",
    responses={200: ORDER_LIST_RESPONSE, 401: ERROR_RESPONSE},
)
class MyOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        moment = clock_now()
        orders = (
            Order.objects.filter(customer=request.user)
            .select_related("cafe", "destination")
            .prefetch_related("items")
        )
        return Response(order_summary_payload(orders, moment=moment))


@extend_schema(
    tags=["orders"],
    summary="Place an order for pickup",
    description=(
        "Prices, totals and timings are computed on the server. Send an "
        "`Idempotency-Key` header (or `idempotency_key` in the body) so a double "
        "submit cannot create two orders. Replaying a key returns the original "
        "order with 200 instead of creating a second one with 201."
    ),
    request=CreateOrderSerializer,
    responses={
        201: ORDER_RESPONSE,
        200: ORDER_RESPONSE,
        400: ERROR_RESPONSE,
        404: ERROR_RESPONSE,
        429: ERROR_RESPONSE,
    },
)
class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "order_create"

    def post(self, request):
        payload = dict(request.data)
        header_key = request.headers.get("Idempotency-Key")
        if header_key and not payload.get("idempotency_key"):
            payload["idempotency_key"] = header_key

        serializer = CreateOrderSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cafe = get_object_or_404(Cafe, slug=data["cafe"], is_active=True)
        destination = None
        if data.get("destination"):
            destination = Destination.objects.filter(
                key=data["destination"], is_active=True
            ).first()

        lines = [
            OrderLineInput(
                menu_item_id=line["menu_item"], quantity=line["quantity"]
            )
            for line in data["items"]
        ]

        result = place_order(
            customer=request.user,
            cafe=cafe,
            destination=destination,
            arrival_time=data["arrival_time"],
            lines=lines,
            notes=data.get("notes", ""),
            idempotency_key=data.get("idempotency_key", ""),
        )

        payload_out = order_payload(result.order, moment=clock_now())
        return Response(
            payload_out,
            status=status.HTTP_201_CREATED if result.created else status.HTTP_200_OK,
        )


@extend_schema(
    tags=["orders"],
    summary="Retrieve one order",
    responses={200: ORDER_RESPONSE, 401: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id: str):
        order = self._fetch(request, public_id)
        return Response(order_payload(order, moment=clock_now()))

    @staticmethod
    def _fetch(request, public_id: str) -> Order:
        order = get_object_or_404(
            Order.objects.select_related("cafe", "destination", "customer").prefetch_related(
                "items", "events"
            ),
            public_id=public_id,
        )
        if order.customer_id == request.user.pk:
            return order
        if request.user.is_admin:
            return order
        if request.user.is_merchant and order.cafe.merchant_id == request.user.pk:
            return order
        # Do not confirm the order exists to someone who cannot see it.
        raise PilotAPIException(
            "We couldn't find that order.", code="not_found", status_code=404
        )


@extend_schema(
    tags=["orders"],
    summary="Lightweight status payload for polling",
    responses={200: ORDER_STATUS_RESPONSE, 401: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class OrderStatusView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "order_status"

    def get(self, request, public_id: str):
        order = OrderDetailView._fetch(request, public_id)
        return Response(order_status_payload(order, moment=clock_now()))


@extend_schema(
    tags=["orders"],
    summary="Cancel an order that has not started being made",
    request=CancelOrderSerializer,
    responses={
        200: ORDER_RESPONSE,
        400: ERROR_RESPONSE,
        404: ERROR_RESPONSE,
        409: ERROR_RESPONSE,
    },
)
class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id: str):
        serializer = CancelOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(
            Order.objects.select_related("cafe", "customer"), public_id=public_id
        )
        if order.customer_id != request.user.pk and not request.user.is_admin:
            raise PilotAPIException(
                "We couldn't find that order.", code="not_found", status_code=404
            )

        transition_order(
            order,
            to_status=OrderStatus.CANCELLED,
            actor=request.user,
            note=serializer.validated_data.get("reason", ""),
            as_customer=True,
        )
        return Response(order_payload(order, moment=clock_now()))


# --------------------------------------------------------------------------- #
#  Merchant
# --------------------------------------------------------------------------- #


@extend_schema(
    tags=["merchant"],
    summary="The café this account manages",
    responses={200: MERCHANT_CAFE_RESPONSE, 401: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class MyCafeView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request):
        cafe = getattr(request.user, "cafe", None)
        if cafe is None:
            raise PilotAPIException(
                "No café is linked to this account yet. Ask a ReadyBy admin to set "
                "it up.",
                code="cafe_not_linked",
                status_code=404,
            )
        return Response(
            {
                "slug": cafe.slug,
                "name": cafe.name,
                "tagline": cafe.tagline,
                "category": cafe.category,
                "address": cafe.address,
                "postcode": cafe.postcode,
                "prep_time_minutes": cafe.prep_time_minutes,
                "is_active": cafe.is_active,
                "is_demo": cafe.is_demo,
            }
        )


@extend_schema(
    tags=["merchant"],
    summary="Orders for the signed-in merchant's café only",
    parameters=[
        OpenApiParameter(
            name="status",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="One of: " + ", ".join(FILTER_KEYS),
        )
    ],
    responses={200: ORDER_LIST_RESPONSE, 400: ERROR_RESPONSE, 401: ERROR_RESPONSE},
)
class MerchantOrderListView(APIView):
    permission_classes = [IsMerchant]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "order_status"

    def get(self, request):
        moment = clock_now()
        orders = (
            Order.objects.for_merchant(request.user)
            .select_related("cafe", "destination")
            .prefetch_related("items")
        )

        requested = (request.query_params.get("status") or "").strip()
        if requested:
            if requested not in BOARD_COLUMNS:
                raise PilotAPIException(
                    "Unknown status filter.", code="invalid_status_filter"
                )
            orders = orders.filter(status__in=BOARD_COLUMNS[requested])

        return Response(order_summary_payload(orders, moment=moment))


@extend_schema(
    tags=["merchant"],
    summary="Counts and pickup sales for the merchant board",
    responses={200: BOARD_SUMMARY_RESPONSE, 401: ERROR_RESPONSE},
)
class MerchantBoardSummaryView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request):
        moment = clock_now()
        window_start = moment - timedelta(hours=14)
        orders = (
            Order.objects.for_merchant(request.user).select_related("cafe")
        )
        return Response(board_summary_payload(orders, moment=moment, window_start=window_start))


@extend_schema(
    tags=["merchant"],
    summary="Move one of this café's orders to the next status",
    description=(
        "Only the café's own orders are visible. The status machine rejects any "
        "transition that is not allowed, with 409."
    ),
    request=UpdateStatusSerializer,
    responses={
        200: ORDER_RESPONSE,
        400: ERROR_RESPONSE,
        404: ERROR_RESPONSE,
        409: ERROR_RESPONSE,
    },
)
class MerchantOrderStatusView(APIView):
    permission_classes = [IsMerchant]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "order_status"

    def patch(self, request, public_id: str):
        serializer = UpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Scoping the lookup to this merchant is the isolation guarantee.
        order = get_object_or_404(
            Order.objects.for_merchant(request.user).select_related(
                "cafe", "customer"
            ),
            public_id=public_id,
        )

        transition_order(
            order,
            to_status=serializer.validated_data["status"],
            actor=request.user,
            note=serializer.validated_data.get("note", ""),
            as_merchant=True,
        )
        return Response(order_payload(order, moment=clock_now()))


@extend_schema(
    tags=["merchant"],
    summary="What action this café should take next on an order",
    responses={200: NEXT_ACTION_RESPONSE, 401: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class MerchantNextActionView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request, public_id: str):
        order = get_object_or_404(
            Order.objects.for_merchant(request.user).select_related("cafe"),
            public_id=public_id,
        )
        action = MERCHANT_ACTIONS.get(order.status)
        return Response(
            {
                "public_id": order.public_id,
                "status": order.status,
                "next_status": action[0] if action else None,
                "next_action_label": action[1] if action else None,
                "suggested_next_status": next_status(order.status),
            }
        )