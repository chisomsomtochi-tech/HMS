from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User
from appointments.models import Appointment, Status as AppointmentStatus
from patients.models import Patient, Sex

from .models import Encounter, EyeExam, Prescription


class EncounterTestMixin:
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="TestPass!234"
        )
        self.reception = User.objects.create_user(
            username="reception", password="TestPass!234", role=Role.RECEPTIONIST
        )
        self.nurse = User.objects.create_user(
            username="nurse",
            password="TestPass!234",
            role=Role.NURSE,
            first_name="Grace",
            last_name="Okoro",
        )
        self.optometrist = User.objects.create_user(
            username="optom",
            password="TestPass!234",
            role=Role.OPTOMETRIST,
            first_name="David",
            last_name="Ibrahim",
        )
        self.patient = Patient.objects.create(
            first_name="Adebayo",
            last_name="Ogunleye",
            sex=Sex.MALE,
            date_of_birth=date(1968, 4, 12),
            phone="+234 805 111 2233",
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.optometrist,
            scheduled_at=timezone.make_aware(
                datetime.combine(timezone.localdate() + timedelta(days=1), time(9, 0))
            ),
            status=AppointmentStatus.CHECKED_IN,
        )
        self.encounter = Encounter.objects.create(
            patient=self.patient,
            appointment=self.appointment,
            clinician=self.optometrist,
            created_by=self.nurse,
        )

    def exam_payload(self, action="save", impression="Mild myopic astigmatism"):
        return {
            "exam-va_distance_od_unaided": "6/18",
            "exam-va_distance_os_unaided": "6/24",
            "exam-va_distance_od_corrected": "6/6",
            "exam-va_distance_os_corrected": "6/6",
            "exam-va_near_od": "N6",
            "exam-va_near_os": "N6",
            "exam-pinhole_od": "6/9",
            "exam-pinhole_os": "6/12",
            "exam-sph_od": "-2.00",
            "exam-cyl_od": "-0.50",
            "exam-axis_od": "180",
            "exam-add_od": "1.50",
            "exam-sph_os": "-2.25",
            "exam-cyl_os": "-0.75",
            "exam-axis_os": "175",
            "exam-add_os": "1.50",
            "exam-iop_od": "16.0",
            "exam-iop_os": "17.2",
            "exam-iop_method": "nct",
            "exam-anterior_segment_od": "Clear cornea and quiet anterior chamber.",
            "exam-anterior_segment_os": "Clear cornea and quiet anterior chamber.",
            "exam-fundus_od": "Healthy disc and macula.",
            "exam-fundus_os": "Healthy disc and macula.",
            "exam-pd": "62.5",
            "exam-exam_notes": "Dilated fundoscopy normal.",
            "assessment-impression": impression,
            "assessment-plan": "Spectacles and review in two weeks.",
            "assessment-follow_up_date": (
                timezone.localdate() + timedelta(days=14)
            ).isoformat(),
            "rx-sph_od": "-2.00",
            "rx-cyl_od": "-0.50",
            "rx-axis_od": "180",
            "rx-add_od": "1.50",
            "rx-sph_os": "-2.25",
            "rx-cyl_os": "-0.75",
            "rx-axis_os": "175",
            "rx-add_os": "1.50",
            "rx-pd": "62.5",
            "rx-lens_type": "progressive",
            "rx-notes": "Anti-reflective coating.",
            "action": action,
        }


class EncounterPermissionTests(EncounterTestMixin, TestCase):
    def test_reception_cannot_open_clinical_encounter_pages(self):
        self.client.force_login(self.reception)
        self.assertEqual(self.client.get(reverse("encounters:list")).status_code, 403)
        self.assertEqual(
            self.client.get(
                reverse("encounters:detail", args=[self.encounter.pk])
            ).status_code,
            403,
        )

    def test_nurse_can_view_and_triage_but_not_record_the_exam(self):
        self.client.force_login(self.nurse)
        self.assertEqual(self.client.get(reverse("encounters:list")).status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse("encounters:detail", args=[self.encounter.pk])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("encounters:triage", args=[self.encounter.pk])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("encounters:exam", args=[self.encounter.pk])
            ).status_code,
            403,
        )

    def test_nurse_records_triage(self):
        self.client.force_login(self.nurse)
        response = self.client.post(
            reverse("encounters:triage", args=[self.encounter.pk]),
            {
                "chief_complaint": "Blurred distance vision.",
                "history": "Wears glasses; last test two years ago.",
                "blood_pressure": "138/86",
                "pulse": "76",
                "temperature_c": "36.6",
                "weight_kg": "78.5",
                "height_cm": "172.0",
                "triage_notes": "Dilating drops instilled.",
            },
        )

        self.assertRedirects(
            response, reverse("encounters:detail", args=[self.encounter.pk])
        )
        self.encounter.refresh_from_db()
        self.assertEqual(self.encounter.chief_complaint, "Blurred distance vision.")
        self.assertEqual(self.encounter.triaged_by, self.nurse)
        self.assertIsNotNone(self.encounter.triaged_at)
        self.assertTrue(self.encounter.has_triage)

    def test_only_administrators_can_reopen_completed_encounters(self):
        self.encounter.impression = "Myopia"
        self.encounter.save(update_fields=["impression"])
        self.encounter.complete(self.optometrist)

        self.client.force_login(self.optometrist)
        self.assertEqual(
            self.client.post(
                reverse("encounters:reopen", args=[self.encounter.pk])
            ).status_code,
            403,
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("encounters:reopen", args=[self.encounter.pk])
        )
        self.assertRedirects(
            response, reverse("encounters:detail", args=[self.encounter.pk])
        )
        self.encounter.refresh_from_db()
        self.encounter.appointment.refresh_from_db()
        self.assertTrue(self.encounter.is_draft)
        self.assertEqual(
            self.encounter.appointment.status, AppointmentStatus.IN_PROGRESS
        )


class EncounterWorkflowTests(EncounterTestMixin, TestCase):
    def test_completion_requires_an_impression(self):
        self.client.force_login(self.optometrist)
        payload = self.exam_payload(action="complete", impression="")
        response = self.client.post(
            reverse("encounters:exam", args=[self.encounter.pk]), payload
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add an impression before completing the encounter.")
        self.encounter.refresh_from_db()
        self.assertTrue(self.encounter.is_draft)

    def test_full_exam_completion_locks_the_record_and_updates_the_appointment(self):
        self.client.force_login(self.optometrist)
        response = self.client.post(
            reverse("encounters:exam", args=[self.encounter.pk]),
            self.exam_payload(action="complete"),
        )

        self.assertRedirects(
            response, reverse("encounters:detail", args=[self.encounter.pk])
        )
        self.encounter.refresh_from_db()
        self.encounter.appointment.refresh_from_db()
        self.assertEqual(self.encounter.status, Encounter.Status.COMPLETED)
        self.assertEqual(self.encounter.completed_by, self.optometrist)
        self.assertIsNotNone(self.encounter.completed_at)
        self.assertEqual(
            self.encounter.appointment.status, AppointmentStatus.COMPLETED
        )

        exam = EyeExam.objects.get(encounter=self.encounter)
        self.assertEqual(exam.sph_od, -2)
        self.assertEqual(exam.va_distance_od_unaided, "6/18")
        self.assertTrue(exam.has_data)

        prescription = Prescription.objects.get(encounter=self.encounter)
        self.assertEqual(prescription.issued_by, self.optometrist)
        self.assertIsNotNone(prescription.issued_at)
        self.assertEqual(prescription.lens_type, Prescription.LensType.PROGRESSIVE)

    def test_completed_encounter_cannot_be_edited(self):
        self.encounter.impression = "Myopia"
        self.encounter.save(update_fields=["impression"])
        self.encounter.complete(self.optometrist)

        self.client.force_login(self.optometrist)
        response = self.client.get(
            reverse("encounters:exam", args=[self.encounter.pk])
        )
        self.assertRedirects(
            response, reverse("encounters:detail", args=[self.encounter.pk])
        )

    def test_print_views_include_patient_and_prescription(self):
        self.encounter.impression = "Mild myopic astigmatism"
        self.encounter.plan = "Spectacles."
        self.encounter.save(update_fields=["impression", "plan"])
        EyeExam.objects.create(encounter=self.encounter, va_distance_od_unaided="6/18")
        Prescription.objects.create(
            encounter=self.encounter,
            sph_od="-2.00",
            cyl_od="-0.50",
            axis_od=180,
            sph_os="-2.25",
            cyl_os="-0.75",
            axis_os=175,
            pd="62.5",
            lens_type=Prescription.LensType.PROGRESSIVE,
            issued_by=self.optometrist,
            issued_at=timezone.now(),
        )
        self.encounter.complete(self.optometrist)

        self.client.force_login(self.optometrist)
        summary = self.client.get(
            reverse("encounters:print", args=[self.encounter.pk])
        )
        self.assertEqual(summary.status_code, 200)
        self.assertContains(summary, "Eye Examination Summary")
        self.assertContains(summary, self.patient.full_name)
        self.assertContains(summary, "Mild myopic astigmatism")

        prescription = self.client.get(
            reverse("encounters:prescription_print", args=[self.encounter.pk])
        )
        self.assertEqual(prescription.status_code, 200)
        self.assertContains(prescription, "Glasses Rx")
        self.assertContains(prescription, "Progressive")
        self.assertContains(prescription, self.patient.mrn)

    def test_prescription_print_redirects_when_no_prescription_exists(self):
        self.client.force_login(self.optometrist)
        response = self.client.get(
            reverse("encounters:prescription_print", args=[self.encounter.pk])
        )
        self.assertRedirects(
            response, reverse("encounters:detail", args=[self.encounter.pk])
        )

    def test_saving_a_draft_does_not_complete_the_encounter(self):
        self.client.force_login(self.optometrist)
        response = self.client.post(
            reverse("encounters:exam", args=[self.encounter.pk]),
            self.exam_payload(action="save"),
        )

        self.assertRedirects(
            response, reverse("encounters:detail", args=[self.encounter.pk])
        )
        self.encounter.refresh_from_db()
        self.assertTrue(self.encounter.is_draft)
        self.assertEqual(EyeExam.objects.count(), 1)
