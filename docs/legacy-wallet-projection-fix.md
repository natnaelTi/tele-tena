# Legacy wallet projection correction

## Root cause

The pre-v1.24 consultation finalization flow debited a patient's `tt_wallet.reserved`
and posted a balanced `ConsultationFinalized` journal, but omitted a corresponding
event from the append-only `tt_ledger` simulation activity log. The v1.13 owner
audit projects only recorded activity events, so a finalized consultation could
appear to leave funds reserved in the legacy projection even when the wallet and
subledger agreed. This is an activity-log omission, not evidence that the wallet
or balanced journal should be adjusted. A follow-up audit found a second gap:
three owners each have a refunded 600-minor-unit earning with an immutable
refund journal and wallet credit but no corresponding legacy `Refund` activity.

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
snapshot with a reason before that owner can transact again. Patch v1.25 applies
the same evidence gate to historical refunds, matching the `EarningRefunded`
journal, patient available credit, clinician pending debit, and earning net
amount before appending one `Refund` event.

## Local evidence and migration result

On the retained isolated Frappe 15 review site, the read-only audit found that
the Review Patient wallet matched its known activity and subledger. Among eight
other synthetic wallets, four discrepancies matched the gross amount of
finalized earnings and are consistent with the missing completion activity
described above. Three additional owners each had a residual 600 minor-unit
available/reserved category difference after that explanation; no records were
deleted or adjusted during that audit. Inspection showed each difference was a
refunded 600-minor-unit earning whose refund journal and wallet credit existed
without a legacy activity event.

Before migration, the isolated preview site and private files were backed up
with Bench at 2026-10-08 11:39 local time. Its site-scoped scheduler was
temporarily disabled; the site had no pending jobs. Maintenance mode blocked
web writes during the migration. No shared worker or unrelated Bench service
was stopped. The scheduler and site availability were restored afterward.

Patch v1.24 added 14 journal-proven `Consumption` activity events. The patch's
write path is insert-only, and it checks exact journal and earning evidence
before each insert. A direct comparison with the pre-migration database backup
confirmed all 91 prior activity rows remain identical; exactly 14 rows were
added and each matches its completion journal and earning. A second backup was
taken before v1.25. Its direct comparison confirmed all 105 prior activity rows
remain identical; exactly 3 `Refund` rows were added, each matching its earning,
journal, posting sides, amount, and timestamp. Repeat migration checks passed
without adding more events; wallet and subledger balances, earnings, and
balanced journals remained unchanged on repeat. Owner-level read-only
reconciliation now finds all 9/9 wallets equal both their subledger accounts and
legacy activity projections, 0 unknown event kinds, and 0 unbalanced journals.
The 3 existing `ReviewRequired` cases remain held intentionally until an
authorized reviewer accepts the now-matching current snapshot. v1.25 refreshed
their visible projection and retained prior evidence in the private audit
history without changing their status. The Review Patient wallet matches.

`tests/presentation.py` passes 40/40, including a synthetic backfill test for
idempotency, timestamp provenance, exact journal/earning evidence and no wallet
mutation. `tests/integration.py` passes 24/24. Repeat migration and financial
snapshot checks passed after both versions. The built-browser package check
passed guest/deep-link access, reviewer sign-in/out, consultation reload, PWA
scope, offline fallback and responsive widths at 390/768/1440. The fresh-site
install/browser check is still pending the operator's disposable database
setup. This does not automatically accept the three preserved review cases.

## Remaining financial gates

- Verify fresh installation after v1.25 on a new disposable site.
- Record an authorized reviewer decision for each preserved case only after
  inspecting the refreshed evidence; migration does not accept it.
- Clinician payouts remain simulated reservations, not external transfers.
