from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel


class Role(BaseModel):
    """
    Configurable role representing a collection of permissions and their scopes.
    Schools can create custom roles or configure existing ones.
    """
    code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_('Machine-readable role code, e.g. "TEACHER", "BURSAR", "SUPER_ADMIN".'),
    )
    name = models.CharField(
        max_length=100,
        help_text=_('Human-friendly role name, e.g. "Senior Teacher".'),
    )
    description = models.TextField(
        blank=True,
        help_text=_('Description of the role responsibility within the school.'),
    )
    is_system = models.BooleanField(
        default=False,
        help_text=_('System roles (e.g. Super Admin, School Admin) cannot be deleted.'),
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_('Inactive roles do not grant permissions to assigned users.'),
    )
    permissions = models.ManyToManyField(
        'permissions.Permission',
        through='permissions.RolePermission',
        related_name='roles',
        blank=True,
    )

    class Meta:
        app_label = 'permissions'
        ordering = ['name']
        verbose_name = _('role')
        verbose_name_plural = _('roles')

    def __str__(self):
        return f'{self.name} [{self.code}]'
