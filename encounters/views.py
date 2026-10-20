from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import Role
from accounts.permissions import capability_required, user_can
from patients.models import Patient

from .forms import (
    EncounterAssessmentForm,
    EncounterStartForm,
    EyeExamForm,
    PrescriptionForm,
    TriageForm,
)
from .models import Encounter, EyeExam, Prescription


@capability_required("view_clinical")
def encounter_list(request):
    selected_status = request.GET.get("status", "")
    encounters = Encounter.objects.select_related("patient", "clinician").order_by(
        "-encounter_date"
    )
    if selected_status in Encounter.Status.values:
        encounters = encounters.filter(status=selected_status)

    paginator = Paginator(encounters, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    counts = {
        "draft": Encounter.objects.filter(status=Encounter.Status.DRAFT).count(),
        "completed": Encounter.objects.filter(status=Encounter.Status.COMPLETED).count(),
        "today": Encounter.objects.filter(encounter_date__date=timezone.localdate()).count(),
    }

    return render(
        request,
        "encounters/encounter_list.html",
        {
            "page_obj": page_obj,
            "encounters": page_obj.object_list,
            "selected_status": selected_status,
            "statuses": Encounter.Status.choices,
            "counts": counts,
            "can_start_encounter": user_can(request.user, "start_encounter"),
        },
    )


@capability_required("start_encounter")
def encounter_create(request):
    patient_id = request.POST.get("patient") or request.GET.get("patient")
    patient = get_object_or_404(Patient, pk=patient_id) if patient_id else None

    if patient:
        draft = Encounter.objects.filter(
            patient=patient, status=Encounter.Status.DRAFT
        ).first()
        if draft:
            messages.info(
                request,
                f"Resumed the open draft encounter for {patient.full_name}.",
            )
            return redirect("encounters:detail", pk=draft.pk)

    initial = {"patient": patient} if patient else {}
    if request.user.is_clinician:
        initial["clinician"] = request.user

    form = EncounterStartForm(request.POST or None, initial=initial)

    if request.method == "POST":
        if patient is None:
            messages.error(request, "Select a patient before starting an encounter.")
        elif form.is_valid():
            encounter = Encounter.objects.create(
                patient=patient,
                clinician=form.cleaned_data["clinician"],
                created_by=request.user,
            )
            messages.success(
                request,
                f"Encounter started for {patient.full_name}. Record triage or the eye exam.",
            )
            return redirect("encounters:detail", pk=encounter.pk)

    return render(
        request,
        "encounters/encounter_create.html",
        {"form": form, "patient": patient},
    )


@capability_required("view_clinical")
def encounter_detail(request, pk):
    encounter = get_object_or_404(
        Encounter.objects.select_related(
            "patient", "clinician", "triaged_by", "completed_by", "appointment"
        ),
        pk=pk,
    )
    eye_exam = EyeExam.objects.filter(encounter=encounter).first()
    prescription = Prescription.objects.filter(encounter=encounter).first()
    is_admin = request.user.is_superuser or request.user.role == Role.ADMIN

    return render(
        request,
        "encounters/encounter_detail.html",
        {
            "encounter": encounter,
            "patient": encounter.patient,
            "eye_exam": eye_exam,
            "prescription": prescription,
            "can_triage": encounter.is_draft and user_can(request.user, "record_triage"),
            "can_record_exam": encounter.is_draft and user_can(request.user, "record_exam"),
            "can_complete": encounter.is_draft and user_can(request.user, "finalize_encounter"),
            "can_reopen": encounter.is_completed and is_admin,
            "can_print": user_can(request.user, "view_clinical"),
        },
    )


@capability_required("record_triage")
def encounter_triage(request, pk):
    encounter = get_object_or_404(Encounter, pk=pk)
    if not encounter.is_draft:
        messages.error(request, "Completed encounters are locked. Reopen it to edit triage.")
        return redirect("encounters:detail", pk=encounter.pk)

    form = TriageForm(request.POST or None, instance=encounter)
    if request.method == "POST" and form.is_valid():
        encounter = form.save(commit=False)
        encounter.triaged_by = request.user
        encounter.triaged_at = timezone.now()
        encounter.save()
        messages.success(request, "Triage recorded.")
        return redirect("encounters:detail", pk=encounter.pk)

    return render(
        request,
        "encounters/encounter_triage_form.html",
        {"encounter": encounter, "patient": encounter.patient, "form": form},
    )


def _prescription_has_data(form):
    if not form.is_valid():
        return False
    return any(
        form.cleaned_data.get(name) not in (None, "")
        for name in (
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
    )


@capability_required("record_exam")
def encounter_exam(request, pk):
    encounter = get_object_or_404(Encounter.objects.select_related("patient"), pk=pk)
    if not encounter.is_draft:
        messages.error(request, "Completed encounters are locked. Reopen it to make changes.")
        return redirect("encounters:detail", pk=encounter.pk)

    eye_exam = encounter.get_eye_exam()
    prescription = getattr(encounter, "prescription", None)
    action = request.POST.get("action", "save")

    exam_form = EyeExamForm(
        request.POST or None, instance=eye_exam, prefix="exam"
    )
    assessment_form = EncounterAssessmentForm(
        request.POST or None, instance=encounter, prefix="assessment"
    )
    rx_form = PrescriptionForm(
        request.POST or None,
        instance=prescription or Prescription(encounter=encounter),
        prefix="rx",
    )

    if request.method == "POST":
        valid = all([exam_form.is_valid(), assessment_form.is_valid(), rx_form.is_valid()])

        if (
            valid
            and action == "complete"
            and not assessment_form.cleaned_data.get("impression", "").strip()
        ):
            assessment_form.add_error(
                "impression", "Add an impression before completing the encounter."
            )
            valid = False

        if valid:
            exam_form.save()
            assessment_form.save()

            if _prescription_has_data(rx_form):
                rx = rx_form.save(commit=False)
                rx.encounter = encounter
                if not rx.issued_by_id:
                    rx.issued_by = request.user
                    rx.issued_at = timezone.now()
                rx.save()
            elif prescription is not None:
                prescription.delete()

            if action == "complete":
                try:
                    encounter.complete(request.user)
                except ValidationError as exc:
                    messages.error(request, "; ".join(exc.messages))
                    return redirect("encounters:exam", pk=encounter.pk)
                messages.success(
                    request,
                    "Encounter completed. The appointment was marked as completed.",
                )
            else:
                messages.success(request, "Eye exam saved as a draft.")
            return redirect("encounters:detail", pk=encounter.pk)

        messages.error(request, "Please correct the highlighted fields.")

    return render(
        request,
        "encounters/encounter_exam_form.html",
        {
            "encounter": encounter,
            "patient": encounter.patient,
            "exam_form": exam_form,
            "assessment_form": assessment_form,
            "rx_form": rx_form,
            "prescription": prescription,
        },
    )


@capability_required("finalize_encounter")
@require_POST
def encounter_complete(request, pk):
    encounter = get_object_or_404(Encounter, pk=pk)
    if not encounter.is_draft:
        messages.info(request, "This encounter is already complete.")
        return redirect("encounters:detail", pk=encounter.pk)

    if not encounter.impression.strip():
        messages.error(request, "Add a clinical impression before completing the encounter.")
        return redirect("encounters:exam", pk=encounter.pk)

    try:
        encounter.complete(request.user)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return redirect("encounters:detail", pk=encounter.pk)

    messages.success(request, "Encounter completed. The appointment was marked as completed.")
    return redirect("encounters:detail", pk=encounter.pk)


@capability_required("manage_staff")
@require_POST
def encounter_reopen(request, pk):
    encounter = get_object_or_404(Encounter, pk=pk)
    if not encounter.is_completed:
        messages.info(request, "This encounter is already open.")
        return redirect("encounters:detail", pk=encounter.pk)

    encounter.reopen()
    messages.success(request, "Encounter reopened for editing.")
    return redirect("encounters:detail", pk=encounter.pk)


@capability_required("view_clinical")
def encounter_print(request, pk):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient", "clinician", "triaged_by", "completed_by"),
        pk=pk,
    )
    return render(
        request,
        "encounters/encounter_print.html",
        {
            "encounter": encounter,
            "patient": encounter.patient,
            "eye_exam": EyeExam.objects.filter(encounter=encounter).first(),
            "prescription": Prescription.objects.filter(encounter=encounter).first(),
        },
    )


@capability_required("view_clinical")
def prescription_print(request, pk):
    encounter = get_object_or_404(
        Encounter.objects.select_related("patient", "clinician"), pk=pk
    )
    prescription = Prescription.objects.filter(encounter=encounter).first()
    if prescription is None:
        messages.error(request, "There is no prescription recorded for this encounter.")
        return redirect("encounters:detail", pk=encounter.pk)

    return render(
        request,
        "encounters/prescription_print.html",
        {
            "encounter": encounter,
            "patient": encounter.patient,
            "prescription": prescription,
        },
    )
