# Consolidation verification

Branch: feat/mvp-consolidation. Source ancestry integrated with merge commits:
PR #3 (619e5ec), PR #4 (05da857), PR #5 (c66ba4c). Source branches preserved.
The rejected PR #5 design report is retained as pr5-design-verification.md.

## Hosted End regression root cause (2026-10-01)
The full UI test reached End successfully but then clicked Refresh call status on
the patient screen. Lifecycle polling had already observed End and removed that
preflight control. The stale interaction timed out; its coarse checkpoint made
this appear to be an End failure. The corrected test observes the patient lifecycle
through polling directly. Both clinician and patient ended-state assertions remain,
with additional assertions for no Join controls and no attached remote media.
PR #5 integration also requires navigating to Appointments before finding a call.

Actual run: `../../env/bin/python scripts/check_hosted_livekit_revocation.py`:
- PASS hosted Cloud direct SDK rejection of original/refreshed participant tokens
  for both opaque identities; patient left before End.
- PASS full independent Chromium contexts exchanging fake-device audio/video,
  preview-mode cleanup, injected connection/publication failures, duplicate Join,
  delayed-token unmount cleanup, polling status, Leave/rejoin and clinician End.
These are hosted automated fake-media tests, not human/device verification.
No configured credentials were replaced and disposable test fixtures were cleaned.
Self-hosted limitation remains: removal/deletion alone does not revoke cached JWTs.

## Integration checks
- Latest integrated frontend production build passed (`npm run build`).
- `npm run lint` exited successfully with non-fatal fast-refresh and stable-time
  sampling advisories. The production build reports the LiveKit client chunk over
  500 kB; it remains a performance follow-up, not a test failure.
- Playwright 1.63 supported Chromium OS dependencies installed by user; actual
  Chromium launch passed.
- A prior migration snapshot overlapped disposable hosted-test fixture creation
  and failed equality. That run was invalidated; the sequential repeat recorded
  below passed against the original development records.
- Redesign and new authentication browser checks completed with synthetic data.

## Redesign browser check
`../../env/bin/python scripts/check_redesign_browser.py` passed using persisted
MariaDB records and isolated synthetic users. It drove the real saved onboarding,
profile, discovery, booking and balance APIs. Only initial phone-code delivery UI
was intercepted in the browser; backend code verification/request tests use mocked
providers. No real OTP message was sent. Screenshot set:
`/tmp/tele-tena-redesign-review/` (homepage, phone entry, code entry, email,
onboarding, patient home/discovery/booking preview/appointments/privacy/payments,
clinician Today/availability/services/care, admin review, preflight, component
showcase in English/Amharic/Afaan Oromo; responsive captures at 390/768/1440,
plus 320 and a 384 CSS-pixel viewport equivalent to 200% zoom on a 768px display). Rendered screenshots were manually inspected. One issue
with administrator identifiers wrapping and compact clinician navigation spacing
was corrected and rerun. Dialog Escape/focus and no-overflow checks passed.

Synthetic-only limitations: browser media uses Chromium fake camera/microphone,
not physical devices. Local-development login uses the explicit email-password
alternative. No real SMS or SMTP delivery, credential uploads/checks, human language
review, screen-reader/device test, or real-money accounting was performed.
Contrast checks (WCAG normal text): primary white 6.34:1; hover white 8.40:1;
primary ink/canvas 14.07:1; secondary/canvas 5.88:1; success/surface 6.55:1;
danger/surface 8.80:1; information/subtle 6.24:1. Apricot is not used for text.

## Final regression rerun
- `../../env/bin/python tests/integration.py` — PASS, 24/24; includes service
  scope permission, profile/disclosure isolation, idempotent reservation, migration,
  role review, OTP throttling/single-use and join/end authorization concurrency.
- `../../env/bin/python tests/contact_auth.py` — PASS, 7/7; includes concurrent
  consumption, expiry/attempt limits, owner-only drafts, role injection and generic
  account/contact response behavior.
- `../../env/bin/python scripts/check_migration.py` — PASS after tests completed
  sequentially: seven numbered patches, repeat migration, legacy and new records,
  service-scope DocType rows, catalog copy and private OTP key unchanged/preserved.
- `npm run build` and `npm run lint` — PASS; lint reports non-fatal React fast-refresh
  and stable-time sampling advisories. Build retains a lazy LiveKit chunk >500 kB.
- `../../env/bin/python scripts/check_hosted_livekit_revocation.py` — PASS on the
  configured LiveKit Cloud development project; direct SDK reconnect was rejected
  for original and refreshed tokens for both identities after End, including a
  participant who left first; two independent Chromium fake-media clients exchanged
  media and passed cleanup/failure/Leave/rejoin/End assertions.
- `../../env/bin/python scripts/check_redesign_browser.py` — PASS after replacing an
  invalid CSS page-scale zoom simulation with a 384 CSS-pixel effective viewport
  check representing 200% zoom on a 768px display. No horizontal overflow at tested
  widths. Captures were inspected; browser tests use synthetic accounts and fake media.

These checks use the running `erp.localhost` development site. No fresh disposable
site install was repeated for this redesign; the preserved-data repeated migration
check ran on the existing site. No physical microphone/camera, real OTP delivery,
translator or screen-reader test was performed.
