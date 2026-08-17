from djrm.db import models


class LogEntry(models.Model):
    action = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = "admin"
