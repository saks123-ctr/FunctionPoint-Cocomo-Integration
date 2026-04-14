from django.conf import settings
from django.db import models


class Project(models.Model):
    """Saved estimation snapshot, owned by a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="estimator_projects",
    )
    name = models.CharField(max_length=255)
    inputs = models.JSONField()
    outputs = models.JSONField(default=dict, blank=True)
    fp = models.FloatField()
    effort_pm = models.FloatField()
    tdev_months = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.name
