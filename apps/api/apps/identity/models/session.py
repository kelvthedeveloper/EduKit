from django.db import models
from django.conf import settings
from django.utils import timezone

from common.models import BaseModel
from common.constants import AUTH_SOURCES, AUTH_SOURCE_PASSWORD


class UserSession(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions',
        db_index=True,
    )
    session_key = models.CharField(
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='Django session key. Null for API-key/token sessions.',
    )
    refresh_token_jti = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='JWT refresh token JTI (if SimpleJWT refresh flow is used).',
    )
    device_id = models.CharField(max_length=128, blank=True, db_index=True)
    device_name = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True)
    auth_source = models.CharField(
        max_length=32,
        choices=AUTH_SOURCES,
        default=AUTH_SOURCE_PASSWORD,
    )
    last_activity = models.DateTimeField(default=timezone.now, db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True, db_index=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_sessions',
    )
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        app_label = 'identity'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'revoked_at']),
        ]

    def __str__(self):
        state = 'REVOKED' if self.revoked_at else 'ACTIVE'
        return f'{state} {self.auth_source} session for {self.user_id} @ {self.ip_address or "?"}'

    @property
    def is_active(self):
        now = timezone.now()
        if self.revoked_at and self.revoked_at <= now:
            return False
        if self.expires_at and self.expires_at <= now:
            return False
        return True

    def touch(self, save=True):
        self.last_activity = timezone.now()
        if save:
            self.save(update_fields=['last_activity', 'updated_at'])
