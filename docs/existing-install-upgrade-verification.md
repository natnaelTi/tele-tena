# Existing-install update correction —14October2026

Corrected installation/build pin **800a591ac6af9c6c3b4afd61ed4353be4ff0826e**,
`feat/mvp-release-handover`, draft PR44 with PR43 ancestry. Use the **corrected
update guide from the latest reviewed PR documentation**, not the historical
first-install guide in an older runtime checkout. Subsequent documentation/CI
evidence commits do not change application/deployment-helper code.

[Selfmade step-by-step update guide](selfmade-final-mvp-update.md).
[Separate shared-environment repair proposal](selfmade-shared-environment-repair.md).

## Defects and corrections

The original guard was first-install only. Snapshot rejected an installed app
after creating an empty folder; plan rejected every existing distribution,
including the intended TeleTena rebuild. The guide incorrectly reused that flow.
This is corrected with explicit `--mode update --app-path …` on snapshot/plan/verify.
Only TeleTena can be replaced. Other additions/replacements are rejected; all
other versions and editable app identities are preserved. Default install mode
still requires absence. Update constraints omit **only** TeleTena. No `--no-deps`,
resolver bypass, relaxed framework constraints or dependency repair is performed.
Private snapshots/accepted plans remain mode600 in an owned mode700 directory;
new attempts use new directories and preserve failed logs. Plan provenance must
match the expected local editable TeleTena path; same-version reinstall is valid.

The original backup check could pass over empty `find` results. The transcript
has database/config archives but **no public/private file archives** and omitted
the backup command itself. The replacement native backup CLI explicitly creates
database.sql.gz, public-files.tar, private-files.tar and site-config.json in a new
private directory. It validates existence, nonzero size, gzip CRC and tar payloads
and records hashes. Re-verification compares to the retained private manifest.
It never extracts private data, overwrites archives or prints credentials. A
process-local client-option-file wrapper avoids DB passwords in argv without
editing core. Encrypted-backup policy stops for a separately verified encrypted
procedure rather than disabling encryption.

## Actual tests

Exact isolated stack: Frappe16.2.1/ERPNext16.1.0 at the target commits,
Python3.14.2, Node24.13.0, MariaDB10.6.22, Redis6.0.16. No shared remote access.

1. Installed **8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6** with normal constrained
   pip into the existing compatibility app env. Created a separate disposable
   `teletena-existing-upgrade.localhost` with Frappe/ERPNext and this old app.
2. Used the old release's supported review API flows for patient/clinician/reviewer,
   approval/scope, private resume, schedule, deposit, confirmed/pending/cancelled
   appointments. Authorized Join/End/private-note/shared-summary/finalize produced
   a historical completed-but-reserved case with an explicit offline media/clock
   adapter. This is a migration fixture, **not** a hosted call test.
3. Captured all26 existing operational tables (41 rows), six private/config/file
   fingerprints, password acceptance and original balances. Created/verified an
   actual complete native database/public/private/config backup.
4. Performed a real resolver dry-run, accepted **only TeleTena**, normal constrained
   pip installation and post-install version/editable-identity verification. Then
   migrated that existing site, repeated migration and checked original columns/
   rows, credentials and wallets. All41 rows preserved. Completed/reserved funds
   became `LegacyHold`, not automatic earnings or release. New schema v1.38.
5. Ran the portable demo acceptance against this **upgraded site with unrelated
   existing records**: dry run, first seed, twice-seed idempotency, explicit refresh,
   request/offer/private-note/evidence denial, couples consent, real-money guard,
   mocked prohibition of outbound HTTP/email and owner reconciliation. PASS:
   five seeded patient owners/four clinician owners/balanced journals. The old
   wallet also reconciles. Original values/credentials remain unchanged.
6. The old fixture had **no encryption/signing key**. First couples seed safely
   initialized that missing key, as previously documented; the config gained one
   field. This initially failed the intentionally strict whole-file fingerprint.
   Diagnosis confirmed every original config value and the other five private/
   credential/file contents were unchanged. This is recorded, not hidden as a
   passed unchanged-file hash. Repeat setup preserves the new key; no existing
   encrypted credential or signing key was overwritten.
7. Separate initial-install venv: normal resolved pip install, private snapshot,
   approved additive plan, post-install verification and pip-check PASS.
8. A real pip **dry-run only** using force-reinstall requested protected packages
   at their existing versions. Guard rejected it; no unrelated install executed.
   Unit checks also reject version changes, unrelated additions, missing packages
   and same-version editable identity changes.10 regressions pass on Python3.12
   and3.14.2, including missing/empty/corrupt backups and the exact lock-only delta.
9. Isolated Bench5.29.0 CLI venv: pip-check and list-apps on the upgraded site PASS.
   It coexists with Frappe's Click8.3.x in the separate application env. This proves
   CLI separation for the tested apps, not all44 remote integrations/services.
10. Final candidate guarded install/verification, Node24 locked production build,
    pip-check and artifact/privacy checks PASS. App runtime/schema is unchanged
    from the migrated/tested candidate; later changes only harden deploy tooling.

Safe result summaries: `docs/evidence/existing-install-upgrade/`.
Private detailed installer/pip reports, matched backup and retained diagnostic
site: `/home/frappe/teletena-compat/runtime/update-check/`. They are not in Git.
Temporary DB admin and its credential are removed; the disposable upgrade site
is retained for audit. Original WSL preview/data/credentials remain unaffected.

## Remote stop conditions

The supplied Selfmade baseline is **not ready to update**: eight pip conflicts
remain until the separately staged repair is validated against all44 apps.
Frappe's Click and app-env Bench5.29.0 requirements are disjoint. Four candidate
library pins have local compatibility evidence; urllib3/old botocore needs its
owning-app constraints. No blind downgrade or unverified boto SDK pair is supplied.

The exact caniuse-lite-only yarn.lock change is preserved and accepted by a
read-only whole-file check; any other framework changes stop the update.
Current service/launcher paths, current code, all-app source/metadata requirements,
optional extras and unknown/direct requirements must be observed before repair.
The transcript's stopped shared services require the pre-migration recovery in
the guide if no further operation occurred. No remote install, repair or migration
was performed here. Existing UI/media evidence is reused because application code
is unchanged; no new live SMS/device/provider/native-language claims.
