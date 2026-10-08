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
need native-language review. The browser regression renders current synthetic
held cases at mobile, tablet, and desktop widths but deliberately does not submit
a decision against retained site records. The browser assertion also checks
that patient email identifiers do not render. Backend decision authorization,
idempotency, and mismatch checks remain covered by the Frappe presentation suite.
