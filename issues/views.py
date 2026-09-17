from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from notifications.services import (
    notify_issue_assigned,
    notify_issue_created,
    notify_issue_status_changed,
    notify_staff_of_new_issue,
)

from .models import Issue
from .permissions import IsIssueParticipant
from .serializers import IssueSerializer, StaffIssueUpdateSerializer


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

        notify_issue_created(
            self.request.user,
            issue,
        )

        notify_staff_of_new_issue(
            issue,
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

        if (
            issue.assigned_to is not None
            and issue.assigned_to != old_assigned_to
        ):
            notify_issue_assigned(
                issue.assigned_to,
                issue,
            )

        if issue.status != old_status:
            notify_issue_status_changed(
                issue.customer,
                issue,
            )
