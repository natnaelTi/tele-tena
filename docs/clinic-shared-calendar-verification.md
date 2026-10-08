# Clinic shared calendar verification — 2026-10-08

## Release identity

- Branch: `feat/clinic-shared-calendar`, stacked on draft PR #41 (`feat/clinic-shared-summary-grants`), which depends on PR #40.
- Source/build commit embedded in the packaged release: `3e433a4b8bf1bfa06941fff3dd998d2b6755dbe0`.
- Local URL: `http://127.0.0.1:8017/teletena/`.
- Site: `tele-tena-pr12-fresh.localhost`, isolated Frappe 15.121.2 review site.
- The page uses the packaged Frappe app assets, not Vite. `release.json` identifies the source commit above; the asset integrity/private-file check passed with zero credential matches.
- Only the isolated preview Gunicorn master on loopback port 8017 was HUP-reloaded. The original `erp.localhost` bench was not migrated or restarted. Five stale headless browser probe process groups, each running for more than eleven hours, were stopped; the current Gunicorn workers remain active.

## Checks run

- `frontend`: `npm run build` passed (TypeScript and Vite production build). Existing warning: LiveKit bundle exceeds 500 kB.
- `scripts/build_review.py` passed for a clean checkout and packaged the current source SHA.
- `scripts/check_review_assets.py --site-private .../private` passed artifact hashes, scope and sensitive-file checks; exact private credential scan count was zero.
- `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost ./env/bin/python apps/tele_tena/tests/presentation.py`: 45/45 passed, including clinic calendar role, timezone, DST-boundary and minimized-response coverage.
- `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost ./env/bin/python apps/tele_tena/tests/integration.py`: 24/24 passed.
- `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost python3 scripts/check_clinic_calendar_browser.py`: passed against the built `/teletena/` route. It verified clinic owner sign-in, authorized route/API, current-week empty state, next-week navigation, timezone update and invalid-timezone feedback, no page overflow at 320/390/768/1440 CSS px, and 403 from a patient calling the schedule endpoint directly.
- Rendered desktop and mobile screenshots were inspected. Browser fixture had no patient-shared appointment in its current week, so the browser shows a legitimate empty state. A populated event row is verified in the Frappe backend test, not claimed as browser-rendered evidence.
- No schema migration was introduced. Fresh install, Frappe 16, and 200% browser zoom were not run for this slice.

## Evidence

- `docs/screenshots/clinic-shared-calendar/empty-390.png`
- `docs/screenshots/clinic-shared-calendar/empty-1440.png`
- `docs/screenshots/clinic-shared-calendar/invalid-timezone-1440.png`

Amharic and Afaan Oromo strings are provisional and have not received native-speaker review. The calendar is a read-only projection over patient-granted appointments; it does not provide clinic resources, shifts, booking, billing, or blanket record access.
