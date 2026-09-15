from django.contrib import admin

from .models import Issue


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "customer",
        "assigned_to",
        "status",
        "priority",
        "created_at",
    ]

    list_filter = [
        "status",
        "priority",
    ]

    search_fields = [
        "title",
        "description",
        "customer__username",
        "customer__email",
    ]
