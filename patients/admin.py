from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("mrn", "full_name", "sex", "date_of_birth", "phone", "is_active", "created_at")
    list_filter = ("sex", "is_active")
    search_fields = ("mrn", "first_name", "last_name", "phone", "email")
    readonly_fields = ("mrn", "created_at", "updated_at")
    date_hierarchy = "created_at"
