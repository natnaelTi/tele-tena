# Tele-tena MVP delivery tracker

Updated 2026-10-01 on merged `main` at PR #6 merge `7222836`. PRs #3/#4 are merged through preserved ancestry; PR #5 was superseded. The hosted LiveKit Cloud End/rejoin/cached-token assertions passed with automated two-browser fake-media. Status describes demonstration evidence, not production readiness. Presentation release work is tracked separately in `docs/presentation-readiness-verification.md`.

**Status meanings:** `implemented` means code and listed checks cover the
demonstration behavior; `partial` means a narrower slice exists or has a known
validation gap; `pending` means agreed scope is not implemented; `blocked` means
do not release/claim the feature until the stated blocker is resolved.

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
| Automatic/manual booking confirmation, slot holds/expiry and mutual rescheduling | partial | Direct booking confirms immediately with transactional slot reservation. Holds, expiry, confirmation policy choice, and mutual rescheduling are absent. |
| Global disclosure defaults, request override and exact per-request preview | implemented | Separate defaults/override, immutable booking snapshot, privacy and profile-edit regression tests. |
| Public review identity separate from account and clinical disclosure identity | pending | Reviews/ratings not implemented. |
| Couples participation with individual consent and optional mutual relationship link | pending | No shared appointment, separate participant permissions, or consent workflow. Payment/partner relationship must not grant record access. |
| Authorized human voice/video, audio-only, mute/camera, Leave and clinician End | partial | Hosted Cloud browser test passed for independent Chromium contexts with fake devices, Leave/rejoin/End and original/refreshed token rejection for both identities, including a departed participant. End test root cause was a stale “Refresh” click after polling; fixed without removing assertions. Human/device testing remains. This remains a demo, not clinical readiness. |
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
| Responsive accessible patient, clinician and administrator journeys/design system | partial | New routes/layouts, original local brand, tokens/components, hosted Playwright 1.63 Chromium and connected booking/onboarding journeys. Synthetic screens captured/inspected at 390/768/1440 plus 320 and 200% zoom; no horizontal overflow. New narrative is partly English in Amharic/Oromo pending translation review. Human device/assistive-tech review remains. |
| Presentation release: recurrence scheduling, bookings, lifecycle, notes, detail pages, private resumes, directory, PWA and tours | pending | State and policy model is recorded in `presentation-release-model.md`; implementation and evidence are tracked in `presentation-readiness-verification.md`. |
| Production safety/escalation, credential verification, hosting and regulated financial/provider readiness | pending | Product contract marks these unresolved/deferred. Demo uses synthetic accounts/data and is not production clinical readiness. |

## Current delivery and remaining sequence

1. Contact verification and onboarding are implemented on the consolidation branch. Live delivery awaits secure local configuration and a consenting recipient. Do not treat codes as SMS/email delivery proof or professional approval.
2. The TeleTena design and focused React journeys are implemented on this same review branch. Hosted browser screenshots and regression evidence are recorded in `docs/consolidation-verification.md`.
3. Discovery, previous clinicians, private requests and offers.
4. Automatic/manual booking, expiry, rescheduling, cancellation rules and simulated reservation releases/refunds.
5. Notes, approved summaries, follow-ups and couples consent.
6. Ratings, responsiveness, pending earnings, simulated withdrawals and explicitly authorized extensions.
7. Any change to calls must retain LiveKit Cloud revocation, both identity aliases, cutoff/concurrency behavior and the full hosted End regression. PR #3’s source branch remains preserved while consolidation is reviewed.

Demonstration funding is not real-money readiness. `tt_ledger` is a simulation transaction log, not a double-entry subledger or ERPNext posting integration. Live SMS, SMTP, credential verification, payout, human/device call testing and production readiness remain outstanding.
