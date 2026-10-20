from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.models import TimeStampedModel


class Sex(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"
    OTHER = "O", "Other"


class PatientQuerySet(models.QuerySet):
    def search(self, query):
        query = (query or "").strip()
        if not query:
            return self
        return self.filter(
            Q(mrn__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
        )


class Patient(TimeStampedModel):
    mrn = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        help_text="Medical record number, assigned automatically.",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=Sex.choices)
    phone = models.CharField(max_length=30, db_index=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=100, blank=True)

    nok_name = models.CharField("next of kin", max_length=150, blank=True)
    nok_phone = models.CharField("next of kin phone", max_length=30, blank=True)
    nok_relationship = models.CharField("relationship", max_length=60, blank=True)

    alert_note = models.TextField(
        blank=True,
        help_text="Allergies, chronic conditions, or other safety alerts.",
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="patients_registered",
    )

    objects = PatientQuerySet.as_manager()

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.full_name} ({self.mrn or 'new patient'})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.mrn:
            self.mrn = f"MRN-{timezone.localdate():%Y}-{self.pk:05d}"
            type(self).objects.filter(pk=self.pk).update(mrn=self.mrn)

    @property
    def full_name(self):
        return " ".join(filter(None, [self.first_name, self.other_name, self.last_name]))

    @property
    def initials(self):
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def age_display(self):
        age = self.age
        return f"{age} yrs" if age is not None else "Age not recorded"

    @property
    def has_alert(self):
        return bool(self.alert_note and self.alert_note.strip())
