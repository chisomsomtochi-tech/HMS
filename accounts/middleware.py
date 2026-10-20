from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """Redirect accounts created by an administrator to the password form."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.must_change_password:
            allowed_paths = {
                reverse("accounts:password_change"),
                reverse("accounts:logout"),
            }
            path = request.path
            if (
                path not in allowed_paths
                and not path.startswith(settings.STATIC_URL)
                and not path.startswith("/admin/")
            ):
                return redirect("accounts:password_change")
        return self.get_response(request)
