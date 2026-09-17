from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Notification


User = get_user_model()


class NotificationAPITests(APITestCase):

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

        self.notification = Notification.objects.create(
            user=self.customer,
            notification_type=(
                Notification.Type.PAYMENT_SUCCESSFUL
            ),
            message="Your payment was successful.",
        )

        self.other_notification = Notification.objects.create(
            user=self.other_customer,
            notification_type=(
                Notification.Type.PAYMENT_FAILED
            ),
            message="Your payment failed.",
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_unauthenticated_user_cannot_list_notifications(self):
        response = self.client.get("/api/notifications/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_can_list_own_notifications(self):
        self.authenticate(self.customer)

        response = self.client.get("/api/notifications/")

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
            self.notification.id,
        )

    def test_customer_cannot_see_other_users_notifications(self):
        self.authenticate(self.customer)

        response = self.client.get("/api/notifications/")

        ids = [
            notification["id"]
            for notification in response.data["results"]
        ]

        self.assertNotIn(
            self.other_notification.id,
            ids,
        )

    def test_customer_can_view_own_notification(self):
        self.authenticate(self.customer)

        response = self.client.get(
            f"/api/notifications/{self.notification.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["id"],
            self.notification.id,
        )

    def test_customer_cannot_view_other_users_notification(self):
        self.authenticate(self.customer)

        response = self.client.get(
            f"/api/notifications/{self.other_notification.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_customer_can_mark_notification_as_read(self):
        self.authenticate(self.customer)

        response = self.client.patch(
            f"/api/notifications/{self.notification.id}/",
            {
                "is_read": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.notification.refresh_from_db()

        self.assertTrue(
            self.notification.is_read
        )

    def test_customer_cannot_modify_notification_message(self):
        self.authenticate(self.customer)

        response = self.client.patch(
            f"/api/notifications/{self.notification.id}/",
            {
                "message": "Modified message",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.notification.refresh_from_db()

        self.assertEqual(
            self.notification.message,
            "Your payment was successful.",
        )

    def test_customer_cannot_create_notification(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/notifications/",
            {
                "notification_type": (
                    "PAYMENT_SUCCESSFUL"
                ),
                "message": "Fake notification",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_customer_can_filter_unread_notifications(self):
        self.authenticate(self.customer)

        response = self.client.get(
            "/api/notifications/?is_read=false"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

    def test_customer_can_filter_by_notification_type(self):
        self.authenticate(self.customer)

        response = self.client.get(
            "/api/notifications/"
            "?notification_type=PAYMENT_SUCCESSFUL"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )

    def test_customer_can_search_notification_message(self):
        self.authenticate(self.customer)

        response = self.client.get(
            "/api/notifications/"
            "?search=payment"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            1,
        )
