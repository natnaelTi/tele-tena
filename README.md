# Tele-tena

Ethiopia-first consultation platform: custom Frappe app + ERPNext accounting + React PWA.

**Status: foundation scaffold, not a functional clinical MVP.** No phone login, clinical
workflows, financial operations, PWA installation or LiveKit integration is implemented yet.

See [product contract](docs/product-contract.md), [architecture](docs/architecture.md),
and [WSL development](docs/development.md). Framework versions await confirmation from
the existing isolated bench. No real patient data or funds should be used.

Frontend: `cd frontend && npm ci && npm run dev`.
Checks: `cd frontend && npm run build`; `python -m compileall -q tele_tena`.

Contribute using a focused feature branch and PR with purpose, behavior, checks and
limitations. Dependencies should be locked; use synthetic fixtures. No product license
has been selected; public visibility alone does not grant an open-source license.
