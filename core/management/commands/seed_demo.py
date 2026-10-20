"""Seed a believable demo clinic for presentations and local testing.

Run with::

    python manage.py seed_demo

The command is idempotent: staff accounts and patients are matched on stable
identifiers, and appointments are matched on clinician + time.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Role, User
from appointments.models import Appointment, AppointmentType, Status as AppointmentStatus
from encounters.models import Encounter, EyeExam, Prescription
from patients.models import Patient, Sex

DEMO_PASSWORD = "Demo@1234"

STAFF = [
    {
        "username": "admin",
        "first_name": "Amina",
        "last_name": "Bello",
        "role": Role.ADMIN,
        "email": "amina.bello@suavedef.example",
        "phone": "+234 803 000 0001",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "reception",
        "first_name": "Tolu",
        "last_name": "Adeyemi",
        "role": Role.RECEPTIONIST,
        "email": "tolu.adeyemi@suavedef.example",
        "phone": "+234 803 000 0002",
    },
    {
        "username": "nurse",
        "first_name": "Grace",
        "last_name": "Okoro",
        "role": Role.NURSE,
        "email": "grace.okoro@suavedef.example",
        "phone": "+234 803 000 0003",
    },
    {
        "username": "optom",
        "first_name": "David",
        "last_name": "Ibrahim",
        "role": Role.OPTOMETRIST,
        "email": "david.ibrahim@suavedef.example",
        "phone": "+234 803 000 0004",
    },
    {
        "username": "ophth",
        "first_name": "Ifeoma",
        "last_name": "Nwankwo",
        "role": Role.OPHTHALMOLOGIST,
        "email": "ifeoma.nwankwo@suavedef.example",
        "phone": "+234 803 000 0005",
    },
]

PATIENTS = [
    {
        "first_name": "Adebayo",
        "last_name": "Ogunleye",
        "sex": Sex.MALE,
        "date_of_birth": date(1968, 4, 12),
        "phone": "+234 805 111 2233",
        "email": "adebayo.ogunleye@example.com",
        "address": "18 Adeola Odeku Street",
        "city": "Victoria Island",
        "state": "Lagos",
        "occupation": "Architect",
        "nok_name": "Bisi Ogunleye",
        "nok_phone": "+234 805 111 2234",
        "nok_relationship": "Spouse",
        "alert_note": "Type 2 diabetes on insulin. Penicillin allergy — avoid penicillin-based drops.",
        "notes": "Long-standing glasses wearer. Prefers morning appointments.",
    },
    {
        "first_name": "Chiamaka",
        "last_name": "Nwosu",
        "sex": Sex.FEMALE,
        "date_of_birth": date(1992, 9, 3),
        "phone": "+234 806 222 3344",
        "email": "chiamaka.nwosu@example.com",
        "address": "7 Ogunlana Drive",
        "city": "Surulere",
        "state": "Lagos",
        "occupation": "Software engineer",
        "nok_name": "Nnamdi Nwosu",
        "nok_phone": "+234 806 222 3345",
        "nok_relationship": "Brother",
        "alert_note": "",
        "notes": "",
    },
    {
        "first_name": "Musa",
        "last_name": "Ibrahim",
        "sex": Sex.MALE,
        "date_of_birth": date(1955, 1, 22),
        "phone": "+234 807 333 4455",
        "email": "",
        "address": "22 Ahmadu Bello Way",
        "city": "Kaduna",
        "state": "Kaduna",
        "occupation": "Retired teacher",
        "nok_name": "Hauwa Ibrahim",
        "nok_phone": "+234 807 333 4456",
        "nok_relationship": "Daughter",
        "alert_note": "Known primary open-angle glaucoma. On latanoprost both eyes.",
        "notes": "Attends glaucoma review every 3 months. Family history of glaucoma.",
    },
    {
        "first_name": "Funmilayo",
        "last_name": "Adeyemi",
        "sex": Sex.FEMALE,
        "date_of_birth": date(1980, 6, 17),
        "phone": "+234 808 444 5566",
        "email": "funmi.adeyemi@example.com",
        "address": "31 Allen Avenue",
        "city": "Ikeja",
        "state": "Lagos",
        "occupation": "Accountant",
        "nok_name": "Kunle Adeyemi",
        "nok_phone": "+234 808 444 5567",
        "nok_relationship": "Spouse",
        "alert_note": "",
        "notes": "Screen use 10+ hours daily; reports evening eye strain.",
    },
    {
        "first_name": "Emeka",
        "last_name": "Obi",
        "sex": Sex.MALE,
        "date_of_birth": date(2001, 11, 30),
        "phone": "+234 809 555 6677",
        "email": "emeka.obi@example.com",
        "address": "4 Nza Street",
        "city": "Enugu",
        "state": "Enugu",
        "occupation": "Student",
        "nok_name": "Ngozi Obi",
        "nok_phone": "+234 809 555 6678",
        "nok_relationship": "Mother",
        "alert_note": "",
        "notes": "",
    },
    {
        "first_name": "Zainab",
        "last_name": "Bello",
        "sex": Sex.FEMALE,
        "date_of_birth": date(1974, 3, 8),
        "phone": "+234 810 666 7788",
        "email": "zainab.bello@example.com",
        "address": "9 Wuse II Close",
        "city": "Abuja",
        "state": "FCT",
        "occupation": "Civil servant",
        "nok_name": "Sani Bello",
        "nok_phone": "+234 810 666 7789",
        "nok_relationship": "Spouse",
        "alert_note": "",
        "notes": "",
    },
    {
        "first_name": "Tunde",
        "last_name": "Bakare",
        "sex": Sex.MALE,
        "date_of_birth": date(1988, 12, 5),
        "phone": "+234 811 777 8899",
        "email": "tunde.bakare@example.com",
        "address": "14 Awolowo Road",
        "city": "Ikoyi",
        "state": "Lagos",
        "occupation": "Logistics manager",
        "nok_name": "Kemi Bakare",
        "nok_phone": "+234 811 777 8900",
        "nok_relationship": "Spouse",
        "alert_note": "",
        "notes": "",
    },
    {
        "first_name": "Ngozi",
        "last_name": "Eze",
        "sex": Sex.FEMALE,
        "date_of_birth": date(1962, 7, 14),
        "phone": "+234 812 888 9900",
        "email": "",
        "address": "3 Ogui Road",
        "city": "Enugu",
        "state": "Enugu",
        "occupation": "Trader",
        "nok_name": "Chidi Eze",
        "nok_phone": "+234 812 888 9901",
        "nok_relationship": "Son",
        "alert_note": "Hypertensive. Sensitive to dilating drops.",
        "notes": "",
    },
    {
        "first_name": "Segun",
        "last_name": "Alabi",
        "sex": Sex.MALE,
        "date_of_birth": date(1996, 2, 19),
        "phone": "+234 813 999 0011",
        "email": "segun.alabi@example.com",
        "address": "27 Ikorodu Road",
        "city": "Yaba",
        "state": "Lagos",
        "occupation": "Driver",
        "nok_name": "Bola Alabi",
        "nok_phone": "+234 813 999 0012",
        "nok_relationship": "Sister",
        "alert_note": "",
        "notes": "",
    },
    {
        "first_name": "Halima",
        "last_name": "Yusuf",
        "sex": Sex.FEMALE,
        "date_of_birth": date(2010, 8, 27),
        "phone": "+234 814 000 1122",
        "email": "",
        "address": "6 Sultan Road",
        "city": "Sokoto",
        "state": "Sokoto",
        "occupation": "Student",
        "nok_name": "Fatima Yusuf",
        "nok_phone": "+234 814 000 1123",
        "nok_relationship": "Mother",
        "alert_note": "",
        "notes": "Brought by mother. First eye examination.",
    },
]


class Command(BaseCommand):
    help = "Create demo staff, patients, appointments, and a completed eye encounter."

    @transaction.atomic
    def handle(self, *args, **options):
        staff = self._seed_staff()
        patients = self._seed_patients(staff["reception"])
        appointments = self._seed_appointments(staff, patients)
        self._seed_completed_encounter(staff, patients[0], appointments["completed"])
        self._seed_draft_encounter(staff, patients[1], appointments["draft"])
        self._seed_future_appointment(staff, patients[9])

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo clinic seeded successfully."))
        self.stdout.write("")
        self.stdout.write("  Sign in at /accounts/login/")
        self.stdout.write(f"  Password for every account: {DEMO_PASSWORD}")
        self.stdout.write("")
        self.stdout.write("  admin      Administrator")
        self.stdout.write("  reception  Receptionist")
        self.stdout.write("  nurse      Nurse")
        self.stdout.write("  optom      Optometrist")
        self.stdout.write("  ophth      Ophthalmologist")
        self.stdout.write("")

    def _seed_staff(self):
        staff = {}
        for data in STAFF:
            data = data.copy()
            username = data.pop("username")
            is_staff = data.pop("is_staff", False)
            is_superuser = data.pop("is_superuser", False)

            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": data["first_name"], "last_name": data["last_name"]},
            )
            for field, value in data.items():
                setattr(user, field, value)
            user.is_active = True
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.must_change_password = False
            user.set_password(DEMO_PASSWORD)
            user.save()

            staff[username] = user
            state = "created" if created else "updated"
            self.stdout.write(f"  Staff {username:<10} {state}")
        return staff

    def _seed_patients(self, reception):
        patients = []
        for data in PATIENTS:
            data = data.copy()
            first_name = data.pop("first_name")
            last_name = data.pop("last_name")
            phone = data["phone"]
            patient, created = Patient.objects.get_or_create(
                phone=phone,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "created_by": reception,
                    **data,
                },
            )
            patients.append(patient)
            if created:
                self.stdout.write(f"  Patient {patient.full_name:<24} {patient.mrn}")
        return patients

    def _seed_appointments(self, staff, patients):
        today = timezone.localdate()
        reception = staff["reception"]
        optom = staff["optom"]
        ophth = staff["ophth"]

        def slot(hour, minute):
            return timezone.make_aware(datetime.combine(today, time(hour, minute)))

        specs = [
            {
                "key": "completed",
                "patient": patients[0],
                "clinician": optom,
                "scheduled_at": slot(9, 0),
                "appointment_type": AppointmentType.FOLLOW_UP,
                "reason": "Review of blurring distance vision and glasses prescription.",
                "status": AppointmentStatus.COMPLETED,
            },
            {
                "key": "draft",
                "patient": patients[1],
                "clinician": optom,
                "scheduled_at": slot(9, 30),
                "appointment_type": AppointmentType.NEW,
                "reason": "Red, gritty eyes since yesterday; possible allergic conjunctivitis.",
                "status": AppointmentStatus.IN_PROGRESS,
            },
            {
                "key": "scheduled_1",
                "patient": patients[2],
                "clinician": optom,
                "scheduled_at": slot(10, 0),
                "appointment_type": AppointmentType.GLAUCOMA,
                "reason": "Routine glaucoma review and IOP check.",
                "status": AppointmentStatus.SCHEDULED,
            },
            {
                "key": "scheduled_2",
                "patient": patients[3],
                "clinician": optom,
                "scheduled_at": slot(10, 30),
                "appointment_type": AppointmentType.REFRACTION,
                "reason": "Eye strain with prolonged screen use.",
                "status": AppointmentStatus.CHECKED_IN,
            },
            {
                "key": "scheduled_3",
                "patient": patients[4],
                "clinician": ophth,
                "scheduled_at": slot(11, 0),
                "appointment_type": AppointmentType.NEW,
                "reason": "Intermittent double vision when reading.",
                "status": AppointmentStatus.SCHEDULED,
            },
            {
                "key": "scheduled_4",
                "patient": patients[5],
                "clinician": ophth,
                "scheduled_at": slot(11, 30),
                "appointment_type": AppointmentType.RETINA,
                "reason": "Floaters in the right eye for one week.",
                "status": AppointmentStatus.SCHEDULED,
            },
            {
                "key": "scheduled_5",
                "patient": patients[6],
                "clinician": ophth,
                "scheduled_at": slot(12, 0),
                "appointment_type": AppointmentType.NEW,
                "reason": "New patient consultation for reading difficulty.",
                "status": AppointmentStatus.SCHEDULED,
            },
            {
                "key": "cancelled",
                "patient": patients[7],
                "clinician": optom,
                "scheduled_at": slot(14, 0),
                "appointment_type": AppointmentType.FOLLOW_UP,
                "reason": "Follow-up for dry eye management.",
                "status": AppointmentStatus.CANCELLED,
                "cancelled_reason": "Patient called to reschedule.",
            },
            {
                "key": "no_show",
                "patient": patients[8],
                "clinician": optom,
                "scheduled_at": slot(14, 30),
                "appointment_type": AppointmentType.NEW,
                "reason": "Routine eye test.",
                "status": AppointmentStatus.NO_SHOW,
            },
        ]

        appointments = {}
        for spec in specs:
            key = spec.pop("key")
            patient = spec.pop("patient")
            clinician = spec.pop("clinician")
            scheduled_at = spec.pop("scheduled_at")

            appointment, created = Appointment.objects.get_or_create(
                clinician=clinician,
                scheduled_at=scheduled_at,
                defaults={
                    "patient": patient,
                    "created_by": reception,
                    "duration_minutes": 30,
                    "appointment_type": spec.pop("appointment_type"),
                    "reason": spec.pop("reason"),
                    "status": spec.pop("status"),
                },
            )
            if not created:
                # Keep the demo's status current without disturbing the slot.
                for field in ("appointment_type", "reason", "status"):
                    if field in spec:
                        setattr(appointment, field, spec[field])
                appointment.save(update_fields=["appointment_type", "reason", "status", "updated_at"])
            appointments[key] = appointment
            if created:
                self.stdout.write(
                    f"  Appointment {timezone.localtime(scheduled_at):%H:%M} "
                    f"{patient.full_name} ({appointment.get_status_display()})"
                )
        return appointments

    def _seed_completed_encounter(self, staff, patient, appointment):
        optom = staff["optom"]
        nurse = staff["nurse"]
        now = timezone.now()

        encounter, created = Encounter.objects.get_or_create(
            appointment=appointment,
            defaults={
                "patient": patient,
                "clinician": optom,
                "created_by": optom,
                "chief_complaint": "Gradual blurring of distance vision in both eyes over the last year.",
                "history": (
                    "Long-standing glasses wearer. Type 2 diabetes for 12 years, on insulin. "
                    "No flashes, floaters, or eye pain. Last eye test two years ago."
                ),
                "blood_pressure": "138/86",
                "pulse": 76,
                "temperature_c": Decimal("36.6"),
                "weight_kg": Decimal("78.5"),
                "height_cm": Decimal("172.0"),
                "triage_notes": "Patient comfortable. No acute complaints. Dilating drops instilled.",
                "triaged_by": nurse,
                "triaged_at": now,
                "impression": (
                    "Presbyopia with mild myopic astigmatism. Dilated fundus examination shows "
                    "no diabetic retinopathy."
                ),
                "plan": (
                    "Progressive spectacles prescribed. Continue glycaemic control and review "
                    "with physician. Return in two weeks for adaptation check."
                ),
                "follow_up_date": timezone.localdate() + timedelta(days=14),
            },
        )
        if not created:
            return

        EyeExam.objects.create(
            encounter=encounter,
            va_distance_od_unaided="6/18",
            va_distance_os_unaided="6/24",
            va_distance_od_corrected="6/6",
            va_distance_os_corrected="6/6",
            va_near_od="N6",
            va_near_os="N6",
            pinhole_od="6/9",
            pinhole_os="6/12",
            sph_od=Decimal("-1.25"),
            cyl_od=Decimal("-0.50"),
            axis_od=180,
            add_od=Decimal("1.50"),
            sph_os=Decimal("-1.50"),
            cyl_os=Decimal("-0.75"),
            axis_os=175,
            add_os=Decimal("1.50"),
            iop_od=Decimal("16.0"),
            iop_os=Decimal("17.2"),
            iop_method=EyeExam.IOPMethod.NCT,
            anterior_segment_od="Conjunctiva clear. Cornea clear. Anterior chamber quiet. Early nuclear sclerosis.",
            anterior_segment_os="Conjunctiva clear. Cornea clear. Anterior chamber quiet. Early nuclear sclerosis.",
            fundus_od="Disc pink, C/D ratio 0.3. Macula clear. No diabetic retinopathy.",
            fundus_os="Disc pink, C/D ratio 0.3. Macula clear. No diabetic retinopathy.",
            pd=Decimal("62.5"),
            exam_notes="Dilated fundoscopy performed. No peripheral retinal lesions or haemorrhages.",
        )

        Prescription.objects.create(
            encounter=encounter,
            sph_od=Decimal("-1.25"),
            cyl_od=Decimal("-0.50"),
            axis_od=180,
            add_od=Decimal("1.50"),
            sph_os=Decimal("-1.50"),
            cyl_os=Decimal("-0.75"),
            axis_os=175,
            add_os=Decimal("1.50"),
            pd=Decimal("62.5"),
            lens_type=Prescription.LensType.PROGRESSIVE,
            notes="Progressive lenses with anti-reflective coating. Advised on the adaptation period.",
            issued_by=optom,
            issued_at=now,
        )

        encounter.complete(optom)
        self.stdout.write(f"  Completed encounter for {patient.full_name} with prescription")

    def _seed_draft_encounter(self, staff, patient, appointment):
        nurse = staff["nurse"]
        optom = staff["optom"]
        now = timezone.now()

        encounter, created = Encounter.objects.get_or_create(
            appointment=appointment,
            defaults={
                "patient": patient,
                "clinician": optom,
                "created_by": nurse,
                "chief_complaint": "Red, gritty eyes since yesterday, worse in the left eye.",
                "history": "Uses a daily contact lens. Slept in lenses two nights ago. No photophobia or discharge.",
                "blood_pressure": "118/74",
                "pulse": 68,
                "temperature_c": Decimal("36.8"),
                "weight_kg": Decimal("64.0"),
                "height_cm": Decimal("165.0"),
                "triage_notes": "Contact lens removed in clinic. Advised to avoid lens wear until reviewed.",
                "triaged_by": nurse,
                "triaged_at": now,
            },
        )
        if created:
            self.stdout.write(f"  Draft encounter for {patient.full_name} (triage recorded)")

    def _seed_future_appointment(self, staff, patient):
        optom = staff["optom"]
        reception = staff["reception"]
        target = timezone.make_aware(
            datetime.combine(timezone.localdate() + timedelta(days=3), time(10, 0))
        )
        appointment, created = Appointment.objects.get_or_create(
            clinician=optom,
            scheduled_at=target,
            defaults={
                "patient": patient,
                "created_by": reception,
                "appointment_type": AppointmentType.NEW,
                "reason": "First eye examination; school vision screening referral.",
                "status": AppointmentStatus.SCHEDULED,
            },
        )
        if created:
            self.stdout.write(
                f"  Future appointment {target:%d %b %H:%M} for {patient.full_name}"
            )
