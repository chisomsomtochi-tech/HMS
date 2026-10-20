from django import forms
from django.utils import timezone

from accounts.models import User
from accounts.permissions import CLINICIAN_ROLES
from core.forms import TailwindFormMixin

from .models import Appointment


class AppointmentForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Appointment
        fields = (
            "patient",
            "clinician",
            "scheduled_at",
            "duration_minutes",
            "appointment_type",
            "reason",
            "notes",
        )
        widgets = {
            "scheduled_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "duration_minutes": forms.NumberInput(attrs={"min": 10, "max": 240, "step": 5}),
            "reason": forms.Textarea(
                attrs={"rows": 3, "placeholder": "e.g. Blurred vision in the left eye"}
            ),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].widget = forms.HiddenInput()
        self.fields["clinician"].queryset = User.objects.filter(
            role__in=CLINICIAN_ROLES, is_active=True
        ).order_by("first_name", "last_name")
        self.fields["scheduled_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]
        self.fields["scheduled_at"].help_text = "Clinic local time."
        self.fields["duration_minutes"].initial = 30

        if self.instance.pk and self.instance.scheduled_at:
            self.initial["scheduled_at"] = timezone.localtime(self.instance.scheduled_at)
