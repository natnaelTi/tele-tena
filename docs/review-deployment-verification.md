# Review deployment verification

Packaging branch: `feat/selfmade-review-deployment`, dependent on **open PR #7**
(`84bd97296e2030e679f621f7d8776921b65f0ec6`). Main remains `7222836`.
PR #7's current head, diff and presentation report were inspected; its four latest
reported check results were successful. Neither PR was merged. No earnings or new
visual redesign work is included.

## Implemented package

- Locked React build copied into the Frappe app's public assets, including local
  font licenses. Normal `bench build --app tele_tena` asset linking succeeds.
- Site-bound `/teletena/` shell/deep links, same-origin session/CSRF APIs, narrow
  `/teletena/` worker scope and public-static-only caching. No Vite runtime.
- Explicit local CLI review configuration; inherited developer mode or CSRF bypass
  is rejected. Public enrollment is disabled uniformly, including both OTP APIs and
  Frappe signup. Email/password review access remains available.
- CLI-only idempotent synthetic seed: unique private credentials, approved clinician
  and service scope, patient and reviewer, synthetic PDF evidence, daily Addis Ababa
  availability, confirmed/cancelled/pending examples and demonstration reservations.
- Site-scoped invisible provider setup; no changes to existing site credentials.
- Read-only preflight and HTTPS smoke scripts, safe environment placeholder example,
  exact observed stack inventory, artifact source SHA and checksums, and dedicated
  site/image deployment and code-plus-data rollback instructions.

## Actual checks run

All database/browser fixtures were synthetic. The disposable production-like site
was **`tele-tena-pr2-test.localhost`**, with developer mode off and CSRF enforced.
Gunicorn ran two workers on **loopback 8017**; a static WSGI middleware served the
app public assets in place of a remote reverse proxy. No port was published.

| Check | Result |
|---|---|
| `env/bin/python apps/tele_tena/tests/integration.py` | **24 passed**: existing approval, OTP, disclosure, idempotency, concurrent booking/balance, rollback and consultation authorization coverage. |
| `env/bin/python apps/tele_tena/tests/presentation.py` | **5 passed**: recurrence/timezone/conflicts, holds/releases, notes/privacy, evidence access and tours. |
| `env/bin/python apps/tele_tena/tests/contact_auth.py` | **7 passed**: contact/onboarding regressions, with mocked delivery. |
| `env/bin/python apps/tele_tena/tests/review_package.py` | **6 passed**: exact site binding, explicit boolean, local Administrator/HTTP restrictions, development/CSRF rejection, closed contact access and renderer namespace. |
| `node apps/tele_tena/tests/service_worker.mjs` | **Passed** for development and packaged modes; API/private/Authorization requests and framework assets/routes bypass caching. |
| `python3 apps/tele_tena/scripts/build_review.py` | **Passed**: `npm ci`, TypeScript/Vite production build and app asset copy. No frontend env files; inherited `VITE_*` removed. LiveKit chunk warning remains. |
| `bench build --app tele_tena` | **Passed**: assets linked; `sites/assets/tele_tena` resolves to this app's public directory. |
| `cd frontend && npm run lint` | **Passed with existing warnings**, including effect dependencies/state, Fast Refresh and render purity. No lint errors. |
| `python -m compileall -q tele_tena scripts tests`; `git diff --check` | **Passed**. |
| `scripts/check_review_assets.py --site-private …/erp.localhost/private` | **Passed**: artifact checksums/scope, no source maps/site configs/development URLs; exact scan for three locally configured provider credential values found none in public artifacts. Values were never printed. |
| `scripts/remote_preflight.py --bench …/frappe-bench` | **Ran locally successfully**, read-only. No remote host has been inspected. |

### Fresh site and built journey

`TELE_TENA_REVIEW_CHECK=hold env/bin/python apps/tele_tena/scripts/check_fresh_install.py`
created Frappe + ERPNext + TeleTena with the real installer. The temporary site was
held while `scripts/check_review_site.py` exercised the following:

- Fresh schema, eight versioned migration entries, native service/scope models,
  roles, guest denial and simulation **off before explicit review configuration**.
- Real review setup and seed, second seed with no duplicate appointment, wrong-site
  seed/funding rejection, and **two successful repeat migrations**.
- Guest and authenticated built page serving, patient/clinician/call deep links,
  browser refresh, fonts/logo, password sign-in/sign-out, session cookies and CSRF
  rejection without the header. Private helper/credential routes were denied.
- Actual seed bookings used normal schedule validation and atomic reservation APIs;
  confirmed, cancelled and pending states were persisted. Existing concurrent
  booking/balance regressions above also passed.
- Patient detail omitted private clinician text while showing its published summary;
  treating clinician could read the private note; reviewer could not read the
  clinical record. Reviewer PDF download succeeded; patient and guest download failed.
- Phone/email OTP requests rejected uniformly in review mode, without delivery.
- Browser scope `/teletena/`, manifest start/scope, public-only cache entries and
  generic offline fallback. Existing framework API/Desk/login/private routes were
  not intercepted by the React shell.
- Screenshots captured at **390, 768 and 1440 px**, with no horizontal overflow;
  mobile and desktop captures were visually inspected. Screenshots contain only
  synthetic information and are at `/tmp/tele-tena-package-review/built-detail-*.png`.

### Hosted LiveKit on the built frontend

The retained hosted regression was run by the disposable-site check, using
`TELE_TENA_TEST_SITE=tele-tena-pr2-test.localhost` and
`TELE_TENA_BROWSER_BASE=http://127.0.0.1:8017/teletena`.
**Passed against the configured LiveKit Cloud development project**:

- Two independent Chromium sessions exchanged fake-device audio/video.
- Leave/rejoin, media cleanup/failure cases and clinician End passed.
- Direct SDK reconnection with **original and refreshed tokens for both identities**
  was rejected after End, including the patient who left before End.
- The connected post-call notes/draft/finalization and patient-summary browser checks
  remained intact. Only base URL and SDK asset discovery were adapted for production
  packaging; no End assertion was removed.

These are automated fake-media results, not physical-device or human-call evidence.
The existing Cloud credentials were copied privately to the disposable site for
this test and removed with it; the source credential file was unchanged.

### Worker check and failures resolved

Two initial attempts reached fresh installation but the built server check failed:
the test launcher used the app directory instead of Frappe's required `sites`
working directory, causing log-path initialization errors. A direct WSGI check
identified the cause; the corrected launcher served HTTP 200. Early diagnostics
withheld the assertion location; the harness now reports safe filenames/line numbers.
No application assertion was weakened.

The final held-site run passed the browser/Cloud checks, then its isolated RQ queue
name was rejected by Frappe's queue-name validation. The test now adds that queue
name **only in the test process's queue configuration**, without modifying shared
Bench configuration. `scripts/check_review_site.py --job-only` then **passed**:
real Redis/RQ execution was bound to the disposable site, the registered expiry
method changed its synthetic pending appointment to Expired and released exactly
its reserved amount. No other site's queued jobs were consumed. Continuous remote
scheduler dispatch still needs the installation smoke check.

### Preservation and cleanup

**Passed**: before/after fingerprints matched for retained `erp.localhost` command
tables, native service/scope records, site configuration and known provider credential
files. Cleanup removed the disposable database/site/site user, temporary localhost
administrator, mode-600 credential file and install log. Authentication with the
removed temporary administrator was denied. No framework core files, source branches
or existing patient/appointment/balance data were reset.

## Remaining target verification

No Selfmade site is deployed or claimed ready. The target layout, versions, hostname,
proxy/TLS, image/build pipeline and backups are still unknown. The HTTPS smoke script
has **not** been run remotely. Gunicorn with a static middleware is local evidence,
not proof of a particular Nginx/Caddy/Docker volume configuration.

After installation: verify HTTPS cookie/proxy behavior, private downloads, scheduler
health, two actual devices and microphone/camera permissions, media connectivity,
PWA installation/update behavior and Cloud End protection on the remote URL. SMS/SMTP
live delivery, human translations and clinical/real-money readiness remain unverified
or outside this review release. The simulation log is not completed accounting.

Installation and presenter steps: [selfmade-review-deployment.md](selfmade-review-deployment.md).
The release SHA is the deployment PR head; a build records that exact checkout in
`tele_tena/public/review/release.json`. `deployment/tested-stack.json` records the
observed environment and original inspected product head, not a claim that main
contains this release.
