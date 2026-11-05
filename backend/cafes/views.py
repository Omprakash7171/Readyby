"""Public discovery endpoints: destinations, cafés and menus."""

from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsMerchant
from orders.services import (
    OrderLineInput,
    quote_pickup,
    slot_order_count,
    slot_remaining,
)
from readyby.clock import format_clock, format_day_clock
from readyby.clock import now as clock_now
from readyby.ready_by import SLOT_INTERVAL_MINUTES, ceil_to_slot
from readyby_api.exceptions import PilotAPIException
from readyby_api.schema import (
    CAFE_LIST_RESPONSE,
    CAFE_MENU_RESPONSE,
    CAFE_RESPONSE,
    DESTINATION_LIST_RESPONSE,
    ERROR_RESPONSE,
)

from .hours import next_closing_at
from .models import Cafe, Destination
from .serializers import (
    MerchantCafeWriteSerializer,
    PickupQuoteRequestSerializer,
    cafe_payload,
    destination_payload,
    menu_payload,
    merchant_cafe_payload,
)
from .services import CafeAvailability, cafe_availability, sort_key

ARRIVAL_PARAMETER = OpenApiParameter(
    name="arrival_time",
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "ISO-8601 arrival time. When supplied, each café returns the start and "
        "ready-by times for that arrival."
    ),
)

DESTINATION_PARAMETER = OpenApiParameter(
    name="destination",
    type=str,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Destination key, e.g. city-centre-salon.",
)


def visible_cafes_queryset():
    """Cafés a real customer may see.

    Only active cafés are ever exposed. Demo cafés are additionally fictional,
    so they are hidden unless ``SHOW_DEMO_CAFES`` is switched on and a pilot
    customer is never offered a made-up café.
    """
    queryset = Cafe.objects.filter(is_active=True).select_related("merchant")
    queryset = queryset.prefetch_related("distances", "menu_items")
    if not getattr(settings, "SHOW_DEMO_CAFES", False):
        queryset = queryset.filter(is_demo=False)
    return queryset


def _parse_arrival(request) -> datetime | None:
    raw = (request.query_params.get("arrival_time") or "").strip()
    if not raw:
        return None
    parsed = parse_datetime(raw)
    if parsed is None:
        raise ValidationError(
            {"arrival_time": ["Use an ISO-8601 time, e.g. 2026-05-01T10:30:00+01:00."]}
        )
    if parsed.tzinfo is None:
        parsed = timezone.make_aware(parsed, timezone.get_default_timezone())
    return parsed


def _resolve_destination(request) -> Destination | None:
    key = (request.query_params.get("destination") or "").strip()
    if not key:
        return None
    return Destination.objects.filter(key=key, is_active=True).first()


def _availability_for(
    cafes, *, destination: Destination | None, arrival_time: datetime | None, moment: datetime
) -> list[CafeAvailability]:
    entries = [
        cafe_availability(
            cafe, destination=destination, arrival_time=arrival_time, moment=moment
        )
        for cafe in cafes
    ]
    return sorted(entries, key=sort_key)


@extend_schema(
    tags=["catalog"],
    summary="Destinations customers can head to",
    responses={200: DESTINATION_LIST_RESPONSE},
)
class DestinationListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        destinations = Destination.objects.filter(is_active=True)
        return Response(
            {
                "count": destinations.count(),
                "results": [
                    destination_payload(item) for item in destinations
                ],
            }
        )


@extend_schema(
    tags=["catalog"],
    summary="Participating cafés near a destination",
    parameters=[DESTINATION_PARAMETER, ARRIVAL_PARAMETER],
    responses={200: CAFE_LIST_RESPONSE, 400: ERROR_RESPONSE},
)
class CafeListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        moment = clock_now()
        arrival_time = _parse_arrival(request)
        destination = _resolve_destination(request)

        entries = _availability_for(
            list(visible_cafes_queryset()),
            destination=destination,
            arrival_time=arrival_time,
            moment=moment,
        )

        return Response(
            {
                "count": len(entries),
                "destination": destination_payload(destination) if destination else None,
                "arrival_time": arrival_time.isoformat() if arrival_time else None,
                "results": [
                    cafe_payload(
                        entry.cafe,
                        availability=entry,
                        arrival_time=arrival_time,
                        moment=moment,
                    )
                    for entry in entries
                ],
            }
        )


@extend_schema(
    tags=["catalog"],
    summary="One café",
    parameters=[DESTINATION_PARAMETER, ARRIVAL_PARAMETER],
    responses={200: CAFE_RESPONSE, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class CafeDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug: str):
        cafe = get_object_or_404(visible_cafes_queryset(), slug=slug, is_active=True)
        moment = clock_now()
        availability = cafe_availability(
            cafe,
            destination=_resolve_destination(request),
            arrival_time=_parse_arrival(request),
            moment=moment,
        )
        return Response(
            cafe_payload(cafe, availability=availability, moment=moment)
        )


@extend_schema(
    tags=["catalog"],
    summary="A café's menu, grouped by category",
    responses={200: CAFE_MENU_RESPONSE, 404: ERROR_RESPONSE},
)
class CafeMenuView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug: str):
        cafe = get_object_or_404(visible_cafes_queryset(), slug=slug, is_active=True)
        return Response(menu_payload(cafe))


@extend_schema(
    tags=["catalog"],
    summary="Live preparation estimate and bookable pickup slots",
    request=PickupQuoteRequestSerializer,
    responses={200: dict, 400: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class CafeQuoteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, slug: str):
        cafe = get_object_or_404(visible_cafes_queryset(), slug=slug, is_active=True)
        serializer = PickupQuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        lines = [
            OrderLineInput(
                menu_item_id=line["menu_item"], quantity=line["quantity"]
            )
            for line in data.get("items", [])
        ]
        return Response(
            quote_pickup(
                cafe,
                lines,
                requested_arrival=data.get("arrival_time"),
            )
        )


def _merchant_cafe(request) -> Cafe:
    cafe = getattr(request.user, "cafe", None)
    if cafe is None:
        raise PilotAPIException(
            "No cafǸ is linked to this account yet. Ask a ReadyBy admin to set it up.",
            code="cafe_not_linked",
            status_code=404,
        )
    return cafe


@extend_schema(
    tags=["merchant"],
    summary="Read or update the cafǸ's profile and kitchen settings",
    request=MerchantCafeWriteSerializer,
    responses={200: dict, 400: ERROR_RESPONSE, 401: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class MerchantCafeView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request):
        return Response(merchant_cafe_payload(_merchant_cafe(request)))

    def patch(self, request):
        cafe = _merchant_cafe(request)
        serializer = MerchantCafeWriteSerializer(
            cafe, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(merchant_cafe_payload(cafe))


@extend_schema(
    tags=["merchant"],
    summary="Upcoming pickup slots and how full they are",
    responses={200: dict, 401: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class MerchantPickupSlotsView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request):
        cafe = _merchant_cafe(request)
        moment = clock_now()
        candidate = ceil_to_slot(moment)
        slots = []
        horizon = moment + timedelta(hours=24)
        while candidate <= horizon and len(slots) < 16:
            closing = next_closing_at(cafe.opening_hours, candidate)
            if closing is not None and candidate < closing:
                booked = slot_order_count(cafe, candidate)
                slots.append(
                    {
                        "arrival_time": candidate.isoformat(),
                        "time_label": format_clock(candidate),
                        "day_label": format_day_clock(candidate),
                        "label": format_day_clock(candidate),
                        "booked": booked,
                        "remaining": slot_remaining(cafe, candidate),
                        "capacity": cafe.slot_capacity,
                        "is_full": booked >= cafe.slot_capacity,
                    }
                )
            candidate += timedelta(minutes=SLOT_INTERVAL_MINUTES)

        return Response(
            {
                "cafe": cafe.slug,
                "slot_capacity": cafe.slot_capacity,
                "slot_interval_minutes": SLOT_INTERVAL_MINUTES,
                "slots": slots,
            }
        )