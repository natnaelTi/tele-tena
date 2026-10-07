# Mutual rescheduling verification

This is a local demonstration workflow. It does not move or refund funds and
does not create a second appointment.

## Rules implemented

- A patient or treating clinician may suggest a new time for a future `Booked`
  appointment before a consultation room exists.
- A single active proposal is allowed. A retry with the same actor, key and
  payload returns the original proposal; reusing the key with changed data is
  rejected.
- The proposed time must pass the existing generated-slot validator for the
  same active offering, approved clinician and service scope, duration and
  consultation format. Current clinician/patient conflicts, buffers, notice,
  horizon, date exceptions and published timezone schedule are rechecked.
- The original appointment continues occupying its slot while awaiting the
  other participant. Only the other participant can accept or decline; only the
  proposer can withdraw. A default 48-hour expiry is configurable with the
  site setting `tele_tena_reschedule_expiry_hours` (1–168 hours).
- Acceptance takes the existing global scheduling lock, repeats eligibility and
  slot validation, then updates the original appointment in place. Its ID,
  price, financial policy, disclosure snapshot and reservation are preserved.
  The resulting timeline event records the action. If the slot was claimed in
  the meantime, the proposal becomes unavailable and the old appointment stays
  booked.
- Declined, withdrawn, expired and superseded proposals do not mutate the
  appointment or create ledger/subledger postings. Cancellation closes a
  pending proposal. Past, pending-confirmation, started-call and finalized
  encounters cannot use this flow.

## Verification record

The additive `v1_15_mutual_rescheduling` patch was applied to the retained
isolated site `tele-tena-pr12-fresh.localhost` after a full site/database/files
backup, and `bench --site ... migrate` was repeated successfully. This is an
upgrade/repeat-migration check, not a fresh-site installation check.

On Frappe 15.121.2 / ERPNext 15.121.6 / Python 3.12.3, the complete presentation
suite passed 26 tests on the migrated site. Focused regressions also passed for
idempotent propose/accept, unauthorized participant and third-party access,
unchanged reservation and successful in-place movement, and a competing booking
making the proposed slot unavailable. The frontend production build and lint
completed; lint retains pre-existing warnings and Vite reports the existing
large LiveKit bundle warning. The packaged `/teletena/` browser journey passed
with independent synthetic patient and clinician sessions: patient selected a
server-generated slot and proposed it, clinician saw and accepted it, and the
appointment/proposal were confirmed persisted as `Booked`/`Accepted`. The
captured desktop screens are `docs/screenshots/mutual-rescheduling/`. This is
functional desktop evidence, not full responsive/accessibility acceptance. No
fresh install, physical-device, or native-language approval is claimed.

Appointment timeline events are presented as human-readable, localized labels;
internal event codes remain private to persistence and are not rendered to
participants. The regression suite checks the accepted-time label in the
patient's authorized timeline.

## Current integrated local checkpoint

The current branch is `feat/mutual-rescheduling`; its production asset manifest
reports source `a4c058d7496f38db7eeb8ff9711601eafbdd0154`. The 390px patient-home screenshot is
`docs/screenshots/mutual-rescheduling/patient-home-390.png`. A fresh browser
context signed into the seeded patient, reached `/teletena/patient`, received
the service worker at `/teletena/sw.js`, and reported no page exceptions.

The correct credentials for this preview are stored privately at
`sites/tele-tena-pr12-fresh.localhost/private/tele_tena_review_accounts.json`.
The similarly named `/tmp/tele-tena-demo-credentials.json` belongs to
`erp.localhost` and does not authenticate against the isolated review site.
No account credentials are included here.

The invited-review browser check passes: the API reports phone OTP and public
registration disabled, the phone Continue action is disabled, and the email /
password alternative remains available. The real backend contact-auth suite
passes 7/7 with registration policy enabled inside its isolated test setup.

After the latest package build, the seeded patient signed into this URL again
and reached `/teletena/patient`; the registered service worker controlled
`/teletena/sw.js`, and the browser reported no page exceptions. The current
clinician package displays setup links for the missing readiness conditions.
No browser cache was cleared; this check used a new browser context and the
asset manifest's current source SHA.

A disposable fresh install reached and passed app installation, schema, role,
guest-denial, and simulation-disabled assertions; its optional browser journey
then stopped at an obsolete homepage-heading expectation before auth testing.
That browser assertion has been updated to the current two-audience hero. The
fresh-install/browser harness has not yet been rerun after the correction.
Its cleanup removed the disposable database/site and temporary database admin
and credential file. The retained preview database and records were
fingerprinted unchanged.

A separate seeded clinician browser session opened
`/teletena/clinician/availability`; the weekly calendar and first configured
work interval were visible, there was no horizontal overflow, and no page
exception occurred. This was a read-only inspection; the existing schedule
was left unchanged. Screenshot:
`docs/screenshots/mutual-rescheduling/availability-1440.png`.

The production-route calendar regression also passed against the same URL:
field-level end-before-start error preserved the entered value; valid Monday
and Tuesday intervals were posted as `start_local`/`end_local`, saved (HTTP
200), and retained after reload; the patient booking page returned a
server-generated slot and completed one booking (HTTP 200). Before the test,
the clinician's schedule was saved to a private local snapshot and restored
afterward; the original appointment and balance records were not changed. The
test's new synthetic patient, deposit and booking were retained as additional
demonstration records. See `docs/screenshots/availability-regression/` for the
earlier full journey evidence.

At 390px, the clinician route uses the weekday agenda and time-field editor,
keeps the calendar grid hidden, and has no horizontal overflow. The editor now
keeps a sticky Save action reachable on mobile and translates its saving and
saved states. Screenshot:
`docs/screenshots/mutual-rescheduling/availability-390.png`.

## Verification update — 2026-10-07

The focused Account change was committed as
`63470939cd652d454b341c70922e7383cd8f5cae` on
`feat/mutual-rescheduling`; its production asset manifest reported that source
SHA during browser verification. The report update is documentation-only; the
packaged asset manifest is regenerated from the final source commit. The local review URL remains
`http://127.0.0.1:8017/teletena/` on the isolated
`tele-tena-pr12-fresh.localhost` site. No Vite server is used. The isolated
Gunicorn process serves this app checkout and production assets; the original
`erp.localhost` site was not migrated or reset.

The clinician Account > Personal profile view no longer repeats an Earnings
panel unrelated to that section. A browser authenticated as the synthetic
clinician verified that the built page contains no Earnings heading. The
earnings activity remains under its dedicated workspace route. The PWA update
prompt test passed against the built Frappe route, and a separate real-worker
browser probe verified the service-worker controller and offline fallback.

`npm run build`, `npm run lint` (exit 0 with existing Oxlint warnings),
`python3 -m compileall`, `git diff --check`, and
`scripts/check_review_assets.py` passed. The backend presentation suite passed
26/26 on the disposable review site. The repository-default `python3
tests/presentation.py` cannot import Bench dependencies; it must use the Bench
virtualenv and an explicitly allowed disposable `TELE_TENA_TEST_SITE`.
GitHub checks passed for this commit on Node 22.23.3/24.13.0 and Python
3.12/3.14.2.

A separate fresh-site run installed Frappe, ERPNext and TeleTena; the asserted
DocTypes, roles, migrations, guest denial, and disabled-by-default simulation
state passed. The optional registration-enabled browser process timed out at
300 seconds after homepage captures, before authentication journeys. This is
recorded as an unresolved browser-harness result, not a fresh-site browser
pass. The same run verified cleanup of the disposable site/database, temporary
database administrator and mode-600 credential file, and confirmed retained
site data fingerprints were unchanged. Its local MariaDB was 10.11.14, outside
Frappe 15's tested range; this is not exact Selfmade-stack compatibility
evidence. Fresh-install schema assertions passed, but full fresh-site browser
acceptance remains open.

The timeout root cause was that the fresh-site journey opened `/teletena`
without a trailing slash while the registered worker scope is `/teletena/`.
Frappe normalized the renderer's internal path, so the first attempted redirect
looped. The renderer now checks the original request path and issues a fixed
308 redirect to `/teletena/`, preserving the query string. The browser journey
asserts this canonical route. On the packaged preview, a real Chromium check
verified the 308, `200` for `/teletena/`, service-worker readiness, controller
after reload, and offline fallback rendering. The harness now emits safe fixed
checkpoint labels, applies bounded Playwright timeouts, and bounds worker
readiness. A complete fresh-site rerun is still pending; this probe does not
substitute for its registration and authentication journeys.

After this correction, `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost
../../env/bin/python tests/presentation.py` passed 26/26; Python and Node syntax
checks and `git diff --check` also passed. This suite reruns the existing
mutual-rescheduling, availability, financial, clinic-access, and request
regressions against the retained disposable integration site.

`git status` was clean after packaging. The isolated local review preview is
still available at the URL above. No live SMS, physical-device media, native
translation approval, or remote deployment is claimed.
