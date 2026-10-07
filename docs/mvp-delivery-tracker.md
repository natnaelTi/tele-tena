# TeleTena delivery tracker

## Current clinic and authentication verification — 2026-10-07

Current branch `feat/clinic-affiliation-review` is a focused dependent slice
on `feat/previous-clinicians`; its latest pushed head is shown by PR #18. The
reviewed backend/product code and packaged frontend source are at
`8e3a298bdc3f2624cdf0fb5d256fc469177fea36`; subsequent branch commits update
tests and verification documents only. This is not the complete
approved A–I product scope. The matching built preview is
`http://127.0.0.1:8017/teletena/`, served from
`/home/frappe/frappe/frappe-bench`, site
`tele-tena-pr12-fresh.localhost`, Frappe 15.121.2 / ERPNext 15.121.6 / Python
3.12.3 / Node 22.23.3. The running backend imported the branch's matching
product code and the production asset manifest records source `8e3a298`; the
app is not served by Vite.
The retained `erp.localhost` site has not been migrated or reseeded. The review
site remains invited-review configuration; phone OTP and public registration
are disabled there.

Clinic registration and clinician affiliation now have persistent native
DocTypes, applicant-owned submission/resubmission, separate human decisions,
audited reasoned transitions, and generic DocType permission checks. A real
Playwright journey against the built Frappe app passed clinician clinic
submission → reviewer verification → clinician affiliation request → separate
reviewer decision. `tests/presentation.py` passed 22/22. The contact-auth
regressions passed 7/7 after separating test configuration from the retained
invited-review site: SMTP configuration and registration policy are mocked
only for that enabled-registration state-machine suite; no mail was sent and
the site's flags were not changed. Screenshots are in
`docs/screenshots/clinic-review/`.

The Frappe integration suite also passed 24/24 after aligning its HTTP origin
with the built port 8017 and replacing stale calls to the retired guest-phone
API with the current `contact_auth` API. The disposable site's phone and public
registration flags were temporarily enabled for that run and restored in
cleanup; the preview is again invited-only. SMS transport was mocked and no
live message was sent.

This is partial clinic onboarding/review, not clinic operations. Memberships,
staff invitations, shared calendars/resources, clinic billing and encounter
grants remain pending. Responsive clinic/admin review, real SMTP/SMS, mobile
devices, native-language review, and Frappe 16 compatibility for this added
schema are not verified. Other A–I scope remains at the per-screen status in
`operational-screen-map.json`; the map is not an implementation claim.

Scheduler status on this disposable site is disabled and no worker is running.
The integration suite covers scheduling/dispatch command behavior but does not
prove queued earnings release or routing executes. Do not demonstrate those
scheduled transitions until an isolated queue and worker are configured; the
shared bench queue must not be drained accidentally.

## Returning-care checkpoint — 2026-10-07

The current dependent branch is `feat/previous-clinicians` at
`fb58ab13815bd3cc16b9e12675c6f6e2474967a1`. Draft PR #17 targets the open
PR #16 branch `feat/teletena-operational-completion` at `503a39df2993cbced46ea067cef97917bac8bcf8`;
neither PR is merged. The patient-home returning-clinician slice is implemented
but Frappe integration and browser verification are pending. PR #17 CI passed
frontend builds on Node 22/24 and Python syntax jobs on Python 3.12/3.14.2.

No valid `/teletena/` preview for this source currently runs. Port 8000 is the
retained Frappe 15 `erp.localhost` bench using its pre-existing checkout; port
8017 is the separate Frappe 16 compatibility test WSGI process at
`/home/frappe/teletena-compat/bench` and is not this branch's matching preview.
Neither service was restarted or migrated. The disposable integration site and
its temporary DB credential are absent. Do not review either URL as this
branch's built application.

## Current implementation checkpoint — 2026-10-07

The active local branch is `feat/teletena-operational-completion` at the PR #15
base commit `3e0965c5fdf6485d945756b382c0a3c008450058`; it preserves PR #14 →
#13 → #12 ancestry. PR #15 is open/draft and has passing frontend/syntax CI but
no executed Frappe integration suite. PR #11 remains open separately. PRs #7–#10
are merged; Selfmade remains unchanged. The WSL Frappe 15 `erp.localhost` site was
backed up before schema work and has not been migrated by this branch.

The expanded approved scope is tracked across A–I in `operational-design-integration.md`.
The 142-screen acceptance map is `operational-screen-map.json`; its status values
are evidence states and are not inferred from a rendered page alone. Current
financial work adds a versioned reconciliation audit/hold; it is not yet run on
a disposable site. The production-built review route has not yet been established
for this source SHA.

Consolidated 2026-10-02: PRs #7, #8, #9 and #10 are merged into `main` at `4cc0be9a0a96c3b209d07b47fd5e7c46ab4c31a2`. The Selfmade site remains pinned to its separately installed commit; merging did not deploy or enable hosted phone access. Earlier PRs #3/#4 are merged through preserved ancestry; PR #5 was superseded. The hosted LiveKit Cloud End/rejoin/cached-token assertions passed with automated two-browser fake-media. Status describes demonstration evidence, not production readiness. Presentation release implementation and verification are tracked in `docs/presentation-readiness-verification.md`; [the next design inventory](design-update-inventory.md) maps every current route and component.

**Status meanings:** `implemented` means code and listed checks cover the
demonstration behavior; `partial` means a narrower slice exists or has a known
validation gap; `pending` means agreed scope is not implemented; `blocked` means
do not release/claim the feature until the stated blocker is resolved.

Hosted review update: site-bound phone OTP, patient registration and clinician
application switches are implemented with a rolling 24-hour site SMS attempt
cap. Frappe's generic public signup remains off; reviewer password login stays
available. SMS Ethiopia account authentication, whitelist, carrier receipt and
actual code verification on the remote server still require the controlled live
test in `selfmade-phone-access-update.md`. Provider acceptance is not delivery.

| Agreed MVP requirement | Status | Evidence / remaining work |
|---|---|---|
| Adults 18+, patient and clinician profiles, private synthetic history, distinct account/disclosure identity | partial | Milestone 1 profiles; phone signup requires an adult attestation, while the attestation is not independent age verification. Existing development accounts continue to work. |
| Phone/email possession codes, expiry, single use, rate/abuse controls and separated onboarding | partial | `contact_auth.py`, `email_delivery.py`, v1_5 migration, 7 contact-auth and 24 integration regressions. SMS/email send adapters are mocked. SMTP and SMS credentials/consenting recipients are not configured or live-tested. Professional evidence intake is narrative only; code proves contact possession, not credential verification. |

| Clinician approval and per-service approval | implemented | Manual approver flow and native Service Scope DocType; PR #2 review verification and MariaDB integration tests. |
| Independent clinicians, clinic affiliations and operational staff memberships without implied record access | partial | Native clinic and affiliation DocTypes retain separate human review; the dependent clinic-membership slice adds role-limited invitations, exact verified-email acceptance, revocation audit, generic DocType permissions and an in-workspace portal. Database tests cover unverified-invite denial, owner/manager separation, idempotent retries and no patient-record access; built-browser evidence is being completed on the disposable Frappe 15 site. Invitations are not emailed. Scheduling/Billing labels have no implemented operations, and clinic manager authority is limited to membership administration. Clinic calendars/resources, billing and encounter grants remain pending. Amharic/Afaan Oromo strings are provisional; Frappe 16 compatibility remains pending. |
| Service definitions, approved clinician offerings, published ETB price and fixed duration | implemented | Native Service and Service Scope; scoped publication/discovery/booking and stale-ID regression checks. |
| Natural-language request suggestions, eligible clinician matching, editable filters, relevance feedback; eligibility before ranking | partial | Service filter/discovery exists. Natural-language suggestion, relevance ranking/feedback and proximity matching are absent. |
| Previous clinicians and repeat care discovery | partial | Dependent slice `feat/previous-clinicians` adds a patient-only dashboard query sourced solely from that patient's Completed appointments and currently approved/publicly bookable clinician offerings, plus profile links and loading/empty/error states. The query returns an opaque profile key and never links other patients' masked encounters. Frappe DB permission and browser verification remain pending because the disposable integration site is not provisioned. |
| Private open patient requests and clinician offers, isolated from competing clinicians | partial | `feat/open-requests` provides private owner-scoped APIs, offers, fund/slot acceptance and polling. Dependent `feat/vetting-catalog-routing` adds bounded waves, scope revalidation, presence readiness reasons, immediate-policy enforcement and continuous feasible-start selection. On 2026-10-05 the Frappe 16 presentation suite passed 20/20 and the packaged two-session journey passed publication → eligible inbox delivery → private offer → acceptance → one appointment and one reservation journal. A separate test correctly received no Wednesday recipient because the retained schedule is Monday/Tuesday only. Immediate grid-boundary regression is fixed; phone/SMS, pilot performance and call-to-earnings acceptance remain separate gaps. See `vetting-routing-verification.md`. |
| Progressive explainable routing, service catalog and clinician vetting | partial | Additive linked native category/approach/topic/format/attribute and per-scope application/assessment DocTypes; catalog remains draft/inactive pending clinical review. Applicant drafts, reviewer assignment, clarification/resubmission, per-scope decisions and private resume reference exist. Proposed rubric v1.0 is not approved. Full mandatory credential/jurisdiction/accessibility validation, affiliation verification, scored assessment, appeals/reverification and transparent eligibility-first ranking remain pending. Structured session-experience, immediate-inbox offer-response, and clinician-attributed cancellation indicators now have versioned formulas and sample suppression in source; Frappe migration/query/privacy/browser acceptance is pending. See `session-experience-metric.md`. |
| Free patient discovery/booking and bring-your-own-patient links | partial | Current demo supports direct discovery/booking; clinician referral links/acquisition attribution not built. |
| Automatic/manual booking confirmation, slot holds/expiry and mutual rescheduling | partial | Recurring server-generated slots, configurable automatic/manual confirmation, atomic slot/fund holds and 24-hour demonstration expiry/release are implemented and regression tested. Mutual rescheduling is not implemented. |
| Global disclosure defaults, request override and exact per-request preview | implemented | Separate defaults/override, immutable booking snapshot, privacy and profile-edit regression tests. |
| Public review identity separate from account and clinical disclosure identity | partial | No public identity or comments are collected. A patient may submit one 1–5 session-experience rating only after their own encounter is ended and finalized; clinician profiles show a rolling 365-day mean only at five or more responses. Migration/API/browser verification remains pending; free-text comments and moderation are not implemented. See `session-experience-metric.md`. |
| Couples participation with individual consent and optional mutual relationship link | pending | No shared appointment, separate participant permissions, or consent workflow. Payment/partner relationship must not grant record access. |
| Authorized human voice/video, audio-only, mute/camera, Leave and clinician End | partial | Hosted Cloud browser test passed for independent Chromium contexts with fake devices, Leave/rejoin/End and original/refreshed token rejection for both identities, including a departed participant. End test root cause was a stale “Refresh” click after polling; fixed without removing assertions. Human/device testing remains. This remains a demo, not clinical readiness. |
| No recording/transcription by default; no automatic charge/release from connection time | implemented | No recorder/transcriber/agent/automatic extension charge/release path in PR #3; keep this invariant in all call work. |
| Clinician notes, patient-authorized summary, email link to authenticated summary, follow-up booking | partial | Private versioned clinician notes, separately published summary revisions, direct API privacy and same-clinician follow-up booking are implemented/tested. Email notification/link is not implemented. |
| Completed-session ratings/reviews | pending | No completed-session lifecycle or rating API/UI. |
| Cancellation rules differ by actor; bounded clinician policy, immutable accepted snapshot, disputes/earnings hold | partial | Authorized pre-start cancellation, accepted demo policy snapshot and exact-once full simulated reservation release are implemented. This is one explicit demo policy, not the requested actor-specific production policy or disputes/earnings hold. |
| Simulated patient deposit and atomic available/reserved booking balance | implemented | Labeled development-only simulation, integer minor units, MariaDB atomicity and rollback tests. Not real-money funding. |
| Balanced demonstration subledger, clinician pending/available earnings, authorized extensions and explicit consent/funds reservation | partial | v1.7 adds an immutable balanced demonstration journal distinct from the old `tt_ledger` activity log; booking, explicit finalization, dispute holds, scheduled release and payout reservations are tested. Paid extensions remain absent. This is not ERPNext accounting or real-money readiness. |
| Simulated payouts and snapshotted withholding | partial | Zero-fee policy and dispute window are captured per booking; release is retry-safe; clinician payout request/cancel reserves/releases available funds exactly once. No external transfer, processing or paid state exists. Post-release refund and dispute workflows are deliberately unsupported pending authorized resolution. |
| Refund unused funds using verified supported route | partial | Demo pre-start release restores simulated balance exactly once; no real refund rails or production refund policy exist. |
| ERPNext accounting/reporting integration and production reconciliation | pending | The demonstration journal has durable references, balance checks and a migration preservation check, but no ERPNext posting, real custody or production reconciliation exists. |
| English, Amharic and Afaan Oromo UI translation | partial | Existing journey keys in all three languages; Amharic/Afaan Oromo strings are provisional and need native review. OTP adds keys under Phase 1. |
| Responsive accessible patient, clinician and administrator journeys/design system | partial | New routes/layouts, original local brand, tokens/components, hosted Playwright 1.63 Chromium and connected booking/onboarding journeys. Synthetic screens captured/inspected at 390/768/1440 plus 320 and 200% zoom; no horizontal overflow. New narrative is partly English in Amharic/Oromo pending translation review. Human device/assistive-tech review remains. |
| Role-specific tours with persisted dismissal/replay and permission-aware steps | implemented | Per-user/role/version progress, patient/clinician/applicant/approver tours, route-safety handling, dismiss persistence, replay, route transitions and missing-target recovery passed API/browser checks; screenshots at 320/390/768/1440 are in `/tmp/tele-tena-presentation-review/`. |
| Presentation release: recurrence scheduling, bookings, lifecycle, notes, detail pages, private resumes, directory, PWA and tours | partial | Existing API/React flows are connected. The availability save defect was reproduced as `start_local`/`end_local` versus API `start`/`end`; focused hotfix is PR #11 (open). The Frappe 16 browser save/reload/booking journey passes again after the fix. Broader layout/e2e work on this branch remains under review; see `presentation-readiness-verification.md`. |
| Production safety/escalation, credential verification, hosting and regulated financial/provider readiness | pending | Product contract marks these unresolved/deferred. Demo uses synthetic accounts/data and is not production clinical readiness. |

## Current delivery and remaining sequence

1. Contact verification and onboarding are implemented. The email OTP state-machine suite passed 7/7 with a mocked provider and enabled-registration fixture; the retained review site remains invitation-only. Live delivery awaits secure local configuration and a consenting recipient. Do not treat codes as SMS/email delivery proof or professional approval.
2. The TeleTena design and focused React journeys are implemented on merged main through PR #6 (`7222836`). This presentation feature branch extends that baseline; its new visual and behavioral evidence is in `docs/presentation-readiness-verification.md`.
3. Discovery, previous clinicians, private requests and offers.
4. Mutual rescheduling, actor-specific production cancellation policy, no-show actions, and production refund rules. This branch adds only an explicit pre-start demonstration cancellation/release policy.
5. Couples consent and sensitive-summary notification/email delivery. This branch adds private notes, separately approved summaries and same-clinician follow-up booking.
6. Ratings, responsiveness, pending earnings, simulated withdrawals and explicitly authorized extensions.
7. Any change to calls must retain LiveKit Cloud revocation, both identity aliases, cutoff/concurrency behavior and the full hosted End regression. PR #3’s source branch remains preserved while consolidation is reviewed.

Demonstration funding is not real-money readiness. `tt_ledger` remains the simulation activity log, while v1.7 `tt_journal` is a separate balanced demonstration subledger; neither is ERPNext posting or settlement. Live SMS, SMTP, credential verification, physical-device call testing and production readiness remain outstanding.

Current release-check note: the additive repeat-migration check now snapshots
the v1.7 account, journal, earning, dispute and payout tables and passed on the
disposable site. The stronger wallet-to-journal reconciliation check exposed a
synthetic seeded patient mismatch after an old loopback test worker had written
legacy events without subledger postings. The records were preserved and no
release claim is based on reconciling that account; a fresh isolated site is
needed for clean financial cutover verification.

### Expanded product scope status (2026-10-07)

| Approved area | Current status | Evidence / remaining work |
|---|---|---|
| Extracted design, React design system, all 142 screens | partial | Existing React flows remain authoritative and the visual tokens now begin moving toward the extracted Inter/blue–teal reference. Screen-level map covers 142 concepts. Most routes still need direct visual and connected interaction review; prototype-only states are not accepted. |
| Clinician vetting and service catalog | partial | Native per-scope application, reviewer decision and draft catalog exist; proposed rubric v1.0 remains subject to medical-lead approval. Evidence-by-scope, affiliation verification, license renewal/suspension/appeal operations and approved clinical terminology review remain. |
| Open requests, private offers and progressive routing | partial | PR #13/#14 implement persisted request/offer state, eligibility, presence and bounded waves. PR #15 adds owned paginated history, awaiting Frappe 15 integration/browser verification. Three-minute results require pilot coverage and are not guaranteed. |
| Owner-level legacy financial reconciliation | implementation in progress | New v1.13 migration records legacy-event, wallet-snapshot, subledger and exact opening-boundary differences without changing existing records. Mismatched owners are held until an authorized reasoned snapshot decision. Fresh/upgrade/repeat tests on a disposable site remain pending. |
| Extensions and dispute/refund policy | pending | No prefunded explicit extension workflow. Refunds/disputes after release or payout state remain gated for authorized operations; no negative balance or history edits are allowed. |
| Clinic operations and record grants | pending | Membership, staff roles, verified affiliations, calendars/resources and explicit encounter grants are not implemented. |
| Adult couples/family care | pending | Separate participant identity, invitations, per-person consent/disclosure, multi-party call permissions and recipient-specific documentation are absent. |
| Laboratory and diagnostics | pending | The v1.12 inactive typed-attribute example is a schema illustration only. Partners, orders, specimen custody, processing, result review/correction/release and integration are absent. |
| Subscriptions | pending | No durable plan entitlements or provider event workflow. Basic records must remain outside any subscription gate. |
| Second opinions and medical travel | pending | No case-sharing, jurisdiction workflow, conditional estimate/proposal or coordination records. |
| Administration and operations | partial | Clinician/scope review, financial disputes and request administration exist in slices. Clinic/lab/metrics/support and scoped financial operations remain. |

Status distinction: “implemented” describes behavior covered by code and listed
checks; “verified” requires the named current-environment run; “external” means
live provider, clinical, legal or partner acceptance is still needed.

## Selfmade review packaging

Deployment packaging and compatible Frappe 16 work were merged through PRs #7–#10.
Selfmade was separately reported installed at `bba5ed9f15bd0b140967618ed2bd982c31a76c1b`;
the operator later reported actual app SHA `8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6`.
No update is implied by local feature work. The current availability hotfix PR #11 is
open and independent of the wider presentation improvement branch.
