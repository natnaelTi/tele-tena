# Direct Telebirr MVP Sprint —27October2026

Baseline: PR49 `24baa364c65d666db7c4f35e69ef3a35ee4e8a56`, packaged
`25458576cf42c18b6afc4e76160c7f1b397ce92f`. Branch `feat/offline-telebirr-mvp`
is dependent on PR49, preserving earlier ancestry. No remote deployment, merge,
scenario reseed, provider change or shared dependency repair.

This checklist extends the authoritative MVP matrix. Requested is not verified.

| Group | Status | Acceptance |
|---|---|---|
|1 Contextual uploads|Requested|Purpose-specific labels, accurate formats/limits, private permission checks|
|2 Ethiopia priority|Requested|Sourced provisional curated priority, reviewer maintenance, server ordering before paging, no nonmatching pins/double entries|
|3 Credentials wording|Requested|Repeatable titles/files/date/issuer preserved; old fields/submissions compatible|
|4 Competencies|Requested|Grouped configurable proposed domains, explicit self-rating, no domain uploads/history loss|
|5 Onboarding sign-out|Requested|Save/discard/error recovery, server logout, sensitive-state clearing and saved-step resume|
|6 Booking language|Requested|Saved care preference/first valid default, explicit-choice retention, actual offering approval revalidation|
|7 Payment modes|Requested|Explicit financial-admin control, no automatic remote mode change, historical mode snapshots/stale-client safety|
|8 Direct Telebirr|Requested|Payee setup, protected payable intent, private immutable receipt history, human verification, booking acceptance, ledgers/refunds/extension/couples/outbox/jobs|
|9 Localization exchange|Requested|Complete source-only CSV, safe reversible spreadsheet encoding, validated reviewed import/diff/history/rollback|
|10 Care languages|Requested|Catalog, explicit claims/self-rating, individual reviewer decisions, offering/discovery/matching enforcement|

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
