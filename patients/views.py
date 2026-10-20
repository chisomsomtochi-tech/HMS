from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from accounts.permissions import capability_required, user_can

from .forms import PatientForm
from .models import Patient


@capability_required("view_patients")
def patient_list(request):
    query = request.GET.get("q", "").strip()
    patients = Patient.objects.search(query)
    paginator = Paginator(patients, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "patients/patient_list.html",
        {
            "page_obj": page_obj,
            "patients": page_obj.object_list,
            "query": query,
            "total": paginator.count,
            "can_manage_patients": user_can(request.user, "manage_patients"),
        },
    )


@capability_required("manage_patients")
def patient_create(request):
    form = PatientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        patient = form.save(commit=False)
        patient.created_by = request.user
        patient.save()
        messages.success(
            request,
            f"{patient.full_name} was registered with medical record number {patient.mrn}.",
        )
        return redirect("patients:detail", pk=patient.pk)

    return render(
        request,
        "patients/patient_form.html",
        {"form": form, "is_create": True},
    )


@capability_required("view_patients")
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    appointments = (
        patient.appointments.select_related("clinician").order_by("-scheduled_at")[:15]
    )
    encounters = []
    if user_can(request.user, "view_clinical"):
        encounters = (
            patient.encounters.select_related("clinician")
            .prefetch_related("prescription")
            .order_by("-encounter_date")[:15]
        )

    return render(
        request,
        "patients/patient_detail.html",
        {
            "patient": patient,
            "appointments": appointments,
            "encounters": encounters,
            "can_manage_patients": user_can(request.user, "manage_patients"),
            "can_book_appointments": user_can(request.user, "manage_appointments"),
            "can_view_clinical": user_can(request.user, "view_clinical"),
            "can_start_encounter": user_can(request.user, "start_encounter"),
        },
    )


@capability_required("manage_patients")
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    form = PatientForm(request.POST or None, instance=patient)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{patient.full_name}'s details were updated.")
        return redirect("patients:detail", pk=patient.pk)

    return render(
        request,
        "patients/patient_form.html",
        {"form": form, "patient": patient, "is_create": False},
    )


@capability_required("view_patients")
def patient_search(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    mode = request.GET.get("mode", "")
    patients = Patient.objects.search(query)[:8] if len(query) >= 2 else []
    return render(
        request,
        "patients/_search_results.html",
        {"patients": patients, "query": query, "mode": mode},
    )


@capability_required("manage_patients")
def patient_duplicate_check(request: HttpRequest) -> HttpResponse:
    first_name = request.GET.get("first_name", "").strip()
    last_name = request.GET.get("last_name", "").strip()
    phone = request.GET.get("phone", "").strip()
    date_of_birth = parse_date(request.GET.get("date_of_birth", "").strip())

    matches = Patient.objects.none()
    if len(phone) >= 7:
        matches = matches | Patient.objects.filter(phone__icontains=phone)
    if len(first_name) >= 2 and len(last_name) >= 2:
        name_query = Q(first_name__icontains=first_name) & Q(last_name__icontains=last_name)
        if date_of_birth:
            name_query &= Q(date_of_birth=date_of_birth)
        matches = matches | Patient.objects.filter(name_query)

    matches = matches.distinct()[:5] if (phone or first_name or last_name) else []
    return render(
        request,
        "patients/_duplicate_warning.html",
        {"matches": matches},
    )
