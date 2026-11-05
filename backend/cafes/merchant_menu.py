"""Café-facing menu management.

A café keeps its own menu current without a ReadyBy engineer: add a drink,
change a price, mark something sold out, remove an item. Every view is scoped to
the signed-in merchant's own café, so one café can never see or edit another's
menu.

Money is a ``Decimal`` end to end. The browser sends a price as a string; it is
parsed by a ``DecimalField`` and stored as a ``Decimal``, never as a float.
"""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsMerchant
from readyby_api.exceptions import PilotAPIException
from readyby_api.schema import ERROR_RESPONSE, MERCHANT_MENU_RESPONSE

from .models import Cafe, MenuItem
from .serializers import MerchantMenuItemWriteSerializer, MenuItemSerializer


def _require_cafe(user) -> Cafe:
    """The café this merchant owns, or a clear 404."""
    cafe = getattr(user, "cafe", None)
    if cafe is None or not cafe.is_active:
        raise PilotAPIException(
            "No café is linked to this account yet. Ask a ReadyBy admin to set it up.",
            code="cafe_not_linked",
            status_code=404,
        )
    return cafe


def _merchant_item(cafe: Cafe, item_id: int) -> MenuItem:
    """Fetch an item, refusing anything that is not this café's.

    Scoping the lookup by café *is* the isolation guarantee: a merchant asking
    for another café's item id simply gets a 404.
    """
    item = MenuItem.objects.filter(cafe=cafe, pk=item_id).first()
    if item is None:
        raise PilotAPIException(
            "That menu item was not found.",
            code="menu_item_not_found",
            status_code=404,
        )
    return item


@extend_schema(
    tags=["merchant"],
    summary="This café's menu",
    responses={200: MERCHANT_MENU_RESPONSE, 401: ERROR_RESPONSE, 404: ERROR_RESPONSE},
)
class MerchantMenuListView(APIView):
    permission_classes = [IsMerchant]

    def get(self, request):
        cafe = _require_cafe(request.user)
        items = list(
            MenuItem.objects.filter(cafe=cafe).order_by("category", "sort_order", "name")
        )
        categories: list[str] = []
        for item in items:
            if item.category not in categories:
                categories.append(item.category)
        return Response(
            {
                "cafe": cafe.slug,
                "count": len(items),
                "categories": categories,
                "results": [MenuItemSerializer(item).data for item in items],
            }
        )


@extend_schema(
    tags=["merchant"],
    summary="Add a menu item",
    description=(
        "Prices are stored as decimals. There is no card payment in the pilot: "
        "the customer pays at the counter."
    ),
    request=MerchantMenuItemWriteSerializer,
    responses={
        201: MERCHANT_MENU_RESPONSE,
        400: ERROR_RESPONSE,
        401: ERROR_RESPONSE,
        404: ERROR_RESPONSE,
    },
)
class MerchantMenuCreateView(APIView):
    permission_classes = [IsMerchant]

    def post(self, request):
        cafe = _require_cafe(request.user)
        serializer = MerchantMenuItemWriteSerializer(
            data=request.data, context={"cafe": cafe}
        )
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(MenuItemSerializer(item).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["merchant"],
    summary="Edit, reprice or sell out one menu item",
    request=MerchantMenuItemWriteSerializer,
    responses={
        200: MERCHANT_MENU_RESPONSE,
        400: ERROR_RESPONSE,
        401: ERROR_RESPONSE,
        404: ERROR_RESPONSE,
    },
)
class MerchantMenuDetailView(APIView):
    permission_classes = [IsMerchant]

    def patch(self, request, item_id: int):
        cafe = _require_cafe(request.user)
        item = _merchant_item(cafe, item_id)
        serializer = MerchantMenuItemWriteSerializer(
            instance=item, data=request.data, partial=True, context={"cafe": cafe}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MenuItemSerializer(serializer.instance).data)

    @extend_schema(
        tags=["merchant"],
        summary="Remove a menu item",
        description=(
            "Past orders keep their own copy of the name and price, so removing "
            "an item never changes an order that has already been placed."
        ),
        responses={204: None, 401: ERROR_RESPONSE, 404: ERROR_RESPONSE},
    )
    def delete(self, request, item_id: int):
        _merchant_item(_require_cafe(request.user), item_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


__all__ = [
    "MerchantMenuCreateView",
    "MerchantMenuDetailView",
    "MerchantMenuListView",
]