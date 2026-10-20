from django import forms
from django.utils import timezone

from core.forms import TailwindFormMixin

from .models import Patient


class PatientForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Patient
        fields = (
            "first_name",
            "last_name",
            "other_name",
            "date_of_birth",
            "sex",
            "phone",
            "email",
            "address",
            "city",
            "state",
            "occupation",
            "nok_name",
            "nok_phone",
            "nok_relationship",
            "alert_note",
            "notes",
        )
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "address": forms.TextInput(attrs={"placeholder": "Street address"}),
            "alert_note": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "e.g. Penicillin allergy; diabetic on insulin",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date_of_birth"].input_formats = ["%Y-%m-%d"]
        self.fields["date_of_birth"].required = True
        self.fields["phone"].required = True
        self.fields["first_name"].widget.attrs["placeholder"] = "First name"
        self.fields["last_name"].widget.attrs["placeholder"] = "Surname"
        self.fields["other_name"].widget.attrs["placeholder"] = "Middle name (optional)"
        self.fields["phone"].widget.attrs["placeholder"] = "+234 800 000 0000"
        self.fields["email"].widget.attrs["placeholder"] = "name@example.com"
        self.fields["nok_name"].widget.attrs["placeholder"] = "Full name"
        self.fields["nok_phone"].widget.attrs["placeholder"] = "+234 800 000 0000"
        self.fields["nok_relationship"].widget.attrs["placeholder"] = "e.g. Spouse, daughter"

    def clean_date_of_birth(self):
        value = self.cleaned_data["date_of_birth"]
        if value and value > timezone.localdate():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return value
