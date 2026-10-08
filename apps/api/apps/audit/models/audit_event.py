from django.db import models
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from common.constants import AuditAction


class AuditEvent(BaseModel):
    """
    Append-only audit trail recording identity, authentication, authorization,
    and security events. Once written, events cannot be updated or deleted.
    """
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
        db_index=True,
        help_text=_('User who performed the action, or null for anonymous/system.'),
    )
    actor_email = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text=_('Snapshot of user email or identifier at time of event.'),
    )
    action = models.CharField(
        max_length=64,
        choices=AuditAction.CHOICES,
        db_index=True,
    )
    resource_type = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text=_('Target resource type, e.g. "User", "Role", "Session".'),
    )
    resource_id = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text=_('Target resource primary key or UUID.'),
    )
    status = models.CharField(
        max_length=32,
        choices=(
            ('SUCCESS', _('Success')),
            ('FAILURE', _('Failure')),
            ('DENIED', _('Denied')),
        ),
        default='SUCCESS',
        db_index=True,
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        db_index=True,
    )
    user_agent = models.TextField(blank=True)
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Sanitized event metadata. Sensitive values must be scrubbed.'),
    )

    class Meta:
        app_label = 'audit'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
        verbose_name = _('audit event')
        verbose_name_plural = _('audit events')

    def __str__(self):
        actor_name = self.actor_email or (f'User<{self.actor_id}>' if self.actor_id else 'Anonymous/System')
        return f'[{self.created_at:%Y-%m-%d %H:%M:%S}] {actor_name} -> {self.action} ({self.status})'

    def save(self, *args, **kwargs):
        # Prevent updating existing audit events
        if self.pk and not kwargs.get('force_insert', False):
            if AuditEvent.objects.filter(pk=self.pk).exists():
                raise PermissionDenied('Audit records are immutable and cannot be updated.')
        # Snapshot actor email if available
        if self.actor and not self.actor_email:
            self.actor_email = getattr(self.actor, 'email', '') or getattr(self.actor, 'username', '') or str(self.actor.pk)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied('Audit records cannot be deleted. History preservation is strictly enforced.')
