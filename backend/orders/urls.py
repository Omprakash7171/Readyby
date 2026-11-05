from django.urls import path

from .views import (
    CancelOrderView,
    CreateOrderView,
    MerchantBoardSummaryView,
    MerchantNextActionView,
    MerchantOrderListView,
    MerchantOrderStatusView,
    MyOrderListView,
    OrderDetailView,
    OrderStatusView,
)

urlpatterns = [
    # Customer
    path("orders/", MyOrderListView.as_view(), name="order-list"),
    path("orders/new/", CreateOrderView.as_view(), name="order-create"),
    path("orders/<str:public_id>/", OrderDetailView.as_view(), name="order-detail"),
    path(
        "orders/<str:public_id>/status/",
        OrderStatusView.as_view(),
        name="order-status",
    ),
    path(
        "orders/<str:public_id>/cancel/",
        CancelOrderView.as_view(),
        name="order-cancel",
    ),
    # Merchant
    path("merchant/orders/", MerchantOrderListView.as_view(), name="merchant-orders"),
    path(
        "merchant/orders/summary/",
        MerchantBoardSummaryView.as_view(),
        name="merchant-summary",
    ),
    path(
        "merchant/orders/<str:public_id>/status/",
        MerchantOrderStatusView.as_view(),
        name="merchant-order-status",
    ),
    path(
        "merchant/orders/<str:public_id>/next-action/",
        MerchantNextActionView.as_view(),
        name="merchant-next-action",
    ),
]