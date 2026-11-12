"""Repeatable local demo data. Existing passwords and bookings stay untouched."""
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from appointments.models import Booking, Resource, Slot


class Command(BaseCommand):
    help = "Create local demo users and seven days of 30-minute appointments."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo accounts are only allowed with DEBUG enabled.")
        users = {}
        for username, staff in [("alex", False), ("sam", False), ("manager", True)]:
            user, created = get_user_model().objects.get_or_create(
                username=username, defaults={"is_staff": staff, "first_name": username.title()},
            )
            if created:
                user.set_password("LearnDjango!2026")
                user.save()
            users[username] = user
        resources = []
        for name, description in [
            ("Discovery room", "A quiet space for planning and focused conversations."),
            ("Morgan Chen", "Project guidance, feedback and team check-ins."),
        ]:
            resource, _ = Resource.objects.get_or_create(name=name, defaults={"description": description})
            resources.append(resource)
        first_run = not Slot.objects.exists()
        today = timezone.localdate()
        for offset in range(7):
            for resource in resources:
                for hour in range(9, 17):
                    for minute in (0, 30):
                        starts_at = timezone.make_aware(datetime.combine(
                            today + timedelta(days=offset), time(hour, minute),
                        ))
                        Slot.objects.get_or_create(resource=resource, starts_at=starts_at)
        # Only seed sample bookings on the first run, so cancellations stay cancelled.
        if first_run:
            slots = Slot.objects.filter(starts_at__gt=timezone.now()).order_by("starts_at")[:3]
            for slot, purpose in zip(slots, ["Product discovery", "Quarterly planning", "Team check-in"]):
                Booking.objects.get_or_create(slot=slot, defaults={
                    "user": users["sam"], "attendee": "Sam Rivera", "purpose": purpose,
                })
        self.stdout.write(self.style.SUCCESS("Demo ready. New accounts: alex, sam, manager"))
        self.stdout.write("Password for newly created accounts: LearnDjango!2026")
