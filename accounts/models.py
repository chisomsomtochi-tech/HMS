from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Administrator"
    RECEPTIONIST = "receptionist", "Receptionist"
    NURSE = "nurse", "Nurse"
    OPTOMETRIST = "optometrist", "Optometrist"
    OPHTHALMOLOGIST = "ophthalmologist", "Ophthalmologist"

    @classmethod
    def clinician_values(cls):
        return [cls.OPTOMETRIST.value, cls.OPHTHALMOLOGIST.value]


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RECEPTIONIST,
        help_text="Controls which parts of the system this account can use.",
    )
    phone = models.CharField(max_length=30, blank=True)
    must_change_password = models.BooleanField(
        default=False,
        help_text="Force a password change at the next sign-in.",
    )

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.get_full_name().strip() or self.username

    @property
    def initials(self):
        name = self.get_full_name().strip()
        if name:
            parts = name.split()
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return self.username[:2].upper()

    @property
    def is_clinician(self):
        return self.role in Role.clinician_values()

    @property
    def role_label(self):
        return self.get_role_display()

    def __str__(self):
        return f"{self.display_name} ({self.get_role_display()})"
