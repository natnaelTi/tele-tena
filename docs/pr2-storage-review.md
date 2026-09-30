# PR #2 review: storage and accounting boundary

Recorded before the review changes. The agreed architecture uses Frappe as the
application and back-office framework and ERPNext for accounting. The initial
all-SQL storage solved generic clinical-record exposure by omitting DocTypes, but
also bypassed native configuration forms, permissions, validation, Version records
and normal schema migration tracking. This is an implementation deviation, not an
agreement to abandon the Frappe back office.

## Smallest sustainable adjustment in this PR

Make the public service catalog and per-clinician approved service scope native
Frappe DocTypes now. These are operational configuration, not patient disclosures.
Approvers can maintain them using normal Frappe document permissions and the React
commands. Controllers enforce scope approval, prohibit self approval and prohibit
deletion; generic DocType writes must obey the same rules. Service scope approvals
are distinct from general clinician approval; existing offerings grant no scope.
No automatically inferred or backfilled service approvals.

Retain private profiles, appointments, disclosures, availability, simulated wallets,
transaction log and existing identifiers in their current SQL tables. Rewriting
those now would broaden the security and transaction change unnecessarily. Native
patient/appointment back-office models remain a proposed follow-up, requiring scoped
read/write controllers, list/report/export/file tests and a transactional cutover;
this PR does not implement that rewrite or grant approvers clinical-record access.

Use immutable numbered Frappe post-model-sync patches and Patch Log entries:
`v1_0_command_storage` adopts/creates existing tables without replacing rows;
`v1_1_native_catalog` copies catalog identifiers/labels/active flags into native
Service documents. Keep `tt_service` as an untouched legacy migration source,
not a second writable catalog. Runtime catalog APIs use the native table only.
`v1_2_catalog_adoption_check` completes adoption on benches that recorded an
early draft of the catalog patch; it also copies only missing documents.
Fresh installation bootstraps the same schema/copy routines after model sync,
because Frappe marks install-time patches complete before after_install. No DROP,
TRUNCATE, identifier rewriting, financial recalculation or record deletion.
Migrations must be repeatable without overwriting subsequent native edits. Verify
existing-record fingerprints and repeated migration, plus a separate fresh install.
Future structural changes require new numbered patches, not edits to old migrations.

## Privacy and idempotency corrections

Profile defaults and appointment override state are distinct React state. A new
request starts from saved defaults; editing a request never edits those defaults.
Saving an unrelated profile field sends only the profile's default controls.
Booking stores request choices separately and never updates profile defaults.

Booking authenticates the patient and locks the wallet before looking up the
patient-scoped retry key. Compute its payload hash from the original submitted
values, using the same digest format as existing bookings. Matching successful
retries return the original ID before inspecting mutable profile disclosure,
price, availability or clinician/service approval. A different payload still fails.
Only a new booking checks current profile and eligibility and reserves funds.

## Simulation transaction log is not accounting

`tt_ledger` is the legacy physical name of the **simulation transaction log**.
Deposit/Reservation rows record simulated events; `tt_wallet` is its accompanying
simulated available/reserved projection. There are no debit/credit lines, chart of
accounts, balanced journal validation, clinician earnings, liability accounting,
reversal journals, ERPNext GL entries, reconciliation or external settlement.
Do not call this implementation the planned double-entry financial subledger.
Keep the table name/rows for compatibility; use simulation-log terminology in code
and docs. It cannot fund or post real-money accounting.

The planned double-entry operational subledger must be designed separately with
accounts, balanced immutable posting batches, reversal references, a single
spendable-balance authority, durable ERPNext posting references/retries and
reconciliation. ERPNext remains the agreed reporting/accounting integration;
none of that integration is implemented or activated by this review fix.
