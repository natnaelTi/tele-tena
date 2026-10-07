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

The next full fresh-site run installed the schema and completed the earlier
homepage and service-worker readiness checkpoints, but failed at the offline
navigation fallback assertion. The harness cleaned the disposable site,
temporary database administrator, credential file and install log, and verified
that re-authentication for the temporary administrator was denied. It did not
reach either registration/login journey, so those remain unverified on the
fresh site. The failure occurred even though an independent Chromium run on the
current packaged preview returned the offline page (`200`, expected heading,
active in-scope controller). The fresh-site browser harness now emits a
privacy-safe diagnostic for navigation resolution, status, expected heading,
controller presence and scope; that diagnostic has passed on the packaged
preview but has not yet been rerun on a fresh site. Do not treat this as a
fresh-site browser pass.

After this correction, `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost
../../env/bin/python tests/presentation.py` passed 26/26; Python and Node syntax
checks and `git diff --check` also passed. This suite reruns the existing
mutual-rescheduling, availability, financial, clinic-access, and request
regressions against the retained disposable integration site.

`git status` was clean after packaging. The isolated local review preview is
still available at the URL above. No live SMS, physical-device media, native
translation approval, or remote deployment is claimed.

## Authoritative fresh-site follow-up — 2026-10-07

This section supersedes earlier statements above that the fresh-site browser
journey or registration path was still pending. The named disposable site
`tele-tena-clinic-access-fresh.localhost` was installed with Frappe 15.121.2,
ERPNext 15.121.6, and this branch's TeleTena app. Fresh schema, app roles,
expected tables, migration patch records, guest denial, and demonstration-mode
defaults passed. `bench --site tele-tena-clinic-access-fresh.localhost migrate`
was run twice successfully. The app was confirmed installed on the site.

The production-built React app, served from the Frappe `/teletena/` route, then
passed the registration-enabled browser journey on the disposable site. It
covered the public/PWA entry, phone/email UI (without sending email or SMS),
patient onboarding draft save/reload/completion and workspace transition,
clinician application entry, persisted booking/disclosure/reservation, and
patient/clinician/reviewer workspaces. The separate invited-review browser check
passed with phone OTP and both public registration switches disabled while the
email/password alternative remained available. These are separate site policy
configurations; neither weakens the other. Browser screenshots are under
`/tmp/tele-tena-presentation-review/`.

The failure traced during this work was in the authorized role-grant context:
`frappe.set_user("Administrator")` overwrote the authenticated session ID and
nested session state. The onboarding save returned success, but the subsequent
session query treated the new user as unauthenticated. Commit `ed7117b` now
restores the complete session snapshot in a `finally` block after the scoped
role grant. The regression `test_authorized_user_change_preserves_authenticated_session_state`
passes, and the browser journey reaches the patient workspace after completion.
The browser harness also waits for DOM readiness instead of network-idle when
capturing pages with active Frappe requests, and checks that the development-only
component showcase is absent from production assets. Error diagnostics emit
response status and safe structural booleans only; they do not print onboarding
values, response bodies, cookies, or server messages.

After the fix, `TELE_TENA_TEST_SITE=tele-tena-clinic-access-fresh.localhost
../../env/bin/python tests/presentation.py` passed **27/27**. Repeat migration
passed again during this follow-up. The isolated site and database were retained
by explicit `TELE_TENA_KEEP_FRESH_SITE=1` harness configuration for diagnosis
and preview; the temporary database administrator and its mode-600 credential
file were removed. The original `erp.localhost` site and Selfmade were not
changed. Local MariaDB is 10.11.14, newer than this Frappe 15 environment's
supported/tested database range; this is not exact Frappe 16/Selfmade
compatibility evidence.

The live review preview remains `http://127.0.0.1:8017/teletena/`, served by the
isolated Gunicorn process from
`/home/frappe/frappe/frappe-bench/apps/tele_tena` on
`tele-tena-pr12-fresh.localhost`; it returned HTTP 200 after the follow-up.
Its packaged frontend manifest records source
`0a6306b4777d5fb4995c2da41e12036efd754f36`; backend branch head is newer and the
latest backend role/session fix is `ed7117b`. It is the built Frappe app, not
Vite. The disposable fresh site is separate from the review URL's site. The
isolated scheduler remains disabled, so this verification does not claim that
scheduled dispatch or earnings release ran.

Not tested by this follow-up: live SMS delivery, physical-device calling,
native-language approval, Frappe 16 compatibility, hosted deployment, or
scheduled job execution. The earlier offline fallback and canonical
`/teletena/` scope checks are recorded above; automated browser media remains
fake-device evidence only.

## Existing synthetic clinician request readiness diagnosis — 2026-10-07

Without resetting the seeded patient or clinician, I called the authenticated
`request_presence` query as the review clinician. It returned
`configured=false`, `ready=false`, with the reason codes
`language_required` and `immediate_policy_required`; the persisted presence was
not fresh. Therefore this saved clinician configuration cannot receive an
immediate request at this moment. The immediate-request matcher intentionally
requires a saved care-language selection, an active service policy that permits
immediate care, and a fresh server-side presence lease. The UI has corresponding
setup links and disables “Go available” while hard requirements are unmet.
Locale selection is not treated as a care-language claim.

This reproduces the reported empty clinician inbox as an eligibility/setup
failure rather than an offering/time-grid failure. The account had no care
languages recorded and its legacy review service was not enabled for immediate
requests. I did not modify either profile or service policy to make the account
appear eligible. The local regression
`test_immediate_request_policy_is_explicit_and_site_scoped` asserts these exact
missing-setup reason codes and denial; the full presentation suite passed
27/27. To complete a truthful synthetic journey, the clinician owner must
select care languages in Account, and an authorized reviewer must enable the
service's immediate-care policy; then the clinician can renew availability.
The immediate policy remains separately gated from general scope approval and
from published recurring availability.

The clinician shell previously treated every failed `set_request_presence`
request as “Connection lost,” including HTTP validation/permission failures.
That could make a policy rejection look like the toggle had succeeded before
the server presence lease expired. Commit `5f9aa2a` classifies network, expired
session, denied permission, and other update failures without exposing raw
Frappe response text; it refreshes the authoritative readiness reasons after a
rejection. New copy has provisional Amharic and Afaan Oromo translations.

`frontend && npm run build` and `npm run lint` passed (lint exits 0 with existing
React warnings). `scripts/build_review.py` and `scripts/check_review_assets.py`
passed; the packaged app now identifies frontend source
`5f9aa2a40ee75edb5a5f458f8d1e8dbcafb3243f`. An authenticated built-app browser
check using the real synthetic clinician confirmed the missing language and
immediate-policy actions are visible, the readiness control remains disabled,
and the state is labeled paused. A separate controlled HTTP 422 fault-injection
asserted a useful update error rather than a network-loss message. Both checks
passed at 390px and 1440px in English, Amharic and Afaan Oromo with no horizontal
overflow; six synthetic screenshots are under
`/tmp/tele-tena-presentation-review/request-readiness/`. The fault-injection
validates UI error handling only; it does not replace a real successful offer
journey. New copy remains provisional pending native-language review.
