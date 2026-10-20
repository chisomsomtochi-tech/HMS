from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Shared audit timestamps for records that change over time."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ClinicSettings:
    """Small accessor used where settings are needed inside Python code."""

    @property
    def name(self):
        return settings.CLINIC_NAME

    @property
    def address(self):
        return settings.CLINIC_ADDRESS
