from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from accounts.permissions import CLINICIAN_ROLES
from core.models import TimeStampedModel
from patients.models import Patient


class AppointmentType(models.TextChoices):
    NEW = "new", "New consultation"
    FOLLOW_UP = "follow_up", "Follow-up"
    REFRACTION = "refraction", "Refraction"
    GLAUCOMA = "glaucoma", "Glaucoma review"
    RETINA = "retina", "Retina"
    OTHER = "other", "Other"


class Status(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    CHECKED_IN = "checked_in", "Checked in"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No show"


ACTIVE_STATUSES = (Status.SCHEDULED, Status.CHECKED_IN, Status.IN_PROGRESS)


class Appointment(TimeStampedModel):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="appointments")
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments",
        limit_choices_to={"role__in": CLINICIAN_ROLES},
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(
        default=30,
        validators=[MinValueValidator(10), MaxValueValidator(240)],
    )
    appointment_type = models.CharField(
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.NEW,
    )
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments_created",
    )

    class Meta:
        ordering = ["scheduled_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["clinician", "scheduled_at"],
                condition=Q(status__in=ACTIVE_STATUSES),
                name="unique_active_clinician_slot",
            )
        ]

    def __str__(self):
        return f"{self.patient.full_name} with {self.clinician.display_name}"

    def clean(self):
        super().clean()
        if (
            self.status not in ACTIVE_STATUSES
            or not self.clinician_id
            or not self.scheduled_at
        ):
            return

        start = self.scheduled_at
        end = start + timedelta(minutes=self.duration_minutes or 30)
        same_day = Appointment.objects.filter(
            clinician_id=self.clinician_id,
            status__in=ACTIVE_STATUSES,
            scheduled_at__date=timezone.localtime(start).date(),
        ).exclude(pk=self.pk)

        for other in same_day:
            other_start = other.scheduled_at
            other_end = other_start + timedelta(minutes=other.duration_minutes or 30)
            if start < other_end and other_start < end:
                local_time = timezone.localtime(other_start).strftime("%H:%M")
                raise ValidationError(
                    {
                        "scheduled_at": (
                            f"{other.clinician.display_name} already has an appointment "
                            f"at {local_time}. Choose another time or clinician."
                        )
                    }
                )

    @property
    def is_active(self):
        return self.status in ACTIVE_STATUSES

    @property
    def ends_at(self):
        return self.scheduled_at + timedelta(minutes=self.duration_minutes or 30)

    @property
    def is_today(self):
        return timezone.localtime(self.scheduled_at).date() == timezone.localdate()

    def check_in(self):
        if self.status != Status.SCHEDULED:
            return False
        self.status = Status.CHECKED_IN
        self.checked_in_at = timezone.now()
        self.save(update_fields=["status", "checked_in_at", "updated_at"])
        return True

    def cancel(self, reason=""):
        if self.status not in (Status.SCHEDULED, Status.CHECKED_IN):
            return False
        self.status = Status.CANCELLED
        self.cancelled_reason = reason
        self.save(update_fields=["status", "cancelled_reason", "updated_at"])
        return True

    def mark_no_show(self):
        if self.status != Status.SCHEDULED:
            return False
        self.status = Status.NO_SHOW
        self.save(update_fields=["status", "updated_at"])
        return True
