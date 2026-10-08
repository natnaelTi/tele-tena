# Legacy wallet projection correction

## Root cause

The pre-v1.24 consultation finalization flow debited a patient's `tt_wallet.reserved`
and posted a balanced `ConsultationFinalized` journal, but omitted a corresponding
event from the append-only `tt_ledger` simulation activity log. The v1.13 owner
audit projects only recorded activity events, so a finalized consultation could
appear to leave funds reserved in the legacy projection even when the wallet and
subledger agreed. This is an activity-log omission, not evidence that the wallet
or balanced journal should be adjusted.

Future finalization now appends one `Consumption` event using the same
`completion:<appointment>` reference inside the transaction that posts the
financial journal. Supported dispute refunds append a `Refund` event alongside
the immutable refund journal. These log rows are not subledger postings.

## Safe migration behavior

Patch v1.24 backfills only an absent completion activity event when all of these
match: an earning with a recorded completion timestamp, the corresponding
`ConsultationFinalized` journal, and the journal's patient reserved debit equal
to the earning's gross amount. The entry uses the journal timestamp and a unique
completion reference. Existing activity rows, wallets, appointments, earnings,
and journals remain unchanged. Conflicting evidence aborts migration. The patch
then reruns the owner audit; existing `ReviewRequired` decisions are not silently
cleared. An authorized reviewer must explicitly accept an unchanged balanced
snapshot with a reason before that owner can transact again.

## Local evidence and migration result

On the retained isolated Frappe 15 review site, the read-only audit found that
the Review Patient wallet matched its known activity and subledger. Among eight
other synthetic wallets, four discrepancies matched the gross amount of
finalized earnings and are consistent with the missing completion activity
described above. Three additional owners each had a residual 600 minor-unit
available/reserved category difference after that explanation; those remain
unexplained and held. No records were deleted or adjusted during that audit.

Before migration, the isolated preview site and private files were backed up
with Bench at 2026-10-08 11:39 local time. Its site-scoped scheduler was
temporarily disabled; the site had no pending jobs. Maintenance mode blocked
web writes during the migration. No shared worker or unrelated Bench service
was stopped. The scheduler and site availability were restored afterward.

Patch v1.24 added 14 journal-proven `Consumption` activity events. The patch's
write path is insert-only, and it checks exact journal and earning evidence
before each insert. A direct comparison with the pre-migration database backup
confirmed all 91 prior activity rows remain identical; exactly 14 rows were
added and each matches its completion journal and earning. Repeat migration
checks passed without adding more events; wallet and subledger balances,
earnings, and balanced journals remained unchanged on repeat. Owner-level
read-only reconciliation after migration found all 9/9 wallets
equal their subledger accounts, 0 unbalanced journals, and 6/9 owners whose
legacy activity projection also matches. The other 3 owners have no unknown
event kinds but retain their unexplained historical category differences and
remain `ReviewRequired`. The existing Review Patient wallet matches.

`tests/presentation.py` passes 40/40, including a synthetic backfill test for
idempotency, timestamp provenance, exact journal/earning evidence and no wallet
mutation. `tests/integration.py` passes 24/24. The built-browser package check
passed guest/deep-link access, reviewer sign-in/out, consultation reload, PWA
scope, offline fallback and responsive widths at 390/768/1440. The fresh-site
install/browser check is still pending the operator's disposable database
setup. This is not proof that the remaining owner discrepancies are resolved.

## Remaining financial gates

- Compare the pre-migration backup with the migrated site to independently
  verify every pre-existing event and obligation is retained.
- Keep the three unexplained 600-minor-unit cases held; do not infer a correction.
- Verify on a new disposable site and repeat migration after v1.24.
- Clinician payouts remain simulated reservations, not external transfers.
