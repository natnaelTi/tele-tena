# Agreed product contract

## First internal demonstration
Adults 18+. English, Amharic and Afaan Oromo with native review before pilot.
Patient and clinician portals; administrator approval; independent and multi-clinic
clinicians; affiliations do not grant records access. Clinician recruitment and approval
belong to the doctor. Guided patient profile and private medical history.

Natural language request -> suggested service and eligible clinicians, with editable
filters and optional relevance feedback. No diagnostic claim. Eligibility precedes
ratings/proximity. Proximity is relevant particularly for in-person care.
Direct booking uses published price. Private open requests and clinician offers work;
competing clinicians cannot access offers. Accepted offer specifies fee, time, format,
expiry. Automatic or manual confirmation, slot holds/expiry, mutual rescheduling.

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
a simulation transaction log, not a subledger.

The one persistent “Demonstration environment — no real payments or clinical care”
ribbon communicates the boundary. Ordinary totals use “Balance”; activity detail
identifies simulated deposits/reservations/releases. This copy choice does not
enable real payments.
