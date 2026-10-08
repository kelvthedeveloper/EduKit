from typing import Optional
from django.utils import timezone

from ..models import (
    EmailVerificationToken,
    PhoneVerificationCode,
    PasswordResetToken,
)
from .authentication import AuthenticationService


class VerificationService:
    @staticmethod
    def send_email_verification(user, email: Optional[str] = None,
                                ip_address=None, user_agent=''):
        target = email or user.email
        if not target:
            from common.exceptions import ValidationError
            raise ValidationError(detail='No email address provided.', code='email_required')
        token = EmailVerificationToken.objects.generate(user=user, email=target)
        token.ip_address = ip_address
        token.user_agent = user_agent
        token.save(update_fields=['ip_address', 'user_agent', 'updated_at'])
        try:
            from ..tasks import send_verification_email
            send_verification_email.delay(str(user.uuid), str(token.uuid))
        except Exception:
            # Task broker may be down (school-server offline); ignore silently.
            pass
        return token

    @staticmethod
    def send_phone_verification(user, phone: Optional[str] = None,
                                ip_address=None, user_agent=''):
        target = phone or user.phone
        if not target:
            from common.exceptions import ValidationError
            raise ValidationError(detail='No phone number provided.', code='phone_required')
        code = PhoneVerificationCode.objects.generate(user=user, phone=target)
        code.ip_address = ip_address
        code.user_agent = user_agent
        code.save(update_fields=['ip_address', 'user_agent', 'updated_at'])
        # SMS provider integration later. For now, placeholder.
        return code

    @staticmethod
    def verify_email(token_str: str):
        try:
            token = EmailVerificationToken.objects.get(token=token_str)
        except EmailVerificationToken.DoesNotExist:
            from common.exceptions import ValidationError
            raise ValidationError(detail='Invalid verification token.', code='invalid_token')
        if not token.is_usable:
            from common.exceptions import ValidationError
            raise ValidationError(detail='Verification token expired.', code='token_expired')
        user = token.user
        if user and token.identifier:
            user.email = user.email or token.identifier
            user.email_verified = True
            if user.account_status == 'PENDING_VERIFICATION':
                user.account_status = 'ACTIVE'
            user.save(update_fields=['email', 'email_verified', 'account_status', 'updated_at'])
        token.consume(save=True)
        try:
            from apps.audit.services import AuditService
            from common.constants import AuditAction
            AuditService.log_security(action=AuditAction.ACCOUNT_VERIFIED, actor=user, entity=user,
                                      ip_address=token.ip_address)
            if user.account_status == 'ACTIVE':
                AuditService.log_security(action=AuditAction.ACCOUNT_ACTIVATED, actor=user,
                                          entity=user, ip_address=token.ip_address)
        except Exception:
            pass
        return user

    @staticmethod
    def verify_phone(phone: str, code: str):
        try:
            record = PhoneVerificationCode.objects.get(
                identifier=phone, token=code)
        except PhoneVerificationCode.DoesNotExist:
            from common.exceptions import ValidationError
            raise ValidationError(detail='Invalid verification code.', code='invalid_code')
        if not record.is_usable:
            from common.exceptions import ValidationError
            raise ValidationError(detail='Verification code expired.', code='code_expired')
        user = record.user
        if user and phone:
            user.phone = user.phone or phone
            user.phone_verified = True
            if user.account_status == 'PENDING_VERIFICATION':
                user.account_status = 'ACTIVE'
            user.save(update_fields=['phone', 'phone_verified', 'account_status', 'updated_at'])
        record.consume(save=True)
        return user

    @staticmethod
    def is_verified(user) -> bool:
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        return bool(user.email_verified or user.phone_verified)

    @staticmethod
    def _notify_password_reset(user, token: PasswordResetToken):
        try:
            from ..tasks import send_password_reset_email
            send_password_reset_email.delay(str(user.uuid), str(token.uuid))
        except Exception:
            pass
