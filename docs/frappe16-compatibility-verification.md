# Frappe 16 installation checkpoint — 2026-10-01

## Result and release dependency

**Local target-stack compatibility passed. No remote deployment was performed.**
This branch includes deployment PR #8 at
`ba674b79bfa493a05689b1cee96d7a0d663766ec`, which includes open PR #7.
Neither source PR is merged by this work. No earnings or visual redesign feature
is included. There were **no required product-code or schema compatibility fixes**.
Changes are isolated-test tooling, a shared-dependency installation guard, CI
runtime coverage, manifests and operator documentation.

Installation SHA: **recorded in the final pin update below**. Do not substitute
main; it does not contain this release. The exact host command sequence is
[selfmade-frappe16-installation.md](selfmade-frappe16-installation.md).

## Exact matched components and environment differences

| Component | Local compatibility run / supplied target |
| --- | --- |
| Frappe | 16.2.1, `8f6e24728b86b7c6427908ed6536289a41ea9cf4` |
| ERPNext | 16.1.0, `bb2bada1fde0ae7a3c3cad32bed781ebd470e27d` |
| Python | 3.14.2 |
| Node | 24.13.0 |
| MariaDB server | `10.6.22-MariaDB-0ubuntu0.22.04.1` |
| Redis server | 6.0.16 |

The requested ERPNext commit differs from the upstream v16.1.0 tag; the **supplied
commit** was tested. Framework checkouts remained clean. The local runtime used
uv-managed CPython, a verified official Node archive, extracted Ubuntu MariaDB
packages from the [Ubuntu snapshot](https://snapshot.ubuntu.com/ubuntu/20250701T000000Z/pool/universe/m/mariadb-10.6/),
and Redis 6.0.16 compiled from its official release. No system packages, global
Node/Python, original Bench env or framework core were upgraded.

This is exact-version/source testing for the table, **not a bit-identical remote
host replica**. Local WSL Ubuntu24 libraries/kernel differ from the remote Ubuntu22
MariaDB packaging environment. Local Redis allocator is jemalloc5.1.0 versus
remote5.2.1. The local HTTP boundary was loopback Gunicorn23 + public static
middleware; remote nginx1.18.0, actual TLS/cookies, remote filesystem/service limits
and device/network behavior remain untested. Local Bench CLI5.31.0 was isolated in
its own venv; the remote CLI version was not supplied. The complete installed
Python package versions and frontend lock digest are in
[the target manifest](../deployment/tested-stack-frappe16.json).

## Isolation and inspection

Separate worktree/bench: `/home/frappe/teletena-compat/bench`; runtime:
`/home/frappe/teletena-compat/runtime` (private). Two fresh disposable sites:
`erp.localhost` and `tele-tena-pr2-test.localhost` **inside that separate bench**.
The original site's matching name does not share its database/configuration.
Database has a private Unix socket and no TCP listener. Independent Redis6
processes use loopback16379/16380; test web servers use loopback8018/8017.

Inspected Python constraints/install resolution, native service/scope DocTypes,
numbered migrations, Frappe page-renderer/after-request hooks, password sessions,
CSRF token API, private downloads, scheduled job hooks, RQ2 execution and LiveKit
Python/client APIs. Frappe16 uses mysqlclient2.2.7, redis Python7.1.1 and RQ2.6.1
in this resolved environment; LiveKit API1.2.1/protocol1.1.27 remain pinned.
Bench5.31.0 and Frappe's requests constraints conflict if placed in one venv;
separating the CLI resolved installation without relaxing framework requirements.

## Checks actually run

Commands used the target env Python and a local wrapper selecting Node24.13.0,
MariaDB10.6 client and isolated Bench CLI. Integration base was explicitly
`http://127.0.0.1:8018`; no tests accidentally reached the original Vite5173.

| Check | Result |
| --- | --- |
| Editable install of exact Frappe/ERPNext + TeleTena in Python3.14.2 | Passed |
| `env/bin/python -m pip check` after installation and verification | No broken requirements |
| `scripts/create_compatibility_sites.py` | Two fresh Frappe + ERPNext + TeleTena installs; simulation initially off |
| `tests/integration.py` | 24 passed, 19.330s |
| `tests/presentation.py` | 5 passed, 5.800s |
| `tests/contact_auth.py` | 7 passed, 2.992s; delivery mocked |
| `tests/review_package.py` | 6 passed |
| `tests/dependency_checkpoint.py` | 3 passed on Python3.14.2 and original Python3.12.3 |
| `scripts/check_review_site.py` | Passed seed idempotency/site binding, repeat migrations, HTTP permissions, browser, Cloud and RQ checks |
| `scripts/check_migration.py` with disposable review-site override | Two further migrations preserve every command/OTP/consultation/onboarding/presentation table fingerprint and service scopes; eight Patch Log entries checked |
| `scripts/build_review.py` with locked npm dependencies | Passed Node24.13.0 production build; packaged source ba674b7 then compatibility tooling commit0e51874 |
| `bench build --apps frappe,erpnext,tele_tena --production` | Passed target framework/ERPNext asset build, local bench only |
| `npm --prefix frontend run lint` | Passed exit0 with existing React warnings; not warning-free |
| `node tests/service_worker.mjs` | Both development and packaged cache-exclusion tests passed |
| `scripts/check_review_assets.py --site-private ...` | Artifact hashes/scope/source-map/config exclusions passed; no match for either actual private LiveKit key/secret |
| `python -m compileall -q tele_tena scripts tests`, `git diff --check` | Passed |
| Original development record/config/provider-credential SHA256 comparison | Passed; no retained data or credential changes |

Coverage includes atomic concurrent booking/overspend prevention, successful
retry ordering, request-sharing/default separation, approved scopes including
stale IDs, timezone/DST/exceptions/cross-offering conflicts, pending expiry and
idempotent cancellation, notes revisions/private versus shared APIs, masked
encounters and private resume authorization. Scheduling executed an actual
site-bound RQ job on its own test queue, confirmed Expired state and exactly one
reservation release; no original/customer queued jobs were consumed.

The production review test checked guest403, password sessions, CSRF400 without
header, logout rejection, authenticated deep-link refresh, `/api`/`/private`/
`/login`/`/app` namespace isolation, no public helper/credential routes, disabled
review OTP enrollment, reviewer denial of clinical notes and patient/guest denial
of resume downloads. Browser checked responsive detail, service-worker scope,
public-only cached URLs and honest offline state without Vite.

### Hosted LiveKit evidence

The actual development **Cloud** project was used with privately copied credentials
in the disposable site. Both assertions passed without modification:

- Direct SDK reconnect with **original and refreshed tokens for both opaque
  identities** rejected after End; patient had left before End.
- Two independent Chromium contexts exchanged **automated fake-device** audio/video;
  Leave/rejoin worked; clinician End closed both sessions. Existing media cleanup,
  failure and post-call documentation assertions were retained.

This does not claim physical microphone/camera quality, mobile background calling,
remote TLS/firewall behavior or self-hosted token revocation. Cached-token
revocation remains LiveKit Cloud-specific.

### Browser evidence

Rendered and visually inspected synthetic patient completed-consultation details
at [390px](screenshots/frappe16/built-detail-390.png),
[768px](screenshots/frappe16/built-detail-768.png) and
[1440px](screenshots/frappe16/built-detail-1440.png). No horizontal overflow;
private clinician text absent. These are compatibility screenshots, not new design
acceptance. Existing presentation limitations (including internal timeline labels)
remain outside this installation checkpoint.

## Reproduction and local diagnostics

The compatibility bootstrap refuses non-disposable sites and original bench paths;
it requires an already provisioned separate target runtime/database administrator
file (mode600). It is **not** a remote installation command. It passes database
bootstrap passwords through a temporary private client option file, not argv.

Private logs were under `/home/frappe/teletena-compat/runtime`: `pip-install.log`,
`integration.log`, `presentation.log`, `contact-auth.log`, `review-check.log`,
`migration-preservation.log`, `bench-build.log`, `compat-frontend-build.log`.
Do not publish raw private install/provider logs. Safe results are summarized here.
An initial unittest module invocation failed because a fixture changes cwd;
individual test scripts were then run successfully. Missing Bench `config/pids`
was created in the new skeleton before the successful asset build. Neither was a
product regression or change to framework code.

## Remote gates and remaining limitations

No unresolved application compatibility failure was found. Remote installation
still depends on additive-only package resolution against **all existing remote
apps**, a verified backup/restore arrangement, actual nginx/TLS routing and worker
subscriptions. The supplied two worker names and 22 queued jobs cannot establish
default-queue consumption or a stuck queue. The runbook includes read-only checks;
no queue purge or shared configuration rewrite is authorized by this report.

No remote installation, remote HTTPS/device test, live SMS/SMTP delivery, real
payments or clinical readiness is claimed. Original Frappe15 product regressions
were not rerun against retained user data in this checkpoint; prior PR8 evidence
remains valid for unchanged product code. New dependency-guard tests passed on
Python3.12.3; CI now covers Python3.12/3.14.2 syntax/guard tests and locked frontend
builds on Node22.23.3/24.13.0. CI is not a substitute for the local full-stack run.

Cleanup status and final installation pin are appended after verification.
