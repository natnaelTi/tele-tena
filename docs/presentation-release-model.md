# Presentation release state and policy model

This is the pre-implementation contract for recurring availability,
appointments, consultation rooms, notes and cancellations. Existing appointment
instants and disclosure snapshots are preserved; migrations add nullable metadata
and new private tables only. No migration infers historical outcomes.

## Persisted state machines

| Domain | States | Transition authority |
|---|---|---|
| Appointment | `PendingConfirmation`, `Booked` (legacy confirmed), `Cancelled`, `Expired`, `Completed`, `NoShow` | Patient request creates; clinician confirms/declines; scheduled expiry worker expires; patient or treating clinician cancels only before scheduled start; treating clinician completes after ending call and finalizing documentation. `NoShow` requires an explicit authorized action and is not assigned by clock. |
| Consultation/call | `NotStarted` (no row), `Open`, `Ended` | Either appointment participant may join/rejoin inside appointment window; only the treating clinician may end; End is terminal and revokes both participant identities. It does not complete the appointment. |
| Documentation | `None`, `Draft`, `Finalized` | Treating clinician saves draft; finalizes only after call End. Finalized revisions are immutable; amendment creates a new revision. |
| Summary visibility | `Private`, `Published` per revision | Treating clinician explicitly publishes the patient-summary portion during finalization/amendment. Patient query returns only published revisions. Previously published revisions stay in the access/history result after later amendments. |
| Schedule | `Draft`, `Published`, `Paused` | Clinician owns edit/publish/pause. Changes affect generated future slots only and never move/cancel existing appointments. |

Appointment status, call status and documentation status are stored/queried
separately. UI groupings are projections, never lifecycle transitions: Upcoming is
future Booked; Needs action includes a pending request and an ended call without
finalized notes; In progress is Open; Past includes terminal appointments and
elapsed Booked records. An elapsed booking with no explicit outcome is labeled
“Past · outcome not recorded”; it is not silently Completed or NoShow. A call End
is shown as “Call ended” regardless of documentation status.

## Scheduling model

Schedules use an IANA timezone and wall-clock weekly intervals keyed by weekday.
An offering has one clinician-owned schedule with zero or more intervals per day.
Date exceptions can mark a whole local date unavailable, replace weekly intervals,
or block a local break interval. Slot generation applies the offering's fixed
duration, schedule format, lead notice, booking horizon and before/after buffers.
An ambiguous/nonexistent DST wall time is omitted instead of guessed. Slot
instants are returned in UTC with the schedule timezone. Booking saves both the
UTC instant and the timezone label used at booking. A later timezone edit does
not shift a saved instant.

Any clinician conflict is checked under a clinician lock across all offerings;
buffered intervals are included. A patient's existing overlapping appointment is
also a conflict. Only server-generated slots can be booked. Existing one-off
availability rows remain readable for historical compatibility; new schedules do
not rewrite them. Changing or pausing schedule rules never edits appointments.

## Explicit demonstration defaults (configurable)

- Confirmation mode defaults to **automatic**, matching existing direct booking;
  a clinician may select manual mode per schedule.
- Manual request hold expires after **24 hours** (`tele_tena_pending_expiry_hours`);
  this is a demonstration default, not an agreed production SLA.
- Default notice is **60 minutes**, horizon **60 days**, buffers **0 minutes**,
  schedule format **video**. These can be changed by the clinician; format may be
  audio or video.
- A request in manual mode reserves the chosen slot and patient's full simulated
  price. Decline, expiry or supported pre-start cancellation releases that amount
  once under the appointment row lock.
- Cancellation is supported only before the scheduled start in this release. The
  demo cancellation policy `demo-full-release-before-start-v1` returns the full
  reservation; it is explicitly not a production fee/refund policy. No release
  or clinician earning is triggered by call duration or End.

## Private records and files

Only the treating clinician may read/edit a consultation's private note. The
patient-facing query selects published summary revisions only and never selects
the private-note column. Approver and clinic roles gain no clinical access.
Care-directory results group only encounters for the same treating clinician
whose bookings explicitly shared the exact same non-empty alias. No patient
account identifier is returned. A masked encounter is keyed and opened only by
its opaque appointment reference and is never joined to another encounter;
different disclosed aliases remain separate groups. Each detail response carries
that booking's disclosure snapshot. Resume PDFs are private, max 5 MiB,
magic-checked server-side, and
downloaded through an authorization-checking endpoint; evidence does not establish
credential validity.

## Tours and PWA

Tour dismiss/completion is stored by account, role, tour ID and content version.
Replay is always available. No tour executes a mutation. The service worker stores
the public shell assets and generic offline document only; APIs, authenticated
responses, private files and financial/clinical data remain network-only. It never
forces a page reload; updates wait for the client's normal close lifecycle.

## Demonstration earnings ledger (v1.7)

`tt_ledger` remains the prior append-only simulation activity log. The v1.7
balanced `tt_journal`/`tt_journal_line` subledger separately records opening
balance snapshots, deposits, reservations, supported releases, finalization,
earnings release, disputes, refunds and payout reservations. It is not ERPNext
accounting or an external money movement system. Every posting has an immutable
event reference/idempotency key; wallet projections are checked before patient
fund changes.

The demonstration defaults are zero platform fee and a 60-minute dispute window
after explicit clinician finalization. Each booking stores the configured fee and
window; later configuration changes do not alter accepted transactions. No
earnings accrue at call End. Finalization atomically consumes the patient
reservation and creates clinician pending earnings once. The scheduled process
runs every five minutes and posts eligible earnings using server time. A dispute
committed before release blocks it under a shared lock; if release wins first,
the patient dispute endpoint rejects the request and the case requires separate
authorized review. Automated refunds after release or while payout is requested
are unsupported. No negative balances or edits to historical postings are
allowed. Payout requests reserve only available earnings; cancelling a Requested
payout releases that reservation once. Current payout states are `Requested`
and `Cancelled`; no processing or paid claim is exposed because no transfer
occurs.

On migration, existing wallet values receive one balanced opening snapshot while
the legacy activity log remains unchanged. Completed appointments with reserved
funds are marked `LegacyHold`, preserved for review, and never automatically
settled or released. See `demo-earnings-model.md` for account mappings and the
acceptance arithmetic.
