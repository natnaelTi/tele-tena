# Architecture decision 001 — Frappe-backed PWA

Status: accepted direction; foundation installation verified on Frappe 15.121.2
and ERPNext 15.121.6. Product workflow compatibility remains to be tested.

React + TypeScript + Vite talks to a dedicated custom Frappe application. ERPNext
provides accounting. Frappe RQ workers and scheduler handle jobs. No Django or Celery.
MariaDB and framework versions must match the user's isolated WSL bench; do not upgrade
that bench automatically. LiveKit carries human-to-human audio/video; Frappe issues
short-lived room-scoped tokens only to authorized appointment participants.

Use same-origin routing in deployment and a local Vite /api proxy in development.
Never place an administrator key in the frontend. Phone OTP requires a custom verified
login flow with expiry, throttling, replay prevention and account recovery. Session
cookies and CSRF must follow the installed Frappe version's supported behavior.

Modules: identity/consent; providers/affiliations; service catalog; marketplace;
scheduling; consultations/records; financial subledger; trust/operations.

Operational ledger owns spendable/reserved funds and clinician earnings. ERPNext owns
financial reporting. Define posting mappings, durable retry references and reconciliation;
never independently calculate two authoritative spendable balances. Regulatory/provider
approval of stored funds is still outstanding. Demo money is simulated only.

Use explicit command APIs for accept_offer, book_appointment, reserve_funds and
request_withdrawal. Generic document writes must not bypass these invariants.
Clinical data and financial account identities are separate. Admin roles are scoped.
All financial/acquisition/disclosure/policy decisions retain versioned evidence.

Future service definitions are configuration records. New clinical workflows can require
new code. Do not create a DocType per specialty or fork framework core.

PWA installation is planned, not implemented in this foundation. Cache static assets
only; no clinical data, tokens, API responses or offline financial commands. No guarantee
of background calling on locked mobile devices.
