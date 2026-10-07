# Mutual rescheduling verification

This is a local demonstration workflow. It does not move or refund funds and
does not create a second appointment.

## Rules implemented

- A patient or treating clinician may suggest a new time for a future `Booked`
  appointment before a consultation room exists.
- A single active proposal is allowed. A retry with the same actor, key and
  payload returns the original proposal; reusing the key with changed data is
  rejected.
- The proposed time must pass the existing generated-slot validator for the
  same active offering, approved clinician and service scope, duration and
  consultation format. Current clinician/patient conflicts, buffers, notice,
  horizon, date exceptions and published timezone schedule are rechecked.
- The original appointment continues occupying its slot while awaiting the
  other participant. Only the other participant can accept or decline; only the
  proposer can withdraw. A default 48-hour expiry is configurable with the
  site setting `tele_tena_reschedule_expiry_hours` (1–168 hours).
- Acceptance takes the existing global scheduling lock, repeats eligibility and
  slot validation, then updates the original appointment in place. Its ID,
  price, financial policy, disclosure snapshot and reservation are preserved.
  The resulting timeline event records the action. If the slot was claimed in
  the meantime, the proposal becomes unavailable and the old appointment stays
  booked.
- Declined, withdrawn, expired and superseded proposals do not mutate the
  appointment or create ledger/subledger postings. Cancellation closes a
  pending proposal. Past, pending-confirmation, started-call and finalized
  encounters cannot use this flow.

## Verification record

The additive `v1_15_mutual_rescheduling` patch was applied to the retained
isolated site `tele-tena-pr12-fresh.localhost` after a full site/database/files
backup, and `bench --site ... migrate` was repeated successfully. This is an
upgrade/repeat-migration check, not a fresh-site installation check.

On Frappe 15.121.2 / ERPNext 15.121.6 / Python 3.12.3, the complete presentation
suite passed 26 tests on the migrated site. Focused regressions also passed for
idempotent propose/accept, unauthorized participant and third-party access,
unchanged reservation and successful in-place movement, and a competing booking
making the proposed slot unavailable. The frontend production build and lint
completed; lint retains pre-existing warnings and Vite reports the existing
large LiveKit bundle warning. The packaged `/teletena/` browser journey passed
with independent synthetic patient and clinician sessions: patient selected a
server-generated slot and proposed it, clinician saw and accepted it, and the
appointment/proposal were confirmed persisted as `Booked`/`Accepted`. The
captured desktop screens are `docs/screenshots/mutual-rescheduling/`. This is
functional desktop evidence, not full responsive/accessibility acceptance. No
fresh install, physical-device, or native-language approval is claimed.

Appointment timeline events are presented as human-readable, localized labels;
internal event codes remain private to persistence and are not rendered to
participants. The regression suite checks the accepted-time label in the
patient's authorized timeline.

## Current integrated local checkpoint

The current branch source is `0660c0ae779e97c374c33553f226a3fbf3359b0f`;
the running production-built `/teletena/` asset manifest reports that exact
source SHA. The 390px patient-home screenshot is
`docs/screenshots/mutual-rescheduling/patient-home-390.png`. A fresh browser
context signed into the seeded patient, reached `/teletena/patient`, received
the service worker at `/teletena/sw.js`, and reported no page exceptions.

The correct credentials for this preview are stored privately at
`sites/tele-tena-pr12-fresh.localhost/private/tele_tena_review_accounts.json`.
The similarly named `/tmp/tele-tena-demo-credentials.json` belongs to
`erp.localhost` and does not authenticate against the isolated review site.
No account credentials are included here.

The invited-review browser check passes: the API reports phone OTP and public
registration disabled, the phone Continue action is disabled, and the email /
password alternative remains available. The real backend contact-auth suite
passes 7/7 with registration policy enabled inside its isolated test setup.

A disposable fresh install reached and passed app installation, schema, role,
guest-denial, and simulation-disabled assertions; its optional browser journey
then stopped at an obsolete homepage-heading expectation before auth testing.
That browser assertion has been updated to the current two-audience hero. The
fresh-install/browser harness has not yet been rerun after the correction.
Its cleanup removed the disposable database/site and temporary database admin
and credential file. The retained preview database and records were
fingerprinted unchanged.

A separate seeded clinician browser session opened
`/teletena/clinician/availability`; the weekly calendar and first configured
work interval were visible, there was no horizontal overflow, and no page
exception occurred. This was a read-only inspection; the existing schedule
was left unchanged. Screenshot:
`docs/screenshots/mutual-rescheduling/availability-1440.png`.

The production-route calendar regression also passed against the same URL:
field-level end-before-start error preserved the entered value; valid Monday
and Tuesday intervals were posted as `start_local`/`end_local`, saved (HTTP
200), and retained after reload; the patient booking page returned a
server-generated slot and completed one booking (HTTP 200). Before the test,
the clinician's schedule was saved to a private local snapshot and restored
afterward; the original appointment and balance records were not changed. The
test's new synthetic patient, deposit and booking were retained as additional
demonstration records. See `docs/screenshots/availability-regression/` for the
earlier full journey evidence.

At 390px, the clinician route uses the weekday agenda and time-field editor,
keeps the calendar grid hidden, and has no horizontal overflow. The editor now
keeps a sticky Save action reachable on mobile and translates its saving and
saved states. Screenshot:
`docs/screenshots/mutual-rescheduling/availability-390.png`.
