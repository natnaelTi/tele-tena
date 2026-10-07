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
- Fresh empty-site installation is pending because this WSL session has no
  non-interactive MariaDB administrator access. The latest harness change
  retains only the named disposable site/database on a failed browser run; no
  current temporary credential file is present. The existing Frappe 16 test
  site was preserved.
- Isolated scheduler/worker execution has not been completed. Because scheduler and worker services are
  shared, automatic date-expiry scanning is not claimed until the new hook is
  verified without disturbing other sites. Explicit reviewer suspension/expiry
  creates flags synchronously.
- Credential issuer/registry verification, jurisdiction-specific expiry-date
  semantics, reminders, malware scanning and patient-care continuity policy
  remain human/external decisions.

The production asset manifest identifies source
`03435bd3a4ae31c263c0bc753222763f90c2b536` in
`tele_tena/public/review/release.json`; the preview is an isolated Frappe 15
site at `http://127.0.0.1:8017/teletena/` and does not use Vite. Frappe 16
compatibility was verified through migrations and backend tests on the
separate compatibility bench, not by replacing this review preview.
