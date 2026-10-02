# Tele-tena MVP delivery tracker

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
| Independent clinicians and multi-clinic affiliations without implied record access | partial | Single-clinician ownership and no affiliation-based access currently; clinic/partner workspace, membership and multiple affiliations not built. |
| Service definitions, approved clinician offerings, published ETB price and fixed duration | implemented | Native Service and Service Scope; scoped publication/discovery/booking and stale-ID regression checks. |
| Natural-language request suggestions, eligible clinician matching, editable filters, relevance feedback; eligibility before ranking | partial | Service filter/discovery exists. Natural-language suggestion, relevance ranking/feedback and proximity matching are absent. |
| Previous clinicians and repeat care discovery | pending | Not represented in current journey/API. |
| Private open patient requests and clinician offers, isolated from competing clinicians | pending | No request board, offer visibility, offer acceptance, or offer fee/time/format/expiry snapshot. |
| Free patient discovery/booking and bring-your-own-patient links | partial | Current demo supports direct discovery/booking; clinician referral links/acquisition attribution not built. |
| Automatic/manual booking confirmation, slot holds/expiry and mutual rescheduling | partial | Recurring server-generated slots, configurable automatic/manual confirmation, atomic slot/fund holds and 24-hour demonstration expiry/release are implemented and regression tested. Mutual rescheduling is not implemented. |
| Global disclosure defaults, request override and exact per-request preview | implemented | Separate defaults/override, immutable booking snapshot, privacy and profile-edit regression tests. |
| Public review identity separate from account and clinical disclosure identity | pending | Reviews/ratings not implemented. |
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

1. Contact verification and onboarding are implemented on the consolidation branch. Live delivery awaits secure local configuration and a consenting recipient. Do not treat codes as SMS/email delivery proof or professional approval.
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

## Selfmade review packaging

Deployment packaging and compatible Frappe 16 work were merged through PRs #7–#10.
Selfmade was separately reported installed at `bba5ed9f15bd0b140967618ed2bd982c31a76c1b`;
the operator later reported actual app SHA `8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6`.
No update is implied by local feature work. The current availability hotfix PR #11 is
open and independent of the wider presentation improvement branch.
