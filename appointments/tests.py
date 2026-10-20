from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User
from encounters.models import Encounter
from patients.models import Patient, Sex

from .forms import AppointmentForm
from .models import Appointment, AppointmentType, Status


class AppointmentModelTests(TestCase):
    def setUp(self):
        self.optometrist = User.objects.create_user(
            username="optom", password="TestPass!234", role=Role.OPTOMETRIST
        )
        self.patient = Patient.objects.create(
            first_name="Adebayo",
            last_name="Ogunleye",
            sex=Sex.MALE,
            date_of_birth=date(1968, 4, 12),
            phone="+234 805 111 2233",
        )
        self.start = timezone.make_aware(
            datetime.combine(timezone.localdate() + timedelta(days=1), time(9, 0))
        )

    def form_data(self, scheduled_at, duration=30):
        return {
            "patient": self.patient.pk,
            "clinician": self.optometrist.pk,
            "scheduled_at": timezone.localtime(scheduled_at).strftime("%Y-%m-%dT%H:%M"),
            "duration_minutes": duration,
            "appointment_type": AppointmentType.NEW,
            "reason": "",
            "notes": "",
        }

    def test_overlapping_appointment_is_rejected(self):
        Appointment.objects.create(
            patient=self.patient,
            clinician=self.optometrist,
            scheduled_at=self.start,
            duration_minutes=30,
        )

        form = AppointmentForm(
            data=self.form_data(self.start + timedelta(minutes=15))
        )
        self.assertFalse(form.is_valid())
        self.assertIn("scheduled_at", form.errors)

    def test_adjacent_appointment_is_allowed(self):
        Appointment.objects.create(
            patient=self.patient,
            clinician=self.optometrist,
            scheduled_at=self.start,
            duration_minutes=30,
        )

        form = AppointmentForm(
            data=self.form_data(self.start + timedelta(minutes=30))
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_cancelled_appointment_does_not_block_the_slot(self):
        Appointment.objects.create(
            patient=self.patient,
            clinician=self.optometrist,
            scheduled_at=self.start,
            status=Status.CANCELLED,
        )

        form = AppointmentForm(data=self.form_data(self.start))
        self.assertTrue(form.is_valid(), form.errors)

    def test_check_in_and_no_show_only_apply_to_scheduled_visits(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.optometrist,
            scheduled_at=self.start,
        )
        self.assertTrue(appointment.check_in())
        self.assertEqual(appointment.status, Status.CHECKED_IN)
        self.assertIsNotNone(appointment.checked_in_at)
        self.assertFalse(appointment.check_in())
        self.assertFalse(appointment.mark_no_show())

    def test_cancelled_visit_cannot_be_cancelled_again(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.optometrist,
            scheduled_at=self.start,
            status=Status.CANCELLED,
        )
        self.assertFalse(appointment.cancel("Again"))


class AppointmentViewTests(TestCase):
    def setUp(self):
        self.reception = User.objects.create_user(
            username="reception", password="TestPass!234", role=Role.RECEPTIONIST
        )
        self.nurse = User.objects.create_user(
            username="nurse", password="TestPass!234", role=Role.NURSE
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
        self.start = timezone.make_aware(
            datetime.combine(timezone.localdate() + timedelta(days=1), time(9, 0))
        )

    def booking_data(self):
        return {
            "patient": self.patient.pk,
            "clinician": self.optometrist.pk,
            "scheduled_at": timezone.localtime(self.start).strftime("%Y-%m-%dT%H:%M"),
            "duration_minutes": 30,
            "appointment_type": AppointmentType.NEW,
            "reason": "Blurred distance vision.",
            "notes": "",
        }

    def test_reception_can_book_and_check_in_a_patient(self):
        self.client.force_login(self.reception)
        response = self.client.post(reverse("appointments:create"), self.booking_data())
        appointment = Appointment.objects.get()
        self.assertRedirects(
            response, reverse("appointments:detail", args=[appointment.pk])
        )
        self.assertEqual(appointment.created_by, self.reception)

        response = self.client.post(
            reverse("appointments:check_in", args=[appointment.pk])
        )
        self.assertRedirects(
            response, reverse("appointments:detail", args=[appointment.pk])
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Status.CHECKED_IN)
        self.assertIsNotNone(appointment.checked_in_at)

    def test_schedule_page_renders_for_reception(self):
        self.client.force_login(self.reception)
        response = self.client.get(reverse("appointments:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Schedule")

    def test_nurse_cannot_book_appointments(self):
        self.client.force_login(self.nurse)
        self.assertEqual(
            self.client.get(reverse("appointments:create")).status_code, 403
        )

    def test_starting_an_encounter_links_it_to_the_appointment(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.optometrist,
            scheduled_at=self.start,
            status=Status.CHECKED_IN,
        )
        self.client.force_login(self.optometrist)
        response = self.client.post(
            reverse("appointments:start_encounter", args=[appointment.pk])
        )

        encounter = Encounter.objects.get(appointment=appointment)
        self.assertRedirects(
            response, reverse("encounters:detail", args=[encounter.pk])
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Status.IN_PROGRESS)
        self.assertEqual(encounter.patient, self.patient)
        self.assertEqual(encounter.clinician, self.optometrist)

    def test_completed_appointment_cannot_be_checked_in(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.optometrist,
            scheduled_at=self.start,
            status=Status.COMPLETED,
        )
        self.client.force_login(self.reception)
        self.client.post(reverse("appointments:check_in", args=[appointment.pk]))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Status.COMPLETED)
