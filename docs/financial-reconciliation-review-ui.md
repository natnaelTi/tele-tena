# Financial reconciliation review screen

The `/admin/financial-disputes` page includes a separate wallet-reconciliation
queue for users with the server-enforced `Tele Tena Approver` role. Its stable
site-secret HMAC reference is opaque and does not encode the table key. It shows
the legacy activity projection, unchanged wallet
snapshot, subledger amounts, and event/boundary counts from the private
reconciliation audit. The queue omits patient account identifiers and does not
show clinical notes or appointment content.

`Accept unchanged snapshot` is an explicit, reason-required call to the existing
`accept_reconciliation_case` command. The queue omits the patient identifier and
free-form audit reason; the server resolves the HMAC case
reference and locks the gate, audit row, and
wallet, verifies the wallet still equals the subledger, and stores reviewer,
reason, and decision time. It does not alter any balance, repair or erase a
historical event, or imply that the original discrepancy was resolved. A
reviewer must investigate the preserved evidence before deciding. Review holds
must never be accepted automatically to unblock an account.

The three Amharic and Afaan Oromo labels added for this queue are provisional and
need native-language review. The browser regression passed on the built
`/teletena/` Frappe app at 390, 768, and 1440 CSS px with no horizontal overflow.
It renders the three retained synthetic held cases and confirms neither email
identifiers nor free-form audit reasons are returned/rendered; it deliberately
does not submit a decision against retained site records. Backend decision
authorization, HMAC-reference privacy, idempotency, and mismatch checks pass in
`tests/presentation.py` (40/40). Screenshots:

- `docs/screenshots/financial-reconciliation/queue-390.png`
- `docs/screenshots/financial-reconciliation/queue-768.png`
- `docs/screenshots/financial-reconciliation/queue-1440.png`

The preview at `http://127.0.0.1:8017/teletena/admin/financial-disputes` uses
the isolated `tele-tena-pr12-fresh.localhost` site. Backend checkout is
`fix/legacy-wallet-projection-audit`; the backend behavior was last changed at
`f975952d53ca2390b91d708b148890b851ac893f`. The exact built-asset source SHA is
recorded in `frontend/dist/release.json` and `tele_tena/public/review/release.json`
after the final packaging run. The isolated Gunicorn preview was HUP-reloaded
after the final backend build. Shared Bench
workers and scheduler were not restarted for this UI-only change.
