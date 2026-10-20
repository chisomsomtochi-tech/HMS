from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Clinic access", {"fields": ("role", "phone", "must_change_password")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Clinic access", {"fields": ("role", "phone", "must_change_password")}),
    )
    list_display = ("username", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter = BaseUserAdmin.list_filter + ("role",)
    search_fields = BaseUserAdmin.search_fields + ("phone",)
