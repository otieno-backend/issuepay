from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from notifications.models import Notification

from .models import Issue
from .permissions import IsIssueParticipant
from .serializers import IssueSerializer, StaffIssueUpdateSerializer


User = get_user_model()


class IssueListCreateView(generics.ListCreateAPIView):
    serializer_class = IssueSerializer
    permission_classes = [
        IsAuthenticated,
        IsIssueParticipant,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "status",
        "priority",
        "assigned_to",
    ]

    search_fields = [
        "title",
        "description",
    ]

    ordering_fields = [
        "created_at",
        "updated_at",
        "priority",
        "status",
    ]

    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        if user.role in ["STAFF", "ADMIN"]:
            return Issue.objects.select_related(
                "customer",
                "assigned_to",
            ).all()

        return Issue.objects.select_related(
            "customer",
            "assigned_to",
        ).filter(customer=user)

    def perform_create(self, serializer):
        issue = serializer.save(
            customer=self.request.user
        )

        # Notify the customer
        Notification.objects.create(
            user=self.request.user,
            notification_type=Notification.Type.ISSUE_CREATED,
            message=(
                f"Your issue '{issue.title}' has been created."
            ),
        )

        # Notify all staff members
        staff_users = User.objects.filter(
            role=User.Role.STAFF
        )

        for staff in staff_users:
            Notification.objects.create(
                user=staff,
                notification_type=Notification.Type.ISSUE_CREATED,
                message=(
                    f"New issue '{issue.title}' "
                    f"has been created by "
                    f"{issue.customer.username}."
                ),
            )


class IssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IssueSerializer
    permission_classes = [
        IsAuthenticated,
        IsIssueParticipant,
    ]

    def get_serializer_class(self):
        if self.request.user.role in ["STAFF", "ADMIN"]:
            if self.request.method in ["PUT", "PATCH"]:
                return StaffIssueUpdateSerializer

        return IssueSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role in ["STAFF", "ADMIN"]:
            return Issue.objects.select_related(
                "customer",
                "assigned_to",
            ).all()

        return Issue.objects.select_related(
            "customer",
            "assigned_to",
        ).filter(customer=user)

    def perform_update(self, serializer):
        old_issue = self.get_object()

        old_assigned_to = old_issue.assigned_to
        old_status = old_issue.status

        issue = serializer.save()

        # Notify newly assigned staff member
        if (
            issue.assigned_to is not None
            and issue.assigned_to != old_assigned_to
        ):
            Notification.objects.create(
                user=issue.assigned_to,
                notification_type=Notification.Type.ISSUE_ASSIGNED,
                message=(
                    f"You have been assigned issue "
                    f"'{issue.title}'."
                ),
            )

        # Notify customer when status changes
        if issue.status != old_status:
            Notification.objects.create(
                user=issue.customer,
                notification_type=Notification.Type.ISSUE_STATUS_CHANGED,
                message=(
                    f"The status of your issue "
                    f"'{issue.title}' has changed to "
                    f"{issue.status}."
                ),
            )
