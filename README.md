# Suavedef Eye Clinic — Management MVP

A proof-of-concept clinic management system for an eye clinic, built with Django. It covers the front-desk and clinical workflow from patient registration through a completed eye examination and printed prescription.

**Stack:** Django 5.2 LTS · SQLite · server-rendered templates · Tailwind CSS + HTMX (CDN, no build step)

---

## What is included

- Staff sign-in with role-based access control
- Administrator-managed staff accounts, temporary passwords, forced password change, and password resets
- Patient registration with automatic medical record numbers (MRNs), search, and duplicate warnings
- Staff-scheduled appointments with overlap protection, check-in, cancellation, and no-show handling
- Eye-check encounters with triage, visual acuity, refraction, IOP, slit lamp/fundus findings, assessment, follow-up, and glasses prescriptions
- Five roles: Administrator, Receptionist, Nurse, Optometrist, Ophthalmologist
- Printable encounter summary and glasses prescription
- A seeded demo clinic with realistic staff, patients, appointments, and clinical records

**Not included (deliberately out of scope):** billing, pharmacy, inventory, lab, admissions, patient portal, SMS/email reminders, multi-branch support, and file uploads.

---

## Quick start

### Prerequisites

- Python 3.12+
- Windows, macOS, or Linux

### 1. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the environment (optional for local demo)

```powershell
Copy-Item .env.example .env
```

The app runs with development defaults if `.env` is not created. Edit `.env` to change the clinic name, contact details, timezone, or secret key.

### 4. Apply migrations and seed the demo

```bash
python manage.py migrate
python manage.py seed_demo
```

### 5. Run the server

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/**.

---

## Demo accounts

All demo accounts use the password **`Demo@1234`**.

| Username | Role | What they can do |
|---|---|---|
| `admin` | Administrator | Everything, including staff management and reopening completed encounters |
| `reception` | Receptionist | Register patients, book/reschedule/cancel appointments, check in |
| `nurse` | Nurse | Register patients, check in, start encounters, record triage |
| `optom` | Optometrist | Check in, start encounters, record the eye exam, complete visits, issue prescriptions |
| `ophth` | Ophthalmologist | Same clinical abilities as the optometrist |

The Django admin is also available at **`/admin/`** for the `admin` account.

> `seed_demo` is safe to run more than once; it will not duplicate demo records. It does reset the demo accounts' passwords to `Demo@1234`.

To start over with a clean database, stop the server and delete `db.sqlite3`, then re-run `python manage.py migrate && python manage.py seed_demo`.

---

## Role and capability matrix

| Capability | Admin | Reception | Nurse | Optometrist | Ophthalmologist |
|---|:--:|:--:|:--:|:--:|:--:|
| Manage staff accounts | ✓ | | | | |
| View patients | ✓ | ✓ | ✓ | ✓ | ✓ |
| Register / edit patients | ✓ | ✓ | ✓ | | |
| View clinical data | ✓ | | ✓ | ✓ | ✓ |
| Book / reschedule / cancel appointments | ✓ | ✓ | | | |
| Check in / mark no-show | ✓ | ✓ | ✓ | ✓ | ✓ |
| Start encounter | ✓ | | ✓ | ✓ | ✓ |
| Record triage | ✓ | | ✓ | ✓ | ✓ |
| Record eye exam | ✓ | | | ✓ | ✓ |
| Finalize encounter | ✓ | | | ✓ | ✓ |
| Issue prescription | ✓ | | | ✓ | ✓ |

Receptionists see patient demographics and appointments, but never clinical findings. Nurses can triage and start encounters, but cannot record the eye exam or finalize a visit. Completed encounters are locked; only an administrator can reopen one.

---

## Suggested demo walkthrough

1. **Sign in as `reception`.**
   - Register a patient from **Patients → Register patient**. Note the generated MRN.
   - Start typing a phone number that already exists — the duplicate warning appears as you type.
   - Book an appointment from the patient record (or **Appointments → Book appointment**), then check the patient in.
2. **Sign in as `optom`.**
   - Open the checked-in appointment and choose **Start encounter**.
   - Record triage, the eye examination, assessment, and prescription.
   - Choose **Save & complete**. The appointment is marked completed.
   - Print the encounter summary and the glasses prescription.
3. **Sign in as `nurse`.** Confirm triage access, but no eye-exam or finalize controls.
4. **Sign in as `reception`.** Confirm clinical records are not visible.
5. **Sign in as `admin`.**
   - Create a staff account under **Staff**. The new user is forced to change their password at first sign-in.
   - Reset a password, deactivate a user, or reopen a completed encounter.

The seeded data includes a completed encounter with a prescription, a draft encounter with triage recorded, and a full day of appointments in different states.

---

## Tests

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check
```

The suite covers:

- MRN generation and uniqueness
- Appointment overlap rules, cancellation, check-in, and no-show transitions
- Every role gate (including receptionist restrictions on clinical data)
- Triage vs. exam permissions
- Completion requires an impression, and completed records are locked
- Prescription creation and printable output
- Administrator reopening of completed encounters
- A full registration → booking → check-in → encounter → completion flow

---

## Project structure

```text
config/           project settings, root URLconf, WSGI/ASGI
core/             dashboard, shared base model, template filters, demo seed command
accounts/         custom user model, roles, capabilities, middleware, staff management
patients/         patient model, MRN generation, registration, search, duplicate checks
appointments/     scheduling, overlap validation, status workflow
encounters/       triage, eye exam, assessment, prescription, print views
templates/        base layout, partials, and page templates
static/           app.css (print refinements) and app.js (small UI helpers)
```

### Key implementation notes

- The custom user model is used from the first migration (`AUTH_USER_MODEL = "accounts.User"`), so the project can grow without a painful user-model migration later.
- Capabilities live in `accounts/permissions.py`; the same map drives views, navigation, and button visibility.
- MRNs use the pattern `MRN-{year}-{pk:05d}` and are assigned immediately after the first insert.
- Appointments validate overlap in `Appointment.clean()` and also carry a conditional unique constraint for active clinician slots.
- Completed encounters cannot be edited through the UI; `Encounter.reopen()` is admin-only.
- Tailwind and HTMX load from CDN for zero-build local demos. For an offline or production deployment, compile Tailwind locally and vendor HTMX.

---

## Configuration

Settings are read from `.env` with safe development defaults:

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | development key | Set a long random value outside local development |
| `DJANGO_DEBUG` | `True` | Set to `False` for production |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames |
| `CLINIC_NAME` | `Suavedef Eye Clinic` | UI and printed letterhead |
| `CLINIC_TAGLINE` | `Comprehensive eye care` | Printed letterhead |
| `CLINIC_ADDRESS`, `CLINIC_PHONE`, `CLINIC_EMAIL` | demo values | Printed letterhead |
| `TIME_ZONE` | `Africa/Lagos` | Clinic local time |

When `DEBUG=False`, the project enables HTTPS redirects, secure cookies, and HSTS. Review those settings before deploying behind a real domain.

---

## Production notes

This is an MVP intended for demonstration and iteration. Before using it with real patient data:

- Move to PostgreSQL and set a strong `DJANGO_SECRET_KEY`.
- Compile/vendor the frontend assets instead of relying on CDNs.
- Add audit logging for clinical record changes and prescription issuance.
- Add backups, monitoring, and a formal data-retention policy.
- Review clinical content and prescription wording with a qualified clinician.
- Add rate limiting and stronger authentication controls appropriate to your jurisdiction.
