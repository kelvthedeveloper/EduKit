from rest_framework.permissions import BasePermission
from django.utils import timezone


class IsAccountActive(BasePermission):
    message = 'Account is not in an active state.'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        if getattr(user, 'locked_until', None) and user.locked_until > timezone.now():
            return False
        return bool(getattr(user, 'is_active', False))
