import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.validators import RegexValidator

from common.models import UUIDModel, TimestampedModel


class _BaseToken(UUIDModel, TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        db_index=True,
        null=True,
        blank=True,
    )
    identifier = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text='Email address or phone number targeted, independent of user foreign key.',
    )
    token = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        state = 'consumed' if self.consumed_at else ('expired' if self.is_expired else 'valid')
        return f'{self.__class__.__name__} {state} for {self.identifier or self.user_id}'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_usable(self):
        return (not self.consumed_at) and (not self.is_expired)

    def consume(self, save=True):
        self.consumed_at = timezone.now()
        if save:
            self.save(update_fields=['consumed_at', 'updated_at'])


class EmailVerificationTokenManager(models.Manager):
    def generate(self, user, email=None, ttl_seconds=60 * 60 * 24):
        return self.create(
            user=user,
            identifier=email or user.email,
            token=secrets.token_urlsafe(48),
            expires_at=timezone.now() + timezone.timedelta(seconds=ttl_seconds),
        )


class PhoneVerificationCodeManager(models.Manager):
    def generate(self, user, phone=None, ttl_seconds=60 * 10, length=6):
        return self.create(
            user=user,
            identifier=phone or user.phone,
            token=get_random_string(length=length, allowed_chars='0123456789'),
            expires_at=timezone.now() + timezone.timedelta(seconds=ttl_seconds),
        )


class PasswordResetTokenManager(models.Manager):
    def generate(self, user, ttl_seconds=60 * 60):
        return self.create(
            user=user,
            identifier=user.email or user.phone or user.username or '',
            token=secrets.token_urlsafe(48),
            expires_at=timezone.now() + timezone.timedelta(seconds=ttl_seconds),
        )


class EmailVerificationToken(_BaseToken):
    objects = EmailVerificationTokenManager()

    class Meta(_BaseToken.Meta):
        app_label = 'identity'


class PhoneVerificationCode(_BaseToken):
    code_validator = RegexValidator(r'^\d{4,8}$', 'Code must be 4-8 digits.')

    objects = PhoneVerificationCodeManager()

    class Meta(_BaseToken.Meta):
        app_label = 'identity'
        verbose_name = 'phone verification code'
        verbose_name_plural = 'phone verification codes'


class PasswordResetToken(_BaseToken):
    objects = PasswordResetTokenManager()

    class Meta(_BaseToken.Meta):
        app_label = 'identity'
