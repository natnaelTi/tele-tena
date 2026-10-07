# Clinic encounter access — initial scheduling-only slice

## Purpose and boundary

Clinic membership, clinic verification, and clinician affiliation do not reveal
appointments or clinical records. This slice lets a patient explicitly share
one confirmed appointment's scheduling details with one verified clinic to
which the treating clinician has a separately verified affiliation.

The grant is **scheduling coordination only**. It exposes service label,
scheduled time/timezone, delivery format, booked duration, appointment status,
and the patient identity permitted by that booking's disclosure snapshot.
It never exposes account email/phone, request narrative, saved history, private
notes, patient-shared summaries, feedback, balances, or other encounters.

Only active Clinic Manager and Scheduling memberships may read a grant. Billing
membership has no appointment access. The clinic owner is treated as a manager
for this operational query. Revoking membership immediately removes access;
revoking the patient grant or changing the appointment out of its active booked
state also removes access. The patient may revoke at any time. A grant expires
seven days after the scheduled end and cannot be renewed for a cancelled or
completed appointment.

## Workflow and acceptance

1. The patient opens their own confirmed appointment and sees only verified
   clinics with a currently verified affiliation for its treating clinician.
2. The patient chooses a clinic and confirms the scheduling-only disclosure.
3. The server records an immutable grant event with grantor, appointment,
   clinic, creation time, expiry and status. Repeating an active identical
   grant is idempotent.
4. Active clinic managers/schedulers can view only the granted appointment's
   minimized scheduling summary. Guessed appointment/grant identifiers, other
   clinics, Billing membership, ordinary clinician affiliation and generic
   DocType APIs are denied.
5. The patient revokes access. Repeating the same revoke is idempotent.

No clinic staff can confirm, cancel, reschedule, join, or document the
consultation in this initial slice. Those are separate authorized workflows.
