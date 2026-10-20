from datetime import timedelta

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.permissions import CLINICIAN_ROLES, capability_required, user_can
from encounters.models import Encounter
from patients.models import Patient

from .forms import AppointmentForm
from .models import Appointment, Status


@capability_required("view_patients")
def appointment_list(request):
    selected_date = parse_date(request.GET.get("date", "")) or timezone.localdate()
    selected_status = request.GET.get("status", "")
    selected_clinician = request.GET.get("clinician", "")

    appointments = Appointment.objects.select_related("patient", "clinician").filter(
        scheduled_at__date=selected_date
    )
    if selected_status in Status.values:
        appointments = appointments.filter(status=selected_status)
    if selected_clinician.isdigit():
        appointments = appointments.filter(clinician_id=selected_clinician)
    appointments = appointments.order_by("scheduled_at")

    day_appointments = Appointment.objects.filter(scheduled_at__date=selected_date)
    counts = {
        "total": day_appointments.exclude(status=Status.CANCELLED).count(),
        "scheduled": day_appointments.filter(status=Status.SCHEDULED).count(),
        "in_clinic": day_appointments.filter(
            status__in=[Status.CHECKED_IN, Status.IN_PROGRESS]
        ).count(),
        "completed": day_appointments.filter(status=Status.COMPLETED).count(),
    }

    clinicians = User.objects.filter(
        role__in=CLINICIAN_ROLES, is_active=True
    ).order_by("first_name", "last_name")

    return render(
        request,
        "appointments/appointment_list.html",
        {
            "appointments": appointments,
            "selected_date": selected_date,
            "prev_date": selected_date - timedelta(days=1),
            "next_date": selected_date + timedelta(days=1),
            "is_today": selected_date == timezone.localdate(),
            "selected_status": selected_status,
            "selected_clinician": selected_clinician,
            "statuses": Status.choices,
            "clinicians": clinicians,
            "counts": counts,
            "can_manage_appointments": user_can(request.user, "manage_appointments"),
        },
    )


@capability_required("manage_appointments")
def appointment_create(request):
    patient_id = request.POST.get("patient") or request.GET.get("patient")
    patient = get_object_or_404(Patient, pk=patient_id) if patient_id else None

    initial = {"patient": patient} if patient else {}
    form = AppointmentForm(request.POST or None, initial=initial)

    if request.method == "POST":
        if patient is None:
            messages.error(request, "Select a patient before booking an appointment.")
        elif form.is_valid():
            appointment = form.save(commit=False)
            appointment.created_by = request.user
            appointment.save()
            messages.success(
                request,
                f"Appointment booked for {appointment.patient.full_name} on "
                f"{timezone.localtime(appointment.scheduled_at):%a %d %b, %H:%M}.",
            )
            return redirect("appointments:detail", pk=appointment.pk)

    return render(
        request,
        "appointments/appointment_form.html",
        {"form": form, "patient": patient, "is_edit": False},
    )


@capability_required("manage_appointments")
def appointment_edit(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.status in (Status.COMPLETED, Status.CANCELLED, Status.NO_SHOW):
        messages.error(request, "This appointment can no longer be rescheduled.")
        return redirect("appointments:detail", pk=appointment.pk)

    form = AppointmentForm(request.POST or None, instance=appointment)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Appointment rescheduled.")
        return redirect("appointments:detail", pk=appointment.pk)

    return render(
        request,
        "appointments/appointment_form.html",
        {
            "form": form,
            "patient": appointment.patient,
            "is_edit": True,
            "appointment": appointment,
        },
    )


@capability_required("view_patients")
def appointment_detail(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "clinician"), pk=pk
    )
    encounter = getattr(appointment, "encounter", None)

    return render(
        request,
        "appointments/appointment_detail.html",
        {
            "appointment": appointment,
            "patient": appointment.patient,
            "encounter": encounter,
            "can_check_in": user_can(request.user, "check_in")
            and appointment.status == Status.SCHEDULED,
            "can_mark_no_show": user_can(request.user, "check_in")
            and appointment.status == Status.SCHEDULED,
            "can_start_encounter": user_can(request.user, "start_encounter")
            and appointment.status in (Status.SCHEDULED, Status.CHECKED_IN)
            and encounter is None,
            "can_cancel": user_can(request.user, "manage_appointments")
            and appointment.status in (Status.SCHEDULED, Status.CHECKED_IN),
            "can_edit": user_can(request.user, "manage_appointments")
            and appointment.status in (Status.SCHEDULED, Status.CHECKED_IN),
        },
    )


@capability_required("check_in")
@require_POST
def appointment_check_in(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.check_in():
        messages.success(request, f"{appointment.patient.full_name} checked in.")
    else:
        messages.error(request, "Only scheduled appointments can be checked in.")
    return redirect("appointments:detail", pk=appointment.pk)


@capability_required("manage_appointments")
@require_POST
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.cancel(request.POST.get("cancelled_reason", "").strip()):
        messages.success(request, "Appointment cancelled. The slot is now free.")
    else:
        messages.error(request, "This appointment cannot be cancelled at this stage.")
    return redirect("appointments:detail", pk=appointment.pk)


@capability_required("check_in")
@require_POST
def appointment_no_show(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.mark_no_show():
        messages.success(request, "Appointment marked as a no-show.")
    else:
        messages.error(request, "Only scheduled appointments can be marked as a no-show.")
    return redirect("appointments:detail", pk=appointment.pk)


@capability_required("start_encounter")
@require_POST
def appointment_start_encounter(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "clinician"), pk=pk
    )

    if appointment.status in (Status.CANCELLED, Status.NO_SHOW, Status.COMPLETED):
        messages.error(request, "This appointment cannot be started.")
        return redirect("appointments:detail", pk=appointment.pk)

    encounter = getattr(appointment, "encounter", None)
    if encounter:
        return redirect("encounters:detail", pk=encounter.pk)

    if appointment.status == Status.SCHEDULED:
        appointment.checked_in_at = timezone.now()
    appointment.status = Status.IN_PROGRESS
    appointment.save(update_fields=["status", "checked_in_at", "updated_at"])

    encounter = Encounter.objects.create(
        patient=appointment.patient,
        appointment=appointment,
        clinician=appointment.clinician,
        created_by=request.user,
    )
    messages.success(request, "Encounter opened. Start with triage or the eye exam.")
    return redirect("encounters:detail", pk=encounter.pk)
