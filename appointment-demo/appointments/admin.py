from django.contrib import admin
from .models import Booking, Resource, Slot

# Django supplies a complete staff editor in three lines.
admin.site.register(Resource)
admin.site.register(Slot)
admin.site.register(Booking)
