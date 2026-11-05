from django.urls import path

from .merchant_menu import (
    MerchantMenuCreateView,
    MerchantMenuDetailView,
    MerchantMenuListView,
)
from .views import (
    CafeDetailView,
    CafeListView,
    CafeMenuView,
    CafeQuoteView,
    DestinationListView,
    MerchantCafeView,
    MerchantPickupSlotsView,
)

urlpatterns = [
    path("destinations/", DestinationListView.as_view(), name="destination-list"),
    path("cafes/", CafeListView.as_view(), name="cafe-list"),
    path("cafes/<slug:slug>/", CafeDetailView.as_view(), name="cafe-detail"),
    path("cafes/<slug:slug>/menu/", CafeMenuView.as_view(), name="cafe-menu"),
    path("cafes/<slug:slug>/quote/", CafeQuoteView.as_view(), name="cafe-quote"),
    path("merchant/cafe/", MerchantCafeView.as_view(), name="merchant-cafe"),
    path(
        "merchant/pickup-slots/",
        MerchantPickupSlotsView.as_view(),
        name="merchant-pickup-slots",
    ),
    # Café-facing menu management. Scoped to the merchant's own café.
    path("merchant/menu/", MerchantMenuListView.as_view(), name="merchant-menu"),
    path("merchant/menu/create/", MerchantMenuCreateView.as_view(), name="merchant-menu-create"),
    path(
        "merchant/menu/<int:item_id>/",
        MerchantMenuDetailView.as_view(),
        name="merchant-menu-detail",
    ),
]