from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import user_can
from appointments.models import Appointment, Status as AppointmentStatus
from encounters.models import Encounter
from patients.models import Patient


def healthz(request):
    """Unauthenticated liveness probe for container orchestration."""
    return HttpResponse("ok", content_type="text/plain")


@login_required
def dashboard(request):
    today = timezone.localdate()
    hour = timezone.localtime().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    appointments_today = Appointment.objects.filter(
        scheduled_at__date=today
    ).select_related("patient", "clinician")

    if request.user.is_clinician:
        schedule = appointments_today.filter(clinician=request.user)
    else:
        schedule = appointments_today
    schedule = schedule.exclude(status=AppointmentStatus.CANCELLED).order_by("scheduled_at")

    stats = {
        "total_patients": Patient.objects.filter(is_active=True).count(),
        "new_patients_today": Patient.objects.filter(created_at__date=today).count(),
        "appointments_today": appointments_today.exclude(status=AppointmentStatus.CANCELLED).count(),
        "scheduled_today": appointments_today.filter(status=AppointmentStatus.SCHEDULED).count(),
        "in_clinic": appointments_today.filter(
            status__in=[AppointmentStatus.CHECKED_IN, AppointmentStatus.IN_PROGRESS]
        ).count(),
        "completed_today": appointments_today.filter(status=AppointmentStatus.COMPLETED).count(),
        "encounters_today": Encounter.objects.filter(encounter_date__date=today).count(),
    }

    follow_ups = []
    if user_can(request.user, "view_clinical"):
        follow_ups = (
            Encounter.objects.filter(
                status=Encounter.Status.COMPLETED,
                follow_up_date__gte=today,
                follow_up_date__lte=today + timedelta(days=14),
            )
            .select_related("patient", "clinician")
            .order_by("follow_up_date")[:6]
        )

    recent_patients = []
    if user_can(request.user, "view_patients"):
        recent_patients = Patient.objects.order_by("-created_at")[:5]

    return render(
        request,
        "core/dashboard.html",
        {
            "greeting": greeting,
            "today": today,
            "stats": stats,
            "schedule": schedule,
            "follow_ups": follow_ups,
            "recent_patients": recent_patients,
            "can_manage_patients": user_can(request.user, "manage_patients"),
            "can_manage_appointments": user_can(request.user, "manage_appointments"),
            "can_start_encounter": user_can(request.user, "start_encounter"),
        },
    )
