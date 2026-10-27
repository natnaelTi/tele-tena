## Direct Telebirr Revision — 27 October 2026

The requested MVP payment model is Offline Direct Payment, subject to explicit
financial-administrator selection after deployment. Installation/upgrade keeps
Wallet and never changes the remote mode automatically. Each appointment keeps
its original mode, quote and policy. Existing wallet balances, holds, postings,
disputes, release/payout history and credentials are preserved.

Offline intents reserve appointment capacity, not money. The authorized payer
transfers externally to the snapshotted clinician receiving number, then submits
a private receipt and transaction reference. The receiving clinician records a
human verification, independently of appointment acceptance. A submitted image
is not verified receipt. No platform custody, fee collection, automated refund,
settlement or payout follows. Late/mismatched/disputed claims stay auditable in
reconciliation/refund states. An extension needs its own consent and payment.

Care-language claims, explicit self-assessment, individual reviewer decisions,
offering languages and patient preference are separate. Prior declarations are
preserved as pending claims without invented ratings/verification; existing
appointments remain intact and authorization changes flag future care for human
review. New booking/publication/matching requires approved offering languages.
The expanded competency/navigation vocabulary and language scale are proposed
for clinical-owner review. Directory priority conveys no accreditation.

Implementation and acceptance remain tracked in `offline-telebirr-sprint.md` and
the existing screen matrix; this section records requested behavior, not a claim
that all browser/scheduler/visual acceptance has passed.

## Clinician Onboarding and Contextual Access — 22 October 2026

The five professional groups are Profile, Qualifications/Certifications, License,
Competency Domains, and Clinic Affiliations/Declaration. Applicant-confirmed prefix,
first and last name replace the editable combined name; legacy names remain intact
without inferred splitting. Bio is limited to50 Unicode-whitespace-delimited words
on submission/public editing; existing longer text is retained for correction.
Profession/specialty, awarded qualification/related area, issuer country/practice
jurisdiction, self-rating/reviewer assessment, and affiliation/clinic verification
are distinct. Directories and manual entries confer no authorization.

Private identification is available only to its owner and an explicitly assigned
credential reviewer who already has the review role. Other private professional
records remain under existing owner/reviewer permissions. CV/certification/license
selections and immutable submitted versions preserve historical evidence. Accuracy
declaration is versioned and separate from adult eligibility and policy choices.
General application approval never approves individual requested scopes. Existing
manual grants, scope evidence requirements and publication/re-review gates remain.

Contextual sign-in/signup preserves care/application returns without adding roles.
Signup is verification-first and has no password alternative; existing-user sign-in
retains explicit password access. Flag/calling-code display does not expand
Ethiopian-only SMS support. See `clinician-onboarding-context-sprint.md` for coverage,
limits and evidence. Directory completeness, credential verification, proposed
self-rating review, identity retention governance and native translation remain
human/external decisions; no clinical approval is invented by these changes.

## Sharing and immediate-request continuity —19October2026

New patient accounts default preferred-name and saved text-history sharing on,
with editable controls. Existing choices are unchanged. When both are on, open
requests publish from Preferences without a separate privacy step; the inline
notice and optional sharing editor remain. Requests disclose name/request text
only, never full history to the recipient pool. Offer acceptance uses a compact
price/funding confirmation with collapsed sharing controls and server-generated
encounter disclosure; disabled preferences open the editor. Individual history
files retain explicit selection and encounter-scoped grants. Acceptance is the
affirmative authorization; no disclosure snapshot or financial check is removed.
Manual request start persists as intent across capacity pauses and expired leases;
effective readiness still requires a fresh authenticated heartbeat, approved
published service and feasible session. Manual pause always wins. The shared
availability card appears on Today and Requests.

## Guest role navigation clarification —18October2026

Guest/non-patient directory cards open the clinician preview only. Booking actions
inside the preview/full profile read Sign in to Book until a patient is signed in.
The selected offering survives authentication. Verified existing sessions visiting
home return to their existing role destination;navigation intent grants no roles.
Horizontal menus align right and use the current role’s supported workspace links.

## Guest-first MVP revision — approved17October2026

The18October instruction supersedes the interpreted-care-query and account-type
chooser entries below. AI care search and its natural-language bar move together
to post-MVP. Public clinicians/services use an allowlisted eligible projection;
selection returns through verified authentication to the chosen offering. Guest
request text stays bounded in memory,not broadcast or stored before authenticated
consent. Existing records/preferences remain unchanged. New-patient alias and text
sharing are visible editable proposals;per-recipient encounter consent remains
mandatory. Universal invitation expansion is not authorized by this revision.
The sole screen matrix's guest_first_revision section tracks requested work and
verification independently;historical acceptance evidence remains historical.

# Agreed product contract

## MVP handover priority — 2026-10-08

The current release boundary is `mvp-release-scope.md` and `mvp-screen-acceptance.json`. The user superseded delivery of the entire expanded platform with the agreed mental-health/counseling MVP and its complete redesign. Working two-adult couples consultations and explicitly prefunded fixed-block extensions remain MVP requirements. Full clinic management, family/group expansion, laboratory operations, subscriptions, second opinions, medical tourism and metered hourly pricing are post-handover. No-show adjudication is explicitly deferred; current pre-start cancellation limits remain. Preserve all existing source/schema/data. Older expanded-scope sections below describe retained future authorization, not the present release gate.

Credential lifecycle update (2026-10-08): future booked or pending-confirmation
appointments affected by expired or revoked scopes receive a logistics-only
operational review flag. It does not change appointment or financial state and
does not expose patient records to vetting reviewers. Human operational
continuity policy remains required.

Clinician profile clarification (2026-10-11): an optional owner-authored public
introduction is distinct from private patient history and application evidence.
It is shown only through the approved clinician profile projection; no approval,
credential verification or service authorization follows from editing it.
Existing records receive no inferred public text.

Patient onboarding clarification (2026-10-11): optional care background is saved
in the owner-only draft and copied to private profile history only on adult-consented
completion. It does not imply disclosure; existing global defaults and per-booking
preview/overrides apply. Existing ready-step drafts keep their stored meaning.

## Initial clinician application structure —2026-10-12

B06/B07 capture self-reported professional category, relevant experience, languages,
qualification and credential identifiers/expiry in the private resumable onboarding
record. These fields use the existing scope-application validators; they are not
credential verification or a substitute for individual human scope assessment.
Only the applicant and authorized vetting reviewers can retrieve this application
metadata. Optional introduction is explicitly intended for the approved public
profile; qualifications and credential identifiers never follow it into discovery.
Existing saved applications remain valid without inferred or fabricated new fields.
No schema, approval, payment or call policy changes follow from this composition.

For the structured initial application, profession, qualification, institution
and care languages replace a duplicate mandatory free-text credential narrative.
Additional narrative and jurisdiction can be saved optionally; existing narrative
applications retain their original requirement. Resume receipt plus complete
self-reported application fields means attachments/information are present, not
that any credential or scope is verified. Per-scope evidence and human mandatory
gates remain separate and unchanged.

## Structured service intake and clinical definition review — 12October2026

Applicants may select multiple structured Draft or Active definitions. Draft intake
is deliberately distinct from authorization: general application approval, a submitted
scope application, and catalog presence never grant a service scope or booking rights.
Each scope retains separate supporting evidence, clarification, decision and appeal.
A designated Medical Lead who also has vetting-review permissions records a reasoned
clinical-definition decision after professional, credential, adult, consent,
jurisdiction, duration and implemented-workflow requirements are supplied. Generic
DocType writes cannot grant clinical-definition approval. Approved definition metadata
is preserved; changes require a new versioned draft. Immediate-care policy remains a
separate reviewed action. None of these actions verifies an external credential.

Initial private onboarding and scope applications support competencies, certifications
and license validity start as applicant claims, in addition to existing qualification,
issuer, expiry, experience and PDF evidence. Existing applications get nullable fields;
no approval, credential, service name or historical snapshot is inferred. The clinical
catalog's ten sourced drafts remain awaiting actual medical-lead requirements/decisions.
Legacy demonstration scopes remain historical and usable under existing rules, but
are excluded from new structured scope selection. No automatic catalog activation.

## First internal demonstration
Adults 18+. English, Amharic and Afaan Oromo with native review before pilot.
Patient and clinician portals; administrator approval; independent and multi-clinic
clinicians; affiliations do not grant records access. Clinician recruitment and approval
belong to the doctor. Guided patient profile and private medical history.

Natural language request -> suggested service and eligible clinicians, with editable
filters and optional relevance feedback. No diagnostic claim. Eligibility precedes
ratings/proximity. Proximity is relevant particularly for in-person care.
Direct booking uses a selected published offering; one approved service scope may
contain multiple clinician-owned titles, descriptions, prices and durations, none of
which can expand the underlying authorization. Private open requests distinguish immediate
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

No prior vetting rubric was agreed. `docs/vetting-rubric-v1.md` is a proposed
human-review instrument, not a clinical standard. Version proposals are
immutable and digest-checked; each scope application and assessment retains its
own rubric snapshot. Only a separately assigned Medical Lead may approve a
version. Until that review occurs, the rubric remains explicitly proposed and
cannot be described as a verified credentialing standard.

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
The initial shared-care release provides only an optional, mutually accepted
adult relationship link. It shows each participant's chosen profile name after
acceptance and grants no appointment, history, note, balance, or call access.
Couple/family offerings remain unavailable until participant-specific booking,
disclosure, multi-party call authorization, and recipient-scoped documentation
are implemented and verified. Adult attestations do not independently verify
age or identity.
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

Acquisition is recorded on the appointment event, not on the patient profile:
direct bookings (`direct_booking`), clinician-shared booking links
(`clinician_share`), and accepted private offers (`open_request`) have separate
source values. Existing appointments remain `unknown`; the system does not
infer historical attribution.

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
idempotent journals. v1.13 audits each owner against the activity log and
wallet/subledger projection, recording unknown events and exact snapshot-boundary
ambiguity without rewriting existing events. v1.24 records a missing historical
`Consumption` activity entry only when an immutable `ConsultationFinalized`
journal, patient reserved debit, and earning agree on appointment and amount; it
does not change balances, earnings, appointments, or journals. v1.25 applies the
same exact-evidence rule to a missing historical `Refund` activity event, using
the `EarningRefunded` journal, patient available credit, clinician pending debit,
and refunded earning amount. New completions and supported dispute refunds
append their activity events atomically with the subledger posting. Owner audit
refreshes preserve prior snapshots in the private audit history and never clear
a review hold. Unexplained mismatches remain held until an authorized, reasoned
decision accepts the unchanged current snapshot. Unknown event kinds and
conflicting evidence stop for review. A deployment cutover stops all old web and
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
staff email into limited roles: Clinic Manager, Scheduling, Billing, or
Care Coordination. The invitee must sign in and prove possession of the exact invited
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
clinical-record access. Clinic Manager and Scheduling members now have a
read-only weekly calendar view over these same active patient-shared future
appointments, with an explicit display timezone. It cannot show unshared
appointments or edit, book, confirm, cancel, or reschedule them. Billing remains
descriptive and grants no calendar access. There are still no clinic resources,
room allocation, clinic-owned availability, clinic-wide patient directory,
billing operations, or blanket patient records. Clinic verification and
affiliation alone enable none of these capabilities. Existing
narrative affiliation fields are preserved and are not automatically converted
into verified affiliations. Native DocType schema
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
other encounters. This is not a clinic-wide record grant. The dedicated weekly
calendar is only a read-only view of active grants and does not create clinic-
owned schedules or resources.

A separate patient-controlled `Patient-shared summary` grant may expose only
published patient-summary revisions from one completed encounter to an active
`Care Coordination` member of a verified clinic affiliated with the treating
clinician. The patient reviews consent before granting and may revoke future
API access; revocation cannot make previously viewed content unseen. Private
clinician notes, unpublished drafts, intake, contact details, balances and all
other encounters remain excluded. Clinic owners, managers, scheduling/billing
staff, administrators, and generic DocType APIs gain no summary access from
clinic membership alone. Current verified clinic status, affiliation and the
Care Coordination membership are rechecked on each read. This is a local
demonstration consent workflow, not a jurisdictional determination of clinic
record-controller obligations. See `clinic-shared-summary-access.md`.

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

## Immediate-care service policy

Immediate-care routing has a separate manually reviewed service-level policy.
General clinician approval, individual scope approval, offering publication,
calendar availability, and the clinician's short-lived request-presence lease
are independent requirements. Changing the service policy requires an
authorized approver, a reason, and an append-only audit event. Legacy test
services are eligible only on a site explicitly bound to review mode; migration
does not enable immediate care. The three-minute target is measured, not
promised.

## Owner profile photos — 13October2026
Patients, clinicians and reviewers can upload/replace/remove a personal raster
photo. Patient/reviewer photos are owner-only and never follow name/history
sharing into encounters or requests. Clinicians choose public-profile visibility;
current discovery eligibility is enforced again on photo download. A photo
provides no credential verification. See `profile-photos.md` for limits, storage,
fictional presentation setup and revocation limitations.

### Connected automatic request availability (19 October revision)
Schedules may opt into immediate-request presence during their Published local intervals,
including replacements and excluding breaks/unavailable dates. Default is off. This is
not unattended on-call coverage: an authenticated reachable clinician workspace renews
a bounded presence lease. Closing/disconnecting the workspace expires availability.
Manual pause persists across navigation, reconnects and expiry until explicitly resumed.
Approval, scope, language, immediate-care policy and full-session/buffer/conflict checks
still apply; automatic preference never reserves a slot. Today owns the controls; the
workspace owns the headless heartbeat. Current booked/buffer time is shown as Occupied,
or In consultation for an opened call within that occupied interval.

An Open consultation row is evidence a call was opened, not evidence of indefinite
participation. After its booked/extended end, lists show Outcome not recorded and Past
until an explicit authorized outcome is recorded. No call, appointment or ledger is
mutated by this presentation rule. Call activity says Call opened, never claims measured
connected time. Existing End/revocation and documentation controls are unchanged.

### Service-grouped public directory (19 October)
Clinicians & services presents the existing approved cards under public service-name
headings with service shortcuts. Filters remain server-enforced; each offering keeps
its own scope, clinician, price, format and booking reference. Display grouping does
not merge catalog definitions or grant additional authorization. Guest cards retain
View profile, with Sign in to Book inside the profile; patients keep direct scheduling.

## Booking Notifications — 19 October Follow-up

Patients use one neutral notification bell for appointment, follow-up, account and system events; appointment delivery history remains on Appointments. Authorization is rechecked on fetch/read/link access, including individual couples consent. Private note content never enters notifications.

New booking policy version `booking-notices-v2` records a 180-second clinician reminder threshold and an explicit confirmation deadline (configured hours, capped at start). One follow-up email is queued after that threshold; minute scheduling and provider availability determine actual sending. Existing bookings retain their accepted policy. Expiry releases the demonstration reservation once under the existing cancellation rules; no new penalty or external refund is implied.

Email/SMS operational booking preferences default on only when no saved choice exists; explicit opt-outs remain honored, with verified contacts, site/provider gates and send caps. Reservation receipts identify demonstration funds. ProviderAccepted is not delivery. The 90-day, minimum-five presented-booking-prompt response metric is separate from clinical competency and patient experience; responsible declines count, unseen expiries do not.

## Compact Account Settings — 19 October

Patient and clinician Account pages expose all account groups through one index and local editors. Profile/history/privacy, notifications, contact methods, language/timezone and help remain discoverable without returning to a separate overview. Practice and shared-care workflows retain explicit authorized entry links. Text entered in an editor survives local section changes; only explicit saves persist it. Unsupported contact changes remain accurately unavailable.

Profile photo selection/drop opens an in-memory crop/zoom/position preview with keyboard alternatives. Cancellation uploads nothing. Saving uses the existing owner-authorized, size/type-validated, normalized private photo API and existing public-visibility choice; no additional sharing permission is implied. No image data is stored in browser persistence or external services.

## Consolidated Private Requests — 19 October Follow-up

Patient Requests contains composition, preferences, immutable disclosure preview, publication, live progress, clinician inspection, private offer comparison, funding and acceptance. Clinician Requests contains the eligible inbox, authorized disclosure, approved-offering response editor and private active/history outcomes. Existing deep links select the corresponding record in these workspaces; only opaque references belong in URLs. Draft clinical text stays in React memory and survives local view/step changes, not a page reload. Hidden drafts still protect against tour navigation; published/sent drafts clear only after durable success.

Acceptance uses the existing atomic appointment/reservation command; this presentation change introduces no parallel booking or accounting workflow. The patient remains on the matched request until opening the authorized appointment. Offer acceptance is a historical event, distinct from the appointment's current status: cancelled/ended/completed appointments are not relabeled confirmed by their old matched request. Schedule-for-later prepares a new draft without silently cancelling or rewriting the original request.
