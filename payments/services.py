from .models import Payment


ALLOWED_STATUS_TRANSITIONS = {
    Payment.Status.PENDING: {
        Payment.Status.SUCCESSFUL,
        Payment.Status.FAILED,
    },
    Payment.Status.SUCCESSFUL: {
        Payment.Status.REFUNDED,
    },
    Payment.Status.FAILED: set(),
    Payment.Status.REFUNDED: set(),
}


def validate_status_transition(payment, new_status):
    if new_status not in Payment.Status.values:
        raise ValueError("Invalid payment status.")

    if payment is None:
        return

    if new_status == payment.status:
        return

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS[payment.status]

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Cannot change payment status from "
            f"{payment.status} to {new_status}."
        )
