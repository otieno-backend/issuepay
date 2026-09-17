from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Payment
from .services import validate_status_transition


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

    def validate(self, attrs):
        issue = attrs.get("issue")
        amount = attrs.get("amount")

        if issue and amount != issue.amount:
            raise serializers.ValidationError(
                {
                    "amount": (
                        "Payment amount must match "
                        "the issue amount."
                    )
                }
            )

        return attrs


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
        try:
            validate_status_transition(
                self.instance,
                value,
            )
        except ValueError as exc:
            raise serializers.ValidationError(
                str(exc)
            )

        return value

