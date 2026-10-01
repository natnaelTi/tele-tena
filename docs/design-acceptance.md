# TeleTena redesign acceptance record

Authoritative requirements are in [design-system.md](design-system.md). An
unchecked item is not a pass. This branch remains under review until its PR checks
complete. Artifacts use synthetic information only.

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

## Merge gate
Merge the consolidation only when hosted call checks pass on the final commit, all
local regressions/build checks pass, and GitHub reports successful required checks.
Do not deploy to production. Preserve PR #3/#4/#5 branches until this merge accounts
for their changes; then mark their PRs superseded without deleting source branches.
