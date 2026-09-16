from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Payment


User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(
        source="customer.username"
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "issue",
            "customer",
            "amount",
            "method",
            "status",
            "transaction_id",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer",
            "status",
            "transaction_id",
            "created_at",
            "updated_at",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Payment amount must be greater than zero."
            )

        return value

    def validate_issue(self, issue):
        request = self.context.get("request")

        if request and request.user.role == User.Role.CUSTOMER:
            if issue.customer != request.user:
                raise serializers.ValidationError(
                    "You can only pay for your own issues."
                )

        return issue


class PaymentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "status",
            "transaction_id",
        ]

    def validate_status(self, value):
        valid_statuses = {
            choice[0]
            for choice in Payment.Status.choices
        }

        if value not in valid_statuses:
            raise serializers.ValidationError(
                "Invalid payment status."
            )

        payment = self.instance

        if payment is None:
            return value

        allowed_transitions = {
            Payment.Status.PENDING: {
                Payment.Status.SUCCESSFUL,
                Payment.Status.FAILED,
            },
            Payment.Status.SUCCESSFUL: {
                Payment.Status.REFUNDED,
            },
            Payment.Status.FAILED: set(),
            Payment.Status.REFUNDED: set(),
        }

        current_status = payment.status

        if value == current_status:
            return value

        if value not in allowed_transitions[current_status]:
            raise serializers.ValidationError(
                f"Cannot change payment status from "
                f"{current_status} to {value}."
            )

        return value
