import uuid
from django.db import models


class UUIDModel(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text='Globally stable identifier for sync across cloud/school-server.',
    )

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class BaseModel(UUIDModel, TimestampedModel):
    class Meta:
        abstract = True
