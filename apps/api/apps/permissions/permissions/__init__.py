from typing import Type
from rest_framework.permissions import BasePermission
from ..services import AuthorizationService


class HasScopedPermission(BasePermission):
    """
    DRF permission class that evaluates scoped permissions.
    Subclasses should define `permission_codename` or views can define `required_permission`.
    """
    permission_codename: str = ''

    def get_permission_codename(self, view) -> str:
        return getattr(view, 'required_permission', self.permission_codename)

    def has_permission(self, request, view):
        perm = self.get_permission_codename(view)
        if not perm:
            return True
        return AuthorizationService.can(request.user, perm)

    def has_object_permission(self, request, view, obj):
        perm = self.get_permission_codename(view)
        if not perm:
            return True
        return AuthorizationService.can(request.user, perm, resource=obj)


def scoped_permission(codename: str) -> Type[BasePermission]:
    """
    Factory creating a DRF Permission class for a specific codename.
    Example:
        permission_classes = [IsAuthenticated, scoped_permission('students.view')]
    """
    name = f'Has_{codename.replace(".", "_")}_Permission'
    return type(name, (HasScopedPermission,), {'permission_codename': codename})


__all__ = ['HasScopedPermission', 'scoped_permission']
