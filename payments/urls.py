from django.urls import path

from .views import (
    MpesaCallbackView,
    MpesaSTKPushView,
    PaymentDetailView,
    PaymentListCreateView,
)


urlpatterns = [
    path(
    "mpesa/callback/",
    MpesaCallbackView.as_view(),
    name="mpesa-callback",
),
    path(
        "mpesa/stk-push/",
        MpesaSTKPushView.as_view(),
        name="mpesa-stk-push",
    ),
    path(
        "",
        PaymentListCreateView.as_view(),
        name="payment-list-create",
    ),
    path(
        "<int:pk>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),
]
