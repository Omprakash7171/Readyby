"""End-to-end API tests: authentication, placement, isolation, error shape."""

from __future__ import annotations

from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from orders.models import Order, OrderStatus
from readyby.testing import (
    ApiTestCase,
    api_client_for,
    arrive_in,
    make_cafe,
    make_customer,
    make_destination,
    make_merchant,
    make_menu_item,
)

ORDER_LIST = "/api/orders/"
ORDER_CREATE = "/api/orders/new/"
MERCHANT_ORDERS = "/api/merchant/orders/"
MERCHANT_SUMMARY = "/api/merchant/orders/summary/"
MERCHANT_CAFE = "/api/merchant/cafe/"


class OrderApiTestCase(ApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.customer = make_customer()
        self.merchant = make_merchant()
        self.cafe = make_cafe("bean-and-brew", merchant=self.merchant, prep_time_minutes=8)
        self.latte = make_menu_item(self.cafe, "Latte", price="3.20")
        self.croissant = make_menu_item(
            self.cafe, "Croissant", price="2.50", category="Breakfast"
        )
        self.destination = make_destination()
        self.client = api_client_for(self.customer)

    def payload(self, **overrides) -> dict:
        body = {
            "cafe": self.cafe.slug,
            "destination": self.destination.key,
            "arrival_time": arrive_in(45).isoformat(),
            "items": [{"menu_item": self.latte.id, "quantity": 2}],
        }
        body.update(overrides)
        return body


class AuthenticationTests(OrderApiTestCase):
    def place_order(self, **overrides):
        response = self.client.post(ORDER_CREATE, self.payload(**overrides), format="json")
        self.assertEqual(response.status_code, 201, msg=str(response.content))
        return response.json()

    def test_anonymous_customers_are_refused(self):
        anonymous = APIClient()
        response = anonymous.post(ORDER_CREATE, self.payload(), format="json")
        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_anonymous_merchant_endpoints_are_refused(self):
        anonymous = APIClient()
        response = anonymous.get(MERCHANT_ORDERS)
        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_a_signed_in_customer_may_not_use_the_merchant_api(self):
        response = self.client.get(MERCHANT_ORDERS)
        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="forbidden")

    def test_a_customer_may_not_patch_an_order_status(self):
        order = self.place_order()
        response = self.client.patch(
            f"/api/merchant/orders/{order['public_id']}/status/",
            {"status": OrderStatus.ACCEPTED},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="forbidden")

    def test_a_customer_may_not_read_the_merchant_board(self):
        response = self.client.get(MERCHANT_SUMMARY)
        self.assertEqual(response.status_code, 403)

    def test_a_customer_may_not_list_their_own_orders_anonymously(self):
        response = APIClient().get(ORDER_LIST)
        self.assertEqual(response.status_code, 401)


class PlaceOrderEndpointTests(OrderApiTestCase):
    def place_order(self, **overrides):
        response = self.client.post(ORDER_CREATE, self.payload(**overrides), format="json")
        self.assertEqual(response.status_code, 201, msg=str(response.content))
        return response.json()

    def test_a_placed_order_returns_the_full_tracking_payload(self):
        body = self.place_order()

        self.assertEqual(body["status"], OrderStatus.PLACED)
        self.assertEqual(body["status_label"], "New order")
        self.assertEqual(body["cafe"]["slug"], self.cafe.slug)
        self.assertEqual(body["destination"]["key"], self.destination.key)
        self.assertEqual(body["subtotal"], "6.40")
        self.assertEqual(body["payment_method"], "PAY_AT_PICKUP")
        self.assertEqual(body["item_count"], 2)
        self.assertEqual(len(body["tracking_steps"]), 5)
        self.assertEqual(len(body["events"]), 1)
        self.assertEqual(body["events"][0]["status"], OrderStatus.PLACED)

    def test_timing_is_computed_by_the_server(self):
        body = self.place_order()
        self.assertEqual(body["prep_time_minutes"], 8)
        self.assertEqual(body["arrival_time"], body["estimated_ready_time"])
        self.assertNotEqual(body["start_preparing_time"], body["arrival_time"])
        self.assertTrue(body["estimated_ready_time_label"].endswith(("AM", "PM")))

    def test_prices_cannot_be_supplied_by_the_client(self):
        """Extra fields are ignored: the server decides the money."""
        body = self.place_order(subtotal="0.01", total="0.01", status=OrderStatus.COLLECTED)
        self.assertEqual(body["subtotal"], "6.40")
        self.assertEqual(body["status"], OrderStatus.PLACED)

    def test_an_idempotency_header_prevents_a_double_submit(self):
        headers = {"HTTP_IDEMPOTENCY_KEY": "submit-abc"}
        first = self.client.post(
            ORDER_CREATE, self.payload(), format="json", **headers
        )
        second = self.client.post(
            ORDER_CREATE, self.payload(), format="json", **headers
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["public_id"], second.json()["public_id"])
        self.assertEqual(Order.objects.count(), 1)

    def test_an_unknown_cafe_is_a_not_found_error(self):
        response = self.client.post(
            ORDER_CREATE, self.payload(cafe="does-not-exist"), format="json"
        )
        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_an_empty_cart_is_refused_with_a_readable_message(self):
        response = self.client.post(
            ORDER_CREATE, self.payload(items=[]), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("items", response.json()["field_errors"])

    def test_a_zero_quantity_is_refused(self):
        response = self.client.post(
            ORDER_CREATE,
            self.payload(items=[{"menu_item": self.latte.id, "quantity": 0}]),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")

    def test_an_arrival_too_soon_is_refused_with_the_reason(self):
        response = self.client.post(
            ORDER_CREATE,
            self.payload(arrival_time=(timezone.now() + timedelta(minutes=1)).isoformat()),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        body = self.assertErrorEnvelope(response, code="arrival_too_soon")
        self.assertIn("arrival_time", body["field_errors"])

    def test_a_malformed_arrival_time_is_refused(self):
        response = self.client.post(
            ORDER_CREATE, self.payload(arrival_time="tomorrow-ish"), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")

    def test_notes_are_accepted(self):
        body = self.place_order(notes="Extra hot please")
        self.assertEqual(body["notes"], "Extra hot please")


class CustomerOrderListTests(OrderApiTestCase):
    def place_order(self, **overrides):
        response = self.client.post(ORDER_CREATE, self.payload(**overrides), format="json")
        self.assertEqual(response.status_code, 201, msg=str(response.content))
        return response.json()

    def test_a_customer_sees_only_their_own_orders(self):
        self.place_order()

        other = make_customer("someone-else@example.com")
        other_client = api_client_for(other)
        other_cafe = make_cafe("other-cafe")
        other_item = make_menu_item(other_cafe, "Tea", price="1.00")
        response = other_client.post(
            ORDER_CREATE,
            {
                "cafe": other_cafe.slug,
                "arrival_time": arrive_in(45).isoformat(),
                "items": [{"menu_item": other_item.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        mine = self.client.get(ORDER_LIST).json()
        self.assertEqual(mine["count"], 1)
        self.assertEqual(mine["results"][0]["cafe"]["slug"], self.cafe.slug)

    def test_the_list_includes_items_and_arrival_details(self):
        self.place_order()
        row = self.client.get(ORDER_LIST).json()["results"][0]

        self.assertEqual(row["items"], ["2 × Latte"])
        self.assertEqual(row["subtotal"], "6.40")
        self.assertEqual(row["destination_label"], self.destination.name)
        self.assertEqual(row["prep_time_minutes"], 8)
        self.assertIsNotNone(row["merchant_hint"])

    def test_a_customer_cannot_read_another_customers_order(self):
        body = self.place_order()
        other = api_client_for(make_customer("nosy@example.com"))

        response = other.get(f"/api/orders/{body['public_id']}/")
        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_the_customer_can_read_their_own_order(self):
        body = self.place_order()
        response = self.client.get(f"/api/orders/{body['public_id']}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["public_id"], body["public_id"])


class StatusPollingTests(OrderApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        response = self.client.post(ORDER_CREATE, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, msg=str(response.content))
        self.order = response.json()

    def test_the_polling_payload_is_small_and_complete(self):
        response = self.client.get(f"/api/orders/{self.order['public_id']}/status/")
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["status"], OrderStatus.PLACED)
        self.assertEqual(body["progress_rank"], 0)
        self.assertIn("status_headline", body)
        self.assertIn("status_message", body)
        self.assertIn("estimated_ready_time", body)
        self.assertIsInstance(body["minutes_until_arrival"], int)

    def test_polling_reflects_the_merchant_moving_the_order_on(self):
        merchant_client = api_client_for(self.merchant)
        response = merchant_client.patch(
            f"/api/merchant/orders/{self.order['public_id']}/status/",
            {"status": OrderStatus.ACCEPTED, "note": "On it"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, msg=str(response.content))

        body = self.client.get(f"/api/orders/{self.order['public_id']}/status/").json()
        self.assertEqual(body["status"], OrderStatus.ACCEPTED)
        self.assertEqual(body["progress_rank"], 1)


class CancellationEndpointTests(OrderApiTestCase):
    def place_order(self):
        response = self.client.post(ORDER_CREATE, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, msg=str(response.content))
        return response.json()

    def test_a_customer_can_cancel_a_new_order(self):
        order = self.place_order()
        response = self.client.post(
            f"/api/orders/{order['public_id']}/cancel/",
            {"reason": "Plans changed"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], OrderStatus.CANCELLED)
        self.assertEqual(response.json()["cancel_reason"], "Plans changed")

    def test_a_customer_cannot_cancel_an_order_being_made(self):
        order = self.place_order()
        merchant_client = api_client_for(self.merchant)
        for status in (OrderStatus.ACCEPTED, OrderStatus.PREPARING):
            response = merchant_client.patch(
                f"/api/merchant/orders/{order['public_id']}/status/",
                {"status": status},
                format="json",
            )
            self.assertEqual(response.status_code, 200, msg=str(response.content))

        response = self.client.post(
            f"/api/orders/{order['public_id']}/cancel/", {}, format="json"
        )
        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="cancellation_closed")

    def test_a_customer_cannot_cancel_someone_elses_order(self):
        order = self.place_order()
        other = api_client_for(make_customer("meddler@example.com"))
        response = other.post(
            f"/api/orders/{order['public_id']}/cancel/", {}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_an_collected_order_cannot_be_cancelled(self):
        order = self.place_order()
        merchant_client = api_client_for(self.merchant)
        for status in (
            OrderStatus.ACCEPTED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.COLLECTED,
        ):
            response = merchant_client.patch(
                f"/api/merchant/orders/{order['public_id']}/status/",
                {"status": status},
                format="json",
            )
            self.assertEqual(response.status_code, 200, msg=str(response.content))

        response = self.client.post(
            f"/api/orders/{order['public_id']}/cancel/", {}, format="json"
        )
        self.assertEqual(response.status_code, 409)


class MerchantIsolationTests(OrderApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        response = self.client.post(ORDER_CREATE, self.payload(), format="json")
        self.order = response.json()
        self.merchant_client = api_client_for(self.merchant)

    def test_a_merchant_sees_only_their_own_cafe_orders(self):
        rival_merchant = make_merchant("rival@example.com")
        rival_cafe = make_cafe("rival-cafe", merchant=rival_merchant)
        rival_item = make_menu_item(rival_cafe, "Tea", price="1.00")

        rival_customer = make_customer("rival-customer@example.com")
        api_client_for(rival_customer).post(
            ORDER_CREATE,
            {
                "cafe": rival_cafe.slug,
                "arrival_time": arrive_in(45).isoformat(),
                "items": [{"menu_item": rival_item.id, "quantity": 1}],
            },
            format="json",
        )

        body = self.merchant_client.get(MERCHANT_ORDERS).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["cafe"]["slug"], self.cafe.slug)

    def test_a_merchant_cannot_move_another_cafe_order(self):
        rival_merchant = make_merchant("rival@example.com")
        rival_client = api_client_for(rival_merchant)

        response = rival_client.patch(
            f"/api/merchant/orders/{self.order['public_id']}/status/",
            {"status": OrderStatus.ACCEPTED},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_a_merchant_cannot_read_another_cafe_order(self):
        rival_client = api_client_for(make_merchant("rival@example.com"))
        response = rival_client.get(f"/api/orders/{self.order['public_id']}/")
        self.assertEqual(response.status_code, 404)

    def test_the_board_summary_only_counts_this_cafe(self):
        rival_merchant = make_merchant("rival@example.com")
        rival_cafe = make_cafe("rival-cafe", merchant=rival_merchant)
        rival_item = make_menu_item(rival_cafe, "Tea", price="1.00")
        api_client_for(make_customer("other-customer@example.com")).post(
            ORDER_CREATE,
            {
                "cafe": rival_cafe.slug,
                "arrival_time": arrive_in(45).isoformat(),
                "items": [{"menu_item": rival_item.id, "quantity": 1}],
            },
            format="json",
        )

        summary = self.merchant_client.get(MERCHANT_SUMMARY).json()
        self.assertEqual(summary["orders_today"], 1)
        self.assertEqual(summary["revenue_today"], "6.40")
        self.assertEqual(summary["new"], 1)

    def test_a_merchant_without_a_cafe_is_told_so(self):
        orphan = make_merchant("orphan@example.com")
        response = api_client_for(orphan).get(MERCHANT_CAFE)
        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="cafe_not_linked")

    def test_a_merchant_can_read_their_own_cafe(self):
        body = self.merchant_client.get(MERCHANT_CAFE).json()
        self.assertEqual(body["slug"], self.cafe.slug)
        self.assertEqual(body["prep_time_minutes"], 8)
        self.assertFalse(body["is_demo"])


class MerchantStatusEndpointTests(OrderApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        response = self.client.post(ORDER_CREATE, self.payload(), format="json")
        self.order = response.json()
        self.merchant_client = api_client_for(self.merchant)

    def patch(self, status: str):
        return self.merchant_client.patch(
            f"/api/merchant/orders/{self.order['public_id']}/status/",
            {"status": status},
            format="json",
        )

    def test_illegal_jumps_are_refused_with_a_conflict(self):
        response = self.patch(OrderStatus.READY)
        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="invalid_transition")

    def test_an_unknown_status_is_refused(self):
        response = self.patch("FLYING")
        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")

    def test_the_full_happy_path_succeeds(self):
        for status in (
            OrderStatus.ACCEPTED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.COLLECTED,
        ):
            response = self.patch(status)
            self.assertEqual(response.status_code, 200, msg=str(response.content))
        self.assertEqual(response.json()["status"], OrderStatus.COLLECTED)

    def test_a_note_is_recorded_on_the_event(self):
        response = self.merchant_client.patch(
            f"/api/merchant/orders/{self.order['public_id']}/status/",
            {"status": OrderStatus.ACCEPTED, "note": "Starting now"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        events = response.json()["events"]
        self.assertEqual(events[-1]["note"], "Starting now")

    def test_the_cafe_can_decline_a_new_order(self):
        response = self.merchant_client.patch(
            f"/api/merchant/orders/{self.order['public_id']}/status/",
            {"status": OrderStatus.REJECTED, "note": "Out of oat milk"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, msg=str(response.content))
        body = response.json()
        self.assertEqual(body["status"], OrderStatus.REJECTED)
        self.assertIsNotNone(body["rejected_at"])
        self.assertEqual(body["rejected_reason"], "Out of oat milk")
        self.assertEqual(body["events"][-1]["status"], OrderStatus.REJECTED)

    def test_a_declined_order_cannot_then_be_accepted(self):
        self.assertEqual(self.patch(OrderStatus.REJECTED).status_code, 200)
        response = self.patch(OrderStatus.ACCEPTED)
        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="invalid_transition")

    def test_an_accepted_order_can_no_longer_be_rejected(self):
        self.assertEqual(self.patch(OrderStatus.ACCEPTED).status_code, 200)
        response = self.patch(OrderStatus.REJECTED)
        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="rejection_closed")

    def test_a_rejected_order_leaves_the_open_board(self):
        self.assertEqual(self.patch(OrderStatus.REJECTED).status_code, 200)
        response = self.merchant_client.get(
            "/api/merchant/orders/", {"status": "rejected"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_the_next_action_endpoint_tells_the_cafe_what_to_do(self):
        response = self.merchant_client.get(
            f"/api/merchant/orders/{self.order['public_id']}/next-action/"
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["next_status"], OrderStatus.ACCEPTED)
        self.assertEqual(body["next_action_label"], "Accept")

    def test_a_board_column_filter_works(self):
        self.patch(OrderStatus.ACCEPTED)
        body = self.merchant_client.get(f"{MERCHANT_ORDERS}?status=accepted").json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["status"], OrderStatus.ACCEPTED)

        body = self.merchant_client.get(f"{MERCHANT_ORDERS}?status=ready").json()
        self.assertEqual(body["count"], 0)

    def test_an_unknown_filter_is_rejected(self):
        response = self.merchant_client.get(f"{MERCHANT_ORDERS}?status=bogus")
        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="invalid_status_filter")


class PublicCatalogueTests(ApiTestCase):
    def test_destinations_are_public(self):
        make_destination("city-centre-salon", name="City Centre Salon")
        response = self.client.get("/api/destinations/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["key"], "city-centre-salon")

    def test_inactive_destinations_are_hidden(self):
        make_destination("closed-place", is_active=False)
        self.assertEqual(self.client.get("/api/destinations/").json()["count"], 0)

    @override_settings(SHOW_DEMO_CAFES=False)
    def test_demo_cafes_are_hidden_from_a_live_pilot(self):
        make_cafe("fictional-cafe", is_demo=True)
        make_cafe("real-cafe", is_demo=False)

        body = self.client.get("/api/cafes/").json()
        self.assertEqual([row["slug"] for row in body["results"]], ["real-cafe"])

    @override_settings(SHOW_DEMO_CAFES=True)
    def test_demo_cafes_are_visible_when_explicitly_enabled(self):
        make_cafe("fictional-cafe", is_demo=True)

        body = self.client.get("/api/cafes/").json()
        self.assertEqual([row["slug"] for row in body["results"]], ["fictional-cafe"])
        self.assertTrue(body["results"][0]["is_demo"])

    @override_settings(SHOW_DEMO_CAFES=False)
    def test_a_demo_cafe_detail_page_is_not_reachable(self):
        make_cafe("fictional-cafe", is_demo=True)
        response = self.client.get("/api/cafes/fictional-cafe/")
        self.assertEqual(response.status_code, 404)

    def test_an_inactive_cafe_is_hidden(self):
        make_cafe("closed-for-now", is_active=False)
        self.assertEqual(self.client.get("/api/cafes/").json()["count"], 0)

    def test_a_cafe_lists_its_menu_with_prices_as_strings(self):
        cafe = make_cafe("menu-cafe")
        make_menu_item(cafe, "Latte", price="3.20")
        make_menu_item(cafe, "Toastie", price="4.50", category="Lunch")

        body = self.client.get("/api/cafes/menu-cafe/menu/").json()
        self.assertEqual(body["categories"], ["Coffee", "Lunch"])
        self.assertEqual(body["items"][0]["price"], "3.20")
        self.assertIsInstance(body["items"][0]["price"], str)

    def test_distances_come_from_the_database_not_the_browser(self):
        destination = make_destination("city-centre-salon")
        near = make_cafe("near-cafe")
        far = make_cafe("far-cafe")
        make_menu_item(near, "Latte")
        make_menu_item(far, "Latte")

        from readyby.testing import make_distance

        make_distance(far, destination, metres=900)
        make_distance(near, destination, metres=120)

        body = self.client.get(
            "/api/cafes/", {"destination": "city-centre-salon", "arrival_time": arrive_in(45).isoformat()}
        ).json()

        self.assertEqual(
            [row["slug"] for row in body["results"]], ["near-cafe", "far-cafe"]
        )
        self.assertEqual(body["results"][0]["distance_metres"], 120)
        self.assertEqual(body["results"][0]["distance_label"], "120 m")

    def test_a_missing_distance_is_stated_not_invented(self):
        make_cafe("lonely-cafe")
        body = self.client.get("/api/cafes/", {"destination": "nowhere"}).json()
        row = body["results"][0]
        self.assertIsNone(row["distance_metres"])
        self.assertEqual(row["distance_label"], "Distance unavailable")

    def test_a_cafe_with_no_arrival_time_is_not_bookable_yet(self):
        make_cafe("cafe", prep_time_minutes=8)
        row = self.client.get("/api/cafes/").json()["results"][0]
        self.assertFalse(row["can_order"])
        self.assertEqual(row["unavailable_reason"], "arrival_unavailable")

    def test_an_open_cafe_with_a_valid_arrival_is_bookable(self):
        make_cafe("cafe", prep_time_minutes=8)
        arrival = arrive_in(45)
        row = self.client.get(
            "/api/cafes/", {"arrival_time": arrival.isoformat()}
        ).json()["results"][0]

        self.assertTrue(row["can_order"])
        self.assertEqual(row["estimated_ready_time"], arrival.isoformat())
        self.assertEqual(row["start_preparing_time"], (arrival - timedelta(minutes=8)).isoformat())
        self.assertEqual(row["open_state"], "open")

    def test_an_unbookable_arrival_is_refused_with_a_reason(self):
        make_cafe("cafe", prep_time_minutes=8)
        row = self.client.get(
            "/api/cafes/",
            {"arrival_time": (timezone.now() + timedelta(minutes=1)).isoformat()},
        ).json()["results"][0]

        self.assertFalse(row["can_order"])
        self.assertEqual(row["unavailable_reason"], "arrival_unavailable")

    def test_a_bad_arrival_query_parameter_is_a_field_error(self):
        response = self.client.get("/api/cafes/", {"arrival_time": "later"})
        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")