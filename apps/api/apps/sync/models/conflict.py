from django.db import models


class Conflict(models.Model):
    class Meta:
        app_label = 'sync'
