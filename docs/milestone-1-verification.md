# Milestone 1 verification and review

Verified on 2026-09-30, isolated `erp.localhost`, Frappe 15.121.2,
ERPNext 15.121.6, tele_tena 0.1.0, Python 3.12.3, Node 22.23.3.
Foundation PR #1 remains unmerged. Milestone branch is based on that foundation.

## Checks actually run

- Foundation HTTP check through Vite: guest 403, temporary synthetic password
  login using Frappe, authenticated 200, exact site and user asserted.
- `env/bin/python apps/tele_tena/tests/integration.py`: **10 tests passed**,
  real MariaDB connections and transactions, independent concurrent threads:
  approval/revocation, private disclosure snapshots, cross-account isolation,
  retries, injected booking/deposit failures and committed rollback, overlapping
  slot race, overspend race, concurrent identical retry, HTTP login/CSRF/method
  restrictions and generic resource rejection, selected-history consent, stale
  preview, stale price/duration, partial-window rejection, development-only funding,
  integer-money validation, deposit idempotency, and no-store response headers.
  Temporary test users and their rows were removed. An upstream RQ UTC deprecation
  warning appeared; no framework code was changed.
- Chromium/Playwright `scripts/browser-review.cjs`: **passed** actual React flow:
  approver service creation; clinician profile/application; Pending -> manual
  Approved; offering publication; availability; patient profile, deposit, discovery,
  request-only preview, booking; ETB 50 available / 50 reserved; reload persistence;
  clinician request-only snapshot; locale switching; 390px login no horizontal
  overflow and no page exceptions. Synthetic review records deliberately retained.
  Browser artifacts are in `/tmp`, outside Git. No trace, video or recording.
- `npm --prefix frontend run build`, `npm --prefix frontend run lint` (no warnings),
  `python3 -m compileall -q tele_tena scripts tests`, `git diff --check`: passed.
- `bench --site erp.localhost execute tele_tena.schema.install` and isolated
  CLI fixture provisioning completed. `bench --site erp.localhost migrate
  --skip-search-index` passed, including the actual after_migrate hook. App hooks cache cleared; actual HTTP
  responses include `Cache-Control: no-store, private` and `Pragma: no-cache`.

The first concurrency run found a deadlock: fixed with the explicit booking gate,
and the final concurrency cases passed. The first migration check rejected raw
DDL inside its transaction; changed the hook to supported `sql_ddl`, then reran
the normal migration successfully. Browser testing found ambiguous select
accessible names: fixed with explicit translated aria labels and rerun successfully.

## Exact browser review on the retained fixtures

1. Keep the existing bench terminal running. Vite is running at
   `http://127.0.0.1:5173`; open `http://localhost:5173` on the WSL host if needed.
   If Vite stopped: `cd frontend && npm run dev -- --host 127.0.0.1`.
2. Read the generated account passwords locally from
   `/tmp/tele-tena-demo-credentials.json` (mode 600). Do not post or commit it.
   Accounts: `patient-demo@example.invalid`, `clinician-demo@example.invalid`,
   `approver-demo@example.invalid`. All use normal Frappe password authentication.
3. Sign in as clinician. The saved synthetic profile and Approved application
   already exist. To review approval again, enter a synthetic credential statement
   and click **Submit for manual approval**; status becomes Pending. Sign out.
4. Sign in as approver. Find the clinician application, click **Approve**. The
   **Service catalog** already contains `general-consultation`. Select it under
   **Service scope to review** and click **Approve service scope** for this clinician;
   general approval alone no longer allows the offering. Sign out.
5. Sign in as patient. Existing available/reserved balances are simulated ETB 50/50.
   Click **Add simulated ETB 100**. Under **Find an approved clinician**, choose
   Synthetic Clinician / Synthetic general consultation (ETB 50, 30 minutes).
6. Existing availability is 2026-10-04 06:00–09:00 UTC (09:00–12:00 Nairobi/Addis).
   The first 06:00–06:30 UTC slot is already booked. Enter **2026-10-04 10:00**
   in the Start field if your browser uses Nairobi/Addis local time; otherwise
   enter the local equivalent of **07:00 UTC**. Enter a synthetic request. Leave
   name/history unchecked. Click **Preview exact disclosure**, inspect request-only
   content, then **Confirm appointment and reserve simulated funds**.
7. Expect available/reserved ETB 100/100 after that one additional deposit/booking.
   Reload to check persistence. Sign out, sign in as clinician, inspect **Your
   appointments**: only the selected request is disclosed, with no withheld history
   or patient account email. Switch English/Amharic/Afaan Oromo at the top.

The browser automation was run against initially empty review fixtures; it is a
one-time review-fixture journey, not a reset tool. Repeating it without fresh
fixtures may conflict with existing availability or alter balance expectations.
Do not reset or delete ledger entries to repeat it. The backend suite is repeatable
and cleans up its separate temporary synthetic fixtures.

## Limitations and checks not run

No production deployment, fresh-site install, GitHub Actions results, real SMS/OTP,
real payments/ERPNext posting, professional credential verification, voice/video,
mobile-device session testing, full mobile journey, Safari/Firefox, load testing,
clinical safety validation or native translation review. Amharic and Afaan Oromo
copy is provisional, with the warning always visible. No authenticated API PWA
caching or service worker. Self-registration/recovery is deferred: roles are
provisioned by an administrator; development fixture setup is CLI-only and
hard-restricted to `erp.localhost`. Funding additionally needs the explicit local
simulation flag; no production funding route exists. No cancellation, settlement,
refund, rescheduling or completion transitions. Framework Administrator remains
an infrastructure superuser. The global booking gate limits throughput intentionally.
Private storage is app-owned SQL with command APIs, not editable Desk DocTypes.

Review correction: the initial Chromium context inherited Africa/Nairobi, while
the script printed its local input as UTC. The original suggested 12:30 Nairobi
start was outside the persisted window. Corrected above; future browser fixture
runs explicitly use a UTC context. Existing appointments/funds were preserved.

Follow-up booking error fix: ran `scripts/browser-booking-error.cjs` with an
explicit Africa/Nairobi context against the retained fixtures. Reproduced the
12:30 local outside-window rejection; asserted the translated specific error,
visible timezone, unchanged wallet/appointment count and preview invalidation
when changing to 10:00. Did not book or consume that review slot. Re-ran all
10 backend tests (including an authenticated HTTP error-code assertion), frontend
build/lint, Python compileall and whitespace checks successfully. The full
fixture-creation browser script was not rerun because it changes retained review
records; its future runs now explicitly use UTC rather than inherited timezone.

PR #2 review follow-up: historical references above to a ledger mean only the
simulation transaction log, not a double-entry financial subledger. The catalog
and service scopes now use native DocTypes; private storage remains command-only.
Current review checks and the fresh-site result are recorded in pr2-review-verification.md.
