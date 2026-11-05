"""Order placement: server-owned money, timing, validation and idempotency."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from readyby_api.exceptions import InvalidTransitionException, OrderPlacementException
from readyby.testing import (
    ALWAYS_OPEN,
    arrive_in,
    make_cafe,
    make_customer,
    make_destination,
    make_merchant,
    make_menu_item,
)
from orders.models import Order, OrderItem, OrderStatus
from orders.services import MAX_LINE_QUANTITY, OrderLineInput, place_order, transition_order


class PlaceOrderTestCase(TestCase):
    def setUp(self) -> None:
        self.customer = make_customer()
        self.cafe = make_cafe(prep_time_minutes=8)
        self.latte = make_menu_item(self.cafe, "Latte", price="3.20")
        self.croissant = make_menu_item(
            self.cafe, "Croissant", price="2.50", category="Breakfast"
        )
        self.destination = make_destination()

    def place(self, **overrides):
        params = {
            "customer": self.customer,
            "cafe": self.cafe,
            "destination": self.destination,
            "arrival_time": arrive_in(45),
            "lines": [OrderLineInput(menu_item_id=self.latte.id, quantity=2)],
        }
        params.update(overrides)
        return place_order(**params)


class ServerOwnedPricingTests(PlaceOrderTestCase):
    def test_prices_come_from_the_database_not_the_client(self):
        """The client only sends item ids; the server prices the order."""
        result = self.place()

        self.assertEqual(result.order.subtotal, Decimal("6.40"))
        line = result.order.items.get()
        self.assertEqual(line.unit_price, Decimal("3.20"))
        self.assertEqual(line.line_total, Decimal("6.40"))
        self.assertEqual(line.name, "Latte")

    def test_multiple_lines_are_totalled_exactly(self):
        result = self.place(
            lines=[
                OrderLineInput(menu_item_id=self.latte.id, quantity=2),
                OrderLineInput(menu_item_id=self.croissant.id, quantity=1),
            ]
        )
        self.assertEqual(result.order.subtotal, Decimal("8.90"))

    def test_money_is_stored_as_exact_decimal_cents(self):
        make_menu_item(self.cafe, "Odd", price="1.15")
        odd = self.cafe.menu_items.get(name="Odd")
        result = self.place(
            lines=[OrderLineInput(menu_item_id=odd.id, quantity=3)]
        )
        self.assertEqual(result.order.subtotal, Decimal("3.45"))

    def test_a_changed_menu_price_does_not_change_an_existing_order(self):
        result = self.place()
        self.latte.price = Decimal("9.99")
        self.latte.save()

        result.order.refresh_from_db()
        self.assertEqual(result.order.subtotal, Decimal("6.40"))

    def test_payment_is_always_pay_at_pickup(self):
        result = self.place()
        self.assertEqual(result.order.payment_method, "PAY_AT_PICKUP")


class TimingTests(PlaceOrderTestCase):
    def test_start_preparing_is_arrival_minus_prep_time(self):
        arrival = arrive_in(45)
        result = self.place(arrival_time=arrival)

        self.assertEqual(result.order.arrival_time, arrival)
        self.assertEqual(result.order.prep_time_minutes, 8)
        self.assertEqual(
            result.order.start_preparing_time, arrival - timedelta(minutes=8)
        )
        self.assertEqual(result.order.estimated_ready_time, arrival)

    def test_an_arrival_that_is_too_soon_is_rejected(self):
        with self.assertRaises(OrderPlacementException) as caught:
            self.place(arrival_time=timezone.now() + timedelta(minutes=2))
        self.assertEqual(caught.exception.code, "arrival_too_soon")

    def test_an_arrival_beyond_24_hours_is_rejected(self):
        with self.assertRaises(OrderPlacementException) as caught:
            self.place(arrival_time=timezone.now() + timedelta(hours=25))
        self.assertEqual(caught.exception.code, "arrival_too_far")

    def test_an_arrival_in_the_past_is_rejected(self):
        with self.assertRaises(OrderPlacementException) as caught:
            self.place(arrival_time=timezone.now() - timedelta(minutes=30))
        self.assertEqual(caught.exception.code, "arrival_unavailable")

    def test_an_order_that_would_be_made_after_closing_is_rejected(self):
        """The café must still be open when the order is ready."""
        closing = timezone.localtime(timezone.now() + timedelta(minutes=20))
        hours = {day: [["00:00", closing.strftime("%H:%M")]] for day in ALWAYS_OPEN}
        shop = make_cafe("closing-soon-cafe", prep_time_minutes=8, opening_hours=hours)

        with self.assertRaises(OrderPlacementException) as caught:
            place_order(
                customer=self.customer,
                cafe=shop,
                destination=self.destination,
                arrival_time=arrive_in(40),
                lines=[OrderLineInput(menu_item_id=self.latte.id, quantity=1)],
            )
        self.assertEqual(caught.exception.code, "cafe_closes_before_ready")

    def test_an_inactive_cafe_cannot_take_orders(self):
        self.cafe.is_active = False
        self.cafe.save()

        with self.assertRaises(OrderPlacementException) as caught:
            self.place()
        self.assertEqual(caught.exception.code, "cafe_inactive")


class MenuValidationTests(PlaceOrderTestCase):
    def test_an_empty_order_is_rejected(self):
        with self.assertRaises(OrderPlacementException) as caught:
            self.place(lines=[])
        self.assertEqual(caught.exception.code, "empty_cart")

    def test_a_zero_quantity_is_rejected(self):
        with self.assertRaises(OrderPlacementException) as caught:
            self.place(lines=[OrderLineInput(menu_item_id=self.latte.id, quantity=0)])
        self.assertEqual(caught.exception.code, "invalid_quantity")

    def test_an_item_from_another_cafe_is_rejected(self):
        other = make_cafe("other-cafe")
        foreign_item = make_menu_item(other, "Secret Flat White", price="99.00")

        with self.assertRaises(OrderPlacementException) as caught:
            self.place(
                lines=[OrderLineInput(menu_item_id=foreign_item.id, quantity=1)]
            )
        self.assertEqual(caught.exception.code, "item_unavailable")

    def test_an_unavailable_item_is_rejected(self):
        self.latte.is_available = False
        self.latte.save()

        with self.assertRaises(OrderPlacementException) as caught:
            self.place()
        self.assertEqual(caught.exception.code, "item_unavailable")

    def test_too_many_of_one_item_is_rejected(self):
        with self.assertRaises(OrderPlacementException) as caught:
            self.place(
                lines=[
                    OrderLineInput(
                        menu_item_id=self.latte.id, quantity=MAX_LINE_QUANTITY + 1
                    )
                ]
            )
        self.assertEqual(caught.exception.code, "quantity_too_high")

    def test_the_limit_itself_is_accepted(self):
        result = self.place(
            lines=[OrderLineInput(menu_item_id=self.latte.id, quantity=MAX_LINE_QUANTITY)]
        )
        self.assertEqual(result.order.items.get().quantity, MAX_LINE_QUANTITY)

    def test_repeated_lines_are_summed_not_duplicated(self):
        result = self.place(
            lines=[
                OrderLineInput(menu_item_id=self.latte.id, quantity=1),
                OrderLineInput(menu_item_id=self.latte.id, quantity=2),
            ]
        )
        self.assertEqual(result.order.items.count(), 1)
        self.assertEqual(result.order.items.get().quantity, 3)


class IdempotencyTests(PlaceOrderTestCase):
    def test_a_replayed_key_returns_the_original_order(self):
        first = self.place(idempotency_key="submit-1")
        second = self.place(idempotency_key="submit-1")

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.order.pk, second.order.pk)
        self.assertEqual(Order.objects.count(), 1)

    def test_a_different_key_creates_a_second_order(self):
        self.place(idempotency_key="submit-1")
        self.place(idempotency_key="submit-2")
        self.assertEqual(Order.objects.count(), 2)

    def test_one_customers_key_does_not_block_anothers(self):
        other_customer = make_customer("other@example.com")
        self.place(idempotency_key="shared-key")
        place_order(
            customer=other_customer,
            cafe=self.cafe,
            destination=self.destination,
            arrival_time=arrive_in(45),
            lines=[OrderLineInput(menu_item_id=self.latte.id, quantity=1)],
            idempotency_key="shared-key",
        )
        self.assertEqual(Order.objects.count(), 2)

    def test_orders_without_a_key_are_never_replayed(self):
        self.place()
        self.place()
        self.assertEqual(Order.objects.count(), 2)


class OrderCreationTests(PlaceOrderTestCase):
    def test_a_new_order_starts_placed_with_an_audit_event(self):
        result = self.place()
        order = result.order

        self.assertEqual(order.status, OrderStatus.PLACED)
        self.assertTrue(order.public_id.startswith("RB-"))
        self.assertEqual(order.customer_name, self.customer.display_name)
        self.assertEqual(order.destination_label, self.destination.name)
        self.assertEqual(order.events.count(), 1)
        self.assertEqual(order.events.get().status, OrderStatus.PLACED)

    def test_an_order_without_a_destination_falls_back_to_the_note(self):
        result = self.place(destination=None, notes="By the blue door")
        self.assertEqual(result.order.destination_label, "By the blue door")

    def test_notes_are_trimmed_to_the_stored_limit(self):
        result = self.place(notes="x" * 500)
        self.assertEqual(len(result.order.notes), 280)

    def test_public_ids_are_unique(self):
        first = self.place()
        second = self.place()
        self.assertNotEqual(first.order.public_id, second.order.public_id)

    def test_a_free_item_is_treated_as_an_empty_order(self):
        free = make_menu_item(self.cafe, "Water", price="0.00")
        with self.assertRaises(OrderPlacementException) as caught:
            self.place(lines=[OrderLineInput(menu_item_id=free.id, quantity=1)])
        self.assertEqual(caught.exception.code, "empty_cart")


class TransitionTests(PlaceOrderTestCase):
    def test_a_merchant_walks_an_order_all_the_way_to_collected(self):
        merchant = make_merchant()
        self.cafe.merchant = merchant
        self.cafe.save()

        order = self.place().order
        for status in (
            OrderStatus.ACCEPTED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.COLLECTED,
        ):
            transition_order(order, to_status=status, actor=merchant, as_merchant=True)

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.COLLECTED)
        self.assertIsNotNone(order.accepted_at)
        self.assertIsNotNone(order.preparing_at)
        self.assertIsNotNone(order.ready_at)
        self.assertIsNotNone(order.collected_at)
        self.assertEqual(order.events.count(), 5)

    def test_skipping_a_stage_is_refused(self):
        order = self.place().order
        with self.assertRaises(InvalidTransitionException) as caught:
            transition_order(order, to_status=OrderStatus.READY, as_merchant=True)
        self.assertEqual(caught.exception.code, "invalid_transition")

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.PLACED)

    def test_an_unknown_status_is_refused(self):
        order = self.place().order
        with self.assertRaises(InvalidTransitionException) as caught:
            transition_order(order, to_status="TELEPORTED", as_merchant=True)
        self.assertEqual(caught.exception.code, "invalid_status")

    def test_a_customer_cannot_cancel_a_preparing_order(self):
        order = self.place().order
        transition_order(
            order, to_status=OrderStatus.ACCEPTED, as_merchant=True
        )
        transition_order(
            order, to_status=OrderStatus.PREPARING, as_merchant=True
        )

        with self.assertRaises(InvalidTransitionException) as caught:
            transition_order(
                order,
                to_status=OrderStatus.CANCELLED,
                actor=self.customer,
                as_customer=True,
            )
        self.assertEqual(caught.exception.code, "cancellation_closed")

    def test_a_merchant_cannot_walk_away_from_a_drink_already_being_made(self):
        order = self.place().order
        transition_order(order, to_status=OrderStatus.ACCEPTED, as_merchant=True)
        transition_order(order, to_status=OrderStatus.PREPARING, as_merchant=True)

        with self.assertRaises(InvalidTransitionException) as caught:
            transition_order(order, to_status=OrderStatus.CANCELLED, as_merchant=True)
        self.assertEqual(caught.exception.code, "cancellation_closed")

    def test_a_customer_cancelling_an_accepted_order_records_the_reason(self):
        order = self.place().order
        transition_order(order, to_status=OrderStatus.ACCEPTED, as_merchant=True)
        transition_order(
            order,
            to_status=OrderStatus.CANCELLED,
            actor=self.customer,
            note="Plans changed",
            as_customer=True,
        )

        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.CANCELLED)
        self.assertEqual(order.cancel_reason, "Plans changed")
        self.assertIsNotNone(order.cancelled_at)

    def test_an_anonymous_actor_cannot_cancel(self):
        order = self.place().order
        with self.assertRaises(InvalidTransitionException):
            transition_order(order, to_status=OrderStatus.CANCELLED)

    def test_every_transition_is_recorded_with_its_actor_role(self):
        merchant = make_merchant()
        order = self.place().order
        transition_order(
            order,
            to_status=OrderStatus.ACCEPTED,
            actor=merchant,
            note="On it",
            as_merchant=True,
        )

        event = order.events.order_by("-created_at", "-id").first()
        self.assertEqual(event.status, OrderStatus.ACCEPTED)
        self.assertEqual(event.actor, merchant)
        self.assertEqual(event.actor_role, "MERCHANT")
        self.assertEqual(event.note, "On it")


class SnapshotTests(PlaceOrderTestCase):
    def test_the_order_keeps_the_name_and_price_it_was_ordered_at(self):
        result = self.place()
        line = result.order.items.get()

        self.latte.name = "Latte (renamed)"
        self.latte.price = Decimal("4.00")
        self.latte.save()

        line.refresh_from_db()
        self.assertEqual(line.name, "Latte")
        self.assertEqual(line.unit_price, Decimal("3.20"))

    def test_a_deleted_menu_item_does_not_break_a_past_order(self):
        result = self.place()
        OrderItem.objects.filter(order=result.order).update(menu_item=None)

        line = result.order.items.get()
        self.assertIsNone(line.menu_item_id)
        self.assertEqual(line.name, "Latte")