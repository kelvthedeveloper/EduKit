from django.db import models


class SyncEvent(models.Model):
    class Meta:
        app_label = 'sync'
