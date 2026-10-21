
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create an initial admin account from environment variables."

    def handle(self, *args, **options):
        User = get_user_model()
        username_field = User.USERNAME_FIELD

        username = os.environ.get(
            f"DJANGO_SUPERUSER_{username_field.upper()}"
        )
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            raise CommandError(
                f"Set DJANGO_SUPERUSER_{username_field.upper()} "
                "and DJANGO_SUPERUSER_PASSWORD."
            )

        lookup = {username_field: username}
        user = User._default_manager.filter(**lookup).first()

        if user:
            self.stdout.write(
                self.style.WARNING(
                    f"User '{username}' already exists; leaving it unchanged."
                )
            )
            return

        user = User(**lookup)

        if hasattr(user, "email"):
            user.email = email

        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)

        user.save()

        self.stdout.write(
            self.style.SUCCESS(f"Superuser '{username}' created successfully.")
        )
