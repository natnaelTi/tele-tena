# Consolidation verification — in progress

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
- Combined source frontend build and lint passed before redesign.
- Playwright 1.63 supported Chromium OS dependencies installed by user; actual
  Chromium launch passed.
- Migration preservation run must be repeated sequentially: an initial snapshot
  overlapped creation of disposable hosted-test fixtures and failed its equality
  assertion. This run is NOT migration-preservation evidence.
- Redesign, new authentication, final migration and visual acceptance pending.
