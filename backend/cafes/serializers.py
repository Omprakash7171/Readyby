"""Catalogue output payloads."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from readyby.clock import format_clock
from rest_framework import serializers

from .hours import format_hours_summary
from .models import Cafe, Destination, MenuItem
from .services import CafeAvailability, format_distance


class MenuItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = (
            "id",
            "name",
            "description",
            "price",
            "category",
            "art",
            "image_url",
            "prep_time_minutes",
            "is_available",
            "is_popular",
            "tag",
        )

    def get_price(self, item: MenuItem) -> str:
        """Money is sent as a string so JavaScript never rounds it as a float."""
        return str(item.price)


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ("id", "key", "name", "kind", "area", "icon", "note")


#: A single menu line cannot cost more than this. Guards against a fat-fingered
#: price (a missing decimal point) ever reaching a customer.
MAX_MENU_PRICE = Decimal("999.99")


class MerchantMenuItemWriteSerializer(serializers.Serializer):
    """Body for creating or editing one of the café's own menu items.

    ``price`` is a decimal field, so a string from the browser becomes an exact
    ``Decimal`` and is never routed through a float.
    """

    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    description = serializers.CharField(
        max_length=240, required=False, allow_blank=True, default=""
    )
    price = serializers.DecimalField(
        max_digits=7,
        decimal_places=2,
        min_value=Decimal("0.00"),
        max_value=MAX_MENU_PRICE,
        required=False,
    )
    category = serializers.CharField(max_length=64, required=False, allow_blank=True)
    image_url = serializers.URLField(
        max_length=500, required=False, allow_blank=True, default=""
    )
    prep_time_minutes = serializers.IntegerField(
        required=False, min_value=1, max_value=120, default=8
    )
    is_available = serializers.BooleanField(required=False)
    is_popular = serializers.BooleanField(required=False)
    sort_order = serializers.IntegerField(required=False, min_value=0, max_value=999)

    def validate_name(self, value: str) -> str:
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Give the item a name.")
        return name

    def validate_category(self, value: str) -> str:
        return value.strip() or "Coffee"

    def validate(self, attrs):
        cafe = self.context["cafe"]
        creating = self.instance is None
        name = attrs.get("name")

        if creating and not name:
            raise serializers.ValidationError({"name": ["Give the item a name."]})

        if name:
            clash = MenuItem.objects.filter(cafe=cafe, name__iexact=name)
            if not creating:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    {"name": [f"You already have an item called “{name}”."]}
                )

        if creating and attrs.get("price") is None:
            raise serializers.ValidationError({"price": ["Set a price for this item."]})

        return attrs

    def create(self, validated_data: dict) -> MenuItem:
        return MenuItem.objects.create(cafe=self.context["cafe"], **validated_data)

    def update(self, instance: MenuItem, validated_data: dict) -> MenuItem:
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class MerchantCafeWriteSerializer(serializers.Serializer):
    """The cafe details an owner is allowed to change themselves."""

    name = serializers.CharField(max_length=120, required=False)
    tagline = serializers.CharField(
        max_length=120, required=False, allow_blank=True, default=""
    )
    category = serializers.CharField(
        max_length=80, required=False, allow_blank=True, default=""
    )
    description = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    image_url = serializers.URLField(
        max_length=500, required=False, allow_blank=True, default=""
    )
    address = serializers.CharField(
        max_length=240, required=False, allow_blank=True, default=""
    )
    postcode = serializers.CharField(
        max_length=16, required=False, allow_blank=True, default=""
    )
    prep_time_minutes = serializers.IntegerField(
        required=False, min_value=1, max_value=120
    )
    kitchen_capacity = serializers.IntegerField(
        required=False, min_value=1, max_value=20
    )
    slot_capacity = serializers.IntegerField(
        required=False, min_value=1, max_value=100
    )

    def validate_name(self, value: str) -> str:
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Give your cafe a name.")
        return name

    def update(self, instance: Cafe, validated_data: dict) -> Cafe:
        for field, value in validated_data.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(instance, field, value)
        instance.save()
        return instance


class PickupQuoteLineSerializer(serializers.Serializer):
    menu_item = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class PickupQuoteRequestSerializer(serializers.Serializer):
    items = PickupQuoteLineSerializer(many=True, required=False, default=list)
    arrival_time = serializers.DateTimeField(required=False, allow_null=True)


def merchant_cafe_payload(cafe: Cafe) -> dict:
    return {
        "slug": cafe.slug,
        "name": cafe.name,
        "tagline": cafe.tagline,
        "category": cafe.category,
        "description": cafe.description,
        "image_url": cafe.image_url,
        "address": cafe.address,
        "postcode": cafe.postcode,
        "prep_time_minutes": cafe.prep_time_minutes,
        "kitchen_capacity": cafe.kitchen_capacity,
        "slot_capacity": cafe.slot_capacity,
        "opening_hours": cafe.opening_hours,
        "opening_hours_summary": format_hours_summary(cafe.opening_hours),
        "is_active": cafe.is_active,
        "is_demo": cafe.is_demo,
    }


def destination_payload(destination: Destination) -> dict:
    return {
        "id": destination.pk,
        "key": destination.key,
        "name": destination.name,
        "kind": destination.kind,
        "area": destination.area,
        "icon": destination.icon,
        "note": destination.note,
    }


def menu_payload(cafe: Cafe) -> dict:
    items = list(
        cafe.menu_items.select_related("cafe").order_by("category", "sort_order", "name")
    )
    categories: list[str] = []
    for item in items:
        if item.category not in categories:
            categories.append(item.category)
    return {
        "cafe": cafe_payload(cafe, arrival_time=None, moment=None),
        "categories": categories,
        "items": [MenuItemSerializer(item).data for item in items],
    }


def cafe_payload(
    cafe: Cafe,
    *,
    availability: CafeAvailability | None = None,
    arrival_time: datetime | None = None,
    moment: datetime | None = None,
) -> dict:
    """One café as the explore screen needs it."""
    plan = availability.plan if availability else None
    open_state = availability.open_state if availability else None

    return {
        "id": cafe.pk,
        "slug": cafe.slug,
        "name": cafe.name,
        "tagline": cafe.tagline,
        "category": cafe.category,
        "description": cafe.description,
        "image_url": cafe.image_url,
        "address": cafe.address,
        "postcode": cafe.postcode,
        "latitude": str(cafe.latitude) if cafe.latitude is not None else None,
        "longitude": str(cafe.longitude) if cafe.longitude is not None else None,
        "rating": str(cafe.rating),
        "review_count": cafe.review_count,
        "prep_time_minutes": cafe.prep_time_minutes,
        "kitchen_capacity": cafe.kitchen_capacity,
        "slot_capacity": cafe.slot_capacity,
        "opening_hours": cafe.opening_hours,
        "opening_hours_summary": format_hours_summary(cafe.opening_hours),
        "open_state": open_state.key if open_state else None,
        "open_state_label": (
            availability.open_state_label if availability else None
        ),
        "is_active": cafe.is_active,
        "is_demo": cafe.is_demo,
        "distance_metres": availability.distance_metres if availability else None,
        "distance_label": format_distance(
            availability.distance_metres if availability else None
        ),
        "walk_minutes": availability.walk_minutes if availability else None,
        "arrival_time": arrival_time.isoformat() if arrival_time else None,
        "start_preparing_time": (
            plan.start_preparing_at.isoformat() if plan else None
        ),
        "start_preparing_time_label": (
            format_clock(plan.start_preparing_at) if plan else None
        ),
        "estimated_ready_time": (
            plan.estimated_ready_at.isoformat() if plan else None
        ),
        "estimated_ready_time_label": (
            format_clock(plan.estimated_ready_at) if plan else None
        ),
        "available_pickup_time": (
            availability.available_pickup_time.isoformat()
            if availability and availability.available_pickup_time
            else None
        ),
        "available_pickup_time_label": (
            format_clock(availability.available_pickup_time)
            if availability and availability.available_pickup_time
            else None
        ),
        "can_order": availability.can_order if availability else False,
        "unavailable_reason": (
            availability.unavailable_reason if availability else None
        ),
        "checked_at": moment.isoformat() if moment else None,
    }