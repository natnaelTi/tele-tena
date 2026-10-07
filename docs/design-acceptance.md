# TeleTena redesign acceptance record

Authoritative requirements are in [design-system.md](design-system.md). An
unchecked item is not a pass. This record documents the merged PR #6 baseline. Presentation release acceptance is
tracked below and in the release verification report. Artifacts use synthetic information only.

- [x] Save the supplied specification and require both frontend design documents in AGENTS.md.
- [x] Fetch and inspect main and PR #3/#4/#5, verification reports, dependencies and working tree. Preserve source branches and data.
- [x] Preserve PR merge ancestry; calls precede OTP and prior UI integration. Resolve API, migration and shared-App conflicts deliberately.
- [x] Keep separate merge, contact/authentication, redesign and verification commits.
- [x] Save the milestone tracker with completed, partial, pending and blocked scope; call behavior and financial readiness are distinct.
- [x] Record verified-contact/onboarding behavior and permission boundary; synthetic-only signup.
- [x] OTP expiry/single-use/attempt and resend/rate rules; request identifiers are idempotent and delivery never retries automatically.
- [x] Legacy phone OTP routes cannot skip onboarding or assign Patient/Applicant roles. Manual approval remains required for clinician access.
- [x] Email OTP sends over backend-only TLS SMTP; credentials use invisible local setup and mode-600 file. No live delivery without credentials and consenting recipient.
- [x] Original local logo symbol, wordmark, mono/reversed lockups and favicon; 16/24/32 px showcase.
- [x] Local SIL OFL Manrope/Noto Sans Ethiopic assets; design colors, spacing and contrast measured.
- [x] Shared buttons, icon buttons, fields, phone/OTP inputs, select, checkbox, radio, switch, cards, dialog/drawer, tabs, navigation, badges, notices, toast, skeleton, empty state, care/disclosure/booking summaries and call controls.
- [x] Public home, distinct phone then code entry and email OTP/password choice.
- [x] Hosted review sign-in reflects site delivery configuration: phone first when enabled and email password when SMTP code delivery is unavailable. Browser OTP sending is mocked; provider delivery is checked separately.
- [x] Resumable adult patient and clinician application onboarding; synthetic professional narrative, no credential upload/verification.
- [x] Focused patient home/discovery/appointments/privacy/payment and clinician Today/availability/services/care routes. Incomplete features identified in UI and tracker.
- [x] Focused application/service-scope admin routes; no patient-record access from admin review.
- [x] Dedicated consultation route with preflight and joined view. Call regression preserves hosted End, Leave/rejoin and token revocation assertions.
- [x] Install Playwright 1.63 Chromium OS dependencies through supported setup and confirm Chromium launches.
- [x] Drive actual persisted sign-in, onboarding save/resume, discovery, price/privacy preview, booking and workspace journeys.
- [x] Capture rendered screens at 390, 768, 1440; homepage and showcase additionally at 320. Assert no horizontal overflow.
- [x] Inspect English layout, Amharic glyph/line rendering and Afaan Oromo sample; capture all three. Not every new product paragraph is translated yet; secondary review notice marks provisional/incomplete copy.
- [x] Test dialog keyboard focus/Escape, reduced-motion CSS, touch-sized controls and a 200% zoom/no-overflow sample.
- [x] Capture actual connected two-browser call layouts at 390/768/1440 (fake camera/microphone only).
- [x] Run 24 existing permission/booking/balance/OTP/consultation regressions and 7 new contact/onboarding regressions.
- [x] Run repeat migration preservation check with exact existing records and DocType service-scope rows.
- [x] Hosted browser, updated End control, Leave/rejoin and cached initial/refreshed token checks passed on this verification commit.
- [x] Final local branch build, lint and Python syntax checks; focused, integration, migration and hosted-call regressions passed.
- [ ] Push reviewable PR and pass its required GitHub checks.
- [ ] Human language review, physical device/assistive-technology testing and live SMS/SMTP delivery.
- [x] Review actual screenshots; artifacts at `/tmp/tele-tena-redesign-review/`.
- [ ] Required GitHub checks on the pushed consolidation PR.

## Presentation release

Detailed states and demonstration policies: [presentation-release-model.md](presentation-release-model.md).
Run evidence is itemized in [presentation-readiness-verification.md](presentation-readiness-verification.md).

- [x] Weekly schedule recurrence, exceptions, timezone conversion, global clinician conflict check, valid-slot booking and manual-confirmation reservation lifecycle.
- [x] Distinct server-enforced appointment/call/documentation states; explicit completion and authorized cancellation/release.
- [x] Private notes, separately published summaries, revision and visibility history, follow-up booking.
- [x] Status-aware consultation detail and focused audio/video room; hosted cached-token End/revocation check passed.
- [x] Clinician care directory and encounter-scoped disclosure history.
- [x] Focused account sections and backed wallet summaries; no fabricated earnings.
- [x] Admin names/status/scopes/resume evidence with permission-checked private upload/download.
- [x] Public-only static cache, offline page and no forced service-worker reload.
- [x] Persisted, dismissible and replayable role-specific tours with English, Amharic and Afaan Oromo copy.
- [x] Synthetic screenshot/browser journeys at 320, 390, 768 and 1440 px, plus the 200%-equivalent narrow-layout check, keyboard flows, language samples and offline navigation.
- [ ] Human translation review, physical-device media and PWA installation review.

## Consolidated baseline and next design coverage

PRs #7–#10 are merged into `main` at `4cc0be9a0a96c3b209d07b47fd5e7c46ab4c31a2`.
The [route and component inventory](design-update-inventory.md) is the coverage
checklist for the forthcoming design brief. Each changed row needs responsive
rendering, connected-flow and three-language review; placeholders remain visibly
unavailable until their backend capability is implemented. The Selfmade site is
still pinned to its installed release and was not updated by these merges.

## Historical merge gate
PR #6 passed the hosted LiveKit and local checks and merged as `7222836`. Source PRs
#3/#4 merged through preserved ancestry; #5 was superseded. Presentation PR #7
subsequently merged through preserved ancestry. No production deployment is
authorized by these merges.

## Review installation packaging

The presentation identity and flows are unchanged. Production URLs add the
`/teletena` namespace; root-relative API authorization remains on Frappe. Built
browser verification and deployment limitations are recorded separately in
`review-deployment-verification.md`, not inferred from prior Vite screenshots.

## Extracted 142-screen product design integration (current branch)

The source visual reference is `/home/frappe/teletena-design-reference`; the
latest `screen-inventory.json` has 142 screens in 14 journeys (the older handoff
mentions 138 concepts). The HTML/CSS is not accepted as application behavior.
This branch has begun porting the approved blue–teal palette and self-hosted
Inter typography into the existing Frappe-served React app, retaining Noto Sans
Ethiopic and the existing TeleTena conversation logo. These code changes are
not yet rendered in the built `/teletena/` app, so no extended visual acceptance
is claimed.

- [ ] Route all 142 screen/state entries through real persisted APIs or mark the
  exact dependency that blocks them in `operational-screen-map.json`.
- [ ] Finish Batch A authentication/onboarding layout and three-language flows.
- [ ] Finish human-led vetting, per-scope catalog and verified trust indicators.
- [ ] Finish discovery, schedule, direct booking and consultation journeys.
- [ ] Finish request routing/offer acceptance and clinician presence states.
- [ ] Finish subledger, dispute, release, payout and explicit extension states.
- [ ] Add clinic memberships/encounter grants and multi-participant adult consent.
- [ ] Add laboratory, subscription, second-opinion and medical-travel operations
  only with real models, permissions and required external partner validation.
- [ ] Complete focused administration, support and audit routes.
- [ ] Render connected populated/empty/error flows at 320/390/768/1440 and 200%
  zoom; capture Amharic and Afaan Oromo layout; get human translation review.
- [ ] Verify fresh/repeat migration and owner-by-owner financial reconciliation
  without editing existing wallet or appointment history.
