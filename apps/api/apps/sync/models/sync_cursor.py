from django.db import models


class SyncCursor(models.Model):
    class Meta:
        app_label = 'sync'
