from .base import BaseScopePolicy
from .scope_policies import (
    GlobalScopePolicy,
    SelfScopePolicy,
    OwnChildrenScopePolicy,
    AssignedClassesScopePolicy,
    AssignedSubjectsScopePolicy,
    DepartmentScopePolicy,
    SelectedClassesScopePolicy,
    DenyAllScopePolicy,
    SCOPE_POLICIES,
    get_policy_for_scope,
)

__all__ = [
    'BaseScopePolicy',
    'GlobalScopePolicy',
    'SelfScopePolicy',
    'OwnChildrenScopePolicy',
    'AssignedClassesScopePolicy',
    'AssignedSubjectsScopePolicy',
    'DepartmentScopePolicy',
    'SelectedClassesScopePolicy',
    'DenyAllScopePolicy',
    'SCOPE_POLICIES',
    'get_policy_for_scope',
]
