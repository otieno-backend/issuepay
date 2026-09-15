from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Issue


User = get_user_model()


class IssueSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source="customer.username")

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.STAFF),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Issue
        fields = [
            "id",
            "title",
            "description",
            "customer",
            "assigned_to",
            "status",
            "priority",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Title cannot be empty."
            )

        return value

    def validate_description(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Description cannot be empty."
            )

        return value
    

class StaffIssueUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = [
            "status",
            "priority",
            "assigned_to",
        ]

    def validate_assigned_to(self, user):
        if user is not None and user.role != User.Role.STAFF:
            raise serializers.ValidationError(
                "Issues can only be assigned to staff members."
            )

        return user
