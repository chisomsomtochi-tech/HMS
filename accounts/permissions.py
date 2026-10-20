"""Role-based capabilities shared by views, templates, and navigation."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .models import Role

CLINICIAN_ROLES = Role.clinician_values()

CAPABILITIES = {
    "manage_staff": {Role.ADMIN.value},
    "view_patients": {
        Role.ADMIN.value,
        Role.RECEPTIONIST.value,
        Role.NURSE.value,
        Role.OPTOMETRIST.value,
        Role.OPHTHALMOLOGIST.value,
    },
    "manage_patients": {
        Role.ADMIN.value,
        Role.RECEPTIONIST.value,
        Role.NURSE.value,
    },
    "view_clinical": {
        Role.ADMIN.value,
        Role.NURSE.value,
        Role.OPTOMETRIST.value,
        Role.OPHTHALMOLOGIST.value,
    },
    "manage_appointments": {Role.ADMIN.value, Role.RECEPTIONIST.value},
    "check_in": {
        Role.ADMIN.value,
        Role.RECEPTIONIST.value,
        Role.NURSE.value,
        Role.OPTOMETRIST.value,
        Role.OPHTHALMOLOGIST.value,
    },
    "start_encounter": {
        Role.ADMIN.value,
        Role.NURSE.value,
        Role.OPTOMETRIST.value,
        Role.OPHTHALMOLOGIST.value,
    },
    "record_triage": {
        Role.ADMIN.value,
        Role.NURSE.value,
        Role.OPTOMETRIST.value,
        Role.OPHTHALMOLOGIST.value,
    },
    "record_exam": {
        Role.ADMIN.value,
        Role.OPTOMETRIST.value,
        Role.OPHTHALMOLOGIST.value,
    },
    "finalize_encounter": {
        Role.ADMIN.value,
        Role.OPTOMETRIST.value,
        Role.OPHTHALMOLOGIST.value,
    },
    "issue_prescription": {
        Role.ADMIN.value,
        Role.OPTOMETRIST.value,
        Role.OPHTHALMOLOGIST.value,
    },
}


def user_can(user, capability):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.role in CAPABILITIES.get(capability, set())


class CapabilityRequiredMixin(LoginRequiredMixin):
    required_capabilities = ()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            for capability in self.required_capabilities:
                if not user_can(request.user, capability):
                    raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def capability_required(*capabilities):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            for capability in capabilities:
                if not user_can(request.user, capability):
                    raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
