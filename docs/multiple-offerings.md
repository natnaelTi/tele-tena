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
- Frontend lint/build passed; lint reports existing warnings. Browser acceptance
  of the new offering form is pending the packaged preview reload. No Frappe 16
  migration, fresh-empty-site install, live clinician publication or patient
  booking with a newly created second offering is claimed in this slice.

This schema does not implement general service-specific intake or authorize
couple, family, group, diagnostic or laboratory workflows.
