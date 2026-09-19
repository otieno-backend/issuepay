import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the production admin account from environment variables."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            self.stdout.write(
                self.style.WARNING(
                    "Superuser environment variables are not set. Skipping."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        user.email = email
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "created" if created else "updated"

        self.stdout.write(
            self.style.SUCCESS(
                f"Production admin '{username}' {action} successfully."
            )
        )
