from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from ..models import Role, Permission, PermissionScope, RoleAssignment
from ..serializers import (
    RoleSerializer,
    RoleCreateUpdateSerializer,
    PermissionSerializer,
    PermissionScopeSerializer,
    RoleAssignmentSerializer,
    AssignRoleRequestSerializer,
)
from ..services import RoleService, AuthorizationService
from apps.identity.permissions import IsAccountActive

User = get_user_model()


class HasRolePermission(permissions.BasePermission):
    """
    Enforces that the user has 'roles.view' for read operations
    and 'roles.manage' for mutation operations.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_system_superuser', False) or getattr(user, 'is_staff', False):
            return True
        if request.method in permissions.SAFE_METHODS:
            return AuthorizationService.can(user, 'roles.view')
        return AuthorizationService.can(user, 'roles.manage')


class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoints for inspecting and configuring school roles.
    """
    queryset = Role.objects.all().prefetch_related(
        'role_permissions__permission',
        'role_permissions__scope',
    )
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated & IsAccountActive & HasRolePermission]
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_system', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def create(self, request, *args, **kwargs):
        ser = RoleCreateUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        code = data.get('code') or data['name'].strip().upper().replace(' ', '_')
        role = RoleService.create_role(
            code=code,
            name=data['name'],
            description=data.get('description', ''),
            permissions=data.get('permissions', []),
            is_system=False,
            actor=request.user,
        )
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        role = self.get_object()
        ser = RoleCreateUpdateSerializer(instance=role, data=request.data, partial=kwargs.get('partial', False))
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        role = RoleService.update_role(
            role=role,
            name=data.get('name'),
            description=data.get('description'),
            is_active=data.get('is_active'),
            permissions=data.get('permissions') if 'permissions' in request.data else None,
            actor=request.user,
        )
        return Response(RoleSerializer(role).data)

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        if role.is_system:
            raise PermissionDenied('System roles are protected and cannot be deleted.')
        RoleService.delete_role(role, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only registry of granular permissions.
    """
    queryset = Permission.objects.all().order_by('resource', 'action')
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated & IsAccountActive & HasRolePermission]
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['resource', 'action', 'is_system']
    search_fields = ['codename', 'name', 'resource']
    ordering = ['resource', 'action']


class ScopeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only listing of available authorization boundary scopes.
    """
    queryset = PermissionScope.objects.all().order_by('code')
    serializer_class = PermissionScopeSerializer
    permission_classes = [permissions.IsAuthenticated & IsAccountActive & HasRolePermission]
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['code', 'name']
    ordering = ['code']


class UserRoleAssignmentView(APIView):
    """
    Inspects, assigns, and revokes roles for a specific user.
    """
    permission_classes = [permissions.IsAuthenticated & IsAccountActive & HasRolePermission]

    def _get_target_user(self, user_uuid):
        try:
            return User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            raise NotFound('Target user not found.')

    def get(self, request, user_uuid):
        target_user = self._get_target_user(user_uuid)
        assignments = target_user.roles_assigned.all().select_related('role', 'scope_override')
        return Response(RoleAssignmentSerializer(assignments, many=True).data)

    def post(self, request, user_uuid):
        target_user = self._get_target_user(user_uuid)
        ser = AssignRoleRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # Find role
        role = None
        if data.get('role_uuid'):
            role = Role.objects.filter(uuid=data['role_uuid']).first()
        elif data.get('role_code'):
            role = Role.objects.filter(code=data['role_code'].upper()).first()

        if not role:
            raise NotFound('Specified role does not exist.')

        # Protect against non-system-superusers trying to grant SUPER_ADMIN
        if role.code == 'SUPER_ADMIN' and not getattr(request.user, 'is_system_superuser', False):
            raise PermissionDenied('Only system superusers can assign the Super Admin role.')

        # Resolve scope override if provided
        scope_override = None
        if data.get('scope_override_code'):
            scope_override = PermissionScope.objects.filter(code=data['scope_override_code']).first()

        assignment = RoleService.assign_role(
            user=target_user,
            role=role,
            assigned_by=request.user,
            expires_at=data.get('expires_at'),
            scope_override=scope_override,
            scope_context=data.get('scope_context', {}),
        )
        return Response(RoleAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_uuid, role_code=None):
        target_user = self._get_target_user(user_uuid)
        role_lookup = role_code or request.data.get('role_code')
        if not role_lookup:
            raise ValidationError('role_code is required to revoke assignment.')

        role = Role.objects.filter(code=role_lookup.upper()).first()
        if not role:
            raise NotFound('Specified role does not exist.')

        if role.code == 'SUPER_ADMIN' and not getattr(request.user, 'is_system_superuser', False):
            raise PermissionDenied('Only system superusers can revoke the Super Admin role.')

        removed = RoleService.remove_role(user=target_user, role=role, actor=request.user)
        if not removed:
            raise NotFound('User does not currently hold this role assignment.')
        return Response(status=status.HTTP_204_NO_CONTENT)
