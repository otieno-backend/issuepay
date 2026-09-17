from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .permissions import IsNotificationOwner
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "is_read",
        "notification_type",
    ]

    search_fields = [
        "message",
    ]

    ordering_fields = [
        "created_at",
        "is_read",
    ]

    ordering = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        )


class NotificationDetailView(
    generics.RetrieveUpdateAPIView
):
    serializer_class = NotificationSerializer

    permission_classes = [
        IsAuthenticated,
        IsNotificationOwner,
    ]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save()
