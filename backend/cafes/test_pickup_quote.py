"""Live pickup quoting, slot capacity and cafe settings."""

from __future__ import annotations

from orders.models import OrderStatus
from orders.services import OrderLineInput, place_order
from readyby.ready_by import ceil_to_slot
from readyby_api.exceptions import OrderPlacementException
from readyby.testing import (
    ApiTestCase,
    api_client_for,
    arrive_in,
    make_cafe,
    make_customer,
    make_merchant,
    make_menu_item,
)


class PickupQuoteTestCase(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.merchant = make_merchant()
        self.cafe = make_cafe(
            "quote-cafe",
            merchant=self.merchant,
            prep_time_minutes=8,
            kitchen_capacity=2,
            slot_capacity=2,
        )
        self.latte = make_menu_item(
            self.cafe, "Latte", price="3.20", prep_time_minutes=4
        )
        self.toastie = make_menu_item(
            self.cafe, "Toastie", price="4.50", category="Lunch", prep_time_minutes=6
        )

    def quote(self, **body):
        response = self.client.post(
            f"/api/cafes/{self.cafe.slug}/quote/", body, format="json"
        )
        self.assertEqual(response.status_code, 200, msg=str(response.content))
        return response.json()


class QuoteMathTests(PickupQuoteTestCase):
    def test_empty_basket_uses_the_cafe_fallback(self):
        body = self.quote(items=[])

        self.assertEqual(body["prep_time_minutes"], 8)

    def test_parallel_kitchen_work_is_not_naively_summed(self):
        body = self.quote(
            items=[{"menu_item": self.latte.id, "quantity": 3}]
        )

        self.assertEqual(body["prep_time_minutes"], 6)

    def test_the_slowest_item_sets_the_floor(self):
        body = self.quote(
            items=[
                {"menu_item": self.latte.id, "quantity": 1},
                {"menu_item": self.toastie.id, "quantity": 1},
            ]
        )

        self.assertEqual(body["prep_time_minutes"], 6)

    def test_quote_returns_bookable_slots_and_a_requested_verdict(self):
        requested = ceil_to_slot(arrive_in(45))

        body = self.quote(
            items=[{"menu_item": self.latte.id, "quantity": 1}],
            arrival_time=requested.isoformat(),
        )

        self.assertGreater(len(body["slots"]), 0)
        self.assertLessEqual(len(body["slots"]), 8)
        self.assertTrue(body["requested_slot"]["is_available"])
        self.assertIsNone(body["requested_slot"]["problem"])

    def test_unavailable_items_are_reported_without_breaking_the_quote(self):
        self.toastie.is_available = False
        self.toastie.save()

        body = self.quote(
            items=[
                {"menu_item": self.latte.id, "quantity": 1},
                {"menu_item": self.toastie.id, "quantity": 1},
            ]
        )

        self.assertEqual(body["unavailable_items"], ["Toastie"])


class SlotCapacityTests(PickupQuoteTestCase):
    def test_a_full_slot_is_not_offered_and_is_rejected_at_checkout(self):
        arrival = ceil_to_slot(arrive_in(45))
        self.cafe.slot_capacity = 1
        self.cafe.save()
        customer = make_customer()
        place_order(
            customer=customer,
            cafe=self.cafe,
            destination=None,
            arrival_time=arrival,
            lines=[OrderLineInput(menu_item_id=self.latte.id, quantity=1)],
        )

        quote = self.quote(
            items=[{"menu_item": self.latte.id, "quantity": 1}],
            arrival_time=arrival.isoformat(),
        )

        self.assertFalse(quote["requested_slot"]["is_available"])
        self.assertEqual(quote["requested_slot"]["problem"], "That arrival slot is fully booked. Please choose another time.")
        self.assertNotIn(
            arrival.isoformat(),
            {slot["arrival_time"] for slot in quote["slots"]},
        )

        with self.assertRaises(OrderPlacementException) as caught:
            place_order(
                customer=make_customer("second@example.com"),
                cafe=self.cafe,
                destination=None,
                arrival_time=arrival,
                lines=[OrderLineInput(menu_item_id=self.latte.id, quantity=1)],
            )
        self.assertEqual(caught.exception.code, "slot_full")

    def test_cancelled_orders_free_their_slot(self):
        arrival = ceil_to_slot(arrive_in(45))
        self.cafe.slot_capacity = 1
        self.cafe.save()
        customer = make_customer()
        result = place_order(
            customer=customer,
            cafe=self.cafe,
            destination=None,
            arrival_time=arrival,
            lines=[OrderLineInput(menu_item_id=self.latte.id, quantity=1)],
        )
        result.order.status = OrderStatus.CANCELLED
        result.order.save(update_fields=["status"])

        quote = self.quote(
            items=[{"menu_item": self.latte.id, "quantity": 1}],
            arrival_time=arrival.isoformat(),
        )

        self.assertTrue(quote["requested_slot"]["is_available"])

    def test_merchant_sees_upcoming_slot_capacity(self):
        client = api_client_for(self.merchant)
        arrival = ceil_to_slot(arrive_in(45))
        place_order(
            customer=make_customer(),
            cafe=self.cafe,
            destination=None,
            arrival_time=arrival,
            lines=[OrderLineInput(menu_item_id=self.latte.id, quantity=1)],
        )

        response = client.get("/api/merchant/pickup-slots/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        slot = next(
            item for item in body["slots"] if item["arrival_time"] == arrival.isoformat()
        )
        self.assertEqual(slot["booked"], 1)
        self.assertEqual(slot["remaining"], 1)
        self.assertFalse(slot["is_full"])


class MerchantCafeSettingsTests(PickupQuoteTestCase):
    def test_the_owner_can_update_profile_and_capacity(self):
        client = api_client_for(self.merchant)

        response = client.patch(
            "/api/merchant/cafe/",
            {
                "name": "Quote Cafe",
                "image_url": "https://example.com/cafe.jpg",
                "kitchen_capacity": 3,
                "slot_capacity": 9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, msg=str(response.content))
        body = response.json()
        self.assertEqual(body["name"], "Quote Cafe")
        self.assertEqual(body["image_url"], "https://example.com/cafe.jpg")
        self.assertEqual(body["kitchen_capacity"], 3)
        self.assertEqual(body["slot_capacity"], 9)
        self.cafe.refresh_from_db()
        self.assertEqual(self.cafe.kitchen_capacity, 3)

    def test_capacity_cannot_be_zero(self):
        client = api_client_for(self.merchant)

        response = client.patch(
            "/api/merchant/cafe/", {"slot_capacity": 0}, format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("slot_capacity", response.json()["field_errors"])

    def test_a_customer_cannot_change_cafe_settings(self):
        response = api_client_for(make_customer()).patch(
            "/api/merchant/cafe/", {"slot_capacity": 99}, format="json"
        )

        self.assertEqual(response.status_code, 403)

