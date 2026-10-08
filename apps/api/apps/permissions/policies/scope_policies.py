from typing import Any, Optional, Dict
from django.db.models import QuerySet, Q
from common.constants import Scope
from .base import BaseScopePolicy


class GlobalScopePolicy(BaseScopePolicy):
    """
    GLOBAL scope: user has unrestricted access to all instances of the resource across the school.
    """
    scope_code = Scope.GLOBAL

    def check(
        self,
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> bool:
        return True

    def filter_queryset(
        self,
        user: Any,
        permission: str,
        queryset: QuerySet,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> QuerySet:
        return queryset


class SelfScopePolicy(BaseScopePolicy):
    """
    SELF scope: user can only access/modify their own personal records.
    Example: Student viewing their own grades, user updating their own profile.
    """
    scope_code = Scope.SELF

    def check(
        self,
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> bool:
        if resource is None:
            return True
        if resource == user or getattr(resource, 'pk', None) == getattr(user, 'pk', None):
            return True
        if getattr(resource, 'user_id', None) == getattr(user, 'pk', None):
            return True
        if getattr(resource, 'user', None) == user:
            return True
        if getattr(resource, 'uuid', None) == getattr(user, 'uuid', None):
            return True
        if getattr(resource, 'user_uuid', None) == getattr(user, 'uuid', None):
            return True
        if context.get('user_id') == getattr(user, 'pk', None):
            return True
        if context.get('user_uuid') == getattr(user, 'uuid', None):
            return True
        return False

    def filter_queryset(
        self,
        user: Any,
        permission: str,
        queryset: QuerySet,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> QuerySet:
        model = queryset.model
        field_names = {f.name for f in model._meta.get_fields()}
        if 'user' in field_names:
            return queryset.filter(user=user)
        if 'user_id' in field_names:
            return queryset.filter(user_id=user.pk)
        if 'pk' in field_names or 'id' in field_names:
            return queryset.filter(pk=user.pk)
        return queryset.none()


class OwnChildrenScopePolicy(BaseScopePolicy):
    """
    OWN_CHILDREN scope: parent / guardian can only view or act upon records for their own children.
    """
    scope_code = Scope.OWN_CHILDREN

    def check(
        self,
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> bool:
        if resource is None:
            return True
        # Check context injection (e.g. mock or domain context)
        child_ids = context.get('children_ids') or context.get('child_ids')
        if child_ids is not None:
            res_id = getattr(resource, 'id', getattr(resource, 'pk', resource))
            return res_id in child_ids
        # Direct relationship checks
        if hasattr(resource, 'guardian_user_id') and resource.guardian_user_id == user.pk:
            return True
        if hasattr(resource, 'guardian_user') and resource.guardian_user == user:
            return True
        if hasattr(resource, 'guardians') and hasattr(resource.guardians, 'filter'):
            return resource.guardians.filter(user=user).exists()
        if hasattr(user, 'children') and hasattr(user.children, 'filter'):
            return user.children.filter(pk=getattr(resource, 'pk', None)).exists()
        if context.get('guardian_id') == getattr(user, 'pk', None):
            return True
        return False

    def filter_queryset(
        self,
        user: Any,
        permission: str,
        queryset: QuerySet,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> QuerySet:
        child_ids = context.get('children_ids') or context.get('child_ids')
        if child_ids is not None:
            return queryset.filter(pk__in=child_ids)
        model = queryset.model
        field_names = {f.name for f in model._meta.get_fields()}
        if 'guardian_user' in field_names:
            return queryset.filter(guardian_user=user)
        if 'guardians' in field_names:
            return queryset.filter(guardians__user=user)
        return queryset.none()


class AssignedClassesScopePolicy(BaseScopePolicy):
    """
    ASSIGNED_CLASSES scope: teacher can only access records belonging to their assigned classes.
    """
    scope_code = Scope.ASSIGNED_CLASSES

    def check(
        self,
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> bool:
        if resource is None:
            return True
        assigned_class_ids = (
            context.get('assigned_class_ids')
            or (scope_params or {}).get('class_ids')
            or getattr(user, 'assigned_class_ids', None)
        )
        if assigned_class_ids is not None:
            res_class_id = getattr(resource, 'class_id', context.get('class_id'))
            return res_class_id in assigned_class_ids
        # Direct model relations
        if hasattr(resource, 'class_teacher_id') and resource.class_teacher_id == user.pk:
            return True
        if hasattr(resource, 'assigned_teachers') and hasattr(resource.assigned_teachers, 'filter'):
            return resource.assigned_teachers.filter(pk=user.pk).exists()
        return False

    def filter_queryset(
        self,
        user: Any,
        permission: str,
        queryset: QuerySet,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> QuerySet:
        assigned_class_ids = (
            context.get('assigned_class_ids')
            or (scope_params or {}).get('class_ids')
            or getattr(user, 'assigned_class_ids', None)
        )
        if assigned_class_ids is not None:
            return queryset.filter(class_id__in=assigned_class_ids)
        return queryset.none()


class AssignedSubjectsScopePolicy(BaseScopePolicy):
    """
    ASSIGNED_SUBJECTS scope: teacher can only access records for subjects they teach.
    """
    scope_code = Scope.ASSIGNED_SUBJECTS

    def check(
        self,
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> bool:
        if resource is None:
            return True
        assigned_subject_ids = (
            context.get('assigned_subject_ids')
            or (scope_params or {}).get('subject_ids')
            or getattr(user, 'assigned_subject_ids', None)
        )
        if assigned_subject_ids is not None:
            res_subject_id = getattr(resource, 'subject_id', context.get('subject_id'))
            return res_subject_id in assigned_subject_ids
        return False

    def filter_queryset(
        self,
        user: Any,
        permission: str,
        queryset: QuerySet,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> QuerySet:
        assigned_subject_ids = context.get('assigned_subject_ids') or (scope_params or {}).get('subject_ids')
        if assigned_subject_ids is not None:
            return queryset.filter(subject_id__in=assigned_subject_ids)
        return queryset.none()


class DepartmentScopePolicy(BaseScopePolicy):
    """
    DEPARTMENT scope: staff member can access resources within their specific department.
    """
    scope_code = Scope.DEPARTMENT

    def check(
        self,
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> bool:
        if resource is None:
            return True
        user_dept = context.get('department_id') or getattr(user, 'department_id', None)
        res_dept = getattr(resource, 'department_id', context.get('resource_department_id'))
        if user_dept is not None and res_dept is not None:
            return user_dept == res_dept
        return False

    def filter_queryset(
        self,
        user: Any,
        permission: str,
        queryset: QuerySet,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> QuerySet:
        user_dept = context.get('department_id') or getattr(user, 'department_id', None)
        if user_dept is not None:
            return queryset.filter(department_id=user_dept)
        return queryset.none()


class SelectedClassesScopePolicy(BaseScopePolicy):
    """
    SELECTED_CLASSES scope: explicit whitelist of class IDs defined in role_permission.scope_parameters.
    """
    scope_code = Scope.SELECTED_CLASSES

    def check(
        self,
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> bool:
        if resource is None:
            return True
        allowed_classes = (scope_params or {}).get('class_ids', [])
        res_class_id = getattr(resource, 'class_id', context.get('class_id'))
        return res_class_id in allowed_classes

    def filter_queryset(
        self,
        user: Any,
        permission: str,
        queryset: QuerySet,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> QuerySet:
        allowed_classes = (scope_params or {}).get('class_ids', [])
        if allowed_classes:
            return queryset.filter(class_id__in=allowed_classes)
        return queryset.none()


# Registry mapping Scope codes to Policy instances
SCOPE_POLICIES: Dict[str, BaseScopePolicy] = {
    Scope.GLOBAL: GlobalScopePolicy(),
    Scope.SELF: SelfScopePolicy(),
    Scope.OWN_CHILDREN: OwnChildrenScopePolicy(),
    Scope.ASSIGNED_CLASSES: AssignedClassesScopePolicy(),
    Scope.ASSIGNED_SUBJECTS: AssignedSubjectsScopePolicy(),
    Scope.DEPARTMENT: DepartmentScopePolicy(),
    Scope.SELECTED_CLASSES: SelectedClassesScopePolicy(),
}


class DenyAllScopePolicy(BaseScopePolicy):
    """
    Fallback policy used when a scope code is unknown / not registered.
    SAFE default: deny ALL access. This is critical — an unknown scope must
    never silently widen access (the previous default was GlobalScopePolicy,
    which was unsafe).
    """
    scope_code = 'DENY_ALL'

    def check(self, user, permission, resource=None, scope=None, scope_params=None, **context):
        return False

    def filter_queryset(self, user, permission, queryset, scope=None, scope_params=None, **context):
        return queryset.none()


_DENY_ALL = DenyAllScopePolicy()


def get_policy_for_scope(scope_code: str) -> BaseScopePolicy:
    policy = SCOPE_POLICIES.get(scope_code)
    if policy is not None:
        return policy
    import logging
    logger = logging.getLogger('apps.permissions')
    logger.warning(
        'Unknown scope_code=%s requested from get_policy_for_scope; '
        'falling back to DENY_ALL safe default (access denied for this scope).',
        scope_code,
    )
    return _DENY_ALL
