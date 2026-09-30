# Foundation verification

Verified on the isolated site `erp.localhost` on 2026-09-30.
Canonical development repository: `/home/frappe/frappe/frappe-bench/apps/tele_tena`.

Passed:
- Bench 5.31.0 local get-app installation, editable Python packaging, app
  registration, and `bench build --app tele_tena`.
- ERPNext installed before `bench --site erp.localhost install-app tele_tena`.
- Site list-apps: Frappe 15.121.2, ERPNext 15.121.6, tele_tena 0.1.0.
- Locked frontend dependency installation (`npm ci`), TypeScript/Vite production
  build, oxlint, Python compileall, and git whitespace checks.
- Real Frappe WSGI request dispatch for `/api/method/tele_tena.api.system.status`:
  guest returned HTTP 403 without application status; temporary Administrator
  cookie session returned HTTP 200 with application `tele-tena`, version `0.1.0`.
  The session was created through Frappe Session, not a permission bypass, and
  deleted afterward. This checks session authorization, not password login.
- Physical Git repository (not a symlink), original commits retained, foundation
  feature branch retained, GitHub origin restored, original source copy unchanged.

Not tested: network web-server/reverse-proxy routing, browser login/CSRF integration,
mobile/browser calls, product workflow permissions, production deployment.
The frontend build remains a standalone development connection-check screen;
Bench asset compilation does not publish that frontend as a Frappe route.
No new product features, core changes, or Frappe/ERPNext upgrades were made.

Foundation completion (this session): ran `scripts/check_foundation.py` against
Vite 127.0.0.1:5173 proxying the running bench on port 8000. Guest 403; synthetic
Website User password login via `/api/method/login`; authenticated status 200;
asserted site `erp.localhost` and session user. Temporary user removed. This is
an HTTP integration check, not a browser automation check. Re-ran frontend build,
oxlint, Python compileall and whitespace checks successfully. Vite now supplies
`X-Frappe-Site-Name` explicitly (override with `FRAPPE_DEV_SITE`).
