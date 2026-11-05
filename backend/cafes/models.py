"""Catalogue models: destinations, participating cafés, menus."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from .hours import default_opening_hours

# Average walking pace used to turn a known distance into a walk time. The pilot
# has no GPS, so distances are entered by a ReadyBy admin and this constant only
# converts metres to minutes for display.
WALK_SPEED_METRES_PER_MINUTE = 80


class Destination(models.Model):
    """Somewhere a customer is heading: an office, a gym, a station."""

    key = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=80, blank=True)
    area = models.CharField(max_length=80, blank=True)
    icon = models.CharField(
        max_length=32,
        default="building",
        help_text="Frontend icon key: scissors, building, graduation, dumbbell, train.",
    )
    note = models.CharField(max_length=140, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Cafe(models.Model):
    """A café taking part in the pilot.

    One café belongs to at most one merchant account. ``is_demo`` marks the
    fictional sample cafés so they can be kept out of a real pilot environment.
    """

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    tagline = models.CharField(max_length=120, blank=True)
    category = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional photo of the cafe or its counter.",
    )

    address = models.CharField(max_length=240, blank=True)
    postcode = models.CharField(max_length=16, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    prep_time_minutes = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(1)],
        help_text="Default preparation time when the basket has no timed items.",
    )
    kitchen_capacity = models.PositiveSmallIntegerField(
        default=4,
        validators=[MinValueValidator(1)],
        help_text="How many items the kitchen can prepare at the same time.",
    )
    slot_capacity = models.PositiveSmallIntegerField(
        default=6,
        validators=[MinValueValidator(1)],
        help_text="Maximum orders accepted in one 15-minute arrival slot.",
    )
    opening_hours = models.JSONField(default=default_opening_hours)
    closing_soon_minutes = models.PositiveSmallIntegerField(default=30)
    walk_speed_m_per_min = models.PositiveSmallIntegerField(
        default=WALK_SPEED_METRES_PER_MINUTE
    )

    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=Decimal("0.0")
    )
    review_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)

    merchant = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cafe",
        help_text="The café account that manages this café's orders.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(prep_time_minutes__gte=1),
                name="cafe_prep_time_at_least_one_minute",
            ),
            models.CheckConstraint(
                condition=models.Q(kitchen_capacity__gte=1),
                name="cafe_kitchen_capacity_at_least_one",
            ),
            models.CheckConstraint(
                condition=models.Q(slot_capacity__gte=1),
                name="cafe_slot_capacity_at_least_one",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def walk_minutes(self, metres: int) -> int:
        return max(1, round(metres / max(1, self.walk_speed_m_per_min)))

    def distance_to(self, destination: Destination | None) -> int | None:
        if destination is None:
            return None
        entry = self.distances.filter(destination=destination).first()
        return entry.metres if entry else None


class CafeDistance(models.Model):
    """A known walking distance between a café and a destination.

    Entered by a ReadyBy admin. This is *not* live GPS: the pilot deliberately
    avoids claiming real-time location data.
    """

    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name="distances")
    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="distances"
    )
    metres = models.PositiveIntegerField()
    route_note = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["cafe__name", "metres"]
        constraints = [
            models.UniqueConstraint(
                fields=["cafe", "destination"], name="unique_cafe_destination_distance"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cafe.name} → {self.destination.name}: {self.metres}m"


class MenuItem(models.Model):
    """One sellable line on a café menu.

    ``price`` is a Decimal; money is never stored or calculated as a float.
    """

    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE, related_name="menu_items")
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=240, blank=True)
    price = models.DecimalField(
        max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    category = models.CharField(max_length=64, default="Coffee")
    art = models.CharField(max_length=32, default="hot-cup")
    image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Optional food photo. Falls back to the illustrated menu art.",
    )
    prep_time_minutes = models.PositiveSmallIntegerField(
        default=8,
        validators=[MinValueValidator(1)],
        help_text="Preparation time for one of this item, in minutes.",
    )
    is_available = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    tag = models.CharField(max_length=32, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["category", "sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["cafe", "name"], name="unique_menu_item_name_per_cafe"
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=Decimal("0.00")),
                name="menu_item_price_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(prep_time_minutes__gte=1),
                name="menu_item_prep_time_at_least_one_minute",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.cafe.name})"