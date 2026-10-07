# Multiple clinician offerings

Status: implementation slice on `feat/multiple-clinician-offerings`, dependent
on the current immediate-service-policy review branch.

The catalog contract permits a clinician to publish several differently priced
or timed offerings within one approved scope. The frozen v1.0 storage constraint
`UNIQUE(clinician, service)` contradicted that contract and caused the existing
publish command to overwrite the clinician's sole offering for that service.

This change removes only that obsolete uniqueness constraint through an
idempotent v1.23 migration. Existing offering IDs, schedules, bookings, price
snapshots and financial records remain intact. Each new offering has a stable
opaque ID and may specify a patient-facing title and description. Scope approval
is still checked for every create/update; changing an offering's service scope is
not allowed. Deactivation preserves historical appointments and schedules.

The create command uses an idempotency key: retrying the same payload returns the
same offering, while reusing the key for changed content fails. Updating requires
an owner-scoped offering ID. Legacy clients without an idempotency key retain
single-offering update behavior; if historical data makes that behavior
ambiguous, the server fails and requires an explicit offering ID.

Acceptance: preserve every existing row through repeat migration; create two
offerings in one approved scope; expose both with distinct IDs and prices in
discovery and clinician practice; deny unapproved scopes and cross-owner updates;
verify retry safety; and confirm existing appointment snapshots do not change.

## Verification, 2026-10-08

- Frappe 15 isolated site `tele-tena-clinic-access-fresh.localhost`: backed up,
  migrated through v1.23, then `tests/presentation.py` passed 33/33. The focused
  regressions cover same-scope multiple records, distinct patient discovery,
  owner denial, create replay/conflict, and repeat migration preserving the
  original legacy values. Existing appointment and schedule regression tests
  passed in the same run.
- Review preview site `tele-tena-pr12-fresh.localhost`: backed up before its
  v1.23 migration. It retains 10 offerings, 39 appointments and 10 schedules
  after the migration; source data was not seeded or reset. A pre-migration
  digest was not recorded, so this count is preservation evidence, not a
  cryptographic before/after comparison.
- The packaged `/teletena/` app on `http://127.0.0.1:8017/teletena/` was rebuilt
  from source SHA `44694b4364e466b1aec3308d01521b9739641ab9`. An existing synthetic
  clinician created the second offering through the browser; it persisted after
  reload. A separate patient browser session found it in discovery, and the
  account email was absent from rendered content. The clinician created a
  published Monday schedule (09:00–10:00 Africa/Addis_Ababa); it persisted after
  reload and generated a patient booking slot. The patient booked the
  30-minute, ETB 649 offering. It first appeared as pending confirmation; the
  clinician confirmed it, and it moved to Upcoming. Existing appointments and
  balances were not reset. Screenshots:
  `docs/screenshots/multiple-offerings/clinician-services-1440.png`,
  `docs/screenshots/multiple-offerings/patient-discovery-390.png`,
  `docs/screenshots/multiple-offerings/availability-1440.png`,
  `docs/screenshots/multiple-offerings/patient-booking-390.png`, and
  `docs/screenshots/multiple-offerings/clinician-confirmation-1440.png`.
- The availability screenshot exposed a frontend status bug: selecting a saved
  offering bubbled a change event to the editor and displayed “Unsaved changes”
  although its values were loaded from the server. Commit `d82c5e7` stops that
  selector event from marking the form dirty and asks before switching away
  from genuine unsaved edits. A rebuilt browser verification is pending; do
  not treat the earlier screenshot as visual proof of the fix.
- Frontend lint/build passed before the status fix; lint reports existing
  warnings and the build has the existing large-chunk advisory. The synthetic
  clinician profile is paused for immediate requests
  because its language setup is incomplete. No Frappe 16 migration or fresh
  empty-site installation for v1.23 is claimed in this slice.

This schema does not implement general service-specific intake or authorize
couple, family, group, diagnostic or laboratory workflows.
