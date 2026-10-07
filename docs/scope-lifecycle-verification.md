# Credential renewal and existing-appointment triage verification

Date: 2026-10-08

## Implemented behavior

- Renewal is a separate `Tele Tena Vetting Scope Application` linked to one
  approved application. New private license/registration evidence, issuer,
  jurisdiction and current credential data are required before submission.
- Repeating an identical submitted payload returns the original renewal; a
  changed payload is rejected. Generic DocType writes cannot forge or edit the
  renewal link/hash. Approval remains a human reviewer action.
- Expired credentials fail closed for new offering publication, discovery and
  direct booking using the Frappe site date. A pending renewal does not extend
  an expired credential; rejection does not revoke a still-valid earlier
  credential.
- Future booked/pending-confirmation appointments affected by expired or
  revoked scope receive a logistics-only review flag. A later distinct expiry
  event on the same appointment has a separate audit row. The flag does not change
  appointment or financial state and its reviewer projection omits patient
  identity, disclosure, health narrative, notes and records.

## Checks actually run

- Frappe 15.121.2 / ERPNext 15.121.6 / Python 3.12.3, site
  `tele-tena-pr12-fresh.localhost`: `tests/presentation.py` passed 30/30. This
  includes fresh renewal evidence, exact retry, changed-payload rejection,
  expired-credential booking/discovery denial, scheduler flag idempotency,
  reviewer/patient authorization, a second expiry episode, and preservation of an existing booked
  appointment and its reserved funds.
- `tests/offer_status_unit.py` and `tests/hosted_phone_unit.py` passed; phone
  unit suite 4/4.
- `node tests/service_worker.mjs` passed both public-only cache/sensitive API
  exclusion checks.
- `python -m compileall` and `git diff --check` passed.
- Frontend `npm run lint` exited successfully with existing hook/purity/Fast
  Refresh warnings. `npm run build` succeeded; Vite reports the existing
  LiveKit bundle chunk-size warning.
- Packaged Frappe browser check at
  `http://127.0.0.1:8017/teletena/admin/vetting` signed in as the local
  synthetic reviewer, loaded the persistent empty operational queue, and
  completed with zero page errors. Screenshot:
  `docs/screenshots/scope-lifecycle/reviewer-empty-1440.png`. The page also
  displayed existing synthetic vetting fixtures; it did not expose real
  personal or clinical data.
- Backed up the isolated review site with database and files before schema
  migration. Frappe migration applied v1.20/v1.21 and a repeat migration
  succeeded.
- A separate Frappe 16.2.1 / ERPNext 16.1.0 / Python 3.14.2 compatibility
  bench site (`tele-tena-pr2-test.localhost`) was backed up before migration.
  Both the initial and repeat migration through v1.21 succeeded, and
  `tests/presentation.py` passed 30/30 on that stack. `pip check` reported no
  broken requirements. The full suite exercises renewal evidence, eligibility,
  preservation, idempotency, privacy and appointment-review permissions. This
  is Frappe integration evidence; it does not establish fresh-empty-site
  installation or Frappe 16 browser behavior.
- GitHub CI for PR #26 passed frontend builds on Node 22.23.3 and Node 24.13.0,
  plus Python syntax jobs on 3.12 and 3.14.2. The local Bench has Node
  22.23.3; Node 24.13.0 was not installed locally.
- The retained disposable site `tele-tena-clinic-access-fresh.localhost` is
  installed with Frappe 15, ERPNext and `tele_tena`; direct read-only schema
  inspection found all checked core, subledger, reconciliation, feedback and
  appointment-review tables plus all 23 `tele_tena` patch-log entries. The
  latest three lifecycle patches are present. Its first-install setup predates
  this checkpoint; a database-and-files backup was taken and `bench migrate`
  was repeated successfully on 2026-10-08. Existing records were not reset.
- The built Frappe browser suite passed against that site on a temporary,
  loopback-only Gunicorn port (8021), with real backend login, onboarding,
  availability load, booking, privacy snapshot, and simulated reservation.
  It also passed offline navigation fallback, tour navigation/replay/missing
  target recovery, patient/clinician/admin layouts, preflight, and responsive
  320/390/768/1440 captures plus the suite's 200%-zoom-equivalent viewport.
  The calendar assertion measured `scrollTop=320px` before responsive captures
  for the synthetic 09:00 opening interval; the rendered 1440px image begins at
  09:00 while later hours remain accessible. Browser-only OTP delivery was
  mocked; pre-created synthetic accounts were used, so this is not live SMS or
  complete new-account phone verification.
  Captures are retained under `docs/screenshots/scope-lifecycle-current/`.
- Tour target lookup now selects a visible target among responsive duplicates
  and observes DOM changes, so hidden mobile/desktop navigation duplicates do
  not mask a genuinely missing target. The browser regression removes duplicate
  tour targets and verifies the accessible recovery notice.
- Read-only site status reports scheduler active
  (`System Settings.enable_scheduler=true`, `pause_scheduler=false`); `bench
  doctor` reports one worker online. These processes are shared across the
  Bench, so this does not prove the new hook was loaded or executed. No
  bench-wide service was restarted for this feature.

## Not yet verified

- Fresh empty-site installation is pending because this WSL session has no
  non-interactive MariaDB administrator access. The existing test site was not
  deleted or reseeded. Run the documented setup helper with a unique disposable
  site/database name to complete it; it prompts for sudo locally and removes
  the temporary account/credential.
- The populated operational review card has backend coverage but has not yet
  been exercised in the rendered browser. Only the reviewer empty state was
  captured.
- A clean empty-site install was not repeated at this final frontend-only
  commit. The earlier disposable install is retained and its schema/repeat
  migration checks are documented above. No temporary database administrator
  or credential file is present; the separate Frappe 16 compatibility site was
  preserved.
- Isolated scheduler/worker execution has not been completed. Because scheduler and worker services are
  shared, automatic date-expiry scanning is not claimed until the new hook is
  verified without disturbing other sites. Explicit reviewer suspension/expiry
  creates flags synchronously.
- Credential issuer/registry verification, jurisdiction-specific expiry-date
  semantics, reminders, malware scanning and patient-care continuity policy
  remain human/external decisions.

The current source/build commit is `2f62775` (full SHA recorded by Git and the
asset manifest in `tele_tena/public/review/release.json`). The preview is an
isolated Frappe 15 site at `http://127.0.0.1:8017/teletena/` and does not use
Vite. Frappe 16 compatibility was verified through migrations and backend
tests on the separate compatibility bench, not by replacing this preview.
