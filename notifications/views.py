from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend


from .models import Notification
from .permissions import IsNotificationOwner
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
    ]

    filterset_fields = [
        "is_read",
        "notification_type",
    ]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by("-created_at")



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
