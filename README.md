# Tele-tena

Ethiopia-first consultation platform: custom Frappe app + ERPNext accounting + React PWA.

**Status: verified synthetic milestone 1 demonstration.** Approved clinician discovery,
disclosure preview, direct booking and simulated fund reservation are connected.
No phone OTP, real payments, PWA installation or LiveKit integration.
See [review steps and test results](docs/milestone-1-verification.md).

See [product contract](docs/product-contract.md), [architecture](docs/architecture.md),
and [WSL development](docs/development.md). Observed installed versions are recorded in the verification docs. No real patient data or funds should be used.

Frontend: `cd frontend && npm ci && npm run dev`.
Checks: `cd frontend && npm run build`; `python -m compileall -q tele_tena`.

Contribute using a focused feature branch and PR with purpose, behavior, checks and
limitations. Dependencies should be locked; use synthetic fixtures. No product license
has been selected; public visibility alone does not grant an open-source license.
