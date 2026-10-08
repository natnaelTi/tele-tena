# Financial activity details verification

This focused slice adds a persisted, owner-scoped detail page for patient
payment activity and clinician earnings/payout activity. It does not change
balances, reconcile wallets, settle earnings, or connect an external payment
provider.

Patient rows link to the legacy simulation log or the balanced demonstration
subledger using opaque UUID-prefixed activity references. Clinician rows link
to their own earning or payout record. The endpoint derives the caller's role
from the authenticated Frappe session and checks ownership in SQL. A caller
cannot select an account, owner, counterparty, or role through request data.
Unknown and other-owner references share the same unavailable response. The
response contains only the caller's bucket changes and a minimal related
appointment summary where the caller is a participant. Payout details always
state that no external transfer occurred.

Legacy simulation activity remains distinct from balanced subledger journals.
The detail screen identifies earlier legacy records and does not relabel the
append-only log as double-entry accounting. Real custody, ERPNext accounting,
refund settlement, and payout provider operations remain out of scope.

## Verification status

- `npm --prefix frontend run build`: passed after the route and page were added.
- `npm --prefix frontend run lint`: exited successfully; it reports existing
  repository-wide warnings, including duplicate localization keys elsewhere.
- Bench Python `compileall` for `tele_tena` and `tests/presentation.py`: passed.
- Focused Frappe assertions for patient log/journal owner privacy and clinician
  payout ownership passed during the presentation run.
- The complete `tests/presentation.py` run on
  `tele-tena-pr12-fresh.localhost` had 32 passing tests, 3 errors, and 1
  failure. The failures were financial reconciliation holds affecting the
  synthetic `p1` fixture after `test_07_legacy_wallet_mismatch_is_held_until_audited_decision`;
  this indicates test-state leakage/order interaction and is not evidence that
  the detail endpoint failed. It must be isolated before claiming a clean full
  suite.
- Production-built browser verification of the new transaction detail route
  has not yet been run. The current checked-in asset manifest still identifies
  the prior source until this feature branch is committed and packaged.

The retained site contains synthetic review data. No patient or clinician
records were reset or manually reconciled for this check.
