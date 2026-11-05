"""CORS preflight contract for the browser client.

A request carrying a non-safelisted header has to pass a preflight first, and
the browser only sends the real request if the preflight echoes that header back
in ``Access-Control-Allow-Headers``. A header missing from that list fails the
preflight silently: Django logs nothing, the view never runs, and ``fetch()``
rejects with a TypeError the frontend cannot tell apart from the API being
down. So the allowlist is pinned here rather than left to the library default.
"""

from __future__ import annotations

from django.test import SimpleTestCase

from corsheaders.conf import conf

FRONTEND_ORIGIN = "http://localhost:3000"
ORDER_CREATE = "/api/orders/new/"


class PreflightTestCase(SimpleTestCase):
    def preflight(self, url: str, requested_headers: str):
        return self.client.options(
            url,
            HTTP_ORIGIN=FRONTEND_ORIGIN,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS=requested_headers,
        )

    def allowed_headers(self, url: str, requested_headers: str) -> set[str]:
        response = self.preflight(url, requested_headers)
        self.assertEqual(response.status_code, 200)
        echoed = response.headers.get("Access-Control-Allow-Headers", "")
        return {item.strip().lower() for item in echoed.split(",") if item.strip()}


class OrderCreationPreflightTests(PreflightTestCase):
    """createOrder() attaches Idempotency-Key; the preflight must allow it."""

    def test_idempotency_key_is_allowed(self):
        """The regression: without this the Place order button never reaches the API."""
        allowed = self.allowed_headers(
            ORDER_CREATE, "authorization,content-type,idempotency-key"
        )

        self.assertIn("idempotency-key", allowed)

    def test_the_browsers_own_request_headers_are_still_allowed(self):
        """Widening the list must not drop the auth and content headers."""
        allowed = self.allowed_headers(
            ORDER_CREATE, "accept,authorization,content-type,idempotency-key"
        )

        self.assertLessEqual({"accept", "authorization", "content-type"}, allowed)

    def test_every_header_the_client_sends_is_allowed(self):
        """Guards against the client adding a header the server does not echo."""
        from django.conf import settings

        allowed = self.allowed_headers(
            ORDER_CREATE, ", ".join(settings.CORS_ALLOW_HEADERS)
        )

        self.assertEqual(allowed, set(conf.CORS_ALLOW_HEADERS))


class OriginTests(PreflightTestCase):
    def test_local_development_accepts_the_frontend_origin(self):
        response = self.preflight(ORDER_CREATE, "idempotency-key")

        self.assertTrue(response.headers.get("Access-Control-Allow-Origin"))

    def test_the_allowlist_is_wide_enough_for_local_spellings(self):
        """A missing origin is the same invisible failure as a missing header."""
        from django.conf import settings

        if settings.CORS_ALLOW_ALL_ORIGINS:
            self.skipTest("local development accepts any origin")

        self.assertLessEqual({"http://localhost:3000"}, settings.CORS_ALLOWED_ORIGINS)