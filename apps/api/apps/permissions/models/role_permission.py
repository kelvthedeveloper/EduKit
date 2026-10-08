from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class RolePermission(BaseModel):
    """
    Associates a Permission to a Role, configured with a specific PermissionScope.
    Example: Role 'Teacher' has permission 'students.view' with scope 'ASSIGNED_CLASSES'.
    """
    role = models.ForeignKey(
        'permissions.Role',
        on_delete=models.CASCADE,
        related_name='role_permissions',
        db_index=True,
    )
    permission = models.ForeignKey(
        'permissions.Permission',
        on_delete=models.CASCADE,
        related_name='role_permissions',
        db_index=True,
    )
    scope = models.ForeignKey(
        'permissions.PermissionScope',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='role_permissions',
        help_text=_('Boundary scope for this permission. If null, treated as GLOBAL.'),
    )
    scope_parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Optional JSON parameters for parameterized scopes (e.g. {"class_ids": [...]}).'),
    )

    class Meta:
        app_label = 'permissions'
        unique_together = ('role', 'permission')
        verbose_name = _('role permission')
        verbose_name_plural = _('role permissions')

    def __str__(self):
        scope_str = self.scope.code if self.scope else 'GLOBAL'
        return f'{self.role.code} -> {self.permission.codename} [{scope_str}]'
