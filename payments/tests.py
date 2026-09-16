
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from issues.models import Issue

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
            customer=self.customer,
        )

        self.other_issue = Issue.objects.create(
            title="Other payment issue",
            description="Another customer's issue.",
            customer=self.other_customer,
        )

        self.payment = Payment.objects.create(
            issue=self.issue,
            customer=self.customer,
            amount="1000.00",
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
                "amount": "1500.00",
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
                "amount": "1500.00",
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
                "amount": "2000.00",
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
                "amount": "2000.00",
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
                "amount": "2000.00",
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

