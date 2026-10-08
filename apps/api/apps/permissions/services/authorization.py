import logging
from typing import Any, Optional, Dict, List
from django.utils import timezone
from django.db.models import QuerySet

from common.constants import Scope, SCOPE_RESTRICTIVENESS
from ..policies import get_policy_for_scope

logger = logging.getLogger('apps.permissions')


def effective_scope_code(role_scope_code: str, override_scope_code: Optional[str]) -> str:
    """
    Enforces the narrowing-only rule for scope overrides.

    A UserRoleAssignment.scope_override can only NARROW (or keep equal) the
    effective scope vs. the underlying RolePermission.scope. It may never WIDEN
    (e.g. turning ASSIGNED_CLASSES into GLOBAL is forbidden).

    Returns the (possibly clamped) effective scope code.
    """
    base = role_scope_code or Scope.GLOBAL
    if not override_scope_code:
        return base
    base_rank = SCOPE_RESTRICTIVENESS.get(base, 1)
    override_rank = SCOPE_RESTRICTIVENESS.get(override_scope_code, None)
    if override_rank is None:
        logger.warning(
            'Ignoring unknown scope override %s; keeping role scope %s',
            override_scope_code, base,
        )
        return base
    if override_rank < base_rank:
        logger.warning(
            'Dropping scope override %s on role scope %s (override would WIDEN access; '
            'narrowing-only rule enforced).',
            override_scope_code, base,
        )
        return base
    return override_scope_code


class AuthorizationService:
    """
    Central production authorization service. Evaluates:
    Request -> User -> Roles -> Permissions -> Action -> Scope -> Policy -> ALLOW / DENY
    """

    @staticmethod
    def get_effective_permissions(user: Any) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculates user's effective permissions across all active assigned roles.
        Returns a dictionary mapping permission codenames to their granted scopes and parameters:
        {
            "students.view": [
                {"scope_code": "ASSIGNED_CLASSES", "parameters": {}},
                {"scope_code": "SELF", "parameters": {}},
            ],
            "finance.view": [{"scope_code": "GLOBAL", "parameters": {}}]
        }
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return {}

        # System superusers have universal GLOBAL capability
        if getattr(user, 'is_system_superuser', False):
            from ..models import Permission
            all_perms = Permission.objects.all().values_list('codename', flat=True)
            return {
                code: [{'scope_code': Scope.GLOBAL, 'parameters': {}}]
                for code in all_perms
            }

        now = timezone.now()
        # Find all active role assignments
        assignments = (
            user.roles_assigned
            .filter(role__is_active=True)
            .filter(expires_at__isnull=True) |
            user.roles_assigned
            .filter(role__is_active=True)
            .filter(expires_at__gt=now)
        ).select_related('role', 'scope_override').prefetch_related(
            'role__role_permissions__permission',
            'role__role_permissions__scope',
        )

        effective: Dict[str, List[Dict[str, Any]]] = {}

        for assignment in assignments:
            override_scope_code = assignment.scope_override.code if assignment.scope_override else None
            assignment_context = assignment.scope_context or {}

            for rp in assignment.role.role_permissions.all():
                perm_code = rp.permission.codename
                role_scope_code = rp.scope.code if rp.scope else Scope.GLOBAL
                scope_code = effective_scope_code(role_scope_code, override_scope_code)
                params = dict(rp.scope_parameters or {})
                if assignment_context and scope_code != role_scope_code:
                    merged = dict(params)
                    merged.update(assignment_context)
                    params = merged

                scope_entry = {'scope_code': scope_code, 'parameters': params}
                if perm_code not in effective:
                    effective[perm_code] = [scope_entry]
                else:
                    effective[perm_code].append(scope_entry)

        return effective

    @staticmethod
    def can(
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        **context: Any,
    ) -> bool:
        """
        Authoritative check: Can user perform the given action on the given resource?
        Usage:
            AuthorizationService.can(user, "students.view", student)
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return False

        if not getattr(user, 'is_active', False):
            return False

        if getattr(user, 'locked_until', None) and user.locked_until > timezone.now():
            return False

        if getattr(user, 'is_system_superuser', False):
            return True

        effective_perms = AuthorizationService.get_effective_permissions(user)
        granted_scopes = effective_perms.get(permission)

        if not granted_scopes:
            return False

        # If no specific resource was provided, permission is granted if granted under any scope
        if resource is None:
            return True

        # Check against each granted scope. If any scope grants access, ALLOW.
        for entry in granted_scopes:
            scope_code = entry.get('scope_code', Scope.GLOBAL)
            scope_params = entry.get('parameters', {})
            policy = get_policy_for_scope(scope_code)
            if policy.check(
                user=user,
                permission=permission,
                resource=resource,
                scope=scope_code,
                scope_params=scope_params,
                **context,
            ):
                return True

        return False

    @staticmethod
    def filter_queryset(
        user: Any,
        permission: str,
        queryset: QuerySet,
        **context: Any,
    ) -> QuerySet:
        """
        Filters a queryset according to the user's granted scopes for this permission.
        Usage:
            filtered_students = AuthorizationService.filter_queryset(request.user, "students.view", Student.objects.all())
        """
        if not user or not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_active', False):
            return queryset.none()

        if getattr(user, 'is_system_superuser', False):
            return queryset

        effective_perms = AuthorizationService.get_effective_permissions(user)
        granted_scopes = effective_perms.get(permission)

        if not granted_scopes:
            return queryset.none()

        # If any scope is GLOBAL, user sees all
        if any(e.get('scope_code') == Scope.GLOBAL for e in granted_scopes):
            return queryset

        # Combine queryset filters for each scope
        combined_qs = queryset.none()
        for entry in granted_scopes:
            scope_code = entry.get('scope_code')
            scope_params = entry.get('parameters', {})
            policy = get_policy_for_scope(scope_code)
            scoped_qs = policy.filter_queryset(
                user=user,
                permission=permission,
                queryset=queryset,
                scope=scope_code,
                scope_params=scope_params,
                **context,
            )
            combined_qs = combined_qs | scoped_qs

        return combined_qs.distinct()
