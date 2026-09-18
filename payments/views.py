from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .services import initiate_mpesa_stk_push
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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

class MpesaSTKPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get("payment_id")
        phone_number = request.data.get("phone_number")

        if not payment_id:
            return Response(
                {"detail": "payment_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not phone_number:
            return Response(
                {"detail": "phone_number is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            request.user.role == "CUSTOMER"
            and payment.customer != request.user
        ):
            return Response(
                {"detail": "You do not have permission to access this payment."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        if payment.status != Payment.Status.PENDING:
            return Response(
                {
                    "detail": (
                        "STK Push can only be initiated "
                        "for a pending payment."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mpesa_response = initiate_mpesa_stk_push(
                payment,
                phone_number,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "message": "STK Push initiated successfully.",
                "data": mpesa_response,
            },
            status=status.HTTP_200_OK,
        )

@method_decorator(csrf_exempt, name="dispatch")
class MpesaCallbackView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        callback_data = request.data

        try:
            stk_callback = callback_data["Body"]["stkCallback"]
        except (KeyError, TypeError):
            return Response(
                {
                    "ResultCode": 1,
                    "ResultDesc": "Invalid callback payload.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc", "")

        checkout_request_id = stk_callback.get(
            "CheckoutRequestID"
        )

        if not checkout_request_id:
            return Response(
                {
                    "ResultCode": 1,
                    "ResultDesc": "CheckoutRequestID is missing.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(
                mpesa_checkout_request_id=checkout_request_id
            )
        except Payment.DoesNotExist:
            return Response(
                {
                    "ResultCode": 1,
                    "ResultDesc": "Payment not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if payment.status == Payment.Status.SUCCESSFUL:
            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc": "Payment already processed.",
                },
                status=status.HTTP_200_OK,
            )



        if result_code == 0:
            callback_metadata = stk_callback.get(
                "CallbackMetadata", {}
            )

            items = callback_metadata.get("Item", [])

            metadata = {}

            for item in items:
                name = item.get("Name")
                value = item.get("Value")

                if name:
                    metadata[name] = value

            receipt_number = metadata.get(
                "MpesaReceiptNumber"
            )

            payment.transaction_id = receipt_number
            payment.status = Payment.Status.SUCCESSFUL

            payment.save(
                update_fields=[
                    "transaction_id",
                    "status",
                    "updated_at",
                ]
            )

        else:
            payment.status = Payment.Status.FAILED

            payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return Response(
            {
                "ResultCode": 0,
                "ResultDesc": "Callback processed successfully.",
            },
            status=status.HTTP_200_OK,
        )
    