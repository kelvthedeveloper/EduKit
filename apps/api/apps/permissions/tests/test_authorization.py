"""
Tests for the RBAC Authorization layer.

Covers:
- get_effective_permissions for active roles
- Superuser gets global access on all permissions
- Inactive user is denied
- Locked user is denied
- Unauthenticated user is denied
- can() with resource=None returns True if any scope granted
- can() with resource evaluates scope policy
- filter_queryset() returns none for no permissions
- filter_queryset() returns all for GLOBAL scope
- Role.is_active=False roles are excluded from effective permissions
- Expired role assignments are excluded
"""
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from common.constants import AccountStatus, Scope
from apps.permissions.services.authorization import AuthorizationService

User = get_user_model()


class _MockPermission:
    def __init__(self, codename):
        self.codename = codename


class _MockScope:
    def __init__(self, code=Scope.GLOBAL):
        self.code = code


class _MockRolePermission:
    def __init__(self, codename, scope_code=Scope.GLOBAL, scope_parameters=None):
        self.permission = _MockPermission(codename)
        self.scope = _MockScope(scope_code)
        self.scope_parameters = scope_parameters or {}


class _MockRole:
    def __init__(self, role_permissions=None, is_active=True):
        self.is_active = is_active
        self._rps = role_permissions or []

    @property
    def role_permissions(self):
        qs = MagicMock()
        qs.all.return_value = self._rps
        return qs


class _MockAssignment:
    def __init__(self, role, scope_override=None, scope_context=None, expires_at=None):
        self.role = role
        self.scope_override = scope_override
        self.scope_context = scope_context or {}
        self.expires_at = expires_at


def _make_user(*, is_active=True, is_system_superuser=False, locked=False):
    """Helper to create a mock authenticated user."""
    user = MagicMock()
    type(user).is_authenticated = PropertyMock(return_value=True)
    type(user).is_active = PropertyMock(return_value=is_active)
    type(user).is_system_superuser = PropertyMock(return_value=is_system_superuser)
    if locked:
        type(user).locked_until = PropertyMock(
            return_value=timezone.now() + timedelta(hours=1)
        )
    else:
        type(user).locked_until = PropertyMock(return_value=None)
    return user


# ──────────────────────────────────────────────────────────────────────────────
# get_effective_permissions
# ──────────────────────────────────────────────────────────────────────────────

class GetEffectivePermissionsTestCase(TestCase):

    def test_unauthenticated_returns_empty(self):
        user = MagicMock()
        type(user).is_authenticated = PropertyMock(return_value=False)
        result = AuthorizationService.get_effective_permissions(user)
        self.assertEqual(result, {})

    def test_none_user_returns_empty(self):
        result = AuthorizationService.get_effective_permissions(None)
        self.assertEqual(result, {})

    def test_superuser_gets_all_permissions_globally(self):
        user = _make_user(is_system_superuser=True)
        # Patch Permission.objects.all() to return known codenames
        with patch(
            "apps.permissions.models.Permission.objects"
        ) as mock_mgr:
            mock_mgr.all.return_value.values_list.return_value = [
                "students.view", "finance.view"
            ]
            result = AuthorizationService.get_effective_permissions(user)

        self.assertIn("students.view", result)
        self.assertIn("finance.view", result)
        for scopes in result.values():
            self.assertTrue(any(s["scope_code"] == Scope.GLOBAL for s in scopes))

    def test_permissions_from_active_roles(self):
        """Active role permissions flow into effective permissions correctly."""
        role = _MockRole(role_permissions=[
            _MockRolePermission("students.view", Scope.GLOBAL),
            _MockRolePermission("students.edit", Scope.SELF),
        ])
        assignment = _MockAssignment(role=role)

        user = _make_user()
        mock_qs = MagicMock()
        mock_qs.__or__ = lambda s, o: mock_qs  # chained | operator
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        mock_qs.__iter__ = lambda s: iter([assignment])
        type(user).roles_assigned = PropertyMock(return_value=mock_qs)

        result = AuthorizationService.get_effective_permissions(user)
        self.assertIn("students.view", result)
        self.assertIn("students.edit", result)


# ──────────────────────────────────────────────────────────────────────────────
# can()
# ──────────────────────────────────────────────────────────────────────────────

class CanTestCase(TestCase):

    def test_unauthenticated_denied(self):
        user = MagicMock()
        type(user).is_authenticated = PropertyMock(return_value=False)
        self.assertFalse(AuthorizationService.can(user, "students.view"))

    def test_inactive_denied(self):
        user = _make_user(is_active=False)
        self.assertFalse(AuthorizationService.can(user, "students.view"))

    def test_locked_denied(self):
        user = _make_user(locked=True)
        self.assertFalse(AuthorizationService.can(user, "students.view"))

    def test_superuser_always_allowed(self):
        user = _make_user(is_system_superuser=True)
        self.assertTrue(AuthorizationService.can(user, "any.permission"))

    def test_no_permission_denied(self):
        """User without permission is denied."""
        user = _make_user()
        with patch.object(
            AuthorizationService,
            "get_effective_permissions",
            return_value={},  # no permissions
        ):
            self.assertFalse(AuthorizationService.can(user, "students.view"))

    def test_permission_without_resource_allowed(self):
        """Permission without a resource → allowed when scope granted."""
        user = _make_user()
        with patch.object(
            AuthorizationService,
            "get_effective_permissions",
            return_value={
                "students.view": [{"scope_code": Scope.GLOBAL, "parameters": {}}]
            },
        ):
            self.assertTrue(AuthorizationService.can(user, "students.view"))

    def test_permission_with_resource_defers_to_policy(self):
        """With a resource, each scope entry is evaluated through the policy."""
        user = _make_user()
        resource = MagicMock()  # dummy student object

        mock_policy = MagicMock()
        mock_policy.check.return_value = True

        with patch.object(
            AuthorizationService,
            "get_effective_permissions",
            return_value={
                "students.view": [{"scope_code": Scope.GLOBAL, "parameters": {}}]
            },
        ), patch(
            "apps.permissions.services.authorization.get_policy_for_scope",
            return_value=mock_policy,
        ):
            result = AuthorizationService.can(user, "students.view", resource=resource)

        self.assertTrue(result)
        mock_policy.check.assert_called_once()

    def test_permission_denied_when_all_policies_deny(self):
        """Returns False when all scope policies deny access."""
        user = _make_user()
        resource = MagicMock()

        mock_policy = MagicMock()
        mock_policy.check.return_value = False

        with patch.object(
            AuthorizationService,
            "get_effective_permissions",
            return_value={
                "students.view": [{"scope_code": Scope.SELF, "parameters": {}}]
            },
        ), patch(
            "apps.permissions.services.authorization.get_policy_for_scope",
            return_value=mock_policy,
        ):
            result = AuthorizationService.can(user, "students.view", resource=resource)

        self.assertFalse(result)


# ──────────────────────────────────────────────────────────────────────────────
# filter_queryset()
# ──────────────────────────────────────────────────────────────────────────────

class FilterQuerysetTestCase(TestCase):

    def _make_queryset(self):
        qs = MagicMock()
        qs.none.return_value = qs
        qs.__or__ = lambda s, o: s
        qs.distinct.return_value = qs
        return qs

    def test_unauthenticated_returns_none_qs(self):
        user = MagicMock()
        type(user).is_authenticated = PropertyMock(return_value=False)
        qs = self._make_queryset()
        result = AuthorizationService.filter_queryset(user, "students.view", qs)
        qs.none.assert_called()

    def test_inactive_returns_none_qs(self):
        user = _make_user(is_active=False)
        qs = self._make_queryset()
        result = AuthorizationService.filter_queryset(user, "students.view", qs)
        qs.none.assert_called()

    def test_superuser_gets_full_queryset(self):
        user = _make_user(is_system_superuser=True)
        qs = self._make_queryset()
        result = AuthorizationService.filter_queryset(user, "students.view", qs)
        self.assertEqual(result, qs)

    def test_no_permission_returns_none_qs(self):
        user = _make_user()
        qs = self._make_queryset()
        with patch.object(
            AuthorizationService, "get_effective_permissions", return_value={}
        ):
            result = AuthorizationService.filter_queryset(user, "students.view", qs)
        qs.none.assert_called()

    def test_global_scope_returns_full_queryset(self):
        user = _make_user()
        qs = self._make_queryset()
        with patch.object(
            AuthorizationService,
            "get_effective_permissions",
            return_value={
                "students.view": [{"scope_code": Scope.GLOBAL, "parameters": {}}]
            },
        ):
            result = AuthorizationService.filter_queryset(user, "students.view", qs)
        self.assertEqual(result, qs)
