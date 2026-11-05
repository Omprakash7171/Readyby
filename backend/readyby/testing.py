"""Test helpers.

Kept out of the ``tests`` modules so every app's tests can build the same
fixtures. Nothing here is imported by production code.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User
from cafes.models import Cafe, CafeDistance, Destination, MenuItem

#: A café open every minute of every day, so arrival-time validation is the only
#: thing under test in the tests that do not care about hours.
ALWAYS_OPEN: dict[str, list[list[str]]] = {
    day: [["00:00", "23:59"]]
    for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
}

#: A café that has already shut for the day.
CLOSED_TODAY: dict[str, list[list[str]]] = {
    day: [["09:00", "17:00"]]
    for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
}


def make_customer(email: str = "customer@example.com", **kwargs) -> User:
    return User.objects.create_user(
        email=email,
        password="correct-horse-battery",
        first_name=kwargs.pop("first_name", "Casey"),
        last_name=kwargs.pop("last_name", "Customer"),
        role=User.Role.CUSTOMER,
        **kwargs,
    )


def make_merchant(email: str = "merchant@example.com", **kwargs) -> User:
    return User.objects.create_user(
        email=email,
        password="correct-horse-battery",
        first_name=kwargs.pop("first_name", "Morgan"),
        last_name=kwargs.pop("last_name", "Merchant"),
        role=User.Role.MERCHANT,
        is_staff=True,
        **kwargs,
    )


def make_cafe(
    slug: str = "test-cafe",
    *,
    merchant: User | None = None,
    opening_hours: dict | None = None,
    prep_time_minutes: int = 8,
    is_demo: bool = False,
    is_active: bool = True,
    **kwargs,
) -> Cafe:
    return Cafe.objects.create(
        slug=slug,
        name=kwargs.pop("name", slug.replace("-", " ").title()),
        tagline=kwargs.pop("tagline", "Test café"),
        category=kwargs.pop("category", "Coffee"),
        prep_time_minutes=prep_time_minutes,
        opening_hours=opening_hours or ALWAYS_OPEN,
        merchant=merchant,
        is_demo=is_demo,
        is_active=is_active,
        **kwargs,
    )


def make_menu_item(
    cafe: Cafe,
    name: str = "Latte",
    *,
    price: str = "3.20",
    is_available: bool = True,
    **kwargs,
) -> MenuItem:
    return MenuItem.objects.create(
        cafe=cafe,
        name=name,
        description=kwargs.pop("description", "A test drink"),
        price=Decimal(price),
        category=kwargs.pop("category", "Coffee"),
        art=kwargs.pop("art", "latte"),
        is_available=is_available,
        **kwargs,
    )


def make_destination(key: str = "test-destination", **kwargs) -> Destination:
    return Destination.objects.create(
        key=key,
        name=kwargs.pop("name", "Test Destination"),
        kind=kwargs.pop("kind", "Office"),
        area=kwargs.pop("area", "Test Area"),
        **kwargs,
    )


def make_distance(
    cafe: Cafe, destination: Destination, metres: int = 320
) -> CafeDistance:
    return CafeDistance.objects.create(
        cafe=cafe, destination=destination, metres=metres
    )


def arrive_in(minutes: int = 45):
    """A timezone-aware arrival far enough ahead to be bookable."""
    return timezone.now() + timedelta(minutes=minutes)


def token_for(user: User) -> str:
    token, _ = Token.objects.get_or_create(user=user)
    return token.key


def api_client_for(user: User) -> APIClient:
    """A client authenticated the way the real frontend authenticates."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token_for(user)}")
    return client


class ApiTestCase(TestCase):
    """Base case for API tests.

    Uses DRF's client so ``.credentials(...)`` and content negotiation behave the
    way the real frontend does, and resets throttle state between tests. The
    throttle cache is process-wide, so without this a long suite would start
    seeing 429s that have nothing to do with what is being tested.
    """

    client_class = APIClient

    def setUp(self) -> None:
        super().setUp()
        cache.clear()

    def assertErrorEnvelope(self, response, *, code: str | None = None) -> dict:
        """Every failure must use the documented error shape."""
        body = response.json()
        self.assertIn("code", body, msg=f"missing error code: {body}")
        self.assertIn("message", body, msg=f"missing error message: {body}")
        self.assertIn("field_errors", body, msg=f"missing field errors: {body}")
        if code is not None:
            self.assertEqual(body["code"], code, msg=f"unexpected body: {body}")
        return body


__all__ = [
    "ALWAYS_OPEN",
    "ApiTestCase",
    "CLOSED_TODAY",
    "api_client_for",
    "arrive_in",
    "make_cafe",
    "make_customer",
    "make_destination",
    "make_distance",
    "make_merchant",
    "make_menu_item",
    "token_for",
]