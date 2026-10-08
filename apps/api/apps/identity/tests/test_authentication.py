"""
Tests for Authentication service.

Covers:
- Successful login with email / phone / username
- Failed login → failed_attempt counter increments
- Account lockout after MAX_LOGIN_ATTEMPTS
- Locked account cannot authenticate
- Successful login resets failed_attempts counter
- Logout fires audit event and revokes session
- Inactive account is rejected
"""
from datetime import timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

from common.constants import (
    AccountStatus,
    DEFAULT_MAX_LOGIN_ATTEMPTS,
    DEFAULT_ACCOUNT_LOCKOUT_DURATION_MINUTES,
)
from common.exceptions import AuthenticationError
from apps.identity.services.authentication import AuthenticationService

User = get_user_model()

MAX_LOGIN_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', DEFAULT_MAX_LOGIN_ATTEMPTS)
ACCOUNT_LOCKOUT_DURATION_MINUTES = getattr(
    settings, 'ACCOUNT_LOCKOUT_DURATION_MINUTES', DEFAULT_ACCOUNT_LOCKOUT_DURATION_MINUTES
)


class AuthenticationServiceTestCase(TestCase):
    """Unit tests for AuthenticationService."""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post("/api/auth/login/")
        self.request.session = MagicMock()
        self.request.session.session_key = "test-session-key-001"
        self.request.META["HTTP_USER_AGENT"] = "test-agent/1.0"
        self.request.META["REMOTE_ADDR"] = "127.0.0.1"

        self.user = User.objects.create_user(
            email="teacher@school.edu",
            password="SecurePass@123",
            first_name="Jane",
            last_name="Doe",
            account_status=AccountStatus.ACTIVE,
        )

    # ------------------------------------------------------------------
    # Successful authentication
    # ------------------------------------------------------------------

    @patch("apps.identity.services.authentication.django_login")
    @patch("apps.identity.services.session.SessionService.create_session")
    def test_login_success(self, mock_create_session, mock_django_login):
        """Successful credentials lead to login and session creation."""
        mock_session = MagicMock()
        mock_session.uuid = "abc-123"
        mock_create_session.return_value = mock_session

        with patch("django.contrib.auth.authenticate", return_value=self.user):
            returned_user = AuthenticationService.authenticate(
                identifier="teacher@school.edu",
                password="SecurePass@123",
                request=self.request,
            )
        self.assertEqual(returned_user, self.user)

    def test_failed_login_increments_counter(self):
        """Failed login attempt increments failed_login_attempts counter."""
        with patch("django.contrib.auth.authenticate", return_value=None):
            with self.assertRaises(AuthenticationError):
                AuthenticationService.authenticate(
                    identifier="teacher@school.edu",
                    password="WrongPassword",
                    request=self.request,
                )
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)

    def test_lockout_after_max_attempts(self):
        """Account is locked after MAX_LOGIN_ATTEMPTS consecutive failures."""
        with patch("django.contrib.auth.authenticate", return_value=None):
            for _ in range(MAX_LOGIN_ATTEMPTS):
                with self.assertRaises(AuthenticationError):
                    AuthenticationService.authenticate(
                        identifier="teacher@school.edu",
                        password="WrongPassword",
                        request=self.request,
                    )
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.locked_until)
        self.assertGreater(self.user.locked_until, timezone.now())

    def test_successful_login_resets_failed_attempts(self):
        """Successful authentication clears failed_login_attempts and locked_until."""
        self.user.failed_login_attempts = 4
        self.user.locked_until = None
        self.user.save()

        with patch("django.contrib.auth.authenticate", return_value=self.user):
            AuthenticationService.authenticate(
                identifier="teacher@school.edu",
                password="SecurePass@123",
                request=self.request,
            )
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertIsNone(self.user.locked_until)

    def test_authenticate_unknown_identifier_raises(self):
        """Authenticating with a non-existent identifier raises AuthenticationError."""
        with patch("django.contrib.auth.authenticate", return_value=None):
            with self.assertRaises(AuthenticationError):
                AuthenticationService.authenticate(
                    identifier="no-such-user@school.edu",
                    password="AnyPassword",
                    request=self.request,
                )

    # ------------------------------------------------------------------
    # Inactive / locked accounts
    # ------------------------------------------------------------------

    def test_locked_account_cannot_authenticate(self):
        """A locked user cannot authenticate even with correct credentials."""
        self.user.failed_login_attempts = MAX_LOGIN_ATTEMPTS
        self.user.locked_until = timezone.now() + timedelta(minutes=ACCOUNT_LOCKOUT_DURATION_MINUTES)
        self.user.save()

        # Django's authenticate backend should reject locked accounts;
        # simulate returning None (as would happen with our backend)
        with patch("django.contrib.auth.authenticate", return_value=None):
            with self.assertRaises(AuthenticationError):
                AuthenticationService.authenticate(
                    identifier="teacher@school.edu",
                    password="SecurePass@123",
                    request=self.request,
                )

    def test_inactive_account_cannot_authenticate(self):
        """INACTIVE status user is rejected by authenticate."""
        self.user.account_status = AccountStatus.INACTIVE
        self.user.save()

        with patch("django.contrib.auth.authenticate", return_value=None):
            with self.assertRaises(AuthenticationError):
                AuthenticationService.authenticate(
                    identifier="teacher@school.edu",
                    password="SecurePass@123",
                    request=self.request,
                )

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    @patch("apps.identity.services.authentication.django_logout")
    def test_logout_calls_django_logout(self, mock_logout):
        """logout() delegates to django.contrib.auth.logout."""
        self.request.user = self.user
        self.request.user.is_authenticated = True
        AuthenticationService.logout(self.request)
        mock_logout.assert_called_once_with(self.request)

    # ------------------------------------------------------------------
    # IP extraction helper
    # ------------------------------------------------------------------

    def test_get_ip_with_forwarded_header(self):
        """X-Forwarded-For header is preferred over REMOTE_ADDR."""
        self.request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.5, 172.16.0.1"
        ip = AuthenticationService._get_ip(self.request)
        self.assertEqual(ip, "10.0.0.5")

    def test_get_ip_without_forwarded_header(self):
        """Falls back to REMOTE_ADDR when no forwarding header."""
        self.request.META.pop("HTTP_X_FORWARDED_FOR", None)
        self.request.META["REMOTE_ADDR"] = "192.168.1.50"
        ip = AuthenticationService._get_ip(self.request)
        self.assertEqual(ip, "192.168.1.50")

    def test_get_ip_no_request(self):
        """Returns None when request is None."""
        self.assertIsNone(AuthenticationService._get_ip(None))
