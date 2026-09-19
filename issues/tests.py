from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from notifications.models import Notification


from .models import Issue


User = get_user_model()


class IssueAPITests(APITestCase):

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
            title="Payment failed",
            description="My payment failed.",
            customer=self.customer,
            priority=Issue.Priority.HIGH,
        )

        self.other_issue = Issue.objects.create(
            title="Account problem",
            description="I cannot access my account.",
            customer=self.other_customer,
            priority=Issue.Priority.MEDIUM,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_unauthenticated_user_cannot_list_issues(self):
        response = self.client.get("/api/issues/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_can_create_issue(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/issues/",
            {
                "title": "New payment issue",
                "description": "Payment was not completed.",
                "priority": "HIGH",
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

        self.assertEqual(
            Issue.objects.count(),
            3,
        )

        notification = Notification.objects.get(
            user=self.customer,
            notification_type=Notification.Type.ISSUE_CREATED,
        )

        self.assertIn(
            "New payment issue",
            notification.message,
        )

        self.assertFalse(
            notification.is_read,
        )


    def test_customer_can_only_see_own_issues(self):
        self.authenticate(self.customer)

        response = self.client.get("/api/issues/")

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
            self.issue.id,
        )

    def test_customer_cannot_view_another_customers_issue(self):
        self.authenticate(self.customer)

        response = self.client.get(
            f"/api/issues/{self.other_issue.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_customer_can_update_own_issue(self):
        self.authenticate(self.customer)

        response = self.client.patch(
            f"/api/issues/{self.issue.id}/",
            {
                "status": "RESOLVED",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_customer_cannot_delete_issue(self):
        self.authenticate(self.customer)

        response = self.client.delete(
            f"/api/issues/{self.issue.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_can_view_all_issues(self):
        self.authenticate(self.staff)

        response = self.client.get("/api/issues/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data["results"]),
            2,
        )

    def test_staff_can_update_issue_status(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/issues/{self.issue.id}/",
            {
                "status": "IN_PROGRESS",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.issue.refresh_from_db()

        self.assertEqual(
            self.issue.status,
            Issue.Status.IN_PROGRESS,
        )

    def test_staff_can_assign_issue(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/issues/{self.issue.id}/",
            {
                "assigned_to": self.staff.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.issue.refresh_from_db()

        self.assertEqual(
            self.issue.assigned_to,
            self.staff,
        )

    def test_filter_by_status(self):
        self.authenticate(self.staff)

        self.issue.status = Issue.Status.IN_PROGRESS
        self.issue.save()

        response = self.client.get(
            "/api/issues/?status=IN_PROGRESS"
        )

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
            self.issue.id,
        )

    def test_filter_by_priority(self):
        self.authenticate(self.staff)

        response = self.client.get(
            "/api/issues/?priority=HIGH"
        )

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
            self.issue.id,
        )

    def test_staff_assignment_creates_notification(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/issues/{self.issue.id}/",
            {
                "assigned_to": self.staff.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        notification = Notification.objects.get(
            user=self.staff,
            notification_type=Notification.Type.ISSUE_ASSIGNED,
        )

        self.assertIn(
            self.issue.title,
            notification.message,
        )

        self.assertFalse(
            notification.is_read,
        )


    def test_status_change_creates_notification_for_customer(self):
        self.authenticate(self.staff)

        response = self.client.patch(
            f"/api/issues/{self.issue.id}/",
            {
                "status": "IN_PROGRESS",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        notification = Notification.objects.get(
            user=self.customer,
            notification_type=Notification.Type.ISSUE_STATUS_CHANGED,
        )

        self.assertIn(
            self.issue.title,
            notification.message,
        )

        self.assertIn(
            "IN_PROGRESS",
            notification.message,
        )

        self.assertFalse(
            notification.is_read,
        )

    def test_customer_creating_issue_notifies_staff(self):
        self.authenticate(self.customer)

        response = self.client.post(
            "/api/issues/",
            {
                "title": "Staff notification test",
                "description": "Staff should be notified.",
                "priority": "HIGH",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        notification = Notification.objects.get(
            user=self.staff,
            notification_type=Notification.Type.ISSUE_CREATED,
        )

        self.assertIn(
            "Staff notification test",
            notification.message,
        )

        self.assertIn(
            self.customer.username,
            notification.message,
        )

        self.assertFalse(
            notification.is_read,
        )

    def test_customer_creating_issue_notifies_all_staff(self):
        second_staff = User.objects.create_user(
            username="staff2",
            email="staff2@example.com",
            password="StrongPassword123",
            role=User.Role.STAFF,
        )

        self.authenticate(self.customer)

        response = self.client.post(
            "/api/issues/",
            {
                "title": "Multiple staff test",
                "description": "All staff should be notified.",
                "priority": "MEDIUM",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        notifications = Notification.objects.filter(
            notification_type=Notification.Type.ISSUE_CREATED,
            user__in=[self.staff, second_staff],
        )

        self.assertEqual(
            notifications.count(),
            2,
        )

        for notification in notifications:
            self.assertIn(
                "Multiple staff test",
                notification.message,
            )

            self.assertFalse(
                notification.is_read,
            )
   
   