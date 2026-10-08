"""
Tests for AuditEvent model and AuditService.

Covers:
- AuditEvent.save() works for new records
- AuditEvent.save() raises PermissionDenied on update
- AuditEvent.delete() is blocked
- AuditService.log() creates AuditEvent with correct fields
- AuditService.sanitize() redacts sensitive keys (password, token, etc.)
- AuditService.sanitize() handles nested structures
- AuditService.sanitize() is safe with non-dict input
- AuditService.log() silently handles exceptions (never raises)
- actor_email is auto-snaphotted from actor
"""
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from common.constants import AuditAction, AccountStatus
from apps.audit.models import AuditEvent
from apps.audit.services import AuditService

User = get_user_model()


class AuditEventModelTestCase(TestCase):
    """Tests for AuditEvent model immutability."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="auditor@school.edu",
            password="SecurePass@123",
            account_status=AccountStatus.ACTIVE,
        )

    def test_create_audit_event(self):
        """A new AuditEvent can be created successfully."""
        event = AuditEvent.objects.create(
            actor=self.user,
            action=AuditAction.LOGIN_SUCCESS,
            resource_type="UserSession",
            resource_id="session-abc",
            ip_address="192.168.1.1",
            status="SUCCESS",
            details={"source": "password"},
        )
        self.assertIsNotNone(event.pk)
        self.assertEqual(event.action, AuditAction.LOGIN_SUCCESS)

    def test_actor_email_auto_snapshots_on_create(self):
        """actor_email is auto-filled from actor.email if blank."""
        event = AuditEvent.objects.create(
            actor=self.user,
            action=AuditAction.LOGIN_SUCCESS,
        )
        self.assertEqual(event.actor_email, self.user.email)

    def test_update_raises_permission_denied(self):
        """Saving an existing AuditEvent raises PermissionDenied."""
        event = AuditEvent.objects.create(
            actor=self.user,
            action=AuditAction.LOGIN_SUCCESS,
        )
        event.status = "FAILURE"
        with self.assertRaises(PermissionDenied):
            event.save()

    def test_delete_raises_permission_denied(self):
        """Deleting an AuditEvent raises PermissionDenied."""
        event = AuditEvent.objects.create(
            actor=self.user,
            action=AuditAction.LOGIN_SUCCESS,
        )
        with self.assertRaises(PermissionDenied):
            event.delete()

    def test_str_representation(self):
        """__str__ includes actor info and action."""
        event = AuditEvent.objects.create(
            actor=self.user,
            action=AuditAction.LOGIN_FAILED,
            status="FAILURE",
        )
        s = str(event)
        self.assertIn(AuditAction.LOGIN_FAILED, s)
        self.assertIn("FAILURE", s)

    def test_anonymous_event_stores_without_actor(self):
        """Events without an actor (anonymous) store successfully."""
        event = AuditEvent.objects.create(
            actor=None,
            action=AuditAction.LOGIN_FAILED,
            actor_email="unknown@attacker.com",
            ip_address="10.0.0.1",
            status="FAILURE",
        )
        self.assertIsNone(event.actor)
        self.assertEqual(event.actor_email, "unknown@attacker.com")


class AuditServiceSanitizeTestCase(TestCase):
    """Tests for AuditService.sanitize()."""

    def test_redacts_password(self):
        data = {"username": "alice", "password": "hunter2"}
        result = AuditService.sanitize(data)
        self.assertEqual(result["password"], "[REDACTED]")
        self.assertEqual(result["username"], "alice")

    def test_redacts_token(self):
        data = {"access_token": "abc123", "action": "login"}
        result = AuditService.sanitize(data)
        self.assertEqual(result["access_token"], "[REDACTED]")

    def test_redacts_nested_sensitive(self):
        data = {
            "user": {"email": "a@b.com", "password": "secret"},
            "meta": "ok",
        }
        result = AuditService.sanitize(data)
        self.assertEqual(result["user"]["password"], "[REDACTED]")
        self.assertEqual(result["user"]["email"], "a@b.com")

    def test_handles_list_input(self):
        data = [{"password": "x"}, {"user": "alice"}]
        result = AuditService.sanitize(data)
        self.assertEqual(result[0]["password"], "[REDACTED]")

    def test_handles_none_gracefully(self):
        result = AuditService.sanitize(None)
        self.assertIsNone(result)

    def test_handles_primitive_input(self):
        self.assertEqual(AuditService.sanitize("hello"), "hello")
        self.assertEqual(AuditService.sanitize(42), 42)

    def test_case_insensitive_key_matching(self):
        data = {"PASSWORD": "secret", "Token": "abc"}
        result = AuditService.sanitize(data)
        self.assertEqual(result["PASSWORD"], "[REDACTED]")
        self.assertEqual(result["Token"], "[REDACTED]")

    def test_preserves_non_sensitive_keys(self):
        data = {"action": "login", "ip": "127.0.0.1", "status": "SUCCESS"}
        result = AuditService.sanitize(data)
        self.assertEqual(result, data)


class AuditServiceLogTestCase(TestCase):
    """Tests for AuditService.log()."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="staff@school.edu",
            password="Password@321",
            account_status=AccountStatus.ACTIVE,
        )

    def test_log_creates_event(self):
        """log() creates an AuditEvent record."""
        event = AuditService.log(
            action=AuditAction.LOGIN_SUCCESS,
            actor=self.user,
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
            status="SUCCESS",
            details={"auth_source": "password"},
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.action, AuditAction.LOGIN_SUCCESS)
        self.assertEqual(event.actor_id, self.user.pk)
        self.assertEqual(event.status, "SUCCESS")

    def test_log_sanitizes_details(self):
        """log() never persists sensitive fields in details."""
        event = AuditService.log(
            action=AuditAction.LOGIN_FAILED,
            actor=self.user,
            details={"identifier": "alice", "password": "hunter2"},
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.details.get("password"), "[REDACTED]")
        self.assertEqual(event.details.get("identifier"), "alice")

    def test_log_handles_unauthenticated_actor(self):
        """log() with actor=None writes an anonymous event."""
        event = AuditService.log(
            action=AuditAction.LOGIN_FAILED,
            actor=None,
            ip_address="5.5.5.5",
        )
        self.assertIsNotNone(event)
        self.assertIsNone(event.actor)

    def test_log_silently_returns_none_on_error(self):
        """log() never raises; returns None on internal failure."""
        with patch("apps.audit.models.AuditEvent.objects") as mock_mgr:
            mock_mgr.create.side_effect = Exception("DB down")
            result = AuditService.log(
                action=AuditAction.LOGIN_SUCCESS,
                actor=self.user,
            )
        self.assertIsNone(result)

    def test_log_truncates_long_user_agent(self):
        """user_agent is truncated to 1000 characters."""
        long_ua = "A" * 2000
        event = AuditService.log(
            action=AuditAction.LOGIN_SUCCESS,
            actor=self.user,
            user_agent=long_ua,
        )
        self.assertIsNotNone(event)
        self.assertLessEqual(len(event.user_agent), 1000)
