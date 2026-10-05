# Agreed product contract

## First internal demonstration
Adults 18+. English, Amharic and Afaan Oromo with native review before pilot.
Patient and clinician portals; administrator approval; independent and multi-clinic
clinicians; affiliations do not grant records access. Clinician recruitment and approval
belong to the doctor. Guided patient profile and private medical history.

Natural language request -> suggested service and eligible clinicians, with editable
filters and optional relevance feedback. No diagnostic claim. Eligibility precedes
ratings/proximity. Proximity is relevant particularly for in-person care.
Direct booking uses published price. Private open requests distinguish immediate
care-seeking from scheduled care; deterministic eligibility requires current
approval, service scope, language, format and valid availability. A bounded set
of eligible clinicians receives minimum-necessary disclosure, and each offer is
visible only to its author and the patient. Acceptance revalidates the offer and
uses the existing appointment, price snapshot and atomic reservation flow. This
workflow is under review on `feat/open-requests`; its business outcome target is
measured, never guaranteed. Offers do not hold slots or funds. Automatic or
manual confirmation, slot holds/expiry, mutual rescheduling.

Global disclosure preferences plus request overrides and exact sharing preview.
Account identity, consultation disclosure and public review identity are distinct.
Couples have individual consent and optional mutually accepted relationship links;
paying or partnership does not grant private record access.

Real voice/video, audio-only option, clinician notes, patient-authorized summaries,
follow-up booking, completed-session ratings. Email links to an authenticated summary;
no sensitive summary in notification body. No recording/transcription by default.

Simulated deposits; available/reserved patient funds; pending/available clinician earnings;
payout processing. Atomic balance/slot reservations; no negative balances. Fixed-duration
sessions; explicit mutual consent and funds reservation for paid extensions. Complimentary
extensions explicit. Connection time alone never authorizes charging. Future hourly
pricing has explicit rates, increments, limits and rounding policies.

Cancellation defaults differ by actor. Clinicians configure within platform limits;
accepted price/policy versions are immutable snapshots. Disputes hold relevant earnings.
Unused funds refundable through verified supported routes. On-demand and scheduled
withdrawals after configured withholding period; external settlement is not instant.

## Commercial direction
Free patient discovery/booking; consultation charges; clinician bring-your-own-patient
links. Acquisition belongs to patient-clinician relationship. Layered clinician/clinic
workspace and later patient convenience subscriptions. Basic record access/export is
not a subscription hostage. No paid clinical ranking.

## Deferred or unresolved
Real-money provider authorization, payment integration activation, actual fees,
policy windows/caps, dispute operations, production safety/escalation protocol,
SMS provider, LiveKit credentials, translated clinical copy review, production hosting.
Labs, diagnostics, diaspora expert access and tourism are future workflows.
The first demonstration uses synthetic data and is not production clinical readiness.

Hosted review contact access is an explicit site-scoped option. Phone OTP sign-in,
new adult patient registration and new clinician applications may be enabled
independently on the bound review site. Contact proof starts guided onboarding;
it does not grant clinician approval or service scopes. Reviewer password access
and the single demonstration-environment disclosure remain in place. Public
Frappe signup and real payments stay disabled. See `hosted-phone-access.md`.

## Presentation release operational rules (2026-10)

Scheduling and lifecycle are governed by `presentation-release-model.md`. Weekly
availability uses clinician-selected IANA timezones; appointments store UTC
instants plus the timezone used at booking. Editing a schedule never changes an
existing appointment. Pending manual-confirmation bookings hold both slot and
simulated funds. The demonstration expiry is 24 hours, configurable; expiry and
decline release funds exactly once. These are demo defaults, not commercial policy.

Completion requires an explicit clinician action after End and documentation.
Call state, appointment state and note state are separate. Past clock time alone
does not imply completion or no-show. Clinician notes are private by default;
patient summaries are separately published and revisioned. Previously published
content remains in a visible sharing history if later amended.

Cancellation is currently limited to before the scheduled start. The explicit
demonstration policy returns the full reserved amount for an authorized pre-start
cancellation, exactly once. This is not a production cancellation/refund promise.
No time-based or call-duration earnings release is permitted. `tt_ledger` remains
an append-only simulation activity log. The additive `tt_journal` tables implement
a separate balanced demonstration subledger for deposits, reservations, completion,
release and payout reservation; this does not constitute ERPNext posting, custody,
real payment or settlement.

The one persistent “Demonstration environment — no real payments or clinical care”
ribbon communicates the boundary. Ordinary totals use “Balance”; activity detail
identifies simulated deposits/reservations/releases. This copy choice does not
enable real payments.

## Presentation behavior now implemented

Clinicians can publish IANA-timezone weekly schedules with date exceptions,
multiple intervals, buffers and confirmation preference. Patients may choose
only server-generated, still-open slots; booking serializes conflicts and fund
reservation. Existing appointments retain their saved instant and policy/disclosure
snapshots when schedule rules change.

Appointment, call and documentation status are distinct. End closes the call and
revokes participant identities but does not complete a consultation or release
earnings. The treating clinician explicitly saves and finalizes versioned private
notes and may separately publish a patient summary. Patients receive only
published summary revisions. Reviewers may access private PDF application
evidence, but neither that role nor a clinic relationship grants patient-record
access. The PWA provides only public static caching and a generic offline page;
it never reports that offline changes were saved.

These are demonstration workflows. The clinician earnings workflow uses an
explicit zero-fee default, a booking-time policy snapshot, a configurable
dispute hold, audited financial disputes and reserved payout requests. Historical
completed appointments that still hold funds migrate to review-only `LegacyHold`
records and are never settled automatically. A dispute/refund after release or an
open payout is unsupported and must stop for authorized review. The scheduler
records simulated availability of earnings; it does not transfer money. Mutual
rescheduling, no-show decisions, notifications, real payments/accounting,
physical-device call quality and production clinical readiness remain outside
the implemented contract; the delivery tracker is authoritative for pending scope.

The versioned v1.8 reconciliation imports known legacy deposit, reservation and
release events created after each v1.7 wallet opening snapshot into balanced,
idempotent journals. It preserves the wallet projection, original activity log,
appointments and reserved obligations. Unknown legacy event kinds stop for
review. A deployment cutover stops all old web and background writers before
migration, then verifies wallet/subledger equality before starting matching code.
