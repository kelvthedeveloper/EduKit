from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from common.constants import Action


class Permission(BaseModel):
    """
    Granular permission combining Resource + Action.
    Example: codename="students.view", resource="students", action="VIEW".
    """
    codename = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_('Machine-readable stable identifier, e.g. "students.view".'),
    )
    name = models.CharField(
        max_length=150,
        help_text=_('Human-readable title, e.g. "View Student Profiles".'),
    )
    resource = models.CharField(
        max_length=64,
        db_index=True,
        help_text=_('Resource identifier, e.g. "students", "results", "finance".'),
    )
    action = models.CharField(
        max_length=32,
        choices=Action.CHOICES,
        db_index=True,
        help_text=_('Action verb on the resource.'),
    )
    description = models.TextField(
        blank=True,
        help_text=_('Detailed explanation of capabilities granted.'),
    )
    is_system = models.BooleanField(
        default=True,
        help_text=_('True for standard built-in system permissions.'),
    )

    class Meta:
        app_label = 'permissions'
        ordering = ['resource', 'action']
        indexes = [
            models.Index(fields=['resource', 'action']),
        ]
        verbose_name = _('permission')
        verbose_name_plural = _('permissions')

    def __str__(self):
        return f'{self.codename} ({self.name})'

    def save(self, *args, **kwargs):
        if not self.codename and self.resource and self.action:
            self.codename = f'{self.resource.lower()}.{self.action.lower()}'
        super().save(*args, **kwargs)
