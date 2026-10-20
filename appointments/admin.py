from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("scheduled_at", "patient", "clinician", "appointment_type", "status")
    list_filter = ("status", "appointment_type", "clinician")
    search_fields = ("patient__first_name", "patient__last_name", "patient__mrn")
    autocomplete_fields = ("patient", "clinician")
    date_hierarchy = "scheduled_at"
