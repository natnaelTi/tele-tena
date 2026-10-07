# Operational implementation checkpoint — 2026-10-07

This is a concise, sanitized progress export for roadmap updates. It is not a release or deployment claim.

- Repository: `natnaelTi/tele-tena`.
- Local branch: `feat/teletena-operational-completion`, current source commit `c621b2fa63b33b09e7febfd3fb0785f49cb5d520`, based on open draft PR #15 head `3e0965c5fdf6485d945756b382c0a3c008450058`; ancestry includes open PR #14 → #13 → #12. PR #11 is separately open. No merge/deploy occurred.
- Active original WSL Bench: `/home/frappe/frappe/frappe-bench`; site `erp.localhost`; Frappe 15.121.2 / ERPNext 15.121.6 / Python 3.12.3 / Node 22.23.3. The site was backed up before changes and has not been migrated. Existing web/worker processes remain untouched.
- Extracted design: `/home/frappe/teletena-design-reference`; inventory contains 142 screens/14 journeys. It is a visual source, not an operational product.
- PR #15 adds the two-sided hero, real request progress, clinician-owned paginated offer history, disclosure-safe patient labels, accepted appointment handoff and offer withdrawal. Current local Frappe integration assertions are pending.
- Added v1.13 financial mismatch audit/hold code and an additive review decision. It preserves source wallet/events and blocks affected wallet writes pending explicit review. The code has compile/unit coverage only until a disposable Frappe site can be migrated.
- Began token/font port to the extracted blue–teal/Inter direction; self-hosted Inter is locally licensed and Noto Sans Ethiopic remains. Built React compilation succeeds, but no current Frappe-served visual/browser acceptance has occurred on this feature worktree.
- Static results: `tests/review_package.py` 9/9; `offer_status_unit.py` 4/4; `hosted_phone_unit.py` 4/4; `dependency_checkpoint.py` 3/3; frontend `npm run build` passes (large LiveKit bundle warning); frontend `npm run lint` exits 0 with pre-existing React warnings; Python compile and `git diff --check` pass.
- Current non-destructive database inspection found one preserved patient wallet whose event projection differs by 1,800 minor units. No financial record was altered. v1.13 is intended to preserve and hold it, pending migration verification.
- No current `/teletena/` preview matching this branch has been started. The older port-8000 root app and Frappe-16 port-8017 preview are different source/site combinations and must not be used to review this branch.

## External gates

No live SMS/SMTP delivery, physical-device media, native language approval, clinical credential validation, laboratory/clinic partner integration, real custody/provider settlement, remote Selfmade update, or production clinical-readiness claim is made.

## Next verification actions

1. Run the disposable fresh-install and registration-mode check, retaining that new disposable site only after a successful check.
2. Run the Frappe 15 integration, presentation, vetting/routing and migration-preservation tests on that disposable site.
3. Exercise the actual built `/teletena/` app and availability/request/booking journeys on the matching backend.
4. Verify owner-by-owner subledger reconciliation, then start only workers/scheduler isolated to that preview site.
5. Continue approved batches and update screen-level statuses only with concrete browser/API evidence.
