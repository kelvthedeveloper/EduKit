from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone

from common.constants import AccountStatus
from common.exceptions import AccountInactiveError, AccountLockedError
from .models import User

UserModel = get_user_model()


class MultiIdentifierAuthenticationBackend(ModelBackend):
    supports_anonymous_user = True
    supports_inactive_user = False

    def authenticate(self, request, username=None, password=None, identifier=None, **kwargs):
        lookup_identifier = identifier or username
        if not lookup_identifier or not password:
            return None
        try:
            user = UserModel.objects.get_by_identifier(lookup_identifier)
        except UserModel.DoesNotExist:
            # Run the default password hasher to avoid timing attacks
            from django.contrib.auth.hashers import check_password
            check_password(password, 'sha256$notauser')
            return None
        if user.locked_until and user.locked_until > timezone.now():
            raise AccountLockedError(
                detail=f'Account locked until {user.locked_until.isoformat()}')
        if user.account_status not in AccountStatus.AUTH_ALLOWED:
            raise AccountInactiveError(
                detail=f'Account status is {user.account_status}. Authentication denied.')
        if user.check_password(password):
            return user
        return None

    def user_can_authenticate(self, user):
        if not getattr(user, 'is_active', True):
            return False
        if user.locked_until and user.locked_until > timezone.now():
            return False
        return True

    def get_user(self, user_id):
        try:
            return UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
