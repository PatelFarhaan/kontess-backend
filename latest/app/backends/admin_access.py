from rest_framework import permissions,status
from rest_framework.response import Response

class AdminAuthenticationPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True
        return False