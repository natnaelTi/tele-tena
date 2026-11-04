# Payment Mode Validation Correction — 28 October 2026

Runtime/build `6f5cd6c387cc2b461ce0b7ef0e50a4973b990db2`, draft PR50, same
branch/ancestry. No migration, provider change or remote deployment.

The owner screenshot supplied Hold0, Verification3, Transition Plan `None`,
Reason `Testing`. Hold must be a whole number5–120; Verification3 is valid
(range1–72 hours). The site had7 historical Wallet obligations and0 active
direct-payment holds. `None` has4 characters, below the20-character minimum for
a plan required when changing modes with historical obligations. Permission was
valid. The old catch-all error obscured field validation with unrelated advice.

The form now has linked field errors/focus, visible bounds, a multiline
transition-plan field and explanatory obligation counts. A plan is required only
for an actual mode change with historical obligations. It accepts20–2,000 trimmed
characters of operational free text; the note is audited, never executed, and
does not convert/release balances, cancel bookings, clear obligations or bypass
active direct holds. State who will manage existing reservations/payout/refund
cases under their original rules. A meaningful plan is a human responsibility;
length validation is not an assessment of its operational adequacy.

API failures distinguish invalid hold/window/reason/plan, blocked active intents,
stale configuration and permission/session errors. Failed submissions retain edits;
successful saves have an explicit status. Backend ranges and authorization remain
enforced, with stable field-specific error codes. Existing history is unchanged.

Verification:18/18 real-MariaDB rollback-isolated payment tests, including no
configuration/audit mutation after invalid values and `None` plan rejection;
4/4 localization exchange tests; production build/lint and private-asset scan
passed. Actual reviewer login and native backend on8017 verified both client
prevalidation and independent server rejection; mode/revision stayed unchanged.
The stale-response browser case uses a controlled response, not a real concurrent
administrator update. Captures at390/768/1440 were inspected; full-page images can
show sticky header stitching at their capture scroll position. Screenshot source
containing the owner's desktop/browser chrome remains outside Git.

See `scripts/browser-payment-config-validation.cjs` and
`docs/screenshots/offline-telebirr/payment-mode-validation-*.png`.
The browser regression requires the explicit financial permission and the retained
Wallet baseline; it never resets the site to manufacture that state. New owned
copy is included in the translation CSV (8,631 entries,4,295 missing per non-English
locale,0 human-approved). Human translation and owner acceptance remain pending.
