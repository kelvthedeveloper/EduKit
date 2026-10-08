from django.db import models


class SyncBatch(models.Model):
    class Meta:
        app_label = 'sync'
