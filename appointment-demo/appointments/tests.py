"""Behavior tests: what must stay true when the code changes?"""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Resource, Slot


class BookingFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alex = get_user_model().objects.create_user("alex", password="test-password")
        cls.sam = get_user_model().objects.create_user("sam", password="test-password")
        cls.manager = get_user_model().objects.create_user("manager", is_staff=True)
        cls.resource = Resource.objects.create(name="Room A", description="Quiet room")
        cls.slot = Slot.objects.create(
            resource=cls.resource, starts_at=timezone.now() + timedelta(days=1),
        )

    def setUp(self):
        self.client.force_login(self.alex)
        self.url = reverse("book", args=[self.slot.pk])
        self.details = {"attendee": "Alex", "purpose": "Project kickoff"}

    def reserve(self, user=None):
        return Booking.objects.create(slot=self.slot, user=user or self.alex, **self.details)

    def test_anonymous_user_is_sent_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_valid_booking_redirects_to_confirmation(self):
        response = self.client.post(self.url, self.details)
        booking = Booking.objects.get()
        self.assertEqual(booking.user, self.alex)
        self.assertRedirects(response, reverse("confirmation", args=[booking.pk]))
        self.assertContains(self.client.get(response.url), "Project kickoff")

    def test_get_does_not_create_booking(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

    def test_blank_purpose_is_rejected(self):
        response = self.client.post(self.url, {"attendee": "Alex", "purpose": "   "})
        self.assertContains(response, "This field is required")
        self.assertFalse(Booking.objects.exists())

    def test_browser_cannot_choose_booking_owner(self):
        self.client.post(self.url, {**self.details, "user": self.sam.pk})
        self.assertEqual(Booking.objects.get().user, self.alex)

    def test_second_user_cannot_book_same_slot(self):
        self.reserve(self.sam)
        response = self.client.post(self.url, self.details)
        self.assertContains(response, "Someone just booked this slot")
        self.assertEqual(Booking.objects.count(), 1)

    def test_opening_booked_slot_does_not_crash(self):
        self.reserve()
        self.assertContains(self.client.get(self.url), "already booked")

    def test_admin_slots_must_start_on_a_half_hour(self):
        self.slot.starts_at = self.slot.starts_at.replace(minute=15)
        with self.assertRaises(ValidationError):
            self.slot.full_clean()
        self.slot.starts_at = self.slot.starts_at.replace(minute=30, second=0, microsecond=0)
        self.slot.full_clean()

    def test_database_also_rejects_duplicate_bookings(self):
        self.reserve()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.reserve(self.sam)

    def test_past_slot_cannot_be_booked(self):
        self.slot.starts_at = timezone.now() - timedelta(hours=1)
        self.slot.save()
        self.assertRedirects(self.client.post(self.url, self.details), reverse("schedule"))
        self.assertFalse(Booking.objects.exists())

    def test_owner_can_cancel_and_slot_can_be_rebooked(self):
        booking = self.reserve()
        response = self.client.post(reverse("cancel", args=[booking.pk]))
        self.assertRedirects(response, reverse("my_bookings"))
        self.assertFalse(Booking.objects.exists())
        self.client.force_login(self.sam)
        self.client.post(self.url, self.details)
        self.assertEqual(Booking.objects.get().user, self.sam)

    def test_other_user_cannot_cancel_or_view_booking(self):
        booking = self.reserve(self.sam)
        self.assertEqual(self.client.post(reverse("cancel", args=[booking.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("confirmation", args=[booking.pk])).status_code, 404)
        self.assertTrue(Booking.objects.exists())

    def test_cancellation_requires_post(self):
        booking = self.reserve()
        self.assertEqual(self.client.get(reverse("cancel", args=[booking.pk])).status_code, 405)
        self.assertTrue(Booking.objects.exists())

    def test_my_appointments_hides_other_users_bookings(self):
        self.reserve(self.sam)
        self.assertNotContains(self.client.get(reverse("my_bookings")), "Project kickoff")

    def test_staff_overview_is_restricted(self):
        self.assertEqual(self.client.get(reverse("overview")).status_code, 403)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("overview")).status_code, 200)

    def test_overview_counts_the_selected_day(self):
        self.reserve()
        self.client.force_login(self.manager)
        response = self.client.get(reverse("overview"), {"date": timezone.localdate(self.slot.starts_at)})
        self.assertEqual(response.context["booked_count"], 1)
        self.assertEqual(response.context["available_count"], 0)

    def test_default_schedule_opens_next_day_with_slots(self):
        response = self.client.get("/")
        self.assertEqual(response.context["day"], timezone.localdate(self.slot.starts_at))

    def test_bad_date_filters_do_not_crash(self):
        for value in ["hello", "2026-99-99", "9999-12-31", ""]:
            self.assertEqual(self.client.get("/", {"date": value}).status_code, 200)

    def test_schedule_filters_by_resource_and_hides_past_slots(self):
        other = Resource.objects.create(name="Other")
        day = timezone.localdate(self.slot.starts_at)
        response = self.client.get("/", {"date": day, "resource": other.pk})
        self.assertEqual(list(response.context["slots"]), [])
        response = self.client.get("/", {"date": day, "resource": self.resource.pk})
        self.assertEqual(list(response.context["slots"]), [self.slot])

    def test_csrf_token_is_required_for_booking(self):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.alex)
        self.assertEqual(browser.post(self.url, self.details).status_code, 403)
        page = browser.get(self.url)
        token = page.cookies["csrftoken"].value
        self.assertEqual(browser.post(self.url, {**self.details, "csrfmiddlewaretoken": token}).status_code, 302)

    def test_refresh_after_redirect_does_not_duplicate_booking(self):
        response = self.client.post(self.url, self.details)
        self.client.get(response.url)
        self.client.get(response.url)
        self.assertEqual(Booking.objects.count(), 1)

    def test_template_escapes_user_input(self):
        response = self.client.post(self.url, {**self.details, "purpose": "<script>alert(1)</script>"})
        self.assertContains(self.client.get(response.url), "&lt;script&gt;")

    @override_settings(TRACE_REQUESTS=True)
    def test_trace_reports_route_and_status_without_form_content(self):
        with patch("appointments.middleware.logger.info") as log:
            self.client.post(self.url, self.details)
        output = str(log.call_args_list)
        self.assertIn("302", output)
        self.assertIn("book", output)
        self.assertNotIn("Project kickoff", output)


class DemoDataTests(TestCase):
    @override_settings(DEBUG=True)
    def test_seed_is_repeatable_and_keeps_cancellations(self):
        call_command("seed_demo", stdout=StringIO())
        count = Slot.objects.count()
        self.assertEqual(count, 224)
        Booking.objects.all().delete()
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Slot.objects.count(), count)
        self.assertEqual(Booking.objects.count(), 0)
        self.assertTrue(get_user_model().objects.get(username="alex").check_password("LearnDjango!2026"))
