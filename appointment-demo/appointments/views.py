"""Read each view in three steps: receive → decide → respond."""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods, require_POST

from .forms import BookingForm
from .models import Booking, Resource, Slot


def selected_day(request):
    # A manually edited URL should not crash the page.
    try:
        day = parse_date(request.GET.get("date", ""))
        return day if day and 1900 <= day.year < 9999 else timezone.localdate()
    except ValueError:
        return timezone.localdate()


@login_required
def schedule(request):
    day = selected_day(request)
    if not request.GET.get("date"):
        # After office hours, open the next day with slots instead of an empty page.
        next_slot = Slot.objects.filter(starts_at__gt=timezone.now()).first()
        if next_slot:
            day = timezone.localdate(next_slot.starts_at)
    slots = Slot.objects.filter(starts_at__date=day, starts_at__gt=timezone.now())
    resource = request.GET.get("resource", "")
    if resource.isdecimal():
        slots = slots.filter(resource_id=resource)
    # Fetch related objects together. Avoid a separate query for every row.
    slots = slots.select_related("resource", "booking")
    return render(request, "appointments/schedule.html", {
        "slots": slots, "day": day, "resources": Resource.objects.all(),
        "selected_resource": resource, "tomorrow": day + timedelta(days=1),
    })


@login_required
@require_http_methods(["GET", "POST"])
def book(request, slot_id):
    slot = get_object_or_404(Slot.objects.select_related("resource"), pk=slot_id)
    # Stop early. Old links cannot reserve a past appointment.
    if slot.starts_at <= timezone.now():
        messages.error(request, "That appointment has already started. Choose a later slot.")
        return redirect("schedule")
    form = BookingForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.user = request.user
        booking.slot = slot
        try:
            # Keep the write atomic. The database decides who gets the slot.
            with transaction.atomic():
                booking.save()
        except IntegrityError:
            # A second submission may arrive after the page was opened.
            form.add_error(None, "Someone just booked this slot. Please choose another.")
        else:
            # Redirect = a NEW GET request. Refresh will not submit the form again.
            return redirect("confirmation", booking_id=booking.pk)
    elif Booking.objects.filter(slot=slot).exists():
        messages.error(request, "This slot is already booked. Please choose another.")
    return render(request, "appointments/book.html", {"form": form, "slot": slot})


@login_required
def confirmation(request, booking_id):
    # Include the owner in the query. Guessing another ID gives a 404.
    booking = get_object_or_404(
        Booking.objects.select_related("slot__resource"),
        pk=booking_id, user=request.user,
    )
    return render(request, "appointments/confirmation.html", {"booking": booking})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(
        user=request.user, slot__starts_at__gt=timezone.now(),
    ).select_related("slot__resource")
    return render(request, "appointments/bookings.html", {"bookings": bookings})


@login_required
@require_POST
def cancel(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    # MVP choice: deleting frees the slot. Cancellation history is not retained.
    booking.delete()
    messages.success(request, "Appointment cancelled. The slot is available again.")
    return redirect("my_bookings")


@login_required
def overview(request):
    if not request.user.is_staff:
        raise PermissionDenied
    day = selected_day(request)
    slots = Slot.objects.filter(starts_at__date=day)
    bookings = Booking.objects.filter(slot__in=slots).select_related("slot__resource", "user")
    return render(request, "appointments/overview.html", {
        "day": day, "bookings": bookings, "booked_count": bookings.count(),
        "available_count": slots.filter(booking__isnull=True, starts_at__gt=timezone.now()).count(),
    })
