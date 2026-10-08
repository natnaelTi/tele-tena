# Appointment acquisition attribution verification

Checkpoint: `feat/relationship-acquisition-attribution`, 2026-10-08. This slice
records how each appointment was created; it does not attribute acquisition to a
patient profile or establish referral fees, external attribution, or ranking.

## Behavior

New direct bookings store `direct_booking`, clinician-shared booking links
store `clinician_share`, and accepted private offers store `open_request`.
Shared-link attribution is accepted only after the opaque token is revalidated
against the selected offering inside the booking transaction. No token or
patient identity is added to analytics or public URLs beyond the existing
opaque link token. Existing appointments remain `unknown`; historical sources
are not inferred. The additive v1.26 migration preserves appointment rows and
fields and is safe to repeat.

## Verification

- `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost
  ../../env/bin/python tests/presentation.py` — **42/42 passed**. Includes
  wrong-token rejection, appointment source persistence, same-payload retry,
  changed-token retry rejection, open-request source, and repeat migration with
  preserved historical appointments.
- `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost
  ../../env/bin/python tests/integration.py` — **24/24 passed**. Includes
  booking idempotency, transactional rollback, concurrent booking/overspend,
  scope and privacy enforcement, OTP, and consultation authorization.
- `../../env/bin/python scripts/build_review.py` — passed using locked frontend
  dependencies; `scripts/check_review_assets.py` — passed, with zero configured
  private credential values found in public artifacts. The release manifest
  identifies the packaged frontend source commit.
- `NODE_PATH=/tmp/tele-tena-browser/node_modules
  TELE_TENA_REVIEW_SITE_PATH=/home/frappe/frappe/frappe-bench/sites/tele-tena-pr12-fresh.localhost
  node scripts/browser-booking-acquisition-source.cjs` — passed against the
  built `/teletena/` application. It signs in as the synthetic clinician,
  opens their share link as the patient, selects a time and disclosure, then
  verifies that the final command includes the opaque token. It deliberately
  aborts that command before persistence; the backend suite verifies persisted
  source behavior. This is a browser integration check, not a second booking.
  One immediate post-reload attempt timed out waiting for the initial sign-in
  field. A direct browser probe then rendered the sign-in screen without page
  errors, and the complete browser flow passed on retry; retain this as a
  transient browser-startup observation rather than hiding it.
- Clean fresh-site installation remains pending.
- The migration was applied only to isolated
  `tele-tena-pr12-fresh.localhost`, after a database and private-files backup,
  under that site's maintenance mode. It adds one column; it does not modify
  existing balances, reservations, or appointment outcomes.
- Local preview: `http://127.0.0.1:8017/teletena/`, served by the isolated
  `tele-tena-pr12-fresh.localhost` site and `scripts.review_test_wsgi` under
  `/home/frappe/frappe/frappe-bench`. The Gunicorn master was HUP-reloaded after
  build to load the current backend checkout. No Vite server is involved.

No hosted site was changed. Automated checks use synthetic local records;
physical-device, live SMS, and live-money behavior are outside this slice.
