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
- Packaged browser flow and clean fresh-site installation: pending. The browser
  check aborts the final booking request deliberately after checking that the
  built route forwards its opaque token; persisted source behavior is covered
  by backend tests.
- The migration was applied only to isolated
  `tele-tena-pr12-fresh.localhost`, after a database and private-files backup,
  under that site's maintenance mode. It adds one column; it does not modify
  existing balances, reservations, or appointment outcomes.

No hosted site was changed. Automated checks use synthetic local records;
physical-device, live SMS, and live-money behavior are outside this slice.
