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

## Local evidence

On the retained isolated Frappe 15 review site, the read-only audit found that
the Review Patient wallet matched its known activity and subledger. Among eight
other synthetic wallets, four discrepancies matched the gross amount of
finalized earnings and are consistent with the missing completion activity
described above. Three additional owners each had a residual 600 minor-unit
available/reserved category difference after that explanation; those remain
unexplained and held. No records were deleted or adjusted during that audit.

`tests/presentation.py` passes 40/40 on the same site, including a synthetic
backfill test that proves exact idempotency, timestamp provenance, balanced
wallet projection, and no wallet mutation. This is not yet proof that v1.24 has
been applied to the retained site or that the remaining owner discrepancies
have been resolved. A site backup and migration run are still required. The
fresh-install browser/install check is also pending the operator's disposable
database setup.

## Remaining financial gates

- Re-run the migration/reconciliation check after a private backup and compare
  every pre-existing ledger row, wallet, earning, appointment, and journal.
- Confirm the four explainable projections align after backfill while their
  previous review cases remain visible pending explicit authorization.
- Keep the three unexplained 600-minor-unit cases held; do not infer a correction.
- Verify on a new disposable site and repeat migration after v1.24.
- Clinician payouts remain simulated reservations, not external transfers.
