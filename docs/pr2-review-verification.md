# PR #2 review verification

Review fixes on the existing `feat/milestone-1-booking` branch. No next feature
milestone, merge, production deployment, framework edits or version upgrades.
Observed Frappe 15.121.2, ERPNext 15.121.6, tele_tena 0.1.0, Python 3.12.3,
Node 22.23.3. See [storage decision](pr2-storage-review.md).

## Review findings addressed

1. Native **Tele Tena Service Scope** records explicitly approve a clinician for
   each service. Publication, discovery, availability lookup and new booking all
   enforce them. General approval alone, revoked scopes and stale offering IDs do
   not grant eligibility. Controller validation applies to generic document writes,
   disallows self approval and stamps the reviewer; native Version and app audit
   evidence retain changes. Scope records cannot be deleted via app/native commands.
2. Profile default controls and request override controls have separate React
   state. New selections start from saved defaults. Unrelated profile saves cannot
   persist an override; omitted API defaults preserve previously saved defaults.
3. Matching successful retries return the original booking before validating mutable
   disclosure/profile, price, time or eligibility. Existing payload hashes/IDs are
   preserved. Changed request text, sharing choices or expected disclosure fail,
   with no additional reservation. Direct-command and authenticated HTTP regressions
   both cover the profile-change case.
4. Catalog and scopes now use native Frappe configuration DocTypes; private tables
   remain unchanged. Numbered post-model-sync patches replace recurring migration
   DDL. Legacy catalog is copied once and retained as an unwritten source; current
   catalog writes use native documents. Future private back-office conversion is
   proposed, not implemented as a broad rewrite.
5. `tt_ledger` remains the historical table name for the **simulation transaction
   log**. Code calls it `simulation_log`; docs distinguish it from the future
   double-entry subledger, ERPNext GL posting and reconciliation. None of those
   accounting integrations or real payments is implemented.

## Checks run

- **14 MariaDB integration tests passed**: original authorization, disclosure,
  CSRF, concurrency, idempotency, overspend, rollback and simulation checks plus
  service scope denial/revocation/stale-ID tests, original-payload replay after
  profile edits (direct and HTTP), independent defaults, native permissions,
  self-approval prevention, native Version creation and catalog-copy preservation.
- **Chromium passed** using isolated temporary fixtures: scope revoke/approve via
  React, filtered discovery, independent profile and request checkboxes, unrelated
  profile save while overrides are active, disclosure preview, booking/reservation,
  reload persistence, next-request reset to defaults, clinician authorized snapshot,
  outside-window rejection with no funding change, and Amharic/Afaan Oromo switching.
  Temporary synthetic users, records and credential file were cleaned up. Existing
  retained demo appointments, wallets and profiles were not reset.
- Existing foundation HTTP-through-Vite authentication check passed: guest 403,
  normal synthetic password login, authenticated 200 and exact site/user routing.
- `scripts/check_migration.py` passed additive upgrade and a second migration:
  three numbered Patch Log records, copied catalog fields, no inferred approvals,
  and identical fingerprints for every legacy `tt_*` table before/after both runs.
  Native edits are preserved when the adoption routine is repeated (integration test).
- Frontend TypeScript/Vite build, oxlint without warnings, Python compileall and
  whitespace checks passed. Frappe and ERPNext Git working trees remained clean.

## Disposable fresh-site check and cleanup

**Passed** on `tele-tena-pr2-test.localhost`, database `teletenapr2test`, separate
from `erp.localhost`. Ran as the normal Linux user, invoking Bench's actual
`new-site` callback in process, with ERPNext installed before tele_tena. Verified
all three installed apps, both native models, command tables, roles, recorded
migrations, no inferred scopes or seeded wallet funds, guest denial and disabled
simulation. Compared retained development-record fingerprints: unchanged.

`sudo -n mariadb` required authentication. The user ran the local setup helper in
another terminal using existing `sudo mariadb` socket administration. The temporary
`tt_pr2_site_admin@localhost` account had global CREATE USER/RELOAD (needed by Bench)
and database-only privileges/grant option for `teletenapr2test`; no root auth changes.
The generated password lived in a mode-600 file outside Git. Root/admin credentials
were passed as in-process arguments, not command-line arguments. Frappe's SQL
bootstrap normally constructs a password-bearing client command: this test process
adapted its command builder to a mode-600 client option file in a private temporary
directory, without editing framework files. All real install/model/bootstrap hooks ran.

Cleanup **passed**: removed disposable database, site database user, site directory,
temporary database administrator and credential file. Re-authentication with the
removed administrator was rejected, and the file/directory absence was checked.
No development-site credentials were changed. The first attempt stopped before
site/database creation because the harness omitted new-site initialization; it
cleaned up, then the corrected command-callback path was rerun successfully.

## Review steps and remaining limits

On the retained demo, general approval is insufficient by design. Sign in as
`approver-demo@example.invalid`; select `general-consultation` in **Service scope
to review**, then click **Approve service scope** for the demo clinician. Existing
records/offerings are retained; migration deliberately grants no approval on your
behalf. Patient discovery then includes that scoped offering.

No full retained-fixture creation script was rerun: it would alter existing demo
availability and balances. The new isolated browser journey covers its applicable
paths. Fresh installation was checked, not a full fresh-site consultation journey.
No production deployment, real OTP/SMS, payments, double-entry/ERPNext accounting,
calls, cancellation/refunds, full mobile/browser matrix, load tests or native
translation review. Native Desk forms were not browser-tested; native validation,
permissions, Version records and generic document saves were integration-tested.
Private profiles/appointments still have no native back-office model; that scoped
migration needs separate design and security tests. The booking gate still limits
throughput. An upstream RQ UTC deprecation warning remains; no framework changes.
