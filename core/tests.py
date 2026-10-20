from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User
from appointments.models import Appointment, Status as AppointmentStatus
from encounters.models import Encounter, Prescription
from patients.models import Patient, Sex


class DashboardRenderTests(TestCase):
    def setUp(self):
        self.users = {
            "admin": User.objects.create_superuser(
                username="admin", password="TestPass!234"
            ),
            "reception": User.objects.create_user(
                username="reception", password="TestPass!234", role=Role.RECEPTIONIST
            ),
            "nurse": User.objects.create_user(
                username="nurse", password="TestPass!234", role=Role.NURSE
            ),
            "optom": User.objects.create_user(
                username="optom", password="TestPass!234", role=Role.OPTOMETRIST
            ),
        }
        self.patient = Patient.objects.create(
            first_name="Adebayo",
            last_name="Ogunleye",
            sex=Sex.MALE,
            date_of_birth=date(1968, 4, 12),
            phone="+234 805 111 2233",
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in")

    def test_every_role_can_render_the_dashboard(self):
        for user in self.users.values():
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(reverse("core:dashboard"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "the clinic today")


class EndToEndFlowTests(TestCase):
    """Registration → booking → check-in → encounter → completion."""

    def setUp(self):
        self.reception = User.objects.create_user(
            username="reception",
            password="TestPass!234",
            role=Role.RECEPTIONIST,
            first_name="Tolu",
            last_name="Adeyemi",
        )
        self.optometrist = User.objects.create_user(
            username="optom",
            password="TestPass!234",
            role=Role.OPTOMETRIST,
            first_name="David",
            last_name="Ibrahim",
        )

    def login(self, username):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": username, "password": "TestPass!234"},
        )
        self.assertEqual(response.status_code, 302)

    def test_reception_to_clinician_visit_flow(self):
        self.login("reception")

        response = self.client.post(
            reverse("patients:create"),
            {
                "first_name": "Chiamaka",
                "last_name": "Nwosu",
                "sex": Sex.FEMALE,
                "date_of_birth": "1992-09-03",
                "phone": "+234 806 222 3344",
                "email": "chiamaka@example.com",
                "alert_note": "Penicillin allergy.",
            },
        )
        patient = Patient.objects.get(first_name="Chiamaka")
        self.assertRedirects(response, reverse("patients:detail", args=[patient.pk]))
        self.assertTrue(patient.mrn.startswith("MRN-"))

        scheduled_at = timezone.make_aware(
            datetime.combine(timezone.localdate() + timedelta(days=1), time(10, 30))
        )
        response = self.client.post(
            reverse("appointments:create"),
            {
                "patient": patient.pk,
                "clinician": self.optometrist.pk,
                "scheduled_at": timezone.localtime(scheduled_at).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "duration_minutes": 30,
                "appointment_type": "new",
                "reason": "Blurred distance vision.",
                "notes": "",
            },
        )
        appointment = Appointment.objects.get(patient=patient)
        self.assertRedirects(
            response, reverse("appointments:detail", args=[appointment.pk])
        )

        self.client.post(reverse("appointments:check_in", args=[appointment.pk]))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, AppointmentStatus.CHECKED_IN)

        self.client.post(reverse("accounts:logout"))
        self.login("optom")

        response = self.client.post(
            reverse("appointments:start_encounter", args=[appointment.pk])
        )
        encounter = Encounter.objects.get(appointment=appointment)
        self.assertRedirects(
            response, reverse("encounters:detail", args=[encounter.pk])
        )

        self.client.post(
            reverse("encounters:triage", args=[encounter.pk]),
            {
                "chief_complaint": "Blurred distance vision for six months.",
                "history": "No eye pain or flashes.",
                "blood_pressure": "118/76",
                "pulse": "70",
                "temperature_c": "36.7",
                "weight_kg": "64.0",
                "height_cm": "165.0",
                "triage_notes": "",
            },
        )

        response = self.client.post(
            reverse("encounters:exam", args=[encounter.pk]),
            {
                "exam-va_distance_od_unaided": "6/18",
                "exam-va_distance_os_unaided": "6/18",
                "exam-sph_od": "-1.50",
                "exam-cyl_od": "-0.25",
                "exam-axis_od": "180",
                "exam-sph_os": "-1.75",
                "exam-cyl_os": "-0.50",
                "exam-axis_os": "175",
                "exam-iop_od": "15.0",
                "exam-iop_os": "16.0",
                "exam-iop_method": "nct",
                "assessment-impression": "Mild myopic astigmatism.",
                "assessment-plan": "Glasses and review in two weeks.",
                "assessment-follow_up_date": (
                    timezone.localdate() + timedelta(days=14)
                ).isoformat(),
                "rx-sph_od": "-1.50",
                "rx-cyl_od": "-0.25",
                "rx-axis_od": "180",
                "rx-sph_os": "-1.75",
                "rx-cyl_os": "-0.50",
                "rx-axis_os": "175",
                "rx-pd": "62.5",
                "rx-lens_type": "single_vision",
                "action": "complete",
            },
        )
        self.assertRedirects(
            response, reverse("encounters:detail", args=[encounter.pk])
        )

        encounter.refresh_from_db()
        appointment.refresh_from_db()
        self.assertEqual(encounter.status, Encounter.Status.COMPLETED)
        self.assertTrue(Prescription.objects.filter(encounter=encounter).exists())
        self.assertEqual(appointment.status, AppointmentStatus.COMPLETED)

        summary = self.client.get(reverse("encounters:print", args=[encounter.pk]))
        self.assertEqual(summary.status_code, 200)
        self.assertContains(summary, patient.full_name)

        prescription = self.client.get(
            reverse("encounters:prescription_print", args=[encounter.pk])
        )
        self.assertEqual(prescription.status_code, 200)
        self.assertContains(prescription, "Glasses Rx")
