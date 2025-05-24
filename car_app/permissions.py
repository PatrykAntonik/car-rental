from rest_framework import exceptions
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Allows access only to users that are marked as admin.
    """
    message = "Access restricted to owners only."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_owner", False)
        )
