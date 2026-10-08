from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class RoleAssignment(BaseModel):
    """
    Assigns a Role to a User. A user may hold multiple roles simultaneously.
    Supports expiration dates and contextual scope constraints.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='roles_assigned',
        db_index=True,
    )
    role = models.ForeignKey(
        'permissions.Role',
        on_delete=models.CASCADE,
        related_name='assignments',
        db_index=True,
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roles_granted',
    )
    assigned_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Optional timestamp when this role assignment automatically expires.'),
    )
    scope_override = models.ForeignKey(
        'permissions.PermissionScope',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignment_overrides',
        help_text=_('Optional scope override applied across this role assignment.'),
    )
    scope_context = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Contextual scope payload (e.g. {"assigned_class_ids": [1, 2]}).'),
    )

    class Meta:
        app_label = 'permissions'
        unique_together = ('user', 'role')
        ordering = ['-assigned_at']
        verbose_name = _('role assignment')
        verbose_name_plural = _('role assignments')

    def __str__(self):
        expiry = f' (expires {self.expires_at:%Y-%m-%d})' if self.expires_at else ''
        return f'{self.user} -> {self.role.code}{expiry}'

    @property
    def is_active(self):
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return self.role.is_active
