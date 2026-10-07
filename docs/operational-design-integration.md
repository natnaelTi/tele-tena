# Historical TeleTena operational design integration checkpoint

This document captures an initial implementation plan and an earlier source snapshot, not the current release. Current status is maintained in `operational-progress-export.md`; screen acceptance remains in `operational-screen-map.json` and `mvp-delivery-tracker.md`.

7 October 2026. Authorized target: implement the complete approved design inventory and extended modules in the existing React/TypeScript + Frappe/ERPNext architecture. The 142-screen extracted source remains the visual/interaction reference, while the existing product and backend remain authoritative. Do not copy the static prototype as a fake implementation or create a second wallet.

## Current slice

Current branch `feat/teletena-operational-completion` starts at PR #15 head `3e0965c5fdf6485d945756b382c0a3c008450058`, based on PR #14 and preserving PR #12–14 ancestry. Current committed head is `c621b2fa63b33b09e7febfd3fb0785f49cb5d520`. PR #15 adds a two-sided homepage, server-state request motion, clinician-owned paginated offer history, a masked patient label from the original disclosure snapshot, accepted-appointment handoff and offer withdrawal. Those backend assertions have not yet run in this local Frappe 15 Bench.

Motion never fabricates an ETA, receipt, offer or booking. Changing prompts describe current facts. Reduced-motion users receive static text. No request narrative or competitor quote is copied into the new history response. The clinician must authenticate with the clinician role and matching profile. The appointment join is actor-scoped. Limits use bounded paging; read-time expiry does not require a scheduler write.

The homepage query is passed through in-memory navigation state, not a new URL query string. Existing patient profiles returning from sign-in can return to discovery. A newly created account still completes onboarding; preserving the original query through every onboarding step requires follow-up acceptance work. Discovery is still a service/name filter, not a complete natural-language classification engine.

## Full approved implementation sequence

1. Establish the PR #15 baseline in the original WSL Frappe 15 Bench: run real MariaDB/API/browser tests on a disposable site, fresh install/repeat migrations, verify the current head's offer-history permissions, then cut over background writers before activating the financial schema on the development site.
2. Port the approved foundations, authentication and onboarding layouts into the connected React app; keep site-scoped invited-review and hosted-registration policies distinct and keep care-query state out of URLs, logs and analytics.
3. Complete per-scope clinician vetting, private evidence/affiliations and a versioned, clinically reviewed catalog. Approval and expertise remain separate trust dimensions; no reviewer decision is automated.
4. Complete discovery, scheduling and consultations: natural-language category suggestions without diagnosis, returning-clinician flow, generated slots, mutual rescheduling and cancellation policy, note/summary/follow-up, hosted LiveKit End protection and explicit extension consent/funding.
5. Complete private open requests, request-ready presence, progressively routed offers and clinician-owned offer history. Keep all hard eligibility and privacy constraints, and measure publication-to-match separately from both-participants-joined time.
6. Complete the owner-reconciled demonstration subledger, authorized dispute holds, scheduled releases, payout request lifecycle and auditable legacy mismatch holds. ERPNext posting and real provider settlement remain separate boundaries.
7. Add clinic administration with explicit membership permissions and per-encounter access grants; membership never grants blanket clinical-record access.
8. Add adult shared-care workflows with independent participant identity, consent, private intake and recipient-specific notes/LiveKit authorization.
9. Add versioned laboratory and diagnostics catalog/orders/specimen/result correction/release flows only after partner, clinical and chain-of-custody acceptance.
10. Add subscription entitlements, second opinions and medical-travel case coordination through the existing authoritative financial system and explicit consent/jurisdiction checks.
11. Complete administrator operations, feedback moderation, routing/financial metrics and full per-screen visual/browser acceptance across all three languages.

`operational-screen-map.json` now includes all 142 screen IDs, the allowed acceptance statuses and, per screen, its intended route, actor, models, actual or explicitly missing API, permissions, transitions, loading/empty/error/success states, responsive/accessibility behavior, localization, dependencies and verification evidence. These are acceptance requirements, not evidence. A screen remains unaccepted until the current local connected flow passes.

## Baseline checks run on 7 October 2026

The active WSL environment is `/home/frappe/frappe/frappe-bench`, site `erp.localhost`, Frappe 15.121.2, ERPNext 15.121.6, Python 3.12.3 and Node 22.23.3. A site/database/public/private-file backup completed before any schema change. The extracted design path was confirmed as `/home/frappe/teletena-design-reference` and the 142-card gallery rendered locally.

Passed so far on the current working source: `pip check`; TypeScript/Vite production build with four licensed Inter weights bundled; lint exits 0 with existing warnings; `tests/review_package.py` (9/9); `tests/offer_status_unit.py` (4/4); `tests/hosted_phone_unit.py` (4/4); `tests/dependency_checkpoint.py` (3/3); earlier service-worker privacy checks; Python compilation; and `git diff --check`. The 142-screen/14-journey acceptance map validates required fields/statuses. No Frappe integration, v1.13 migration, financial test, production asset packaging, or current-source browser test has run yet.

## Current blockers and preview boundary

`sudo -n mariadb` requires local interactive authentication. The integration fixtures are now guarded against `erp.localhost`; they must run on a dedicated `tele-tena-*.localhost` site. Commit `1f85253` adds v1.13 per-owner legacy/wallet/subledger mismatch audit, a write hold, a reasoned current-snapshot decision API, and regression coverage. It has only passed syntax/static checks so far and has not run against a Frappe database. The current development database contains one preserved patient wallet whose legacy deposit/reservation log does not explain its available projection (a sanitized pseudonymous aggregate differs by 1,800 minor units). No record has been changed.

The original Bench route currently returns 404 at `/teletena/`; port 8000 serves its older root application. The separate port-8017 review preview still serves the Frappe 16 compatibility branch at PR #14's source, not this PR #15-based branch. Neither URL is being represented as the current product preview. A matching built preview will be started only after the disposable Frappe 15 site has the matching schema and source.

Live SMS/email delivery, physical-device calls, native translation review, clinical approval, provider settlement and Selfmade deployment remain external gates. No PR has been merged or deployed remotely.
