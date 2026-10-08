from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from common.constants import Scope


class PermissionScope(BaseModel):
    """
    Defines the boundaries / scope within which an action can be executed on a resource.
    Examples: GLOBAL, ASSIGNED_CLASSES, ASSIGNED_SUBJECTS, DEPARTMENT, SELECTED_CLASSES, OWN_CHILDREN, SELF.
    """
    code = models.CharField(
        max_length=64,
        unique=True,
        choices=Scope.CHOICES,
        db_index=True,
        help_text=_('Machine-readable scope identifier.'),
    )
    name = models.CharField(
        max_length=100,
        help_text=_('Human-friendly display name for the scope.'),
    )
    description = models.TextField(
        blank=True,
        help_text=_('Explanation of boundary rules for this scope.'),
    )
    is_system = models.BooleanField(
        default=True,
        help_text=_('Indicates whether this is a core built-in scope.'),
    )

    class Meta:
        app_label = 'permissions'
        ordering = ['code']
        verbose_name = _('permission scope')
        verbose_name_plural = _('permission scopes')

    def __str__(self):
        return f'{self.name} ({self.code})'
