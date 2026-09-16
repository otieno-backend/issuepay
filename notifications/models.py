from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        ISSUE_CREATED = "ISSUE_CREATED", "Issue Created"
        ISSUE_ASSIGNED = "ISSUE_ASSIGNED", "Issue Assigned"
        ISSUE_STATUS_CHANGED = (
            "ISSUE_STATUS_CHANGED",
            "Issue Status Changed",
        )
        PAYMENT_SUCCESSFUL = (
            "PAYMENT_SUCCESSFUL",
            "Payment Successful",
        )
        PAYMENT_FAILED = "PAYMENT_FAILED", "Payment Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=30,
        choices=Type.choices,
    )

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"
