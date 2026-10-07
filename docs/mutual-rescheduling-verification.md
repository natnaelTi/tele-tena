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
