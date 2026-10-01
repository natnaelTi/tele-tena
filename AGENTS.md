# Tele-tena engineering instructions

Read docs/product-contract.md and docs/architecture.md before changing workflows.
For all frontend work, follow docs/design-system.md and docs/design-acceptance.md.
The TeleTena design specification is authoritative; rendered-browser evidence is
required before visual acceptance. Build/lint alone do not establish acceptance.
Use focused feature branches, conventional commits, and pull requests. Never force-push
or modify Frappe/ERPNext core. Refactor separately when practical; preserve behavior
with meaningful tests. Do not declare features working on the basis of UI alone.

All permissions are enforced server-side, including generic DocType APIs, files,
reports and exports. Deny access by default. Clinic or partner affiliation never
implies clinical-record access. Do not use ignore_permissions to bypass authorization.

Never commit credentials, site configuration, database dumps, patient data or tokens.
Use synthetic fixtures. Never log clinical text, OTPs, authorization headers or room tokens.
No recording/transcription by default. No authenticated API or clinical-data PWA caching.

Money uses integer minor units or exact decimals, never binary float. Balance checks,
reservations and booking conflict checks must be transactional. External notifications
must be authenticated and idempotent. Corrections reverse ledger entries; no silent edits.
Simulation must be labeled and inaccessible as a real-money funding route.

Run relevant checks and document exactly what was not tested. Framework compatibility
and deployment access must be observed, not inferred. Never expose API secrets in VITE_ variables.
