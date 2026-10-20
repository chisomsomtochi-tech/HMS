from django.conf import settings


def clinic(request):
    """Expose clinic identity to every template."""
    return {
        "CLINIC_NAME": settings.CLINIC_NAME,
        "CLINIC_TAGLINE": settings.CLINIC_TAGLINE,
        "CLINIC_ADDRESS": settings.CLINIC_ADDRESS,
        "CLINIC_PHONE": settings.CLINIC_PHONE,
        "CLINIC_EMAIL": settings.CLINIC_EMAIL,
    }
