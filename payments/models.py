from django.conf import settings
from django.db import models

from issues.models import Issue


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESSFUL = "SUCCESSFUL", "Successful"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    class Method(models.TextChoices):
        MPESA = "MPESA", "M-Pesa"
        CARD = "CARD", "Card"
        BANK = "BANK", "Bank Transfer"

    issue = models.ForeignKey(
        Issue,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    method = models.CharField(
        max_length=20,
        choices=Method.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )

    mpesa_checkout_request_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.amount}"
