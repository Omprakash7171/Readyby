"""Registration and login: a customer can never make themselves a merchant."""

from __future__ import annotations

from accounts.models import User
from readyby.testing import ApiTestCase, make_merchant


class RegistrationTests(ApiTestCase):
    url = "/api/auth/register/"

    def register(self, **overrides):
        body = {
            "first_name": "New",
            "last_name": "Customer",
            "email": "new.customer@example.com",
            "password": "g0ldfish-battery-staple",
            "confirm_password": "g0ldfish-battery-staple",
        }
        body.update(overrides)
        return self.client.post(self.url, body, format="json")

    def test_registering_returns_a_working_token(self):
        response = self.register()
        self.assertEqual(response.status_code, 201, msg=str(response.content))
        body = response.json()

        self.assertTrue(body["token"])
        self.assertEqual(body["user"]["email"], "new.customer@example.com")
        self.assertEqual(body["user"]["role"], User.Role.CUSTOMER)
        self.assertIsNone(body["user"]["cafe"])

    def test_the_returned_token_authenticates_the_next_request(self):
        token = self.register().json()["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "new.customer@example.com")

    def test_the_new_account_reports_its_status_and_creation_date(self):
        body = self.register().json()["user"]

        self.assertEqual(body["status"], User.Status.ACTIVE)
        self.assertTrue(body["is_active"])
        self.assertTrue(body["created_at"])

    def test_the_names_are_stored_separately_and_composed_for_display(self):
        body = self.register().json()["user"]

        self.assertEqual(body["first_name"], "New")
        self.assertEqual(body["last_name"], "Customer")
        self.assertEqual(body["full_name"], "New Customer")
        self.assertEqual(body["display_name"], "New Customer")
        self.assertEqual(body["initials"], "NC")

    def test_a_last_name_is_optional(self):
        response = self.register(last_name="")

        self.assertEqual(response.status_code, 201, msg=str(response.content))
        self.assertEqual(response.json()["user"]["last_name"], "")
        self.assertEqual(response.json()["user"]["full_name"], "New")

    def test_a_suspension_cannot_be_requested_at_registration(self):
        self.register()

        response = self.register(
            email="second.customer@example.com",
            status="SUSPENDED",
            is_active=False,
        )

        user = User.objects.get(email="second.customer@example.com")
        self.assertEqual(user.status, User.Status.ACTIVE)
        self.assertTrue(user.is_active)
        self.assertEqual(response.status_code, 201)

    def test_a_new_customer_is_never_a_merchant_or_admin(self):
        """A customer must not be able to ask for elevated privileges."""
        response = self.register(role="MERCHANT")
        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email="new.customer@example.com")
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertFalse(user.is_merchant)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)

        body = response.json()["user"]
        self.assertEqual(body["role"], User.Role.CUSTOMER)

    def test_the_password_is_never_echoed_back(self):
        body = self.register().json()
        self.assertNotIn("password", body["user"])
        self.assertNotIn("password", str(body))

    def test_duplicate_emails_are_rejected(self):
        self.register()
        response = self.register()
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["field_errors"])

    def test_a_duplicate_email_is_detected_regardless_of_case(self):
        self.register(email="New.Customer@Example.com")

        response = self.register(email="new.customer@example.com")

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["field_errors"])

    def test_a_short_password_is_rejected(self):
        response = self.register(
            password="abc", confirm_password="abc"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json()["field_errors"])

    def test_a_common_password_is_rejected(self):
        response = self.register(password="password123", confirm_password="password123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json()["field_errors"])

    def test_an_invalid_email_is_rejected(self):
        response = self.register(email="not-an-email")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["field_errors"])

    def test_a_first_name_is_required(self):
        response = self.register(first_name="")
        self.assertEqual(response.status_code, 400)
        self.assertIn("first_name", response.json()["field_errors"])

    def test_a_single_letter_first_name_is_refused(self):
        response = self.register(first_name="J")
        self.assertEqual(response.status_code, 400)
        self.assertIn("first_name", response.json()["field_errors"])

    def test_a_single_letter_last_name_is_refused(self):
        response = self.register(last_name="X")
        self.assertEqual(response.status_code, 400)
        self.assertIn("last_name", response.json()["field_errors"])

    def test_a_usable_phone_number_is_stored(self):
        response = self.register(phone="+44 7700 900123")

        self.assertEqual(response.status_code, 201, msg=str(response.content))
        self.assertEqual(
            User.objects.get(email="new.customer@example.com").phone,
            "+44 7700 900123",
        )

    def test_an_unusable_phone_number_is_refused(self):
        response = self.register(phone="ring the café please")

        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", response.json()["field_errors"])

    def test_the_confirmation_must_match(self):
        response = self.register(confirm_password="something-else-entirely")

        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", response.json()["field_errors"])

    def test_the_confirmation_is_required(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "New",
                "email": "new.customer@example.com",
                "password": "g0ldfish-battery-staple",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", response.json()["field_errors"])

    def test_registering_again_does_not_reset_an_existing_account(self):
        self.register()
        self.register(password="a-completely-different-passphrase")
        self.assertEqual(User.objects.count(), 1)


class LoginTests(ApiTestCase):
    url = "/api/auth/login/"

    def setUp(self) -> None:
        super().setUp()
        from readyby.testing import make_customer

        self.user = make_customer()

    def test_valid_credentials_return_the_same_token_every_time(self):
        first = self.client.post(
            self.url,
            {"email": self.user.email, "password": "correct-horse-battery"},
            format="json",
        )
        second = self.client.post(
            self.url,
            {"email": self.user.email, "password": "correct-horse-battery"},
            format="json",
        )

        self.assertEqual(first.status_code, 200, msg=str(first.content))
        self.assertEqual(first.json()["token"], second.json()["token"])

    def test_the_login_is_case_insensitive_on_the_email(self):
        response = self.client.post(
            self.url,
            {"email": self.user.email.upper(), "password": "correct-horse-battery"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_a_wrong_password_is_rejected_without_hinting(self):
        response = self.client.post(
            self.url,
            {"email": self.user.email, "password": "wrong-password-here"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("Incorrect email or password", body["message"])
        self.assertNotIn("token", body)

    def test_an_unknown_email_gives_the_same_message_as_a_wrong_password(self):
        unknown = self.client.post(
            self.url,
            {"email": "nobody@example.com", "password": "correct-horse-battery"},
            format="json",
        )
        wrong = self.client.post(
            self.url,
            {"email": self.user.email, "password": "wrong-password-here"},
            format="json",
        )
        self.assertEqual(unknown.status_code, wrong.status_code)
        self.assertEqual(unknown.json()["message"], wrong.json()["message"])

    def test_an_inactive_account_cannot_sign_in(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            self.url,
            {"email": self.user.email, "password": "correct-horse-battery"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_a_merchant_sees_their_cafe_on_the_profile(self):
        from readyby.testing import make_cafe

        merchant = make_merchant()
        cafe = make_cafe("merchant-cafe", merchant=merchant)

        response = self.client.post(
            self.url,
            {"email": merchant.email, "password": "correct-horse-battery"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["cafe"]["slug"], cafe.slug)


class LogoutTests(ApiTestCase):
    def test_logging_out_invalidates_the_token(self):
        from readyby.testing import api_client_for, make_customer

        user = make_customer()
        client = api_client_for(user)

        self.assertEqual(client.get("/api/auth/me/").status_code, 200)

        response = client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 204)

        self.assertEqual(client.get("/api/auth/me/").status_code, 401)

    def test_a_customer_can_sign_in_again_after_logging_out(self):
        from readyby.testing import api_client_for, make_customer

        user = make_customer()
        api_client_for(user).post("/api/auth/logout/")

        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "correct-horse-battery"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["token"])


class MeEndpointTests(ApiTestCase):
    def test_the_profile_never_exposes_the_password_hash(self):
        from readyby.testing import api_client_for, make_customer

        client = api_client_for(make_customer())
        response = client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.json())
        self.assertNotIn("correct-horse-battery", response.content.decode())

    def test_anonymous_access_is_refused(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)


class ProfileUpdateTests(ApiTestCase):
    """A person may change their own details, and nothing else."""

    def setUp(self) -> None:
        super().setUp()
        from readyby.testing import api_client_for, make_customer

        self.user = make_customer(first_name="Casey", last_name="Customer")
        self.client = api_client_for(self.user)

    def patch(self, **payload):
        return self.client.patch("/api/auth/me/", payload, format="json")

    def test_the_name_and_phone_can_be_changed(self):
        response = self.patch(
            first_name="Robin", last_name="Baker", phone="020 7946 0958"
        )

        self.assertEqual(response.status_code, 200, msg=str(response.content))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Robin")
        self.assertEqual(self.user.last_name, "Baker")
        self.assertEqual(self.user.phone, "020 7946 0958")

    def test_an_unusable_phone_is_refused(self):
        response = self.patch(phone="ask for Casey")

        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", self.assertErrorEnvelope(response)["field_errors"])

    def test_a_role_change_is_ignored(self):
        """The account owner does not get to promote themselves."""
        response = self.patch(role="MERCHANT", status="SUSPENDED", is_active=False)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, User.Role.CUSTOMER)
        self.assertEqual(self.user.status, User.Status.ACTIVE)
        self.assertTrue(self.user.is_active)

    def test_the_email_address_cannot_be_changed_this_way(self):
        response = self.patch(email="somebody.else@example.com")

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "customer@example.com")

    def test_a_cafe_cannot_be_claimed_through_the_profile(self):
        from cafes.models import Cafe
        from readyby.testing import make_cafe

        cafe = make_cafe("profile-cafe")

        self.patch(cafe=cafe.slug)

        self.assertFalse(Cafe.objects.filter(merchant=self.user).exists())
        self.assertIsNone(cafe.merchant)

    def test_a_password_change_needs_the_current_one(self):
        response = self.patch(password="a-brand-new-passphrase")

        self.assertEqual(response.status_code, 400)
        self.assertIn("current_password", self.assertErrorEnvelope(response)["field_errors"])

    def test_a_wrong_current_password_is_refused(self):
        response = self.patch(
            password="a-brand-new-passphrase",
            current_password="not-the-one",
            confirm_password="a-brand-new-passphrase",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("current_password", self.assertErrorEnvelope(response)["field_errors"])
        self.assertTrue(self.user.check_password("correct-horse-battery"))

    def test_a_matching_password_change_works_and_the_new_one_signs_in(self):
        response = self.patch(
            password="a-brand-new-passphrase",
            current_password="correct-horse-battery",
            confirm_password="a-brand-new-passphrase",
        )

        self.assertEqual(response.status_code, 200, msg=str(response.content))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("a-brand-new-passphrase"))

        login = self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "a-brand-new-passphrase"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)

    def test_a_mismatched_confirmation_is_refused(self):
        response = self.patch(
            password="a-brand-new-passphrase",
            current_password="correct-horse-battery",
            confirm_password="something-else",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", self.assertErrorEnvelope(response)["field_errors"])

    def test_a_new_password_that_is_too_weak_is_refused(self):
        response = self.patch(
            password="password123",
            current_password="correct-horse-battery",
            confirm_password="password123",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", self.assertErrorEnvelope(response)["field_errors"])

    def test_anonymous_users_cannot_edit_a_profile(self):
        from rest_framework.test import APIClient

        response = APIClient().patch(
            "/api/auth/me/", {"first_name": "Mallory"}, format="json"
        )
        self.assertEqual(response.status_code, 401)


class AccountStatusTests(ApiTestCase):
    """``status`` and ``is_active`` must never disagree."""

    def setUp(self) -> None:
        super().setUp()
        from readyby.testing import make_customer

        self.user = make_customer()

    def test_a_new_account_is_active(self):
        self.assertEqual(self.user.status, User.Status.ACTIVE)
        self.assertTrue(self.user.is_active)

    def test_deactivating_the_account_suspends_it(self):
        self.user.is_active = False
        self.user.save()

        self.assertEqual(self.user.status, User.Status.SUSPENDED)

    def test_setting_the_status_suspends_the_account(self):
        self.user.set_suspended()

        self.user.refresh_from_db()
        self.assertEqual(self.user.status, User.Status.SUSPENDED)
        self.assertFalse(self.user.is_active)

    def test_a_suspended_account_cannot_sign_in(self):
        self.user.set_suspended()

        response = self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "correct-horse-battery"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_restoring_the_account_lets_them_sign_in_again(self):
        self.user.set_suspended()
        self.user.set_suspended(False)

        response = self.client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "correct-horse-battery"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)


class JwtTests(ApiTestCase):
    """JWT is accepted alongside the opaque token, not instead of it."""

    def setUp(self) -> None:
        super().setUp()
        from readyby.testing import make_customer

        self.user = make_customer()
        self.credentials = {
            "email": self.user.email,
            "password": "correct-horse-battery",
        }

    def test_the_token_endpoint_returns_a_usable_pair(self):
        response = self.client.post("/api/auth/token/", self.credentials, format="json")
        self.assertEqual(response.status_code, 200, msg=str(response.content))
        body = response.json()
        self.assertTrue(body["access"])
        self.assertTrue(body["refresh"])

        client = self.client_class()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {body['access']}")
        me = client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], self.user.email)

    def test_login_also_returns_the_jwt_pair(self):
        """One call gives a client both schemes."""
        response = self.client.post(
            "/api/auth/login/", self.credentials, format="json"
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["token"])
        self.assertTrue(body["access"])
        self.assertTrue(body["refresh"])

    def test_a_refresh_token_buys_a_new_access_token(self):
        refresh = self.client.post(
            "/api/auth/token/", self.credentials, format="json"
        ).json()["refresh"]

        response = self.client.post(
            "/api/auth/token/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["access"])

    def test_a_garbage_refresh_token_is_refused(self):
        response = self.client.post(
            "/api/auth/token/refresh/", {"refresh": "not-a-jwt"}, format="json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_a_missing_refresh_token_is_a_field_error(self):
        response = self.client.post("/api/auth/token/refresh/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")

    def test_a_wrong_password_yields_no_jwt(self):
        response = self.client.post(
            "/api/auth/token/",
            {"email": self.user.email, "password": "wrong-password-here"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access", response.json())

    def test_the_opaque_token_still_works(self):
        """Adding JWT must not break the credential browsers already hold."""
        from readyby.testing import api_client_for

        self.assertEqual(api_client_for(self.user).get("/api/auth/me/").status_code, 200)

    def test_a_garbage_bearer_token_is_refused(self):
        client = self.client_class()
        client.credentials(HTTP_AUTHORIZATION="Bearer not-a-jwt")
        response = client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_the_jwt_login_is_throttled_like_the_password_one(self):
        for _ in range(12):
            self.client.post("/api/auth/token/", self.credentials, format="json")
        response = self.client.post("/api/auth/token/", self.credentials, format="json")
        self.assertEqual(response.status_code, 429)