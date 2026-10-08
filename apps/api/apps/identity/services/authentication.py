from typing import Tuple, Optional
from django.conf import settings
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import HttpRequest

from common.constants import (
    AUTH_SOURCE_PASSWORD,
    DEFAULT_MAX_LOGIN_ATTEMPTS,
    DEFAULT_ACCOUNT_LOCKOUT_DURATION_MINUTES,
)
from common.exceptions import (
    AuthenticationError,
    ValidationError,
)
from ..models import UserSession

User = get_user_model()


class AuthenticationService:
    @staticmethod
    def authenticate(identifier: str, password: str, request: Optional[HttpRequest] = None):
        from django.contrib.auth import authenticate
        from common.exceptions import AccountLockedError, AccountInactiveError
        try:
            user = authenticate(request=request, identifier=identifier, password=password)
        except (AccountLockedError, AccountInactiveError):
            AuthenticationService._record_failed_attempt(identifier, request)
            raise
        if user is None:
            AuthenticationService._record_failed_attempt(identifier, request)
            raise AuthenticationError(
                detail='Invalid credentials.',
                code='invalid_credentials',
                status_code=401,
            )
        AuthenticationService._reset_failed_attempts(user)
        return user

    @staticmethod
    def login(user, request: HttpRequest,
              device_meta: Optional[dict] = None,
              auth_source: str = AUTH_SOURCE_PASSWORD
              ) -> Tuple[object, UserSession]:
        request.session.flush()
        django_login(request, user)
        from .session import SessionService
        session_key = request.session.session_key
        device_meta = device_meta or {}
        user_session = SessionService.create_session(
            user=user,
            request=request,
            session_key=session_key,
            device_id=device_meta.get('device_id'),
            device_name=device_meta.get('device_name'),
            ip_address=device_meta.get('ip_address') or AuthenticationService._get_ip(request),
            user_agent=device_meta.get('user_agent') or request.META.get('HTTP_USER_AGENT', ''),
            auth_source=auth_source,
            expires_seconds=settings.SESSION_COOKIE_AGE,
        )
        user.last_login = timezone.now()
        user.last_active = timezone.now()
        user.save(update_fields=['last_login', 'last_active', 'updated_at'])
        try:
            from apps.audit.services import AuditService
            from common.constants import AuditAction
            AuditService.log(
                action=AuditAction.LOGIN_SUCCESS,
                actor=user,
                resource_type='UserSession',
                resource_id=str(user_session.uuid) if user_session else '',
                ip_address=AuthenticationService._get_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'auth_source': auth_source, 'device_id': device_meta.get('device_id', '')},
            )
        except Exception:
            pass
        return user, user_session

    @staticmethod
    def logout(request: HttpRequest):
        user = getattr(request, 'user', None)
        session_key = getattr(request.session, 'session_key', None)
        if user and user.is_authenticated:
            try:
                from apps.audit.services import AuditService
                from common.constants import AuditAction
                AuditService.log(
                    action=AuditAction.LOGOUT,
                    actor=user,
                    ip_address=AuthenticationService._get_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
                )
            except Exception:
                pass
            if session_key:
                from .session import SessionService
                SessionService.revoke_by_session_key(session_key, actor=user, source='logout')
        django_logout(request)
        return True

    @staticmethod
    def refresh_session(request: HttpRequest):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            raise AuthenticationError()
        session_key = getattr(request.session, 'session_key', None)
        if session_key:
            from .session import SessionService
            SessionService.touch_session(session_key)
        user.last_active = timezone.now()
        user.save(update_fields=['last_active', 'updated_at'])
        return user

    @staticmethod
    def _record_failed_attempt(identifier, request):
        user = None
        try:
            user = User.objects.get_by_identifier(identifier)
        except User.DoesNotExist:
            user = None

        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', DEFAULT_MAX_LOGIN_ATTEMPTS)
            lockout_min = getattr(settings, 'ACCOUNT_LOCKOUT_DURATION_MINUTES',
                                   DEFAULT_ACCOUNT_LOCKOUT_DURATION_MINUTES)
            if user.failed_login_attempts >= max_attempts:
                user.locked_until = timezone.now() + timezone.timedelta(
                    minutes=lockout_min)
            user.save(update_fields=['failed_login_attempts', 'locked_until', 'updated_at'])

        try:
            from apps.audit.services import AuditService
            from common.constants import AuditAction
            AuditService.log(
                action=AuditAction.LOGIN_FAILED,
                actor=user,
                status='FAILURE',
                ip_address=AuthenticationService._get_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
                details={'identifier': identifier},
            )
            if user and user.locked_until:
                AuditService.log(
                    action=AuditAction.ACCOUNT_LOCKED,
                    actor=user,
                    status='FAILURE',
                    ip_address=AuthenticationService._get_ip(request),
                    details={'locked_until': user.locked_until.isoformat()},
                )
        except Exception:
            pass
        return user

    @staticmethod
    def _reset_failed_attempts(user):
        if user.failed_login_attempts or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=['failed_login_attempts', 'locked_until', 'updated_at'])

    @staticmethod
    def _get_ip(request: Optional[HttpRequest]):
        if not request:
            return None
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
