from django import forms

from accounts.models import User
from accounts.permissions import CLINICIAN_ROLES
from core.forms import TailwindFormMixin
from patients.models import Patient

from .models import Encounter, EyeExam, Prescription

VA_PLACEHOLDER = "e.g. 6/6"


class EncounterStartForm(TailwindFormMixin, forms.Form):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        widget=forms.HiddenInput,
    )
    clinician = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Attending clinician",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["clinician"].queryset = User.objects.filter(
            role__in=CLINICIAN_ROLES, is_active=True
        ).order_by("first_name", "last_name")
        self.fields["clinician"].help_text = "The optometrist or ophthalmologist who will see the patient."


class TriageForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Encounter
        fields = (
            "chief_complaint",
            "history",
            "blood_pressure",
            "pulse",
            "temperature_c",
            "weight_kg",
            "height_cm",
            "triage_notes",
        )
        widgets = {
            "chief_complaint": forms.Textarea(
                attrs={"rows": 3, "placeholder": "e.g. Blurred vision in the right eye for 2 weeks"}
            ),
            "history": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Relevant ocular and medical history"}
            ),
            "blood_pressure": forms.TextInput(attrs={"placeholder": "e.g. 120/80"}),
            "pulse": forms.NumberInput(attrs={"min": 20, "max": 250, "placeholder": "bpm"}),
            "temperature_c": forms.NumberInput(
                attrs={"step": "0.1", "min": 30, "max": 45, "placeholder": "°C"}
            ),
            "weight_kg": forms.NumberInput(
                attrs={"step": "0.1", "min": 1, "max": 400, "placeholder": "kg"}
            ),
            "height_cm": forms.NumberInput(
                attrs={"step": "0.1", "min": 30, "max": 260, "placeholder": "cm"}
            ),
            "triage_notes": forms.Textarea(attrs={"rows": 3}),
        }


class EncounterAssessmentForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Encounter
        fields = ("impression", "plan", "follow_up_date")
        widgets = {
            "impression": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Clinical impression and diagnoses"}
            ),
            "plan": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Treatment, advice, investigations, and review"}
            ),
            "follow_up_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["follow_up_date"].input_formats = ["%Y-%m-%d"]


class EyeExamForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = EyeExam
        fields = (
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
        widgets = {
            "va_distance_od_unaided": forms.TextInput(attrs={"placeholder": VA_PLACEHOLDER}),
            "va_distance_os_unaided": forms.TextInput(attrs={"placeholder": VA_PLACEHOLDER}),
            "va_distance_od_corrected": forms.TextInput(attrs={"placeholder": VA_PLACEHOLDER}),
            "va_distance_os_corrected": forms.TextInput(attrs={"placeholder": VA_PLACEHOLDER}),
            "va_near_od": forms.TextInput(attrs={"placeholder": "e.g. N6"}),
            "va_near_os": forms.TextInput(attrs={"placeholder": "e.g. N6"}),
            "pinhole_od": forms.TextInput(attrs={"placeholder": VA_PLACEHOLDER}),
            "pinhole_os": forms.TextInput(attrs={"placeholder": VA_PLACEHOLDER}),
            "sph_od": forms.NumberInput(attrs={"step": "0.25"}),
            "cyl_od": forms.NumberInput(attrs={"step": "0.25"}),
            "axis_od": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 180}),
            "add_od": forms.NumberInput(attrs={"step": "0.25"}),
            "sph_os": forms.NumberInput(attrs={"step": "0.25"}),
            "cyl_os": forms.NumberInput(attrs={"step": "0.25"}),
            "axis_os": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 180}),
            "add_os": forms.NumberInput(attrs={"step": "0.25"}),
            "iop_od": forms.NumberInput(attrs={"step": "0.1", "min": 0, "max": 80}),
            "iop_os": forms.NumberInput(attrs={"step": "0.1", "min": 0, "max": 80}),
            "anterior_segment_od": forms.Textarea(attrs={"rows": 2}),
            "anterior_segment_os": forms.Textarea(attrs={"rows": 2}),
            "fundus_od": forms.Textarea(attrs={"rows": 2}),
            "fundus_os": forms.Textarea(attrs={"rows": 2}),
            "pd": forms.NumberInput(attrs={"step": "0.5", "placeholder": "mm"}),
            "exam_notes": forms.Textarea(attrs={"rows": 3}),
        }

    ARIA_LABELS = {
        "va_distance_od_unaided": "Right eye distance visual acuity, unaided",
        "va_distance_os_unaided": "Left eye distance visual acuity, unaided",
        "va_distance_od_corrected": "Right eye distance visual acuity, corrected",
        "va_distance_os_corrected": "Left eye distance visual acuity, corrected",
        "va_near_od": "Right eye near visual acuity",
        "va_near_os": "Left eye near visual acuity",
        "pinhole_od": "Right eye pinhole visual acuity",
        "pinhole_os": "Left eye pinhole visual acuity",
        "sph_od": "Right eye sphere",
        "cyl_od": "Right eye cylinder",
        "axis_od": "Right eye axis",
        "add_od": "Right eye near addition",
        "sph_os": "Left eye sphere",
        "cyl_os": "Left eye cylinder",
        "axis_os": "Left eye axis",
        "add_os": "Left eye near addition",
        "iop_od": "Right eye intraocular pressure",
        "iop_os": "Left eye intraocular pressure",
        "anterior_segment_od": "Right eye anterior segment",
        "anterior_segment_os": "Left eye anterior segment",
        "fundus_od": "Right eye fundus",
        "fundus_os": "Left eye fundus",
        "pd": "Pupillary distance",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, label in self.ARIA_LABELS.items():
            self.fields[name].widget.attrs["aria-label"] = label


class PrescriptionForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Prescription
        fields = (
            "sph_od",
            "cyl_od",
            "axis_od",
            "add_od",
            "sph_os",
            "cyl_os",
            "axis_os",
            "add_os",
            "pd",
            "lens_type",
            "notes",
        )
        widgets = {
            "sph_od": forms.NumberInput(attrs={"step": "0.25"}),
            "cyl_od": forms.NumberInput(attrs={"step": "0.25"}),
            "axis_od": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 180}),
            "add_od": forms.NumberInput(attrs={"step": "0.25"}),
            "sph_os": forms.NumberInput(attrs={"step": "0.25"}),
            "cyl_os": forms.NumberInput(attrs={"step": "0.25"}),
            "axis_os": forms.NumberInput(attrs={"step": 1, "min": 0, "max": 180}),
            "add_os": forms.NumberInput(attrs={"step": "0.25"}),
            "pd": forms.NumberInput(attrs={"step": "0.5", "placeholder": "mm"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
