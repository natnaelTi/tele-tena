# TeleTena operational progress export

Sanitized local development checkpoint for roadmap updates. This is not a merge,
deployment, real-patient-readiness, or real-money claim.

## Current source and preview

- Worktree: branch `feat/clinic-staff-workspace`, app-code commit
  `a1f62b10f710fa758ccbc84228947847d8e93f77`, stacked locally on
  `feat/clinic-encounter-access` → PR #20 head branch
  `fix/session-feedback-translations`. PR #20 remains open. The clinic branch
  has not yet been pushed or opened as a PR because GitHub returned HTTP 500
  Internal Server Error on repeated push attempts. No branches were force-pushed,
  merged, or deployed.
- Local review URL: `http://127.0.0.1:8017/teletena/`, site
  `tele-tena-pr12-fresh.localhost`, Bench
  `/home/frappe/frappe/frappe-bench`. The app is production-built and served by
  the dedicated Gunicorn process; it is not Vite. `release.json` identifies app
  source `a1f62b10f710fa758ccbc84228947847d8e93f77`. The backend checkout is the
  same working tree; its isolated preview workers were gracefully reloaded.
- Local framework tested: Frappe 15.121.2 / ERPNext 15.121.6, Python 3.12.3,
  Node 22.23.3. The review site's scheduler is disabled. Shared Bench workers,
  scheduler, original `erp.localhost`, and remote Selfmade were not changed.

## Verified work in this checkpoint

- Clinic encounter schedule grants: patient consent is bound to one future
  booked encounter and one verified clinic affiliated with the treating
  clinician. The clinic receives a minimal scheduling projection only;
  membership, appointment, and generic DocType checks remain server-enforced.
  Patient grant/reload/revoke passed in the built browser app. Backend
  `tests/presentation.py` passed 24/24, including membership-role boundaries,
  another-patient denial, exact projection fields, idempotency, and revocation.
- Clinic staff entry: authenticated session includes a navigation hint for a
  verified invitation, verified clinic owner, or active Clinic Manager/Scheduling
  membership. `/clinic` is guarded by that hint; all data APIs independently
  authorize each operation. Billing membership does not qualify. The browser
  journey passed clinic submit → reviewer verification → manager invite →
  verified invitee acceptance → `/clinic` workspace → audited revocation.
  Width checks passed at 320, 390, 768, and 1440 CSS px. A 320px overflow caused
  by long invitation email text was found and fixed. Screenshots are in
  `docs/screenshots/clinic-staff-workspace/` and
  `docs/screenshots/clinic-encounter-access/`.
- `npm run build`, `npm run lint` (exit 0; existing React warnings),
  `scripts/build_review.py`, `scripts/check_review_assets.py`, the 24-case Frappe
  presentation suite, browser clinic flow, and controlled PWA update check
  passed. Vite retains its LiveKit bundle-size advisory. The hosted LiveKit
  two-party End/revocation suite was not rerun in this clinic-only slice.

## Full approved scope remains active

The 142-screen acceptance map is `docs/operational-screen-map.json`; statuses
are evidence states, not assumptions from UI presence. Current work is a partial
clinic slice. Clinic calendars/resources, clinic billing, dedicated clinic team
routes, clinic-wide or broader clinical-record access, couples/family, lab and
diagnostics workflows, subscriptions, second opinions, medical tourism,
extensions, complete administrator operations, and whole-product visual
acceptance remain incomplete. See `docs/mvp-delivery-tracker.md` and the
per-screen evidence.

The isolated site's scheduler remains off, so scheduled earnings release and
background request routing are not claimed operational. A fresh-site install
for the clinic DocTypes is pending. The scoped setup helper now targets a new
disposable database, but local `sudo -n` is unavailable; the operator must run
`python3 /home/frappe/frappe/frappe-bench/apps/tele_tena/scripts/prepare_fresh_install_db_admin.py`
in WSL to authorize that setup. The previous temporary scoped database account
and file were removed; existing review-site records were preserved.

SMS/SMPP/email provider delivery, physical-device calling, native Amharic/Afaan
Oromo approval, clinical/legal approval, partner integrations, real custody or
settlement, Frappe 16 compatibility for the latest clinic addition, and Selfmade
installation remain separate gates.
