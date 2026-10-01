# Tele-tena MVP delivery tracker

Updated 2026-10-01 against merged `main` (PR #2 merge). PR #3 remains open and
unmerged on `feat/milestone-2-consultations`; its hosted-browser End assertion is
a release blocker for voice/video. The SMS phase is being developed separately
from main. Statuses describe implementation evidence, not production readiness.

**Status meanings:** `implemented` means code and listed checks cover the
demonstration behavior; `partial` means a narrower slice exists or has a known
validation gap; `pending` means agreed scope is not implemented; `blocked` means
do not release/claim the feature until the stated blocker is resolved.

| Agreed MVP requirement | Status | Evidence / remaining work |
|---|---|---|
| Adults 18+, patient and clinician profiles, private synthetic history, distinct account/disclosure identity | partial | Milestone 1 profiles and adult attestation; no verified-phone onboarding yet; existing email accounts continue to work. |
| Phone possession OTP, expiry, single use, rate/abuse controls, clinician application entry | pending | Phase 1 contract in `phone-otp.md`; provider credential and live whitelist check still require operator input. OTP is not credential verification. |
| Clinician approval and per-service approval | implemented | Manual approver flow and native Service Scope DocType; PR #2 review verification and MariaDB integration tests. |
| Independent clinicians and multi-clinic affiliations without implied record access | partial | Single-clinician ownership and no affiliation-based access currently; clinic/partner workspace, membership and multiple affiliations not built. |
| Service definitions, approved clinician offerings, published ETB price and fixed duration | implemented | Native Service and Service Scope; scoped publication/discovery/booking and stale-ID regression checks. |
| Natural-language request suggestions, eligible clinician matching, editable filters, relevance feedback; eligibility before ranking | partial | Service filter/discovery exists. Natural-language suggestion, relevance ranking/feedback and proximity matching are absent. |
| Previous clinicians and repeat care discovery | pending | Not represented in current journey/API. |
| Private open patient requests and clinician offers, isolated from competing clinicians | pending | No request board, offer visibility, offer acceptance, or offer fee/time/format/expiry snapshot. |
| Free patient discovery/booking and bring-your-own-patient links | partial | Current demo supports direct discovery/booking; clinician referral links/acquisition attribution not built. |
| Automatic/manual booking confirmation, slot holds/expiry and mutual rescheduling | partial | Direct booking confirms immediately with transactional slot reservation. Holds, expiry, confirmation policy choice, and mutual rescheduling are absent. |
| Global disclosure defaults, request override and exact per-request preview | implemented | Separate defaults/override, immutable booking snapshot, privacy and profile-edit regression tests. |
| Public review identity separate from account and clinical disclosure identity | pending | Reviews/ratings not implemented. |
| Couples participation with individual consent and optional mutual relationship link | pending | No shared appointment, separate participant permissions, or consent workflow. Payment/partner relationship must not grant record access. |
| Authorized human voice/video, audio-only, mute/camera, Leave and clinician End | blocked | Implemented on PR #3 with hosted Cloud token revocation and focused fake-media tests, but the complete hosted browser journey still fails at its final End-control assertion. Keep PR #3 open; resolve and rerun full demonstration acceptance before release. |
| No recording/transcription by default; no automatic charge/release from connection time | implemented | No recorder/transcriber/agent/automatic extension charge/release path in PR #3; keep this invariant in all call work. |
| Clinician notes, patient-authorized summary, email link to authenticated summary, follow-up booking | pending | Not implemented. Summary notification body must not contain sensitive clinical data. |
| Completed-session ratings/reviews | pending | No completed-session lifecycle or rating API/UI. |
| Cancellation rules differ by actor; bounded clinician policy, immutable accepted snapshot, disputes/earnings hold | pending | No cancellation, policy versions or dispute hold. No policy windows/caps are assumed. |
| Simulated patient deposit and atomic available/reserved booking balance | implemented | Labeled development-only simulation, integer minor units, MariaDB atomicity and rollback tests. Not real-money funding. |
| Double-entry operational subledger, clinician pending/available earnings, authorized extensions and explicit consent/funds reservation | pending | Current `tt_ledger` is only an append-only simulation transaction log. No double-entry subledger or extension flow; see `pr2-storage-review.md`. |
| Simulated withdrawals/payout processing and configured withholding | pending | No earnings or payout workflow. External settlement is not instant and requires separate design. |
| Refund unused funds using verified supported route | pending | No cancellation/refund workflow. Existing reservations stay as recorded. |
| ERPNext accounting/reporting integration, durable posting references/retries and reconciliation | pending | ERPNext is the agreed accounting system, but no posting or reconciliation exists. Never treat simulation events as accounting completion. |
| English, Amharic and Afaan Oromo UI translation | partial | Existing journey keys in all three languages; Amharic/Afaan Oromo strings are provisional and need native review. OTP adds keys under Phase 1. |
| Responsive accessible patient, clinician and administrator journeys/design system | pending | Current React app is a demonstration screen, not the planned reusable design system or focused portal navigation; scheduled after the OTP checkpoint. |
| Production safety/escalation, credential verification, hosting and regulated financial/provider readiness | pending | Product contract marks these unresolved/deferred. Demo uses synthetic accounts/data and is not production clinical readiness. |

## Delivery sequence

1. **Phone OTP/access** — `feat/phone-otp` from merged main. Record criteria in
   `docs/phone-otp.md`; mock provider tests only until local key and consenting
   whitelisted recipient are supplied. Open a PR; do not merge automatically.
2. **React design system and focused journeys** — after Phase 1 PR is opened,
   create a distinct branch with an explicit dependency on the phone-auth API
   shape. No clinical/authenticated API caching. Connect only real APIs; show
   unfinished behavior as unavailable rather than fabricated.
3. **Discovery/marketplace** — clinician profiles, previous clinicians,
   relevance/proximity constraints, private open requests/offers and visibility.
4. **Booking lifecycle** — automatic/manual confirmation, holds and expiry,
   rescheduling, cancellation policy snapshots, releases/refunds and disputes.
5. **Clinical records and shared care** — notes, approved summaries, follow-ups,
   couples links and individual consent.
6. **Trust and finance** — ratings, responsiveness, pending/available earnings,
   simulated withdrawal, authorized extensions with explicit mutual consent and
   reservation. Design the double-entry/ERPNext boundary separately.
7. **Corrected LiveKit acceptance** — resolve PR #3 release blocker, then pass
   authorized two-party join/media/Leave/End, token-revocation and full browser
   demonstration acceptance. No merge or deployment is implied by a phase.

## Readiness boundary

Current booking funds and deposits are simulated demo records only. SMS API
acceptance is not delivery, and OTP is not clinician credential approval.
Production payment activation, real-money safeguarding, double-entry records,
ERPNext posting, reconciliation, dispute operations and provider/regulatory
approval remain unimplemented. No release or launch claim should blur these
boundaries.
