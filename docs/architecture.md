# Architecture decision 001 — Frappe-backed PWA

Status: accepted direction; foundation installation verified on Frappe 15.121.2
and ERPNext 15.121.6. Product workflow compatibility remains to be tested.

Deployment checkpoint update: the presentation/deployment release now also passed
isolated compatibility tests on the exact Selfmade Frappe16.2.1/ERPNext16.1.0 commits,
Python3.14.2, Node24.13.0, MariaDB10.6.22 and Redis6.0.16. See
`frappe16-compatibility-verification.md` for tested workflows and explicit host/TLS
differences. This does not authorize upgrading the retained development bench or
changing shared remote dependencies.

React + TypeScript + Vite talks to a dedicated custom Frappe application. ERPNext
provides accounting. Frappe RQ workers and scheduler handle jobs. No Django or Celery.
MariaDB and framework versions must match the user's isolated WSL bench; do not upgrade
that bench automatically. LiveKit carries human-to-human audio/video; Frappe issues
short-lived room-scoped tokens only to authorized appointment participants.

Use same-origin routing in deployment and a local Vite /api proxy in development.
Never place an administrator key in the frontend. Phone OTP requires a custom verified
login flow with expiry, throttling, replay prevention and account recovery. Session
cookies and CSRF must follow the installed Frappe version's supported behavior.

Modules: identity/consent; providers/affiliations; service catalog; marketplace;
scheduling; consultations/records; financial subledger; trust/operations.

The versioned `v1_7_demo_subledger` adds app-owned `tt_financial_account`,
`tt_journal`, `tt_journal_line`, `tt_earning`, `tt_dispute` and `tt_payout` tables.
This balanced operational subledger is separate from the legacy `tt_ledger`
simulation activity log. It is used only for demonstration balances and simulated
earnings. `tt_wallet` remains the patient-facing projection and each command checks
it against the subledger before changing funds. Posting references are unique and
retry-safe; corrections use audited, balanced reversals. ERPNext remains the future
accounting/reporting boundary: there is no ERPNext posting, bank custody, payment
provider or external payout integration. Real-money/provider readiness remains
unapproved. Historical completed appointments with reserved funds become
review-only `LegacyHold` rows; migration preserves old balances and events and does
not settle those appointments.

Use explicit command APIs for accept_offer, book_appointment, reserve_funds and
request_withdrawal. Generic document writes must not bypass these invariants.
Clinical data and financial account identities are separate. Admin roles are scoped.
All financial/acquisition/disclosure/policy decisions retain versioned evidence.

Future service definitions are configuration records. New clinical workflows can require
new code. Do not create a DocType per specialty or fork framework core.

PWA installation is planned, not implemented in this foundation. Cache static assets
only; no clinical data, tokens, API responses or offline financial commands. No guarantee
of background calling on locked mobile devices.

## Milestone 1 storage implementation

App-owned InnoDB tables (`tt_*`) back the private authorized command/query APIs. Private
records have no generic DocType, Desk, report, export or file interface. Installation
and migration use the framework DDL method; runtime commands never perform DDL
or commit intermediate state. A global booking gate, followed by patient/wallet
and clinician locks, provides explicit low-volume serialization. Wallet values
and simulation transaction-log amounts use BIGINT minor units; no ERPNext posting or real
settlement is active. Role provisioning is administrator-controlled; the isolated
review fixtures use normal Frappe password sessions, not a web login bypass.

## PR #2 review adjustment

Service configuration and per-clinician service approvals now use native versioned
Frappe DocTypes, with approver permissions and validation shared by generic APIs
and React commands. General approval never supplies a service scope. Legacy catalog
rows and all private transactional records remain preserved. Numbered post-model-sync
patches record adoption; repeated after_migrate DDL is removed. See
[storage review](pr2-storage-review.md) for the smallest staged back-office adjustment
and explicit limits of the simulation log versus the future double-entry subledger.

## Milestone 2 consultation storage

`tt_consultation` is an additive, versioned app-owned table keyed by the booked
appointment. It holds a random room name and opaque participant identities, while
the appointment-to-account map remains in private application storage. The
`v1_3_consultations` and `v1_4_consultation_close_state` patches are included in
fresh-install bootstrap and normal Patch Log migration. Frappe issues room-scoped LiveKit participant tokens after
checking the session account against the appointment; the browser never receives
the backend API key or secret. The five-minute token lifetime and 15-minute early /
30-minute late join limits are configurable demo values, not approved policy.

Join and End take the appointment row lock in the same order. End commits the
Ended state before provider operations, then LiveKit Cloud `RemoveParticipant`
revokes both opaque identities (including a participant who has left) using an
explicit cutoff 30 seconds ahead, followed by room deletion. This covers tokens
refreshed between the application commit and provider revocation. Provider errors
leave closure visibly retryable; End retries revocation for both identities and
room deletion. The cutoff is intentionally within LiveKit Cloud's documented
±60-second acceptance range ([participant management](https://docs.livekit.io/intro/basics/rooms-participants-tracks/participants/),
[token revocation](https://docs.livekit.io/frontends/reference/tokens-grants/)).
LiveKit documents token revocation as Cloud-only. Self-hosted
deletion disconnects active clients but does not invalidate cached tokens, which
may remain usable until their short TTL expires. Participant leave remains an
ordinary disconnect and leaves the consultation Open for authorized rejoin. No
clinical notes, recording, transcript, billing action, or
earnings posting is part of this table or workflow.

## Review packaging (merged through PRs #7–#10)

The production build lives in the app's public `review` assets, served by Frappe's
normal `/assets/tele_tena/` mapping. A site-bound renderer owns only `/teletena/*`;
React uses that basename and same-origin APIs. There is no Vite runtime requirement
or catch-all proxy fallback. The service worker's scope is `/teletena/`, with an
allowlist for this app's public assets only. HTML and authenticated responses are
not cached. See `selfmade-review-deployment.md` for the dedicated-site/isolation gate,
private CLI configuration, explicit synthetic seed and code-plus-data rollback.
The review configuration does not enable generic Frappe signup, real payments or
clinical use. Later site-bound switches can explicitly enable phone OTP and
patient/clinician registration on the designated review site without changing
demonstration funding or granting clinician approval. These switches remain
disabled by default; live SMS delivery is unverified.

## v1.8 financial cutover

The `v1_8_legacy_event_reconciliation` patch imports legacy `Deposit`,
`Reservation` and `Release` events created after a patient's v1.7 opening
snapshot. It adds one balanced, idempotent `LegacyEventImported` journal per
known legacy reference and leaves `tt_wallet`, `tt_ledger`, appointments and
obligations unchanged. Unknown event kinds stop migration for review. Operators
must stop all old web processes, workers, scheduler processes and queued writers
before migration, install matching application code, migrate and verify wallet /
subledger equality before restarting matching processes. If an old writer
remains after cutover, financial commands fail closed on projection mismatch;
restarting old code can reintroduce legacy-only writes.

## v1.13 owner-level reconciliation audit

`tt_financial_reconciliation` is a private app-owned operational table because it
contains per-owner balances and legacy integrity findings and must not be
available through Desk, generic DocType APIs, or reports. Migration compares
the existing event projection, immutable v1.7 wallet snapshot and new subledger
for each patient; it records exact opening-boundary and unknown-event cases but
never adjusts any source. A `ReviewRequired` owner is blocked from further
patient-fund mutations. Only an explicitly authorized reviewer can accept the
unchanged current snapshot with a reason, and only if wallet and subledger agree.
That audited choice preserves the unresolved historical difference; it does not
claim to reconstruct missing history or create a balancing entry. All future
financial records remain on the existing subledger path.

## Clinic operational memberships

`Tele Tena Clinic Membership` is an additive native DocType. Its state machine
is `Invited → Active | Declined | Revoked` and `Active → Revoked`; terminal
states cannot be reopened. The inviting clinic owner or active Clinic Manager
may issue/revoke an invitation. Acceptance or decline is available only to the
authenticated account with a verified `tt_contact_identity` email equal to the
invited address. Generic DocType list/document permissions use the same clinic
manager and accepted-member boundary; controller validation rejects direct
writes and deletes. Membership roles are limited to `Clinic Manager`,
`Scheduling`, and `Billing`. Only Clinic Manager currently authorizes further
membership administration; the other labels do not imply enabled calendar or
billing operations. No membership role grants clinical-record, appointment,
consultation-note, resume, or service-scope access. Invite delivery is not
implemented, so an invitee must already know to sign in and verify their
address. Audit events record invitation, acceptance/decline, and revocation.
