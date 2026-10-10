# TeleTena MVP release and handover scope

Authoritative release boundary: user priority change on 2026-10-08, plus the
explicit decision that working two-adult couples consultations are required.
This supersedes implementation of every extended-platform screen before handover.
The 142-screen reference remains preserved; it is not the release completion target.

## Source and preservation checkpoint

- Preserved branch: `feat/adult-relationship-links`, pushed at
  `1e8d161468eb8d3563f1b5743982722c749bbcbf`, draft PR #43, dependent on #42.
- Release continuation: `feat/mvp-release-handover`, branched from that checkpoint;
  all stacked work remains in its ancestry. No PR was merged or remotely deployed.
- Bench: `/home/frappe/frappe/frappe-bench`; isolated review site:
  `tele-tena-pr12-fresh.localhost`; preview:
  `http://127.0.0.1:8017/teletena/`. Keep original `erp.localhost` unchanged.
- Production-built React assets, same-origin Frappe APIs. The packaged
  `tele_tena/public/review/release.json` is authoritative for the served build SHA.
  A process running is not proof of a job executing or of a browser flow passing.
- Current schema/records, credentials, extended foundations and source branches
  are preserved. This scope change does not run migrations or seed records.

## Active preview correction — 2026-10-10

The original source/preservation checkpoint above is historical. Current review URL
still http://127.0.0.1:8017/teletena/, now on a **separate clean presentation site**
`teletena-mvp-presentation.localhost`, packaged `c3e1ff1263eaec2851a1817a1bf54c90f894a40c`.
The old fixture site remains retained. Scope does not change. See the current journey
report and existing screen matrix for per-state evidence and remaining release blockers.

## Agreed release capabilities and acceptance

The separate [screen matrix](mvp-screen-acceptance.json) records every inventory
screen's release disposition, inherited implementation status and release gate.
Inherited checks are evidence for their recorded commit, not a current full-release
pass. The current candidate is **not ready for handover**.

| Capability | Applicable design IDs | Current state / exact remaining work | Required release acceptance |
|---|---|---|---|
| Public care/clinician entry | A01–A03 | Two-sided landing exists; inspect current composition against extracted source, care-query memory code updated; password journey passes, OTP/new-user onboarding pending | Both entry paths reach appropriate persisted workspace without health text in URL/logs |
| Phone/email/password access | A04–A07 | Site-scoped access and backend OTP exist; current complete registration-enabled and invited-review browser checks remain pending | Real backend test transport, expiry/single-use/racing verification, throttling/caps, truthful provider availability and reviewer password access |
| Adult patient onboarding/profile/privacy | B01–B05, H01,H03,H04 | Resumable onboarding and defaults exist; volatile query return implemented; new-user OTP/onboarding and all step/error/mobile states need current acceptance | Small saved steps, explicit adult consent, profile defaults separate from booking/request overrides |
| Clinician onboarding/vetting/evidence | B06–B12,I01–I06,I09 | Individual scopes, private PDF evidence, clarification/revision/provenance and proposed rubric exist; full current applicant→reviewer→scope journey and visual acceptance pending | Approve one scope, clarify one, reject one; publish only permitted scopes; private file/generic-API denial; no autonomous clinical approval |
| Service catalog and offerings | F08,F09,I07,I08 | Versioned native catalog and multiple offerings exist; draft clinical definitions remain non-final; verify clinician presentation and human-controlled publication | Stable scope/version snapshots, exact approval/language/format eligibility; no implicit child-scope authorization |
| Clinic onboarding/affiliation | B08,J11 (limited),I01 | Registry and separately reviewed affiliation implemented; existing limited staff/grant foundations preserved | Register→review clinic→request/verify affiliation; no implied scope or clinical-record access. Full clinic management is deferred |
| Discovery/returning care | C01–C04,F12 | Existing filtered discovery/trust and returning-care API; natural-language category suggestion/relevance feedback still incomplete in roadmap; query continuity and source-faithful populated/empty layouts pending | Non-diagnostic suggestions with editable filters, eligible results, honest no-results, own previous clinicians and sample-aware trust |
| Direct booking/availability | C05–C09,F05–F07 | Recurrence, exceptions, drawer/calendar, atomic valid-slot booking and field errors implemented; latest full clinician→patient persisted browser and keyboard/mobile acceptance pending | Publish/reload/edit schedule without moving bookings; grid/day editor, notice/buffers/timezones/DST, confirmation/expiry, conflict/idempotency protection |
| Private requests/offers | D01–D09,F02–F04,F13–F15,I10 (bounded routing diagnostics) | Immediate continuous-start eligibility, private waves, presence/inbox/history exist; current integrated publish→offer→accept journey and asynchronous waves/expiry pending | Required scope/language/format/presence/free time; mutually private offers; insufficient funds retry; one winner/appointment/reservation; no-response/reconnect fallback |
| Appointments/reschedule/cancellation | E01–E04,E13,E14 | Persisted lifecycle, policy/disclosure snapshots and mutual reschedule exist; supported cancellation is pre-start full demo release; no-show adjudication is not implemented | Actor-scoped actions and snapshots, original hold until accepted reschedule, cancellation exactly once, no inferred completion/no-show. Record and expose supported limits explicitly |
| Real consultation/notes/care records | E05–E09,E11,E13,E14,F10,F11 | Existing LiveKit, private notes/shared summaries and encounter-scoped care; current joined/cached-token End release regression and complete visual acceptance pending | Two independent browser sessions, Leave/rejoin/End, old/refreshed-token rejection, private-note API omission, amendment/sharing history, follow-up |
| Paid extensions | E10 | Fixed extension block proposal, consent, prefunding, release/settlement implemented with focused tests; current connected call acceptance pending | Patient explicitly accepts snapshotted price before start; no negative balance/duplicate reserve/automatic duration charge; pending earnings use same policy |
| Two-adult couples consultations | N01–N08, SH01 | Required by explicit user decision. Relationship invitations work; appointment participant model/consent, couple offering eligibility, 3-person room and recipient-scoped notes are missing | Two authenticated adults individually consent and preview disclosure; payer gets no private access; clinician plus both adults join/end; independent private intake and explicit note/summary recipients; revocation/state tests |
| Demonstration finance | G01–G08,I11 | Balanced journals, reservation/completion/dispute/release/payout and owner mismatch holds exist; current scheduler-driven lifecycle, full opening-boundary/per-owner upgrade/fresh checks and visuals pending | ETB 1,000→book 300→available 700/reserved 300→finalize pending 300→release available 300→payout reserve 200; retries/concurrency, reversals and exact owner reconciliation |
| Structured session feedback | E12,F12 | One eligible completed-encounter structured rating and sample-aware indicators implemented; full current browser and actor/state checks pending | Own encounter only, one record, no fabricated reviews or treatment-effectiveness claim. No public free-text comments, therefore no public-comment moderation workflow |
| Account/tours/mobile/PWA | H01–H04,H08 plus shared states | Connected focused sections, wallet detail, role tours and public-static cache exist; current all-MVP composition/state/language/actual-zoom acceptance pending | Every MVP route has populated/empty/loading/error coverage, 320/390/768/1440 and actual 200% zoom, keyboard/reduced motion, safe updates, no private/offline writes/cache |

## Conflicts and resolved depth

1. **Couples:** the original demo contract includes individual couples consent;
   later relationship-link text defers couples appointments. The user resolved
   this on 2026-10-08: working two-adult couples consultations are mandatory for
   this handover. Family/group expansion is deferred. Existing prohibition stays
   active until the complete participant/consent/call/note workflow passes.
2. **Hourly pricing:** the contract explicitly calls hourly pricing future work.
   This MVP retains fixed durations plus explicitly accepted prefunded blocks;
   metered/hourly rates, rounding and unilateral duration billing are excluded.
3. **Clinic depth:** independent/multi-clinic affiliation is MVP; full staff,
   resources, clinic-owned booking/billing and blanket records workspaces are not.
   Preserve already implemented narrowly consented clinic grant/member workflows.
4. **Finance:** demonstration custody/subledger is MVP; actual provider transfers,
   general withdrawal/refund settlement and ERPNext accounting are activation work.
   Unsupported post-release refunds stop for audited resolution, not balance edits.
5. **No-shows and cancellation:** past scheduled time never establishes an outcome.
   Current pre-start cancellation/refund is an explicitly documented demo default.
   The user explicitly deferred no-show adjudication on 2026-10-08 and retained
   current cancellation limits. Broader penalties and no-show decisions are
   post-handover; they cannot be described as implemented or silently inferred.

## Immediate remaining work, in execution order

1. Stabilize one loopback preview and record runtime/build/source identity. Diagnose
   test failures by stage; preserve failing evidence rather than rerunning blindly.
2. Verify critical persisted booking, immediate/scheduled request, auth and finance
   journeys. Verify site-scoped current-code scheduler/worker execution, not just
   a configured hook or direct function call; prevent old financial writers.
3. Finish the approved composition across **every MVP screen/state**. Map extracted
   screen IDs to shared React routes, not one new route per static prototype card.
   Keep old visual evidence historical and collect new screen-specific evidence.
4. Finish missing non-diagnostic discovery and two-adult couples behavior. Preserve
   each adult's encounter disclosure and independent permissions; do not weaken
   current individual booking or token revocation to add participants.
5. Complete fresh installation and representative owner-level upgrade/repeat
   migration reconciliation; current v1.30 fresh-install verification is pending.
6. Run one complete release-candidate permission/concurrency/backend/browser/build
   check set, then prepare the private accounts, presenter walkthrough, config,
   site backup/update/rollback instructions and exact release SHA/PRs.

## External activation and validation

Live SMS and SMTP receipt, physical-device/HTTPS media and installation checks,
native Amharic/Afaan Oromo approval, Medical Lead catalog/rubric approval,
independent credential checks and real-care safety/legal operations remain explicit
external gates. Hosted LiveKit Cloud revocation requires configured project access;
local fake-media browser evidence is separate from physical-device testing.
Real payments, custody, withdrawals, ERPNext posting and clinical use remain disabled.
External gates do not block unrelated local persisted-flow implementation.

## Explicit post-handover scope

Full clinic management/resource/billing workspaces (J01–J10,J12), laboratory and
diagnostics operations (K), second opinions/medical tourism (L), subscriptions (M),
family/group adult-care expansion beyond two-adult couples, metered hourly pricing,
advanced revenue, public free-text reviews/moderation, contact-change/security and
notification/support modules not already agreed as functioning MVP capabilities.
Retain their source, schema and design entries in the backlog. Existing operational
features are not removed or rolled back simply because they are outside the gate.

## Handover gate

No claim of readiness until every included acceptance criterion has authoritative
current-source evidence or an explicitly allowed external-activation limitation.
A designed, mocked or rendered screen is not operational acceptance. No automatic
merge, deployment, seed, legacy adjustment or external delivery is authorized.

## Couples operational implementation contract — v1 (2026-10-10)

Two independently authenticated adults explicitly consent to a single selected
service, slot, duration and whole-session price before the payer confirms. One
patient is the payer; the other has no wallet or private-record access through
participation. The existing reservation, cancellation, completion and earning
postings remain authoritative and occur once for the appointment. Invitations
are private, manually shared, short-lived bearer links whose digest is stored;
relationship affiliation is neither required nor sufficient for participation.

Each adult approves an immutable clinician-facing disclosure preview, including
any private intake they voluntarily share. Another adult receives their own
snapshot only. Opaque participant identities are separate from email/accounts.
New or altered service/time/price requires a new invitation and both consents.
Plans hold no slot or money; confirmation revalidates both accounts, current
scope, all participants' conflicts, schedule and funds atomically.

A couple appointment requires both active consents to issue any new room token.
The clinician and two adults have independent opaque room identities; End
revokes every issued identity, including departed participants, using the
existing Cloud cutoff behavior. Leave never withdraws consent. Private clinician
notes stay private. Publication explicitly selects participant recipients per
revision; no recipient is inferred from payment or relationship. A withdrawn
participant loses new room/clinical access. Earlier sharing remains audited.

Demonstration withdrawal rule: before the scheduled start, withdraw cancels the
whole appointment and returns its one reservation exactly once; during/after
start it ends the room and holds the unchanged reservation for operational
resolution, without automatically charging, refunding or finalizing. Unsupported
post-release corrections stop for authorized review. No-show adjudication stays
deferred. Family/group and couples open-request matching remain post-handover;
this release's couples entry uses explicitly consented direct booking.

Statuses: Invited → Consented → Booked; prebooking Cancelled/Expired, participant
Consented → Withdrawn, and existing appointment/call/document states independently.
Acceptance: independent consent and preview; no cross-person disclosure; concurrent
confirmation makes one appointment/reservation; participant conflicts; three
media sessions, Leave/rejoin and all-identity End revocation; explicit recipients;
withdrawal/outsider denials; one consumed reservation and pending earning.
Implementation and verification remain open until that evidence passes.
