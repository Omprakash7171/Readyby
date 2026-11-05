"""Authorisation helpers shared by the customer and merchant APIs."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from readyby_api.exceptions import PilotAPIException


class IsMerchant(BasePermission):
    message = "This endpoint is for café accounts."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_merchant)


class IsAdmin(BasePermission):
    message = "This endpoint is for ReadyBy administrators."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin)


class IsCustomerOrMerchant(BasePermission):
    """Signed-in users of either role; the view narrows the queryset further."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)


def require_merchant_for(user, cafe):
    """Raise a clean 404-style failure when a merchant touches another café.

    Merchant isolation is enforced here rather than only in the queryset so a
    shared view cannot accidentally forget to filter.
    """
    if user.is_admin:
        return
    if not user.is_merchant or cafe.merchant_id != user.id:
        raise PilotAPIException(
            "Café not found.",
            code="cafe_not_found",
            status_code=404,
        )