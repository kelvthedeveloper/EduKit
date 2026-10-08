from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from common.constants import AccountStatus
from ..managers import UserManager


phone_validator = RegexValidator(
    regex=r'^\+?[1-9]\d{1,14}$',
    message='Phone number must be entered in E.164 format: "+233XXXXXXXXX".',
)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(
        _('email address'),
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        error_messages={'unique': _('A user with that email already exists.')},
    )
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        validators=[phone_validator],
        error_messages={'unique': _('A user with that phone number already exists.')},
    )
    username = models.CharField(
        _('username / staff / student id'),
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        error_messages={'unique': _('A user with that username already exists.')},
    )
    first_name = models.CharField(_('first name'), max_length=100, blank=True)
    last_name = models.CharField(_('last name'), max_length=100, blank=True)
    display_name = models.CharField(
        _('display name'),
        max_length=200,
        blank=True,
        help_text=_('Public display name. Falls back to first_name + last_name.'),
    )

    account_status = models.CharField(
        max_length=32,
        choices=AccountStatus.CHOICES,
        default=AccountStatus.PENDING_VERIFICATION,
        db_index=True,
    )
    email_verified = models.BooleanField(default=False, db_index=True)
    phone_verified = models.BooleanField(default=False, db_index=True)

    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_('If set, the account is locked until this timestamp (failed login throttle).'),
    )
    failed_login_attempts = models.PositiveIntegerField(default=0)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the Django admin site.'),
    )
    is_active_legacy_unused = models.BooleanField(
        _('active (legacy; see account_status)'),
        default=True,
        db_column='is_active',
    )
    is_system_superuser = models.BooleanField(
        _('system-level super administrator'),
        default=False,
        help_text=_(
            'Hard-coded system capability: bypass policy, modify security infrastructure, '
            'destroy audit history. Cannot be granted via ordinary role configuration.'
        ),
    )

    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    last_active = models.DateTimeField(_('last activity'), blank=True, null=True, db_index=True)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        app_label = 'identity'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['account_status', 'is_staff']),
        ]

    @property
    def is_active(self):
        return self.account_status in AccountStatus.AUTH_ALLOWED

    @is_active.setter
    def is_active(self, value):
        if value:
            if self.account_status in (None, AccountStatus.INACTIVE, AccountStatus.PENDING_VERIFICATION):
                self.account_status = AccountStatus.ACTIVE
        else:
            self.account_status = AccountStatus.INACTIVE

    @property
    def full_name(self):
        parts = [p for p in (self.first_name, self.last_name) if p]
        return ' '.join(parts).strip()

    def get_full_name(self):
        return self.full_name

    @property
    def name(self):
        if self.display_name:
            return self.display_name
        return self.full_name or self.username or self.email or self.phone or f'user-{self.uuid}'

    def get_short_name(self):
        return self.first_name or self.name

    def __str__(self):
        return f'{self.name} <{self.email or self.phone or self.username}>'

    def clean(self):
        super().clean()
        if not any([self.email, self.phone, self.username]):
            from django.core.exceptions import ValidationError
            raise ValidationError('At least one of email, phone, or username must be set.')
