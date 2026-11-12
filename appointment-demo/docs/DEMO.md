# Five-minute management demo

## Prepare (before the meeting)

- Run `python start.py`. Keep the terminal running.
- Open the app at http://127.0.0.1:8000 in a normal browser and a private window.
- Sign in as `alex` in the normal window and `manager` in the private window.
- Choose a day that has available slots; note the date and resource.
- Use invented attendee details. No real personal information is needed.
- Keep `docs/LEARN.md` ready for technical questions.

## 0:00–0:30 · The problem

“We often coordinate appointments through messages. This prototype gives people
one place to find an opening, reserve it, and see what is coming up.”

## 0:30–2:00 · Book a meeting

As Alex, select a date and resource. Book an available time.
Use attendee **Alex Taylor** and purpose **Project kickoff**.
Show the confirmation and My appointments.

“The appointment is saved, and I can find it again without searching a message thread.”

## 2:00–3:00 · Show the shared picture

As Manager, open Team overview and select the same date. Show Alex's booking.
Open Book a time and show that the slot is now marked Booked.

“Availability is shared. The database prevents two bookings for the same slot.”

Optional: open the slot form in both browsers before booking. Submit one, then
submit the other. Show the friendly conflict message.

## 3:00–4:00 · Change plans

As Alex, open My appointments → Cancel appointment → Yes, cancel.
Refresh the manager's schedule and show that the slot is available again.

“People can manage their own appointments, and a cancelled time becomes reusable.”

## 4:00–5:00 · Explain value and scope

“This working prototype covers booking, conflict prevention, ownership, cancellation,
and a staff overview. It uses sample data and runs locally. It does not send invites
or integrate with our calendars yet.”

“Before expansion, I would pilot it with a small group and measure coordination time,
booking conflicts, and missed appointments. Reminders and calendar sync would follow
if the pilot shows they are needed.”

Do not claim measured savings, production readiness, or delivered calendar invites.

## Technical questions: a 30-second answer

“The browser sends a request. Django resolves its URL to a view. For a booking,
the view validates a ModelForm and saves through the ORM. The database enforces
one booking per slot. Django returns a redirect, and a new GET renders the confirmation.
Middleware wraps the process; you can see the requests and responses in the terminal.”

## Backup if time is short

Show only: book → confirmation → manager overview. That is one complete business story.
