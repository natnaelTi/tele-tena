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
- The first complete `tests/presentation.py` run had 32 passing tests, 3
  errors, and 1 failure. Root cause: the new transaction-detail test posted a
  reservation to the subledger without updating the legacy wallet projection,
  so later spending tests correctly failed closed. The regression fixture now
  moves both projections together and posts a matching release. The complete
  suite is being rerun before reporting final status.
- Production-built browser verification of the new transaction detail route
  passed for the patient journey: password alternative on the invited-review
  site → Payments → an existing persisted reservation → detail → reload →
  generic unknown-record denial. The browser used the review account file
  without printing credentials. Screenshots are in
  `docs/screenshots/financial-activity/` at 390, 768 and 1440 CSS px. Visual
  inspection found no horizontal overflow at those sizes; 320px and 200% zoom,
  plus a clinician-owned detail browser journey, remain pending.

The packaged preview was built from source commit
`464dde31d94205ff2ccbe9fe6dec4e53e8e2bc3e` and served at
`http://127.0.0.1:8017/teletena/` by the isolated review site. The user selected
the visible “Use email instead” path because this site intentionally has no
SMS/email OTP delivery configured; this does not alter the authentication
policy or imply OTP delivery works.

The retained site contains synthetic review data. No patient or clinician
records were reset or manually reconciled for this check.
