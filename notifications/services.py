from .models import Notification


def notify_issue_created(user, issue):
    Notification.objects.create(
        user=user,
        notification_type=Notification.Type.ISSUE_CREATED,
        message=f"Your issue '{issue.title}' has been created.",
    )


def notify_staff_of_new_issue(issue):
    staff_users = issue.customer.__class__.objects.filter(
        role=issue.customer.Role.STAFF
    )

    notifications = []

    for staff in staff_users:
        notifications.append(
            Notification(
                user=staff,
                notification_type=Notification.Type.ISSUE_CREATED,
                message=(
                    f"New issue '{issue.title}' "
                    f"has been created by "
                    f"{issue.customer.username}."
                ),
            )
        )

    Notification.objects.bulk_create(notifications)


def notify_issue_assigned(staff, issue):
    Notification.objects.create(
        user=staff,
        notification_type=Notification.Type.ISSUE_ASSIGNED,
        message=f"You have been assigned issue '{issue.title}'.",
    )


def notify_issue_status_changed(customer, issue):
    Notification.objects.create(
        user=customer,
        notification_type=Notification.Type.ISSUE_STATUS_CHANGED,
        message=(
            f"The status of your issue "
            f"'{issue.title}' has changed to "
            f"{issue.status}."
        ),
    )

def notify_payment_successful(payment):
    Notification.objects.create(
        user=payment.customer,
        notification_type=Notification.Type.PAYMENT_SUCCESSFUL,
        message=(
            f"Your payment of {payment.amount} "
            f"for issue '{payment.issue.title}' "
            f"was successful."
        ),
    )


def notify_payment_failed(payment):
    Notification.objects.create(
        user=payment.customer,
        notification_type=Notification.Type.PAYMENT_FAILED,
        message=(
            f"Your payment of {payment.amount} "
            f"for issue '{payment.issue.title}' "
            f"failed."
        ),
    )
