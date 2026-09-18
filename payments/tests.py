from decimal import Decimal
from unittest.mock import patch, Mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from issues.models import Issue
from notifications.models import Notification


from .models import Payment




User = get_user_model()


class PaymentAPITests(APITestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer1",
            email="customer1@example.com",
            password="StrongPassword123",
            role=User.Role.CUSTOMER,
        )

        self.other_customer = User.objects.create_user(
            username="customer2",
            email="customer2@example.com",
            password="StrongPassword123",
            role=User.Role.CUSTOMER,
        )

        self.staff = User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="StrongPassword123",
            role=User.Role.STAFF,
        )

        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@example.com",
            password="StrongPassword123",
            role=User.Role.ADMIN,
        )

        self.issue = Issue.objects.create(
            title="Payment issue",
            description="Customer needs to make a payment.",
            amount="1000.00",
            customer=self.customer,
        )


        self.other_issue = Issue.objects.create(
            title="Other payment issue",
            description="Another customer's issue.",
            amount="500.00",
            customer=self.other_customer,
        )


        self.payment = Payment.objects.create(
            issue=self.issue,
            customer=self.customer,
            amount=Decimal("1000.00"),
            method=Payment.Method.MPESA,
        )

        self.other_payment = Payment.objects.create(
            issue=self.other_issue,
            customer=self.other_customer,
            amount="500.00",
            method=Payment.Method.CARD,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_unauthenticated_user_cannot_list_payments(self):
        response = self.client.get("/api/payments/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_can_create_payment_for_own_issue(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.issue.id,
                "amount": Decimal("1000.00"),
                "method": "MPESA",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["customer"],
            self.customer.username,
        )

        payment = Payment.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            payment.customer,
            self.customer,
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

    def test_customer_cannot_pay_for_another_customers_issue(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.other_issue.id,
                "amount": Decimal("1000.00"),
                "method": "MPESA",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_customer_can_only_see_own_payments(self):
        self.authenticate(self.customer)

        response = self.client.get("/api/payments/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

        self.assertEqual(
            response.data["results"][0]["id"],
            self.payment.id,
        )

    def test_customer_cannot_view_another_customers_payment(self):
        self.authenticate(self.customer)

        response = self.client.get(
            f"/api/payments/{self.other_payment.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_customer_cannot_update_payment(self):
        self.authenticate(self.customer)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "amount": Decimal("1000.00"),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_customer_cannot_delete_payment(self):
        self.authenticate(self.customer)

        response = self.client.delete(
            f"/api/payments/{self.payment.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_customer_cannot_set_payment_status(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.issue.id,
                "amount": Decimal("1000.00"),
                "method": "CARD",
                "status": "SUCCESSFUL",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payment = Payment.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            payment.status,
            Payment.Status.PENDING,
        )

    def test_customer_cannot_set_transaction_id(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.issue.id,
                "amount": Decimal("1000.00"),
                "method": "CARD",
                "transaction_id": "TXN-12345",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payment = Payment.objects.get(
            id=response.data["id"]
        )

        self.assertIsNone(
            payment.transaction_id,
        )

    def test_payment_amount_must_be_positive(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.issue.id,
                "amount": "0.00",
                "method": "MPESA",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.issue.id,
                "amount": "-100.00",
                "method": "MPESA",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_staff_can_view_all_payments(self):
        self.authenticate(self.staff)

        response = self.client.get("/api/payments/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            2,
        )

    def test_admin_can_view_all_payments(self):
        self.authenticate(self.admin)

        response = self.client.get("/api/payments/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            2,
        )

    def test_staff_can_view_payment(self):
        self.authenticate(self.staff)

        response = self.client.get(
            f"/api/payments/{self.payment.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.payment.id,
        )

    def test_admin_can_view_payment(self):
        self.authenticate(self.admin)

        response = self.client.get(
            f"/api/payments/{self.payment.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_staff_can_update_payment_status(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "SUCCESSFUL",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCESSFUL,
        )

    def test_staff_can_add_transaction_id(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "transaction_id": "TXN-12345",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.transaction_id,
            "TXN-12345",
        )

    def test_admin_can_update_payment_status(self):
        self.authenticate(self.admin)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "SUCCESSFUL",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCESSFUL,
        )

    def test_pending_payment_can_become_successful(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "SUCCESSFUL",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCESSFUL,
        )

    def test_pending_payment_can_become_failed(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "FAILED",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.FAILED,
        )

    def test_successful_payment_can_be_refunded(self):
        self.payment.status = Payment.Status.SUCCESSFUL
        self.payment.save()

        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "REFUNDED",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.REFUNDED,
        )

    def test_successful_payment_cannot_become_pending(self):
        self.payment.status = Payment.Status.SUCCESSFUL
        self.payment.save()

        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "PENDING",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_failed_payment_cannot_become_successful(self):
        self.payment.status = Payment.Status.FAILED
        self.payment.save()

        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "SUCCESSFUL",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_refunded_payment_cannot_change_status(self):
        self.payment.status = Payment.Status.REFUNDED
        self.payment.save()

        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "SUCCESSFUL",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_transaction_id_can_be_added_once(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "transaction_id": "TXN-10001",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.transaction_id,
            "TXN-10001",
        )

    def test_duplicate_transaction_id_is_rejected(self):
        self.payment.transaction_id = "TXN-10001"
        self.payment.save()

        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.other_payment.id}/",
            {
                "transaction_id": "TXN-10001",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_customer_cannot_add_transaction_id(self):
        self.authenticate(self.customer)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "transaction_id": "TXN-CUSTOMER",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_cannot_create_payment(self):
        self.authenticate(self.staff)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.other_issue.id,
                "amount": "750.00",
                "method": "MPESA",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_cannot_create_payment(self):
        self.authenticate(self.admin)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.issue.id,
                "amount": "750.00",
                "method": "MPESA",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_payment_amount_must_match_issue_amount(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.issue.id,
                "amount": "500.00",
                "method": "MPESA",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_payment_amount_matching_issue_amount_is_accepted(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/payments/",
            {
                "issue": self.issue.id,
                "amount": "1000.00",
                "method": "MPESA",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        payment = Payment.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            payment.amount,
            Decimal("1000.00"),
        )

    def test_successful_payment_notifies_customer(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "SUCCESSFUL",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        notification = Notification.objects.filter(
            user=self.customer,
            notification_type=Notification.Type.PAYMENT_SUCCESSFUL,
        ).latest("created_at")

        self.assertIn(
            "successful",
            notification.message,
        )

        self.assertFalse(
            notification.is_read,
        )

    def test_failed_payment_notifies_customer(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/payments/{self.payment.id}/",
            {
                "status": "FAILED",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        notification = Notification.objects.filter(
            user=self.customer,
            notification_type=Notification.Type.PAYMENT_FAILED,
        ).latest("created_at")

        self.assertIn(
            "failed",
            notification.message,
        )

        self.assertFalse(
            notification.is_read,
        )
   
    def test_mpesa_successful_callback_marks_payment_successful(self):
        self.payment.mpesa_checkout_request_id = "ws_CO_123456789"
        self.payment.save()

        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-1",
                    "CheckoutRequestID": "ws_CO_123456789",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {
                                "Name": "Amount",
                                "Value": 1000,
                            },
                            {
                                "Name": "MpesaReceiptNumber",
                                "Value": "NLJ7RT61SV",
                            },
                            {
                                "Name": "TransactionDate",
                                "Value": 20260917083000,
                            },
                            {
                                "Name": "PhoneNumber",
                                "Value": 254712345678,
                            },
                        ]
                    },
                }
            }
        }

        response = self.client.post(
            "/api/payments/mpesa/callback/",
            callback_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCESSFUL,
        )

    def test_mpesa_successful_callback_saves_receipt_number(self):
        self.payment.mpesa_checkout_request_id = "ws_CO_RECEIPT123"
        self.payment.save()

        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-2",
                    "CheckoutRequestID": "ws_CO_RECEIPT123",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {
                                "Name": "Amount",
                                "Value": 1000,
                            },
                            {
                                "Name": "MpesaReceiptNumber",
                                "Value": "ABC123XYZ",
                            },
                            {
                                "Name": "TransactionDate",
                                "Value": 20260917083000,
                            },
                            {
                                "Name": "PhoneNumber",
                                "Value": 254712345678,
                            },
                        ]
                    },
                }
            }
        }

        response = self.client.post(
            "/api/payments/mpesa/callback/",
            callback_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.transaction_id,
            "ABC123XYZ",
        )

    def test_mpesa_failed_callback_marks_payment_failed(self):
        self.payment.mpesa_checkout_request_id = "ws_CO_FAILED123"
        self.payment.save()

        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-3",
                    "CheckoutRequestID": "ws_CO_FAILED123",
                    "ResultCode": 1032,
                    "ResultDesc": "Request canceled by user.",
                }
            }
        }

        response = self.client.post(
            "/api/payments/mpesa/callback/",
            callback_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.FAILED,
        )

    def test_mpesa_callback_rejects_unknown_checkout_request_id(self):
        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-4",
                    "CheckoutRequestID": "ws_CO_UNKNOWN",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                }
            }
        }

        response = self.client.post(
            "/api/payments/mpesa/callback/",
            callback_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            response.data["ResultCode"],
            1,
        )

    def test_mpesa_callback_rejects_malformed_payload(self):
        callback_payload = {
            "invalid": "payload"
        }

        response = self.client.post(
            "/api/payments/mpesa/callback/",
            callback_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["ResultCode"],
            1,
        )

    def test_mpesa_callback_requires_checkout_request_id(self):
        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-5",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                }
            }
        }

        response = self.client.post(
            "/api/payments/mpesa/callback/",
            callback_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["ResultCode"],
            1,
        )

    @patch("payments.services.requests.post")
    @patch("payments.services.get_mpesa_access_token")
    def test_mpesa_stk_push_saves_checkout_request_id(
        self,
        mock_get_access_token,
        mock_post,
    ):
        from .services import initiate_mpesa_stk_push

        mock_get_access_token.return_value = "fake-access-token"

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": "ws_CO_123456789",
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing",
        }

        mock_post.return_value = mock_response

        with patch(
            "payments.services.settings.MPESA_SHORTCODE",
            "174379",
        ), patch(
            "payments.services.settings.MPESA_PASSKEY",
            "fake-passkey",
        ), patch(
            "payments.services.settings.MPESA_CALLBACK_URL",
            "https://example.com/api/payments/mpesa/callback/",
        ):
            result = initiate_mpesa_stk_push(
                self.payment,
                "254712345678",
            )

        self.payment.refresh_from_db()

        self.assertEqual(
            result["CheckoutRequestID"],
            "ws_CO_123456789",
        )

        self.assertEqual(
            self.payment.mpesa_checkout_request_id,
            "ws_CO_123456789",
        )

        mock_get_access_token.assert_called_once()
        mock_post.assert_called_once()


    @patch("payments.services.requests.post")
    @patch("payments.services.get_mpesa_access_token")
    def test_mpesa_stk_push_sends_correct_payload(
        self,
        mock_get_access_token,
        mock_post,
    ):
        from .services import initiate_mpesa_stk_push

        mock_get_access_token.return_value = "fake-access-token"

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "CheckoutRequestID": "ws_CO_PAYLOAD123",
            "ResponseCode": "0",
        }

        mock_post.return_value = mock_response

        with patch(
            "payments.services.settings.MPESA_SHORTCODE",
            "174379",
        ), patch(
            "payments.services.settings.MPESA_PASSKEY",
            "fake-passkey",
        ), patch(
            "payments.services.settings.MPESA_CALLBACK_URL",
            "https://example.com/api/payments/mpesa/callback/",
        ):
            initiate_mpesa_stk_push(
                self.payment,
                "254712345678",
            )

        mock_post.assert_called_once()

        payload = mock_post.call_args.kwargs["json"]

        self.assertEqual(
            payload["BusinessShortCode"],
            "174379",
        )

        self.assertEqual(
            payload["Amount"],
            1000,
        )

        self.assertEqual(
            payload["PartyA"],
            "254712345678",
        )

        self.assertEqual(
            payload["PartyB"],
            "174379",
        )

        self.assertEqual(
            payload["PhoneNumber"],
            "254712345678",
        )

        self.assertEqual(
            payload["AccountReference"],
            f"ISSUE-{self.payment.issue_id}",
        )

        self.assertEqual(
            payload["TransactionDesc"],
            f"Payment for Issue {self.payment.issue_id}",
        )

    @patch("payments.services.requests.get")
    def test_get_mpesa_access_token(self, mock_get):
        from .services import get_mpesa_access_token

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "access_token": "fake-access-token"
        }

        mock_get.return_value = mock_response

        with patch(
            "payments.services.settings.MPESA_CONSUMER_KEY",
            "fake-consumer-key",
        ), patch(
            "payments.services.settings.MPESA_CONSUMER_SECRET",
            "fake-consumer-secret",
        ), patch(
            "payments.services.settings.MPESA_ENVIRONMENT",
            "sandbox",
        ):
            token = get_mpesa_access_token()

        self.assertEqual(
            token,
            "fake-access-token",
        )

        mock_get.assert_called_once()

        url = mock_get.call_args.args[0]

        self.assertEqual(
            url,
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
        )

        kwargs = mock_get.call_args.kwargs

        self.assertEqual(
            kwargs["auth"],
            (
                "fake-consumer-key",
                "fake-consumer-secret",
            ),
        )

        self.assertEqual(
            kwargs["timeout"],
            30,
        )

    @patch("payments.services.requests.get")
    def test_get_mpesa_access_token_raises_http_error(
        self,
        mock_get,
    ):
        from .services import get_mpesa_access_token
        import requests

        mock_response = Mock()

        mock_response.raise_for_status.side_effect = (
            requests.HTTPError("401 Client Error")
        )

        mock_get.return_value = mock_response

        with patch(
            "payments.services.settings.MPESA_CONSUMER_KEY",
            "fake-consumer-key",
        ), patch(
            "payments.services.settings.MPESA_CONSUMER_SECRET",
            "fake-consumer-secret",
        ), patch(
            "payments.services.settings.MPESA_ENVIRONMENT",
            "sandbox",
        ):
            with self.assertRaises(requests.HTTPError):
                get_mpesa_access_token()

        mock_get.assert_called_once()   

    def test_normalize_mpesa_phone_number(self):
        from .services import normalize_mpesa_phone_number

        self.assertEqual(
            normalize_mpesa_phone_number("0712345678"),
            "254712345678",
        )

        self.assertEqual(
            normalize_mpesa_phone_number("+254712345678"),
            "254712345678",
        )

        self.assertEqual(
            normalize_mpesa_phone_number("254712345678"),
            "254712345678",
        )

        self.assertEqual(
            normalize_mpesa_phone_number("0712 345 678"),
            "254712345678",
        )

    def test_normalize_mpesa_phone_number_rejects_invalid_numbers(
        self,
    ):
        from .services import normalize_mpesa_phone_number

        invalid_numbers = [
            "123456789",
            "071234",
            "abcdefghij",
            "256712345678",
            "254812345678",
            "",
        ]

        for phone_number in invalid_numbers:
            with self.assertRaises(ValueError):
                normalize_mpesa_phone_number(phone_number)

    @patch("payments.services.requests.post")
    @patch("payments.services.get_mpesa_access_token")
    def test_mpesa_stk_push_normalizes_phone_number(
        self,
        mock_get_access_token,
        mock_post,
    ):
        from .services import initiate_mpesa_stk_push

        mock_get_access_token.return_value = "fake-access-token"

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "CheckoutRequestID": "ws_CO_PHONE123",
            "ResponseCode": "0",
        }

        mock_post.return_value = mock_response

        with patch(
            "payments.services.settings.MPESA_SHORTCODE",
            "174379",
        ), patch(
            "payments.services.settings.MPESA_PASSKEY",
            "fake-passkey",
        ), patch(
            "payments.services.settings.MPESA_CALLBACK_URL",
            "https://example.com/api/payments/mpesa/callback/",
        ):
            initiate_mpesa_stk_push(
                self.payment,
                "0712 345 678",
            )

        payload = mock_post.call_args.kwargs["json"]

        self.assertEqual(
            payload["PartyA"],
            "254712345678",
        )

        self.assertEqual(
            payload["PhoneNumber"],
            "254712345678",
        )

    def test_stk_push_rejects_zero_payment_amount(self):
        self.payment.amount = Decimal("0.00")
        self.payment.save()

        self.client.force_authenticate(
            user=self.customer
        )

        response = self.client.post(
            reverse("mpesa-stk-push"),
            {
                "payment_id": self.payment.id,
                "phone_number": "0712345678",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["detail"],
            "Payment amount must be greater than zero.",
        )

    def test_stk_push_rejects_negative_payment_amount(self):
        self.payment.amount = Decimal("-100.00")
        self.payment.save()

        self.client.force_authenticate(
            user=self.customer
        )

        response = self.client.post(
            reverse("mpesa-stk-push"),
            {
                "payment_id": self.payment.id,
                "phone_number": "0712345678",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["detail"],
            "Payment amount must be greater than zero.",
        )

    def test_stk_push_rejects_invalid_phone_number(self):
        self.client.force_authenticate(
            user=self.customer
        )

        response = self.client.post(
            reverse("mpesa-stk-push"),
            {
               "payment_id": self.payment.id,
                "phone_number": "071234",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["detail"],
            "Enter a valid Kenyan phone number.",
        )

    def test_customer_cannot_initiate_stk_push_for_another_customers_payment(self):
        self.client.force_authenticate(
            user=self.customer
        )

        response = self.client.post(
            reverse("mpesa-stk-push"),
            {
                "payment_id": self.other_payment.id,
                "phone_number": "0712345678",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            response.data["detail"],
            "You do not have permission to access this payment.",
        ) 
    
    def test_mpesa_success_callback_requires_receipt_number(self):
        self.payment.mpesa_checkout_request_id = "ws_CO_NO_RECEIPT123"
        self.payment.save()

        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-13",
                    "CheckoutRequestID": "ws_CO_NO_RECEIPT123",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {
                                "Name": "Amount",
                                "Value": 1000,
                            },
                            {
                                "Name": "PhoneNumber",
                                "Value": 254712345678,
                            },
                        ]
                    },
                }
            }
        }

        response = self.client.post(
            "/api/payments/mpesa/callback/",
            callback_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.PENDING,
        )

        self.assertIsNone(
            self.payment.transaction_id,
        )

    def test_mpesa_duplicate_successful_callback_does_not_overwrite_receipt(
        self,
    ):
        self.payment.mpesa_checkout_request_id = "ws_CO_DUPLICATE123"
        self.payment.save()

        first_callback = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-10",
                    "CheckoutRequestID": "ws_CO_DUPLICATE123",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {
                                "Name": "MpesaReceiptNumber",
                                "Value": "FIRST123",
                            },
                        ]
                    },
                }
            }
        }

        first_response = self.client.post(
            "/api/payments/mpesa/callback/",
            first_callback,
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCESSFUL,
        )

        self.assertEqual(
            self.payment.transaction_id,
            "FIRST123",
        )

        duplicate_callback = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-11",
                    "CheckoutRequestID": "ws_CO_DUPLICATE123",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {
                                "Name": "MpesaReceiptNumber",
                                "Value": "SECOND456",
                            },
                        ]
                    },
                }
            }
        }

        duplicate_response = self.client.post(
            "/api/payments/mpesa/callback/",
            duplicate_callback,
            format="json",
        )

        self.assertEqual(
            duplicate_response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCESSFUL,
        )

        self.assertEqual(
            self.payment.transaction_id,
            "FIRST123",
        )

    def test_mpesa_failed_callback_does_not_change_successful_payment(
        self,
    ):
        self.payment.mpesa_checkout_request_id = "ws_CO_SUCCESS_FAILED123"
        self.payment.status = Payment.Status.SUCCESSFUL
        self.payment.transaction_id = "ORIGINAL123"
        self.payment.save()

        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-12",
                    "CheckoutRequestID": "ws_CO_SUCCESS_FAILED123",
                    "ResultCode": 1032,
                    "ResultDesc": "Request canceled by user.",
                }
            }
        }

        response = self.client.post(
            "/api/payments/mpesa/callback/",
            callback_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.payment.refresh_from_db()

        self.assertEqual(
            self.payment.status,
            Payment.Status.SUCCESSFUL,
        )

        self.assertEqual(
            self.payment.transaction_id,
            "ORIGINAL123",
        )
