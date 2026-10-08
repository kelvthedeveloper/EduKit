from typing import Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import HttpRequest

from common.models import BaseModel
from ..models import UserSession
from common.constants import AUTH_SOURCE_PASSWORD

User = get_user_model()


class SessionService:
    @staticmethod
    def create_session(user,
                       request: Optional[HttpRequest] = None,
                       session_key: Optional[str] = None,
                       refresh_token_jti: Optional[str] = None,
                       device_id: Optional[str] = None,
                       device_name: Optional[str] = None,
                       ip_address: Optional[str] = None,
                       user_agent: str = '',
                       auth_source: str = AUTH_SOURCE_PASSWORD,
                       expires_seconds: Optional[int] = None) -> UserSession:
        expires_at = None
        if expires_seconds:
            expires_at = timezone.now() + timezone.timedelta(seconds=expires_seconds)
        elif settings.SESSION_COOKIE_AGE:
            expires_at = timezone.now() + timezone.timedelta(seconds=settings.SESSION_COOKIE_AGE)
        session = UserSession.objects.create(
            user=user,
            session_key=session_key,
            refresh_token_jti=refresh_token_jti,
            device_id=device_id or '',
            device_name=device_name or SessionService._infer_device_name(user_agent),
            ip_address=ip_address,
            user_agent=user_agent[:2000],
            auth_source=auth_source,
            expires_at=expires_at,
        )
        return session

    @staticmethod
    def touch_session(session_key: str):
        if not session_key:
            return None
        s = UserSession.objects.filter(session_key=session_key).first()
        if s and s.is_active:
            s.touch(save=True)
            return s
        return None

    @staticmethod
    def list_sessions(user):
        return list(UserSession.objects.filter(user=user).order_by('-last_activity'))

    @staticmethod
    def revoke_by_uuid(session_uuid, actor, source='manual'):
        try:
            s = UserSession.objects.get(uuid=session_uuid)
        except UserSession.DoesNotExist:
            return None
        SessionService._do_revoke(s, actor, source)
        return s

    @staticmethod
    def revoke_by_session_key(session_key, actor=None, source='manual'):
        if not session_key:
            return None
        s = UserSession.objects.filter(session_key=session_key).first()
        if s:
            SessionService._do_revoke(s, actor, source)
        return s

    @staticmethod
    def revoke_all_other(user, current_session_key, actor=None, source='manual'):
        actor = actor or user
        qs = UserSession.objects.filter(
            user=user,
            revoked_at__isnull=True,
        ).exclude(session_key=current_session_key)
        now = timezone.now()
        return qs.update(
            revoked_at=now,
            revoked_by=actor,
            updated_at=now,
        )

    @staticmethod
    def revoke_all(user, actor=None, source='manual'):
        actor = actor or user
        now = timezone.now()
        return UserSession.objects.filter(user=user, revoked_at__isnull=True).update(
            revoked_at=now,
            revoked_by=actor,
            updated_at=now,
        )

    @staticmethod
    def cleanup_expired(days_old: int = 30):
        cutoff = timezone.now() - timezone.timedelta(days=days_old)
        n, _ = UserSession.objects.filter(
            revoked_at__isnull=False, revoked_at__lt=cutoff,
        ).delete()
        return n

    @staticmethod
    def _do_revoke(s: UserSession, actor, source):
        if s.revoked_at:
            return
        s.revoked_at = timezone.now()
        s.revoked_by = actor
        s.save(update_fields=['revoked_at', 'revoked_by', 'updated_at'])
        # Invalidate Django session table
        if s.session_key:
            from django.contrib.sessions.backends.db import SessionStore
            store = SessionStore(session_key=s.session_key)
            if store.exists(s.session_key):
                store.delete()
        try:
            from apps.audit.services import AuditService
            from common.constants import AuditAction
            AuditService.log_security(
                action=AuditAction.SESSION_REVOKED,
                actor=actor or s.user,
                entity=s,
                ip_address=getattr(actor, '_ip', None),
                extra={'source': source},
            )
        except Exception:
            pass

    @staticmethod
    def _infer_device_name(user_agent: str) -> str:
        ua = (user_agent or '').lower()
        if not ua:
            return 'Unknown device'
        if 'edukit-mobile' in ua:
            return 'EduKit Mobile App'
        name_parts = []
        if 'android' in ua:
            name_parts.append('Android')
        elif 'iphone' in ua or 'ipad' in ua:
            name_parts.append('iOS')
        elif 'mac os' in ua:
            name_parts.append('macOS')
        elif 'windows' in ua:
            name_parts.append('Windows')
        elif 'linux' in ua:
            name_parts.append('Linux')
        if 'firefox' in ua:
            name_parts.append('Firefox')
        elif 'edg' in ua:
            name_parts.append('Edge')
        elif 'chrome' in ua:
            name_parts.append('Chrome')
        elif 'safari' in ua:
            name_parts.append('Safari')
        return ' '.join(name_parts) or 'Unknown device'
