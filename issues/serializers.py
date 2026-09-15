from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Issue


User = get_user_model()


class IssueSerializer(serializers.ModelSerializer):
    customer = serializers.ReadOnlyField(source="customer.username")

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="STAFF"),
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
