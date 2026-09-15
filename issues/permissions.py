from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsIssueParticipant(BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        
        if user.role == "ADMIN":
            return True

        
        if user.role == "STAFF":
            return True

        
        if user.role == "CUSTOMER":
            if obj.customer != user:
                return False

            
            if request.method in SAFE_METHODS:
                return True

            
            return False

        return False
