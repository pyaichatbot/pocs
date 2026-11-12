from django import forms

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        # Ownership and slot come from the server, never from editable inputs.
        fields = ["attendee", "purpose"]
        labels = {"attendee": "Attendee name", "purpose": "What is the meeting about?"}
        widgets = {
            "attendee": forms.TextInput(attrs={"autocomplete": "name"}),
            "purpose": forms.TextInput(attrs={"placeholder": "e.g. Project kickoff"}),
        }
