from django.contrib.auth import get_user_model
from django.db.models import Q
from ..models import UserSession

User = get_user_model()


def user_get_by_uuid(uuid):
    return User.objects.filter(uuid=uuid).first()


def user_get_by_identifier(identifier):
    try:
        return User.objects.get_by_identifier(identifier)
    except User.DoesNotExist:
        return None


def user_list_by_role_codes(role_codes):
    if not role_codes:
        return User.objects.none()
    return User.objects.filter(
        roles_assigned__role__code__in=role_codes,
        roles_assigned__expires_at__isnull=True,
    ).distinct()


def session_list_active(user):
    return UserSession.objects.filter(
        user=user,
        revoked_at__isnull=True,
    ).select_related('user').order_by('-last_activity')


def session_get_by_key(session_key):
    if not session_key:
        return None
    return UserSession.objects.filter(session_key=session_key).first()


def session_get_by_uuid(session_uuid):
    return UserSession.objects.filter(uuid=session_uuid).first()
