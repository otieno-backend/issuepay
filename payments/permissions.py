from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPaymentParticipant(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role in ["STAFF", "ADMIN"]:
            return True

        if user.role == "CUSTOMER":
            return (
                request.method in SAFE_METHODS
                and obj.customer == user
            )

        return False


class CanCreatePayment(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "CUSTOMER"
        )
