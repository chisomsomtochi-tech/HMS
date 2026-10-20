from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from accounts.permissions import CLINICIAN_ROLES
from appointments.models import Appointment
from appointments.models import Status as AppointmentStatus
from core.models import TimeStampedModel
from patients.models import Patient


class Encounter(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="encounters")
    appointment = models.OneToOneField(
        Appointment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="encounter",
    )
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="encounters",
        limit_choices_to={"role__in": CLINICIAN_ROLES},
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    encounter_date = models.DateTimeField(default=timezone.now)

    chief_complaint = models.TextField(blank=True)
    history = models.TextField(blank=True)
    blood_pressure = models.CharField(max_length=20, blank=True)
    pulse = models.PositiveSmallIntegerField(null=True, blank=True)
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    triage_notes = models.TextField(blank=True)
    triaged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="triage_encounters",
    )
    triaged_at = models.DateTimeField(null=True, blank=True)

    impression = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)

    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="completed_encounters",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="encounters_created",
    )

    class Meta:
        ordering = ["-encounter_date"]

    def __str__(self):
        return f"{self.patient.full_name} — {self.get_status_display()}"

    def clean(self):
        super().clean()
        if (
            self.appointment_id
            and self.patient_id
            and self.appointment.patient_id != self.patient_id
        ):
            raise ValidationError("The selected appointment belongs to another patient.")

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def has_triage(self):
        return self.triaged_at is not None

    def get_eye_exam(self):
        exam, _ = EyeExam.objects.get_or_create(encounter=self)
        return exam

    def complete(self, user):
        if not self.impression or not self.impression.strip():
            raise ValidationError("An impression is required before completing the encounter.")

        self.status = self.Status.COMPLETED
        self.completed_by = user
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_by", "completed_at", "updated_at"])

        if self.appointment_id:
            appointment = self.appointment
            appointment.status = AppointmentStatus.COMPLETED
            appointment.save(update_fields=["status", "updated_at"])

    def reopen(self):
        self.status = self.Status.DRAFT
        self.completed_by = None
        self.completed_at = None
        self.save(update_fields=["status", "completed_by", "completed_at", "updated_at"])

        if (
            self.appointment_id
            and self.appointment.status == AppointmentStatus.COMPLETED
        ):
            appointment = self.appointment
            appointment.status = AppointmentStatus.IN_PROGRESS
            appointment.save(update_fields=["status", "updated_at"])


class EyeExam(TimeStampedModel):
    class IOPMethod(models.TextChoices):
        NCT = "nct", "Non-contact tonometry"
        GAT = "gat", "Goldmann applanation"
        OTHER = "other", "Other"

    encounter = models.OneToOneField(
        Encounter, on_delete=models.CASCADE, related_name="eye_exam"
    )

    va_distance_od_unaided = models.CharField(max_length=10, blank=True)
    va_distance_os_unaided = models.CharField(max_length=10, blank=True)
    va_distance_od_corrected = models.CharField(max_length=10, blank=True)
    va_distance_os_corrected = models.CharField(max_length=10, blank=True)
    va_near_od = models.CharField(max_length=10, blank=True)
    va_near_os = models.CharField(max_length=10, blank=True)
    pinhole_od = models.CharField(max_length=10, blank=True)
    pinhole_os = models.CharField(max_length=10, blank=True)

    sph_od = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cyl_od = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    axis_od = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(180)],
    )
    add_od = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    sph_os = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cyl_os = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    axis_os = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(180)],
    )
    add_os = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    iop_od = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(80)],
    )
    iop_os = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(80)],
    )
    iop_method = models.CharField(max_length=10, choices=IOPMethod.choices, blank=True)

    anterior_segment_od = models.TextField(blank=True)
    anterior_segment_os = models.TextField(blank=True)
    fundus_od = models.TextField(blank=True)
    fundus_os = models.TextField(blank=True)

    pd = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    exam_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Eye exam for {self.encounter}"

    @property
    def has_data(self):
        tracked = (
            "va_distance_od_unaided",
            "va_distance_os_unaided",
            "va_distance_od_corrected",
            "va_distance_os_corrected",
            "va_near_od",
            "va_near_os",
            "pinhole_od",
            "pinhole_os",
            "sph_od",
            "cyl_od",
            "axis_od",
            "add_od",
            "sph_os",
            "cyl_os",
            "axis_os",
            "add_os",
            "iop_od",
            "iop_os",
            "iop_method",
            "anterior_segment_od",
            "anterior_segment_os",
            "fundus_od",
            "fundus_os",
            "pd",
            "exam_notes",
        )
        return any(getattr(self, name) not in (None, "") for name in tracked)


class Prescription(TimeStampedModel):
    class LensType(models.TextChoices):
        SINGLE_VISION = "single_vision", "Single vision"
        BIFOCAL = "bifocal", "Bifocal"
        PROGRESSIVE = "progressive", "Progressive"

    encounter = models.OneToOneField(
        Encounter, on_delete=models.CASCADE, related_name="prescription"
    )

    sph_od = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cyl_od = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    axis_od = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(180)],
    )
    add_od = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    sph_os = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cyl_os = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    axis_os = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(180)],
    )
    add_os = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    pd = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    lens_type = models.CharField(max_length=20, choices=LensType.choices, blank=True)
    notes = models.TextField(blank=True)

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="prescriptions_issued",
    )
    issued_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Prescription for {self.encounter.patient.full_name}"
