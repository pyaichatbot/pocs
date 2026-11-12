"""Three tables. Read top to bottom: resource → slot → booking."""
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Resource(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=160)

    def __str__(self):
        return self.name


class Slot(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    starts_at = models.DateTimeField()

    class Meta:
        ordering = ["starts_at", "resource__name"]
        constraints = [models.UniqueConstraint(
            fields=["resource", "starts_at"], name="unique_resource_start"
        )]

    def clean(self):
        if not self.starts_at:
            return  # The field itself reports a missing date.
        # Admin-created slots must align, or two 30-minute slots could overlap.
        start = timezone.localtime(self.starts_at) if timezone.is_aware(self.starts_at) else self.starts_at
        if start.minute not in (0, 30) or start.second or start.microsecond:
            raise ValidationError({"starts_at": "Start on the hour or half hour (seconds must be zero)."})

    @property
    def ends_at(self):
        # One duration keeps the first project easy to reason about.
        return self.starts_at + timedelta(minutes=30)

    def __str__(self):
        return f"{self.resource} · {self.starts_at:%d %b %H:%M}"


class Booking(models.Model):
    # Database rule: one slot can have only ONE booking, even across users.
    slot = models.OneToOneField(Slot, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attendee = models.CharField(max_length=80)
    purpose = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["slot__starts_at"]

    def __str__(self):
        return f"{self.attendee} — {self.purpose}"
