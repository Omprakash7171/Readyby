"""Café-facing menu management.

The café must be able to run its own menu, and must never be able to reach
another café's.
"""

from __future__ import annotations

from decimal import Decimal

from readyby.testing import (
    ApiTestCase,
    api_client_for,
    make_cafe,
    make_customer,
    make_menu_item,
    make_merchant,
)

MENU = "/api/merchant/menu/"
CREATE = "/api/merchant/menu/create/"


class MerchantMenuTestCase(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.merchant = make_merchant()
        self.cafe = make_cafe("my-cafe", merchant=self.merchant)
        self.client = api_client_for(self.merchant)
        self.latte = make_menu_item(self.cafe, "Latte", price="4.00")

    def detail(self, item_id: int) -> str:
        return f"/api/merchant/menu/{item_id}/"


class MerchantMenuReadTests(MerchantMenuTestCase):
    def test_the_cafe_sees_its_own_menu(self):
        make_menu_item(self.cafe, "Croissant", category="Food", price="3.20")

        response = self.client.get(MENU)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 2)
        self.assertEqual(body["cafe"], "my-cafe")
        names = {item["name"] for item in body["results"]}
        self.assertEqual(names, {"Latte", "Croissant"})

    def test_categories_are_listed_in_menu_order(self):
        make_menu_item(self.cafe, "Tea", category="Tea", price="2.80")

        body = self.client.get(MENU).json()

        self.assertEqual(body["categories"], ["Coffee", "Tea"])

    def test_prices_are_sent_as_decimal_strings(self):
        body = self.client.get(MENU).json()
        latte = next(i for i in body["results"] if i["name"] == "Latte")
        self.assertEqual(latte["price"], "4.00")

    def test_availability_is_reported(self):
        self.client.patch(self.detail(self.latte.pk), {"is_available": False}, format="json")

        body = self.client.get(MENU).json()
        latte = next(i for i in body["results"] if i["name"] == "Latte")
        self.assertFalse(latte["is_available"])


class MerchantMenuWriteTests(MerchantMenuTestCase):
    def test_the_cafe_can_add_an_item(self):
        response = self.client.post(
            CREATE,
            {
                "name": "Flat White",
                "description": "Small",
                "price": "3.90",
                "category": "Coffee",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, msg=str(response.content))
        self.assertEqual(response.json()["name"], "Flat White")
        self.assertEqual(response.json()["price"], "3.90")
        self.assertTrue(response.json()["is_available"])

    def test_a_price_is_stored_as_a_decimal_not_a_float(self):
        self.client.post(CREATE, {"name": "Tea", "price": "2.80"}, format="json")

        item = self.cafe.menu_items.get(name="Tea")
        self.assertIsInstance(item.price, Decimal)
        self.assertEqual(item.price, Decimal("2.80"))

    def test_the_cafe_can_change_a_price(self):
        response = self.client.patch(
            self.detail(self.latte.pk), {"price": "4.40"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["price"], "4.40")
        self.latte.refresh_from_db()
        self.assertEqual(self.latte.price, Decimal("4.40"))

    def test_the_cafe_can_sell_out_and_restore_an_item(self):
        self.assertEqual(
            self.client.patch(
                self.detail(self.latte.pk), {"is_available": False}, format="json"
            ).status_code,
            200,
        )
        self.latte.refresh_from_db()
        self.assertFalse(self.latte.is_available)

        self.client.patch(
            self.detail(self.latte.pk), {"is_available": True}, format="json"
        )
        self.latte.refresh_from_db()
        self.assertTrue(self.latte.is_available)

    def test_an_item_can_be_deleted(self):
        response = self.client.delete(self.detail(self.latte.pk))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(self.cafe.menu_items.filter(pk=self.latte.pk).exists())

    def test_deleting_an_item_does_not_rewrite_an_order_that_used_it(self):
        """A ticket placed yesterday must still read correctly tomorrow."""
        from datetime import timedelta

        from django.utils import timezone

        from orders.models import Order, OrderItem

        order = Order.objects.create(
            customer=make_customer(),
            customer_name="Casey",
            customer_email="casey@example.com",
            cafe=self.cafe,
            destination_label="Office",
            arrival_time=timezone.now() + timedelta(minutes=45),
            prep_time_minutes=8,
            start_preparing_time=timezone.now() + timedelta(minutes=37),
            estimated_ready_time=timezone.now() + timedelta(minutes=45),
            subtotal=Decimal("4.00"),
        )
        OrderItem.objects.create(
            order=order,
            menu_item=self.latte,
            name=self.latte.name,
            unit_price=self.latte.price,
            quantity=1,
            line_total=Decimal("4.00"),
        )

        self.client.delete(self.detail(self.latte.pk))

        line = OrderItem.objects.get(order=order)
        self.assertEqual(line.name, "Latte")
        self.assertEqual(line.unit_price, Decimal("4.00"))


class MerchantMenuValidationTests(MerchantMenuTestCase):
    def assertFieldError(self, response, field: str, code: str = "validation_error"):
        self.assertEqual(response.status_code, 400, msg=str(response.content))
        body = self.assertErrorEnvelope(response, code=code)
        self.assertIn(field, body["field_errors"])

    def test_an_item_needs_a_name(self):
        response = self.client.post(CREATE, {"price": "3.00"}, format="json")
        self.assertFieldError(response, "name")

    def test_a_blank_name_is_refused(self):
        response = self.client.post(
            CREATE, {"name": "   ", "price": "3.00"}, format="json"
        )
        self.assertFieldError(response, "name")

    def test_an_item_needs_a_price(self):
        response = self.client.post(CREATE, {"name": "Tea"}, format="json")
        self.assertFieldError(response, "price")

    def test_a_negative_price_is_refused(self):
        response = self.client.post(
            CREATE, {"name": "Tea", "price": "-1.00"}, format="json"
        )
        self.assertFieldError(response, "price")

    def test_an_absurd_price_is_refused(self):
        response = self.client.post(
            CREATE, {"name": "Tea", "price": "99999.00"}, format="json"
        )
        self.assertFieldError(response, "price")

    def test_a_price_that_is_not_a_number_is_refused(self):
        response = self.client.post(
            CREATE, {"name": "Tea", "price": "free"}, format="json"
        )
        self.assertFieldError(response, "price")

    def test_a_duplicate_name_in_the_same_cafe_is_refused(self):
        response = self.client.post(
            CREATE, {"name": "latte", "price": "3.00"}, format="json"
        )
        self.assertFieldError(response, "name")

    def test_the_same_name_in_another_cafe_is_fine(self):
        """Uniqueness is per café, so two cafés may both sell a Flat White."""
        make_cafe("other-cafe", merchant=make_merchant(email="other@example.com"))

        response = self.client.post(
            CREATE, {"name": "Flat White", "price": "3.50"}, format="json"
        )

        self.assertEqual(response.status_code, 201, msg=str(response.content))
        self.assertEqual(response.json()["name"], "Flat White")

    def test_renaming_an_item_to_its_own_name_is_allowed(self):
        response = self.client.patch(
            self.detail(self.latte.pk), {"name": "Latte"}, format="json"
        )
        self.assertEqual(response.status_code, 200)


class MerchantMenuIsolationTests(MerchantMenuTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.rival_merchant = make_merchant(email="rival@example.com")
        self.rival_cafe = make_cafe("rival-cafe", merchant=self.rival_merchant)
        self.rival_item = make_menu_item(self.rival_cafe, "Rival Flat White", price="3.90")

    def test_a_cafe_does_not_see_another_cafe_menu(self):
        body = self.client.get(MENU).json()
        names = {item["name"] for item in body["results"]}
        self.assertNotIn("Rival Flat White", names)

    def test_a_cafe_cannot_edit_another_cafe_item(self):
        response = self.client.patch(
            self.detail(self.rival_item.pk), {"price": "0.01"}, format="json"
        )

        self.assertEqual(response.status_code, 404)
        self.rival_item.refresh_from_db()
        self.assertEqual(self.rival_item.price, Decimal("3.90"))

    def test_a_cafe_cannot_delete_another_cafe_item(self):
        response = self.client.delete(self.detail(self.rival_item.pk))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.rival_cafe.menu_items.filter(pk=self.rival_item.pk).exists())

    def test_a_customer_cannot_use_the_menu_management_api(self):
        customer_client = api_client_for(make_customer())

        self.assertEqual(customer_client.get(MENU).status_code, 403)
        self.assertEqual(
            customer_client.post(
                CREATE, {"name": "Free Coffee", "price": "0.00"}, format="json"
            ).status_code,
            403,
        )
        self.assertEqual(
            customer_client.delete(self.detail(self.latte.pk)).status_code, 403
        )

    def test_anonymous_users_are_refused(self):
        from rest_framework.test import APIClient

        anonymous = APIClient()
        self.assertEqual(anonymous.get(MENU).status_code, 401)
        self.assertEqual(
            anonymous.post(CREATE, {"name": "X", "price": "1.00"}, format="json").status_code,
            401,
        )

    def test_a_merchant_without_a_cafe_is_told_so(self):
        orphan = make_merchant(email="orphan@example.com")

        response = api_client_for(orphan).get(MENU)

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="cafe_not_linked")


class PublicMenuReflectsChangesTests(MerchantMenuTestCase):
    def test_a_sold_out_item_still_shows_on_the_public_menu_as_unavailable(self):
        self.client.patch(
            self.detail(self.latte.pk), {"is_available": False}, format="json"
        )

        response = self.client.get(f"/api/cafes/{self.cafe.slug}/menu/")

        self.assertEqual(response.status_code, 200)
        latte = next(i for i in response.json()["items"] if i["name"] == "Latte")
        self.assertFalse(latte["is_available"])

    def test_a_new_item_appears_on_the_public_menu(self):
        self.client.post(
            CREATE, {"name": "Cortado", "price": "3.10", "category": "Coffee"}, format="json"
        )

        body = self.client.get(f"/api/cafes/{self.cafe.slug}/menu/").json()

        self.assertIn("Cortado", {item["name"] for item in body["items"]})