from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "notification_type",
            "message",
            "is_read",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "notification_type",
            "message",
            "created_at",
        ]
