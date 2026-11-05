"""Order models: the order itself, its lines, and its status history."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q

from cafes.models import Cafe, Destination, MenuItem


class OrderStatus(models.TextChoices):
    PLACED = "PLACED", "Placed"
    ACCEPTED = "ACCEPTED", "Accepted"
    PREPARING = "PREPARING", "Preparing"
    READY = "READY", "Ready"
    COLLECTED = "COLLECTED", "Collected"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class PaymentMethod(models.TextChoices):
    PAY_AT_PICKUP = "PAY_AT_PICKUP", "Pay at pickup"


PUBLIC_ID_PREFIX = "RB"
PUBLIC_ID_START = 1000


class OrderQuerySet(models.QuerySet):
    def for_merchant(self, user) -> "OrderQuerySet":
        """Only orders belonging to the cafés this user manages."""
        return self.filter(cafe__merchant=user)

    def open_orders(self) -> "OrderQuerySet":
        return self.exclude(
            status__in=[
                OrderStatus.COLLECTED,
                OrderStatus.REJECTED,
                OrderStatus.CANCELLED,
            ]
        )


class Order(models.Model):
    public_id = models.CharField(
        max_length=16, unique=True, editable=False, blank=True
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()

    cafe = models.ForeignKey(Cafe, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(
        max_length=16, choices=OrderStatus.choices, default=OrderStatus.PLACED
    )

    destination = models.ForeignKey(
        Destination,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    destination_label = models.CharField(max_length=120)

    arrival_time = models.DateTimeField()
    prep_time_minutes = models.PositiveSmallIntegerField()
    start_preparing_time = models.DateTimeField()
    estimated_ready_time = models.DateTimeField()

    subtotal = models.DecimalField(max_digits=9, decimal_places=2)
    payment_method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        default=PaymentMethod.PAY_AT_PICKUP,
    )
    notes = models.CharField(max_length=280, blank=True)

    idempotency_key = models.CharField(max_length=64, blank=True, editable=False)

    accepted_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.CharField(max_length=140, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=140, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(subtotal__gte=Decimal("0.00")),
                name="order_subtotal_not_negative",
            ),
            models.CheckConstraint(
                condition=Q(prep_time_minutes__gte=1),
                name="order_prep_time_at_least_one_minute",
            ),
            # Guards against a double submit creating two identical orders.
            models.UniqueConstraint(
                fields=["customer", "idempotency_key"],
                condition=~Q(idempotency_key=""),
                name="unique_order_idempotency_per_customer",
            ),
        ]
        indexes = [
            models.Index(fields=["cafe", "status"], name="order_cafe_status_idx"),
            models.Index(fields=["customer", "-created_at"], name="order_customer_idx"),
            models.Index(fields=["arrival_time"], name="order_arrival_idx"),
        ]

    def __str__(self) -> str:
        return self.public_id or f"Order #{self.pk}"

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        if not self.public_id:
            expected = f"{PUBLIC_ID_PREFIX}-{PUBLIC_ID_START + self.pk}"
            type(self).objects.filter(pk=self.pk).update(public_id=expected)
            self.public_id = expected

    @property
    def is_open(self) -> bool:
        return self.status not in {
            OrderStatus.COLLECTED,
            OrderStatus.REJECTED,
            OrderStatus.CANCELLED,
        }

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def ready_by(self):
        """The headline number: the time the order will be finished."""
        return self.estimated_ready_time


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(
        MenuItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_items",
    )
    # Snapshot fields: an order must stay readable even if the menu changes.
    name = models.CharField(max_length=120)
    unit_price = models.DecimalField(max_digits=7, decimal_places=2)
    quantity = models.PositiveSmallIntegerField()
    line_total = models.DecimalField(max_digits=9, decimal_places=2)
    art = models.CharField(max_length=32, default="hot-cup")

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="order_item_quantity_at_least_one"
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=Decimal("0.00")),
                name="order_item_price_not_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quantity} × {self.name}"


class OrderStatusEvent(models.Model):
    """Immutable audit trail of every status change on an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=16, choices=OrderStatus.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_events",
    )
    actor_role = models.CharField(max_length=16, blank=True)
    note = models.CharField(max_length=140, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"{self.order.public_id}: {self.status}"