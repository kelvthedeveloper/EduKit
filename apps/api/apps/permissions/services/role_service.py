from typing import Optional, List, Dict, Any
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from common.constants import AuditAction, SCOPE_RESTRICTIVENESS
from ..models import Role, Permission, RolePermission, RoleAssignment, PermissionScope


SUPER_ADMIN_ROLE_CODES = {'SUPER_ADMIN'}


class RoleService:
    @staticmethod
    def _role_grants_permissions(role: Role) -> List[Dict[str, Any]]:
        """
        Returns the effective permissions a role would grant (role-level scopes only).
        """
        result = []
        for rp in role.role_permissions.select_related('permission', 'scope').all():
            result.append({
                'permission_code': rp.permission.codename,
                'scope_code': rp.scope.code if rp.scope else 'GLOBAL',
            })
        return result

    @staticmethod
    def _actor_can_assign_role(actor, role):
        from .authorization import AuthorizationService
        if getattr(actor, 'is_system_superuser', False):
            return True
        target_perms = RoleService._role_grants_permissions(role)
        for p in target_perms:
            codename = p['permission_code']
            if not AuthorizationService.can(actor, codename, resource=None):
                return False
        return True

    @staticmethod
    def _actor_can_grant_scope_override(role_scope_code, override_scope_code):
        if override_scope_code is None:
            return True
        base_rank = SCOPE_RESTRICTIVENESS.get(role_scope_code or 'GLOBAL', 1)
        override_rank = SCOPE_RESTRICTIVENESS.get(override_scope_code, None)
        if override_rank is None:
            return False
        return override_rank >= base_rank

    @staticmethod
    def _enforce_scope_narrowing(role, scope_override):
        """Raises PermissionDenied if the scope_override would widen any role permission."""
        if scope_override is None:
            return
        override_code = scope_override.code
        for rp in role.role_permissions.select_related('scope').all():
            role_scope_code = rp.scope.code if rp.scope else 'GLOBAL'
            if not RoleService._actor_can_grant_scope_override(role_scope_code, override_code):
                raise PermissionDenied(
                    f'scope_override={override_code} would WIDEN permission '
                    f'{rp.permission.codename} (role scope={role_scope_code}). '
                    'Scope overrides may only narrow access.'
                )

    @staticmethod
    def create_role(
        code: str,
        name: str,
        description: str = '',
        permissions: Optional[List[Dict[str, Any]]] = None,
        is_system: bool = False,
        actor: Optional[Any] = None,
    ) -> Role:
        clean_code = code.strip().upper().replace(' ', '_')
        if Role.objects.filter(code=clean_code).exists():
            raise ValidationError(f'Role with code {clean_code} already exists.')
        if actor is not None and not getattr(actor, 'is_system_superuser', False):
            raise PermissionDenied('Only system superusers may create roles.')

        with transaction.atomic():
            role = Role.objects.create(
                code=clean_code,
                name=name,
                description=description,
                is_system=is_system,
            )
            if permissions:
                RoleService.set_role_permissions(role, permissions, actor=actor)

            try:
                from apps.audit.services import AuditService
                AuditService.log(
                    action=AuditAction.ROLE_CREATED,
                    actor=actor,
                    resource_type='Role',
                    resource_id=str(role.uuid),
                    details={'code': role.code, 'name': role.name, 'is_system': is_system},
                )
            except Exception:
                pass

        return role

    @staticmethod
    def update_role(
        role: Role,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        permissions: Optional[List[Dict[str, Any]]] = None,
        actor: Optional[Any] = None,
    ) -> Role:
        if actor is not None and not getattr(actor, 'is_system_superuser', False):
            if permissions is not None:
                raise PermissionDenied('Only system superusers may alter role permissions.')

        updates = []
        if name is not None:
            role.name = name
            updates.append('name')
        if description is not None:
            role.description = description
            updates.append('description')
        if is_active is not None:
            role.is_active = is_active
            updates.append('is_active')

        with transaction.atomic():
            if updates:
                role.save(update_fields=updates + ['updated_at'])

            if permissions is not None:
                RoleService.set_role_permissions(role, permissions, actor=actor)

            try:
                from apps.audit.services import AuditService
                AuditService.log(
                    action=AuditAction.ROLE_UPDATED,
                    actor=actor,
                    resource_type='Role',
                    resource_id=str(role.uuid),
                    details={'code': role.code, 'updated_fields': updates},
                )
            except Exception:
                pass

        return role

    @staticmethod
    def delete_role(role: Role, actor: Optional[Any] = None) -> bool:
        if role.is_system:
            raise PermissionDenied('System roles are protected and cannot be deleted.')
        if actor is not None and not getattr(actor, 'is_system_superuser', False):
            raise PermissionDenied('Only system superusers may delete roles.')

        role_code = role.code
        role_uuid = str(role.uuid)

        with transaction.atomic():
            role.delete()
            try:
                from apps.audit.services import AuditService
                AuditService.log(
                    action=AuditAction.ROLE_DELETED,
                    actor=actor,
                    resource_type='Role',
                    resource_id=role_uuid,
                    details={'code': role_code},
                )
            except Exception:
                pass

        return True

    @staticmethod
    def set_role_permissions(
        role: Role,
        permissions_data: List[Dict[str, Any]],
        actor: Optional[Any] = None,
    ):
        if actor is not None and not getattr(actor, 'is_system_superuser', False):
            raise PermissionDenied('Only system superusers may configure role permissions.')
        with transaction.atomic():
            # Clear existing permissions
            RolePermission.objects.filter(role=role).delete()

            created_perms = []
            for item in permissions_data:
                perm_code = item.get('permission_code') or item.get('codename')
                scope_code = item.get('scope_code')
                params = item.get('scope_parameters', {})

                try:
                    permission = Permission.objects.get(codename=perm_code)
                except Permission.DoesNotExist:
                    continue

                scope = None
                if scope_code:
                    scope = PermissionScope.objects.filter(code=scope_code).first()

                rp = RolePermission.objects.create(
                    role=role,
                    permission=permission,
                    scope=scope,
                    scope_parameters=params,
                )
                created_perms.append(perm_code)

            try:
                from apps.audit.services import AuditService
                AuditService.log(
                    action=AuditAction.PERMISSION_CHANGED,
                    actor=actor,
                    resource_type='Role',
                    resource_id=str(role.uuid),
                    details={'role_code': role.code, 'permissions': created_perms},
                )
            except Exception:
                pass

    @staticmethod
    def assign_role(
        user: Any,
        role: Role,
        assigned_by: Optional[Any] = None,
        expires_at: Optional[Any] = None,
        scope_override: Optional[PermissionScope] = None,
        scope_context: Optional[Dict[str, Any]] = None,
    ) -> RoleAssignment:
        if assigned_by is not None and assigned_by.pk == user.pk:
            raise PermissionDenied('Self-service role assignment is not permitted.')

        if role.code in SUPER_ADMIN_ROLE_CODES and not getattr(assigned_by, 'is_system_superuser', False):
            raise PermissionDenied('Only system superusers may assign SUPER_ADMIN.')

        if not getattr(assigned_by, 'is_system_superuser', False):
            if not RoleService._actor_can_assign_role(assigned_by, role):
                raise PermissionDenied(
                    'Cannot assign role containing permissions you do not hold at GLOBAL scope.'
                )

        RoleService._enforce_scope_narrowing(role, scope_override)

        if not getattr(assigned_by, 'is_system_superuser', False) and getattr(user, 'is_system_superuser', False):
            raise PermissionDenied('Only system superusers may modify system superuser roles.')

        assignment, created = RoleAssignment.objects.update_or_create(
            user=user,
            role=role,
            defaults={
                'assigned_by': assigned_by,
                'expires_at': expires_at,
                'scope_override': scope_override,
                'scope_context': scope_context or {},
            },
        )

        try:
            from apps.audit.services import AuditService
            AuditService.log(
                action=AuditAction.ROLE_ASSIGNED,
                actor=assigned_by or user,
                resource_type='User',
                resource_id=str(user.uuid),
                details={
                    'role_code': role.code,
                    'role_name': role.name,
                    'expires_at': expires_at.isoformat() if expires_at else None,
                },
            )
        except Exception:
            pass

        return assignment

    @staticmethod
    def remove_role(user: Any, role: Role, actor: Optional[Any] = None) -> bool:
        if actor is not None and actor.pk == user.pk and role.code in SUPER_ADMIN_ROLE_CODES:
            other_supers = type(user)._default_manager.filter(
                is_system_superuser=True,
            ).exclude(pk=user.pk).exists()
            if not other_supers and RoleAssignment.objects.filter(
                role__code__in=SUPER_ADMIN_ROLE_CODES,
            ).exclude(user=user).count() == 0:
                raise PermissionDenied(
                    'Cannot remove the last superuser-equivalent role; '
                    'have another superuser do this to avoid lockout.'
                )

        count, _ = RoleAssignment.objects.filter(user=user, role=role).delete()
        if count > 0:
            try:
                from apps.audit.services import AuditService
                AuditService.log(
                    action=AuditAction.ROLE_REMOVED,
                    actor=actor or user,
                    resource_type='User',
                    resource_id=str(user.uuid),
                    details={'role_code': role.code, 'role_name': role.name},
                )
            except Exception:
                pass
            return True
        return False

