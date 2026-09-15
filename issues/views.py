from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.permissions import IsAuthenticated

from .models import Issue
from .permissions import IsIssueParticipant
from .serializers import IssueSerializer


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
        serializer.save(customer=self.request.user)


class IssueDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = IssueSerializer
    permission_classes = [
        IsAuthenticated,
        IsIssueParticipant,
    ]

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
