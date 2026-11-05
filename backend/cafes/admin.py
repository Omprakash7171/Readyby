from django.contrib import admin

from .models import Cafe, CafeDistance, Destination, MenuItem


class CafeDistanceInline(admin.TabularInline):
    model = CafeDistance
    extra = 1


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = (
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
        "sort_order",
    )


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "prep_time_minutes",
        "kitchen_capacity",
        "slot_capacity",
        "is_active",
        "is_demo",
        "merchant",
    )
    list_filter = ("is_active", "is_demo")
    search_fields = ("name", "slug", "address", "postcode")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("merchant",)
    inlines = [CafeDistanceInline, MenuItemInline]
    fieldsets = (
        (
            "Identity",
            {"fields": ("name", "slug", "tagline", "category", "description", "image_url")},
        ),
        (
            "Location",
            {
                "fields": ("address", "postcode", "latitude", "longitude", "walk_speed_m_per_min"),
                "description": "Distances to destinations are added below.",
            },
        ),
        (
            "ReadyBy",
            {
                "fields": (
                    "prep_time_minutes",
                    "kitchen_capacity",
                    "slot_capacity",
                    "opening_hours",
                    "closing_soon_minutes",
                ),
                "description": (
                    "prep_time_minutes is the fallback; each menu item also has its "
                    "own prep time. kitchen_capacity limits parallel work and "
                    "slot_capacity limits orders per 15-minute pickup slot. "
                    "opening_hours is JSON, e.g. "
                    '{"mon": [["07:00", "18:00"]], "tue": [["07:00", "18:00"]]}.'
                ),
            },
        ),
        (
            "Pilot",
            {
                "fields": ("is_active", "is_demo", "merchant", "rating", "review_count"),
                "description": "Tick is_demo only for fictional sample cafés.",
            },
        ),
    )


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "kind", "area", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "key", "area")
    prepopulated_fields = {"key": ("name",)}


@admin.register(CafeDistance)
class CafeDistanceAdmin(admin.ModelAdmin):
    list_display = ("cafe", "destination", "metres", "route_note")
    list_filter = ("cafe",)
    search_fields = ("cafe__name", "destination__name")
    autocomplete_fields = ("cafe", "destination")


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "cafe",
        "price",
        "category",
        "prep_time_minutes",
        "is_available",
    )
    list_filter = ("cafe", "category", "is_available")
    search_fields = ("name", "description")
    autocomplete_fields = ("cafe",)