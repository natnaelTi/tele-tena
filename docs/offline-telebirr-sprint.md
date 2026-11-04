# Direct Telebirr MVP Sprint —27October2026

Baseline: PR49 `24baa364c65d666db7c4f35e69ef3a35ee4e8a56`, packaged
`25458576cf42c18b6afc4e76160c7f1b397ce92f`. Branch `feat/offline-telebirr-mvp`
is dependent on PR49, preserving earlier ancestry. No remote deployment, merge,
scenario reseed, provider change or shared dependency repair.

This checklist extends the authoritative MVP matrix. Initial request recorded27October; verified local evidence added28October. Owner acceptance is separate. See [final evidence](offline-telebirr-verification-2026-10-28.md).

| Group | Status | Acceptance |
|---|---|---|
|1 Contextual uploads|Locally verified; owner review pending|Purpose-specific labels, accurate formats/limits, private permission checks|
|2 Ethiopia priority|Locally verified; owner review pending|Sourced provisional curated priority, reviewer maintenance, server ordering before paging, no nonmatching pins/double entries|
|3 Credentials wording|Locally verified; owner review pending|Repeatable titles/files/date/issuer preserved; old fields/submissions compatible|
|4 Competencies|Locally verified; owner review pending|Grouped configurable proposed domains, explicit self-rating, no domain uploads/history loss|
|5 Onboarding sign-out|Locally verified; owner review pending|Save/discard/error recovery, server logout, sensitive-state clearing and saved-step resume|
|6 Booking language|Locally verified; owner review pending|Saved care preference/first valid default, explicit-choice retention, actual offering approval revalidation|
|7 Payment modes|Locally verified; owner review pending|Explicit financial-admin control, no automatic remote mode change, historical mode snapshots/stale-client safety|
|8 Direct Telebirr|Locally verified; owner review pending|Payee setup, protected payable intent, private immutable receipt history, human verification, booking acceptance, ledgers/refunds/extension/couples/outbox/jobs|
|9 Localization exchange|Locally verified; owner review pending|Complete source-only CSV, safe reversible spreadsheet encoding, validated reviewed import/diff/history/rollback|
|10 Care languages|Locally verified; owner review pending|Catalog, explicit claims/self-rating, individual reviewer decisions, offering/discovery/matching enforcement|

## Payment decisions and safety boundary

Offline payments are claims and human-verification records, never platform custody,
API-verified Telebirr receipt or automatic settlement. Mode selection must be explicit
for an existing installation; migrations preserve wallet history and current mode.
No receiving number appears in public/unmatched request responses. Historical
transactions retain their snapshotted rules. No default bulk external messages.
Policy-based payment holds and verification deadlines are distinct from the existing
three-minute appointment-confirmation reminder. Refunds are externally performed
and tracked, not fabricated transfers. Final defaults and operating assumptions
will be recorded with the implemented state diagram and operator instructions.

External validation remains distinct: live consenting SMS/email, physical devices,
clinical vocabulary/priority review, native translations and production policies.

## Development Evidence — 27 October

- `tests/direct_payments.py`:12/12 on Frappe16.2.1/ERPNext16.1.0,
  Python3.14.2, MariaDB10.6.22. Rollback-isolated existing synthetic accounts;
  explicit synthetic language decision inside each test. No live Telebirr/media
  or SMS/email delivery. Covers receipt retry, private denial, corrected evidence,
  reused references, late/mismatched proof, manual acceptance, cancellation/refund,
  additional extension payment, mode privilege/holds/stale client, reminder
  deduplication and language withdrawal flags. Concurrency/browser/jobs still open.
- Fresh `teletena-payments-v147-fresh.localhost`: installation plus two native
  migrations passed. Wallet retained, access/provider switches off, private
  application/payment tables empty,630 care languages and78 competency domains.
- Populated compatibility upgrade:69 original protected tables /1225 rows and
  six private/config files hash-preserved. Database/public/private/config backup
  archives verified. Repeat full-schema preservation is being checked separately.
- Frontend build passes; lint reports warnings requiring review, not visual proof.
- Localization exchange:4 source-only tests pass (Unicode/formulas/placeholders,
  duplicate/unknown/stale rejection, provisional exclusion, reviewed history).
- Production preview still serves the previous packaged commit until the new
  source is checkpointed, packaged and browser-verified. No release acceptance.


## Completion Evidence — 28 October

Runtime/build `d553253d8dc24681ceaa5cd71c9bc6881fe46483`. The earlier development checks above remain historical. Final17 payment tests,9 professional tests,4 localization exchange tests, fresh/upgrade/repeat migrations, both-mode browsers, full clinician submission, actual scheduler/restart recovery and paired responsive/200% visual evidence are recorded in the final report. External/human gates are explicitly separate. No remote mode switch, deployment, merge or existing demo reseed.
