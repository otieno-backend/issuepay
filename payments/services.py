import base64
import re
from datetime import datetime

import requests
from django.conf import settings

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


def get_mpesa_base_url():
    if settings.MPESA_ENVIRONMENT == "production":
        return "https://api.safaricom.co.ke"

    return "https://sandbox.safaricom.co.ke"


def get_mpesa_access_token():
    if not settings.MPESA_CONSUMER_KEY:
        raise RuntimeError("MPESA_CONSUMER_KEY is not configured.")

    if not settings.MPESA_CONSUMER_SECRET:
        raise RuntimeError("MPESA_CONSUMER_SECRET is not configured.")

    url = f"{get_mpesa_base_url()}/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        url,
        auth=(
            settings.MPESA_CONSUMER_KEY,
            settings.MPESA_CONSUMER_SECRET,
        ),
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["access_token"]


def generate_password(timestamp):
    raw_password = (
        f"{settings.MPESA_SHORTCODE}"
        f"{settings.MPESA_PASSKEY}"
        f"{timestamp}"
    )

    return base64.b64encode(
        raw_password.encode("utf-8")
    ).decode("utf-8")

def normalize_mpesa_phone_number(phone_number):
    """
    Validate and normalize a Kenyan M-Pesa phone number.

    Returns the number in 2547XXXXXXXX format.
    """
    if not isinstance(phone_number, str):
        raise ValueError("Phone number must be a string.")

    phone_number = phone_number.strip()

    # Remove spaces, hyphens, and parentheses.
    phone_number = re.sub(r"[\s\-()]", "", phone_number)

    if phone_number.startswith("+254"):
        phone_number = "254" + phone_number[4:]

    elif phone_number.startswith("07"):
        phone_number = "254" + phone_number[1:]

    elif phone_number.startswith("01"):
        phone_number = "254" + phone_number[1:]

    elif phone_number.startswith("254"):
        pass

    else:
        raise ValueError(
            "Enter a valid Kenyan phone number."
        )

    if not re.fullmatch(r"254[17]\d{8}", phone_number):
        raise ValueError(
            "Enter a valid Kenyan phone number."
        )

    return phone_number

def initiate_mpesa_stk_push(
    payment,
    phone_number,
):
    """
    Initiate an M-PESA STK Push for a Payment.

    This requires valid Daraja credentials.
    """
    phone_number = normalize_mpesa_phone_number(phone_number)

    required_settings = {
        "MPESA_SHORTCODE": settings.MPESA_SHORTCODE,
        "MPESA_PASSKEY": settings.MPESA_PASSKEY,
        "MPESA_CALLBACK_URL": settings.MPESA_CALLBACK_URL,
    }

    missing = [
        name
        for name, value in required_settings.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing M-PESA configuration: "
            + ", ".join(missing)
        )


    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password = generate_password(timestamp)

    access_token = get_mpesa_access_token()

    url = (
        f"{get_mpesa_base_url()}"
        "/mpesa/stkpush/v1/processrequest"
    )

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(payment.amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"ISSUE-{payment.issue_id}",
        "TransactionDesc": f"Payment for Issue {payment.issue_id}",
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    checkout_request_id = data.get("CheckoutRequestID")

    if checkout_request_id:
        payment.mpesa_checkout_request_id = checkout_request_id
        payment.save(
            update_fields=[
                "mpesa_checkout_request_id",
                "updated_at",
            ]
        )

    return data
