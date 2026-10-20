from django.contrib import admin

from .models import Encounter, EyeExam, Prescription


class EyeExamInline(admin.StackedInline):
    model = EyeExam
    extra = 0


class PrescriptionInline(admin.StackedInline):
    model = Prescription
    extra = 0


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ("patient", "clinician", "encounter_date", "status", "completed_at")
    list_filter = ("status", "clinician")
    search_fields = ("patient__first_name", "patient__last_name", "patient__mrn")
    autocomplete_fields = ("patient", "clinician")
    date_hierarchy = "encounter_date"
    inlines = [EyeExamInline, PrescriptionInline]


@admin.register(EyeExam)
class EyeExamAdmin(admin.ModelAdmin):
    list_display = ("encounter", "iop_od", "iop_os", "iop_method")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("encounter", "lens_type", "issued_by", "issued_at")
