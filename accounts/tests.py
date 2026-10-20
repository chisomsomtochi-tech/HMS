from django.test import TestCase
from django.urls import reverse

from .models import Role, User
from .permissions import user_can


class CapabilityTests(TestCase):
    def create_user(self, username, role):
        return User.objects.create_user(
            username=username, password="TestPass!234", role=role
        )

    def test_superuser_is_administrator_and_has_every_capability(self):
        admin = User.objects.create_superuser(username="root", password="TestPass!234")
        self.assertEqual(admin.role, Role.ADMIN)
        for capability in (
            "manage_staff",
            "view_patients",
            "manage_patients",
            "view_clinical",
            "manage_appointments",
            "check_in",
            "start_encounter",
            "record_triage",
            "record_exam",
            "finalize_encounter",
            "issue_prescription",
        ):
            self.assertTrue(user_can(admin, capability), capability)

    def test_receptionist_can_register_and_book_but_not_view_clinical_data(self):
        reception = self.create_user("reception", Role.RECEPTIONIST)
        self.assertTrue(user_can(reception, "view_patients"))
        self.assertTrue(user_can(reception, "manage_patients"))
        self.assertTrue(user_can(reception, "manage_appointments"))
        self.assertTrue(user_can(reception, "check_in"))
        self.assertFalse(user_can(reception, "view_clinical"))
        self.assertFalse(user_can(reception, "record_triage"))
        self.assertFalse(user_can(reception, "record_exam"))

    def test_nurse_can_triage_but_not_record_exam_or_finalize(self):
        nurse = self.create_user("nurse", Role.NURSE)
        self.assertTrue(user_can(nurse, "view_clinical"))
        self.assertTrue(user_can(nurse, "start_encounter"))
        self.assertTrue(user_can(nurse, "record_triage"))
        self.assertFalse(user_can(nurse, "record_exam"))
        self.assertFalse(user_can(nurse, "finalize_encounter"))
        self.assertFalse(user_can(nurse, "issue_prescription"))

    def test_optometrist_can_record_and_finalize_exam(self):
        optometrist = self.create_user("optom", Role.OPTOMETRIST)
        self.assertTrue(optometrist.is_clinician)
        self.assertTrue(user_can(optometrist, "record_exam"))
        self.assertTrue(user_can(optometrist, "finalize_encounter"))
        self.assertFalse(user_can(optometrist, "manage_appointments"))
        self.assertFalse(user_can(optometrist, "manage_patients"))
        self.assertFalse(user_can(optometrist, "manage_staff"))

    def test_anonymous_user_has_no_capabilities(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertFalse(user_can(AnonymousUser(), "view_patients"))
        self.assertFalse(user_can(None, "view_patients"))


class StaffManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="TestPass!234", first_name="Amina", last_name="Bello"
        )
        self.reception = User.objects.create_user(
            username="reception",
            password="TestPass!234",
            role=Role.RECEPTIONIST,
            first_name="Tolu",
            last_name="Adeyemi",
        )

    def test_only_administrators_can_open_staff_management(self):
        self.client.force_login(self.reception)
        self.assertEqual(self.client.get(reverse("accounts:staff_list")).status_code, 403)

        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:staff_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tolu Adeyemi")

    def test_admin_created_staff_must_change_password_at_first_login(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("accounts:staff_create"),
            {
                "username": "new.optom",
                "first_name": "New",
                "last_name": "Optometrist",
                "email": "new.optom@example.com",
                "phone": "+234 800 000 0000",
                "role": Role.OPTOMETRIST,
                "password1": "StrongPass!234",
                "password2": "StrongPass!234",
            },
        )

        member = User.objects.get(username="new.optom")
        self.assertTrue(member.must_change_password)
        self.assertEqual(member.role, Role.OPTOMETRIST)
        self.assertRedirects(response, reverse("accounts:staff_detail", args=[member.pk]))

        self.client.force_login(member)
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(response, reverse("accounts:password_change"))

        # The password form itself stays reachable while the flag is set.
        self.assertEqual(
            self.client.get(reverse("accounts:password_change")).status_code, 200
        )

    def test_administrator_cannot_deactivate_their_own_account(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("accounts:staff_toggle", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_last_administrator_cannot_be_demoted(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("accounts:staff_edit", args=[self.admin.pk]),
            {
                "first_name": "Amina",
                "last_name": "Bello",
                "email": "",
                "phone": "",
                "role": Role.RECEPTIONIST,
            },
        )
        self.admin.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.admin.role, Role.ADMIN)
        self.assertContains(response, "cannot remove your own administrator role")
