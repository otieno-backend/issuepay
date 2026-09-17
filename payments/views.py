from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from .models import Payment
from .permissions import IsPaymentParticipant,CanCreatePayment
from .serializers import PaymentSerializer,PaymentUpdateSerializer
from notifications.services import notify_payment_failed, notify_payment_successful


class PaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "status",
        "method",
        "issue",
    ]

    search_fields = [
        "transaction_id",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "amount",
        "status",
    ]

    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = [
                IsAuthenticated,
                CanCreatePayment,
            ]
        else:
            permission_classes = [
                IsAuthenticated,
            ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_queryset(self):
        user = self.request.user

        queryset = Payment.objects.select_related(
            "customer",
            "issue",
        )

        if user.role in ["STAFF", "ADMIN"]:
            return queryset.all()

        return queryset.filter(customer=user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
        IsAuthenticated,
        IsPaymentParticipant,
    ]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PaymentUpdateSerializer

        return PaymentSerializer

    def get_queryset(self):
        user = self.request.user

        queryset = Payment.objects.select_related(
            "customer",
            "issue",
        )

        if user.role in ["STAFF", "ADMIN"]:
            return queryset.all()

        return queryset.filter(customer=user)

    def perform_update(self, serializer):
        old_status = self.get_object().status

        payment = serializer.save()

        if (
            payment.status != old_status
            and payment.status == Payment.Status.SUCCESSFUL
        ):
            notify_payment_successful(payment)

        if (
            payment.status != old_status
            and payment.status == Payment.Status.FAILED
        ):
            notify_payment_failed(payment)
