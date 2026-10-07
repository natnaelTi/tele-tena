# Agreed product contract

Credential lifecycle update (2026-10-08): future booked or pending-confirmation
appointments affected by expired or revoked scopes receive a logistics-only
operational review flag. It does not change appointment or financial state and
does not expose patient records to vetting reviewers. Human operational
continuity policy remains required.

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
approval, exact active service scope, language, format, an enabled service policy
for immediate care, fresh presence for immediate care, and feasible full-duration
availability. A bounded set
of eligible clinicians receives minimum-necessary disclosure, and each offer is
visible only to its author and the patient. Acceptance revalidates the offer and
uses the existing appointment, price snapshot and atomic reservation flow. This
workflow and dependent vetting/routing changes remain under review; its business
outcome target is measured, never guaranteed. Offers do not hold slots or funds. Automatic or
manual confirmation, slot holds/expiry, mutual rescheduling.

Global disclosure preferences plus request overrides and exact sharing preview.
Account identity, consultation disclosure and public review identity are distinct.
Couples have individual consent and optional mutually accepted relationship links;
paying or partnership does not grant private record access.

Real voice/video, audio-only option, clinician notes, patient-authorized summaries,
follow-up booking, and one structured patient session-experience rating per
completed encounter. Clinician profile indicators keep patient experience,
immediate-inbox offer response, clinician-attributed cancellations, and approved
credentials/scopes separate. Patient experience is distinct from clinical
competence and outcomes; aggregates suppress rates/averages below a minimum
sample. No-show attribution and free-text review moderation remain unimplemented.
Email links to an authenticated summary;
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

## Expanded approved product scope (2026-10-07)

The product target now includes complete human-led vetting and per-scope
credential evidence uploads and immutable revision references, a versioned service catalog, distinct trust indicators,
private progressive open-request routing, the balanced demonstration earnings
lifecycle and explicitly funded extensions. It also includes explicit clinic
membership and encounter grants, adult couples/family consent, laboratory and
diagnostics workflows, subscriptions, second opinions, medical-tourism
coordination, and their focused administrator operations. These additions are
approved implementation scope, not evidence of completion. Every capability
must use persisted Frappe models, server-enforced authorization, auditable state
transitions, connected-browser evidence and its own integration/partner gates.

The design source is the extracted 142-screen inventory at
`/home/frappe/teletena-design-reference`; it is a visual/interaction reference,
not a system of record. Natural-language need descriptions may suggest a service
category but must not create or imply diagnoses. Patient requests remain private;
matching cannot relax an explicit scope, credential, age, format, language,
consent, availability or budget condition. An offer does not reserve funds or a
slot. Acceptance must revalidate authorization and create one appointment and
one reservation atomically.

Clinic membership never grants blanket access to clinical records. Shared adult
care requires each participant's separate identity, consent and disclosure.
Laboratory results require a real partner, specimen chain-of-custody and human
review before release. Second-opinion and medical-travel estimates are
conditional, not treatment guarantees or confirmed capacity. Subscriptions may
not gate basic personal-record access. No paid ranking is permitted.

The demonstration finance target adds balanced immutable subledger postings,
owner-by-owner legacy reconciliation and explicit mismatch holds, scheduled
earnings release, dispute holds, reserved/cancellable payout requests and
prefunded consent-based extensions. It remains separate from custody, payment
providers and ERPNext accounting. A legacy discrepancy requires a reasoned,
audited reviewer decision; no migration may rewrite or delete it.

## Commercial direction
Free patient discovery/booking; consultation charges; clinician bring-your-own-patient
links. Acquisition belongs to patient-clinician relationship. Layered clinician/clinic
workspace and later patient convenience subscriptions. Basic record access/export is
not a subscription hostage. No paid clinical ranking.

## External and policy gates
Real-money provider authorization, payment integration activation, actual fees,
policy windows/caps, dispute operations, production safety/escalation protocol,
SMS provider, LiveKit credentials, translated clinical copy review, production hosting.
Labs, diagnostics, diaspora expert access and tourism are future workflows.
The first demonstration uses synthetic data and is not production clinical readiness.

### Credential expiry and re-verification (demonstration)

Credential expiry is evaluated against the site's Frappe date. An expired
credential immediately disqualifies its service scope from new discovery,
offering publication, matching and bookings, while existing appointments and
their accepted snapshots remain unchanged. An applicant can create a separate
scope re-verification application, submit fresh private license/registration
evidence, and receive a new human decision. Pending renewal does not extend an
expired scope; a still-valid old credential remains in effect until its date.
Rejecting renewal evidence does not revoke that still-valid prior credential,
while explicit suspension or expiry does. Jurisdiction-specific timezone/date
rules, reminders, grace periods and operations for appointments after expiry
remain policy decisions. See `scope-reverification.md`.

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
records simulated availability of earnings; it does not transfer money. No-show
decisions, notifications, real payments/accounting, physical-device call quality
and production clinical readiness remain outside the implemented contract; the
delivery tracker is authoritative for pending scope.

The versioned v1.8 reconciliation imports known legacy deposit, reservation and
release events created after each v1.7 wallet opening snapshot into balanced,
idempotent journals. v1.13 audits each owner against both the original activity
log and wallet/subledger projection, recording unknown events and exact snapshot
boundary ambiguity without rewriting records. A mismatched owner is held until
an authorized, reasoned decision accepts the unchanged wallet snapshot for
future demo operations; the historical mismatch remains visible. Unknown legacy
event kinds stop for review. A deployment cutover stops all old web and
background writers before migration, then verifies owner-by-owner wallet and
subledger equality or records an explicit hold before starting matching code.
# Returning care and previous clinicians

The patient workspace may offer a returning-care shortcut only for clinicians
with whom that signed-in patient has a completed appointment. The query is
patient-authorized and returns an opaque public profile key, the clinician's
public display name, the latest booked session instant, and that patient's
completed-session count. It does not join or infer relationships from another
patient's encounters. A clinician appears only while enabled, manually approved,
and holding a current approved scope with a published active offering and
schedule. Historical appointments remain unchanged when an offering is no
longer eligible; the clinician is then omitted from this shortcut and remains
available in the patient's appointment history.

The current slice is implemented in the patient dashboard and backend query.
Fresh-site Frappe permission/database and browser verification are pending; it
must not be represented as locally verified until those checks pass.

## Clinic registration and affiliation (initial slice)

Clinic registration and clinician affiliation are separate human-reviewed
records. A clinician or applicant may submit a clinic profile with legal name,
registration reference, jurisdiction and a non-sensitive public description.
An authorized reviewer records Verified, Rejected or Suspended with an audited
reason. Registration references and legal names are visible only to the
applicant and authorized reviewers; the clinician-facing directory returns
verified public clinic name and jurisdiction only.

A clinician or applicant may request an affiliation with a verified clinic and
submit a role and evidence summary. A reviewer may verify, request clarification,
reject or revoke that affiliation. Re-submission after clarification keeps the
same record and review history; repeat identical submissions are idempotent.
The affiliation never grants service-scope approval, request eligibility,
appointment access or patient-record access. A clinic verification or
affiliation cannot be used to create or approve a `Tele Tena Service Scope`.

This is an initial registry/affiliation workflow. A separate operational
membership workflow lets a verified clinic's submitting manager invite a
staff email into one of three limited roles: Clinic Manager, Scheduling, or
Billing. The invitee must sign in and prove possession of the exact invited
email before accepting. Invitations are not emailed by this local slice; they
are visible only after the invited contact is verified. Managers can revoke
active memberships with a recorded reason. Membership grants no clinical
service authority and no patient or appointment access by itself. A patient may
separately grant one verified clinic scheduling-only access to a single future
confirmed encounter when the treating clinician has a verified affiliation. The
projection contains only the booking-approved identity label and appointment
logistics; it excludes notes, contact details, request text, history, balances,
and other encounters. The patient may revoke at any time; membership revocation,
expiry, cancellation, or completion also closes access. This does not grant
clinical-record access. The
Scheduling and Billing roles are currently descriptive and do not expose
calendar, resource, or billing capabilities. Clinic Manager may manage clinic
memberships only. Clinic verification and affiliation never enable clinic
calendars/resources, clinic billing, explicit encounter grants, or clinic-wide
patient records. Existing narrative affiliation fields are preserved and are
not automatically converted into verified affiliations. Native DocType schema
is additive and synchronized by normal Frappe migration.

Verified Clinic Manager and Scheduling memberships (and a verified clinic
owner) expose a separate `/clinic` operational workspace. A pending invitation
appears only after the exact email is verified, and an account without a patient
or clinician profile can be routed to that invitation workspace after sign-in.
This session flag is navigation only: each clinic API independently checks
membership, role, clinic status, and encounter-specific patient permission.
Billing membership does not unlock the scheduling workspace. Invitation
delivery is not configured; out-of-band coordination is still required.


## Clinic encounter access (scheduling-only initial slice)

A patient may grant one verified clinic scheduling-only access to a single
future confirmed appointment when the treating clinician has a separately
verified affiliation with that clinic. Active Clinic Manager and Scheduling
members can view only service, appointment time/timezone, format, duration,
status and the identity label already permitted by that encounter's accepted
disclosure. Billing membership grants no appointment access. The grant expires
seven days after the scheduled end, can be revoked by the patient, and closes
when the appointment is cancelled/completed or the membership is revoked. It
does not allow joining, confirmation, cancellation, rescheduling, notes, shared
summary, contact details, request text, profile history, balances, or access to
other encounters. This is not a clinic-wide record grant or shared calendar.

## Mutual appointment rescheduling (demonstration)

Either booked participant may propose a new time before the appointment begins
and before a consultation room has been created. The proposal must match a
server-generated slot for the same active offering, currently approved service
scope, duration and consultation format. The existing appointment continues to
occupy its original slot until the other participant explicitly accepts. At
acceptance, a global scheduling lock rechecks approval, schedule and conflicts
while excluding only the appointment being moved. If the proposed time became
unavailable, the proposal closes as unavailable and the original booking remains
unchanged. Decline, withdrawal, expiry or supersession never changes the booking
or moves money. Acceptance updates the existing appointment and writes an audit
event; price, policy and disclosure snapshots, appointment identity and the
single existing reservation are preserved. The demonstration proposal expiry is
48 hours by default and configurable per site; it is not a production policy.
See `mutual-rescheduling-verification.md` for the current implementation and
verification state.
