import logging
from django.contrib.auth import logout as django_logout
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('apps.identity')


class SessionRevocationMiddleware(MiddlewareMixin):
    """
    Verifies that the Django session used on an authenticated request corresponds
    to an active (non-revoked, non-expired) UserSession record. If not, the user is
    logged out server-side so subsequent requests are treated as anonymous.

    This closes the gap where UserSession.revoked_at was set administratively but
    Django's cached_db session backend continued to honour the original session key.
    """

    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', False):
            return None
        session_key = getattr(request.session, 'session_key', None)
        if not session_key:
            return None
        from apps.identity.models import UserSession
        now = timezone.now()
        qs = UserSession.objects.filter(
            user=user,
            session_key=session_key,
            revoked_at__isnull=True,
        )
        row = qs.first()
        if row is None:
            logger.info(
                'Session key %s for user %s not found in UserSession (possibly revoked); '
                'forcing server-side logout.',
                session_key[:8] + '***' if session_key else 'None',
                str(getattr(user, 'uuid', user.pk)),
            )
            django_logout(request)
            return None
        if row.expires_at and row.expires_at < now:
            logger.info(
                'Session key %s for user %s expired at %s; forcing logout.',
                session_key[:8] + '***',
                str(getattr(user, 'uuid', user.pk)),
                row.expires_at.isoformat(),
            )
            django_logout(request)
            return None
        return None
