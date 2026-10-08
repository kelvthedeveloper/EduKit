from celery import shared_task
from django.utils import timezone
from django.core import management

from ..models import UserSession


@shared_task(bind=True, ignore_result=True, name='identity.cleanup_expired_sessions')
def cleanup_expired_sessions(self):
    cutoff = timezone.now()
    qs = UserSession.objects.filter(
        revoked_at__isnull=False, revoked_at__lt=cutoff - timezone.timedelta(days=30))
    n, _ = qs.delete()
    management.call_command('clearsessions', verbosity=0)
    return {'revoked_deleted': n}


@shared_task(bind=True, ignore_result=True, name='identity.send_verification_email')
def send_verification_email(self, user_uuid, token_uuid):
    """Placeholder - email-sending logic; integrate Resend/SMTP later."""
    return {'user_uuid': user_uuid, 'token_uuid': token_uuid, 'status': 'placeholder'}


@shared_task(bind=True, ignore_result=True, name='identity.send_password_reset_email')
def send_password_reset_email(self, user_uuid, token_uuid):
    return {'user_uuid': user_uuid, 'token_uuid': token_uuid, 'status': 'placeholder'}
