"""A URL is the front door. Each route points to one view."""
from django.urls import path
from . import views

urlpatterns = [
    path("", views.schedule, name="schedule"),
    path("slots/<int:slot_id>/book/", views.book, name="book"),
    path("bookings/", views.my_bookings, name="my_bookings"),
    path("bookings/<int:booking_id>/", views.confirmation, name="confirmation"),
    path("bookings/<int:booking_id>/cancel/", views.cancel, name="cancel"),
    path("overview/", views.overview, name="overview"),
]
