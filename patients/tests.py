from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, User

from .models import Patient, Sex


class PatientModelTests(TestCase):
    def make_patient(self, **overrides):
        data = {
            "first_name": "Adebayo",
            "last_name": "Ogunleye",
            "sex": Sex.MALE,
            "date_of_birth": date(1968, 4, 12),
            "phone": "+234 805 111 2233",
        }
        data.update(overrides)
        return Patient.objects.create(**data)

    def test_mrn_is_generated_after_insert_and_is_unique(self):
        first = self.make_patient()
        second = self.make_patient(
            first_name="Chiamaka", last_name="Nwosu", phone="+234 806 222 3344"
        )

        self.assertEqual(
            first.mrn, f"MRN-{timezone.localdate():%Y}-{first.pk:05d}"
        )
        self.assertEqual(
            second.mrn, f"MRN-{timezone.localdate():%Y}-{second.pk:05d}"
        )
        self.assertNotEqual(first.mrn, second.mrn)
        self.assertFalse(Patient.objects.filter(mrn__isnull=True).exists())

    def test_age_and_display_helpers(self):
        patient = self.make_patient(date_of_birth=date(1990, 1, 1))
        expected_age = timezone.localdate().year - 1990
        self.assertEqual(patient.age, expected_age)
        self.assertEqual(patient.age_display, f"{expected_age} yrs")
        self.assertEqual(patient.initials, "AO")

    def test_search_matches_mrn_name_phone_and_email(self):
        patient = self.make_patient(email="adebayo@example.com")

        for term in ("MRN-", "Adebayo", "+234 805", "adebayo@example.com"):
            self.assertIn(patient, Patient.objects.search(term))

    def test_alert_flag(self):
        self.assertFalse(self.make_patient().has_alert)
        self.assertTrue(self.make_patient(alert_note="Penicillin allergy").has_alert)


class PatientViewTests(TestCase):
    def setUp(self):
        self.reception = User.objects.create_user(
            username="reception", password="TestPass!234", role=Role.RECEPTIONIST
        )
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

    def test_reception_can_register_a_patient(self):
        self.client.force_login(self.reception)
        response = self.client.post(
            reverse("patients:create"),
            {
                "first_name": "Chiamaka",
                "last_name": "Nwosu",
                "other_name": "",
                "date_of_birth": "1992-09-03",
                "sex": Sex.FEMALE,
                "phone": "+234 806 222 3344",
                "email": "chiamaka@example.com",
                "address": "7 Ogunlana Drive",
                "city": "Surulere",
                "state": "Lagos",
                "occupation": "Engineer",
                "nok_name": "Nnamdi Nwosu",
                "nok_phone": "+234 806 222 3345",
                "nok_relationship": "Brother",
                "alert_note": "",
                "notes": "",
            },
        )

        patient = Patient.objects.get(first_name="Chiamaka")
        self.assertRedirects(response, reverse("patients:detail", args=[patient.pk]))
        self.assertTrue(patient.mrn.startswith("MRN-"))
        self.assertEqual(patient.created_by, self.reception)

    def test_clinician_without_registration_capability_is_denied(self):
        self.client.force_login(self.optometrist)
        self.assertEqual(self.client.get(reverse("patients:create")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("patients:edit", args=[self.patient.pk])).status_code,
            403,
        )

    def test_patient_list_and_detail_render_for_reception(self):
        self.client.force_login(self.reception)
        list_response = self.client.get(reverse("patients:list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Adebayo Ogunleye")

        detail_response = self.client.get(
            reverse("patients:detail", args=[self.patient.pk])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, self.patient.mrn)

    def test_duplicate_warning_flags_an_existing_phone_number(self):
        self.client.force_login(self.reception)
        response = self.client.get(
            reverse("patients:duplicate_check"),
            {"first_name": "Adebayo", "last_name": "Ogunleye", "phone": "+234 805 111 2233"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient.mrn)
        self.assertContains(response, "existing record", status_code=200)

    def test_future_date_of_birth_is_rejected(self):
        self.client.force_login(self.reception)
        response = self.client.post(
            reverse("patients:create"),
            {
                "first_name": "Future",
                "last_name": "Person",
                "sex": Sex.OTHER,
                "date_of_birth": "2999-01-01",
                "phone": "+234 800 999 0000",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Date of birth cannot be in the future")
        self.assertFalse(Patient.objects.filter(first_name="Future").exists())
