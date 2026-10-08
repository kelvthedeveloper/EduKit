from datetime import timedelta
from typing import Optional
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from common.exceptions import ValidationError as ApiValidationError, AuthenticationError
from ..models import PasswordResetToken

User = get_user_model()


class PasswordService:
    @staticmethod
    def validate_strength(password: str, user=None):
        errors = []
        try:
            password_validation.validate_password(password, user)
        except DjangoValidationError as exc:
            errors = list(exc.messages)
        if not any(c.isupper() for c in password):
            errors.append('Password must contain at least one uppercase letter.')
        if not any(c.isdigit() for c in password):
            errors.append('Password must contain at least one digit.')
        if errors:
            raise ApiValidationError(
                detail=errors,
                code='weak_password',
                data={'errors': errors},
            )
        return True

    @staticmethod
    def change_password(user, old_password: str, new_password: str):
        if not user.check_password(old_password):
            raise AuthenticationError(detail='Old password is incorrect.',
                                     code='old_password_invalid',
                                     status_code=401)
        PasswordService.validate_strength(new_password, user)
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])
        try:
            from apps.audit.services import AuditService
            from common.constants import AuditAction
            AuditService.log(
                action=AuditAction.PASSWORD_CHANGED,
                actor=user,
                resource_type='User',
                resource_id=str(user.uuid),
            )
        except Exception:
            pass
        return user

    @staticmethod
    def request_reset(identifier: str, ip=None, user_agent=''):
        try:
            user = User.objects.get_by_identifier(identifier)
        except User.DoesNotExist:
            # Do not reveal whether the user exists; return sent=False
            return {'sent': False}
        token = PasswordResetToken.objects.generate(user, ttl_seconds=60 * 60)
        token.ip_address = ip
        token.user_agent = user_agent
        token.save(update_fields=['ip_address', 'user_agent', 'updated_at'])
        try:
            from apps.audit.services import AuditService
            from common.constants import AuditAction
            AuditService.log(
                action=AuditAction.PASSWORD_RESET_REQUESTED,
                actor=user,
                resource_type='User',
                resource_id=str(user.uuid),
                ip_address=ip,
                user_agent=user_agent,
            )
        except Exception:
            pass
        from .verification import VerificationService
        if hasattr(VerificationService, '_notify_password_reset'):
            VerificationService._notify_password_reset(user, token)
        return {'sent': True, 'token_uuid': str(token.uuid)}

    @staticmethod
    def confirm_reset(token_str: str, new_password: str):
        try:
            token = PasswordResetToken.objects.get(token=token_str)
        except PasswordResetToken.DoesNotExist:
            raise ApiValidationError(detail='Invalid or expired reset token.',
                                     code='invalid_token')
        if not token.is_usable:
            raise ApiValidationError(detail='Invalid or expired reset token.',
                                     code='token_expired')
        user = token.user
        if not user:
            raise ApiValidationError(detail='Invalid token target user.',
                                     code='invalid_user')
        PasswordService.validate_strength(new_password, user)
        user.set_password(new_password)
        if user.account_status == 'PENDING_VERIFICATION':
            # Set to active after password reset confirms email/phone control
            user.account_status = 'ACTIVE'
        user.save(update_fields=['password', 'account_status', 'updated_at'])
        token.consume(save=True)
        # Revoke all other sessions after password reset
        from .session import SessionService
        SessionService.revoke_all(user, actor=user, source='password_reset')
        try:
            from apps.audit.services import AuditService
            from common.constants import AuditAction
            AuditService.log(
                action=AuditAction.PASSWORD_RESET_COMPLETED,
                actor=user,
                resource_type='User',
                resource_id=str(user.uuid),
                ip_address=token.ip_address,
            )
        except Exception:
            pass
        return user
