from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem, OrderStatusEvent
from .presentation import STATUS_LABEL


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("name", "unit_price", "quantity", "line_total", "art")
    fields = ("menu_item", "name", "quantity", "unit_price", "line_total", "art")

    def has_add_permission(self, request, obj=None) -> bool:
        # Lines are only ever created by the order service, which prices them.
        return False


class OrderEventInline(admin.TabularInline):
    model = OrderStatusEvent
    extra = 0
    readonly_fields = ("status", "actor", "actor_role", "note", "created_at")
    fields = ("status", "actor", "actor_role", "note", "created_at")

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "cafe",
        "customer_name",
        "status_badge",
        "arrival_time",
        "estimated_ready_time",
        "subtotal",
    )
    list_filter = ("status", "cafe", "created_at")
    search_fields = ("public_id", "customer_name", "customer_email", "cafe__name")
    readonly_fields = (
        "public_id",
        "customer",
        "customer_name",
        "customer_email",
        "cafe",
        "destination_label",
        "arrival_time",
        "prep_time_minutes",
        "start_preparing_time",
        "estimated_ready_time",
        "subtotal",
        "payment_method",
        "idempotency_key",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline, OrderEventInline]
    date_hierarchy = "created_at"

    @admin.display(description="Status")
    def status_badge(self, order: Order) -> str:
        return format_html(
            "<strong>{}</strong>", STATUS_LABEL.get(order.status, order.status)
        )

    def has_add_permission(self, request) -> bool:
        # Orders must go through the API so prices and timings are computed.
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False