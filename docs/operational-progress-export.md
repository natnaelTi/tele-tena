# Current operational checkpoint — 2026-10-07

## Clinic affiliation subflow — 2026-10-07

The focused branch `feat/clinic-affiliation-review` is at
`c5c2bf2c532e2b3c50d3416291ae63e32484569b`, based on
`feat/previous-clinicians`. On disposable Frappe 15, presentation API tests
passed 22/22, OTP state-machine tests passed 7/7 with a mocked mail provider
and enabled-registration test fixture, and a built `/teletena/` browser journey
passed clinic and affiliation human-review workflows. The local preview is
`http://127.0.0.1:8017/teletena/`, site `tele-tena-pr12-fresh.localhost`; both
backend and production asset source match this branch. No live email/SMS was
sent. The branch remains partial: clinic staff/workspace/resource/billing and
encounter-grant operations, Frappe 16 compatibility, and responsive/native
language evidence remain outstanding. This checkpoint does not claim the wider
screen/product inventory complete.

The presentation/integration regressions now pass 22/22 and 24/24 respectively;
integration temporarily enabled only this disposable site's signup flags,
restored invited-review mode, and mocked SMS. The test site's scheduler remains
disabled and no site-isolated worker runs, so queued financial release/routing
is not represented as operational.

## Later dependent branch checkpoint

Current source is `fb58ab13815bd3cc16b9e12675c6f6e2474967a1` on
`feat/previous-clinicians`; draft PR #17 depends on PR #16 at
`503a39df2993cbced46ea067cef97917bac8bcf8`. The browser code and patient-only
query for returning clinicians are implemented. PR #17 CI passed. The
Frappe-backed regression and matching local `/teletena/` preview remain pending.
The original Frappe 15 site was preserved and not migrated. Port 8017 is still
the separate Frappe 16 compatibility WSGI app and does not serve this checkout.

This current section supersedes the historical checkpoint below. Do not use its old source SHA as the current release.

- Current implementation branch: `feat/teletena-operational-completion`; draft PR #16 targets PR #15’s integration branch and retains PR #12–#15 ancestry. It is pushed for review but remains unmerged; no remote deployment occurred.
- Added one immutable 1–5 patient session-experience rating after an ended and explicitly finalized encounter. Same-payload retry is idempotent; changed retry, premature feedback, other-patient access, clinician access, and concurrent duplicate submissions have regression assertions. Public clinician profiles expose a rolling 365-day experience aggregate, a 90-day offer response rate for immediate requests actually fetched while availability is fresh, and a 365-day clinician-attributed cancellation rate. Each metric has separate evidence counts and hides rates below five observations. Patient cancellations, unconfirmed holds, and unsupported no-shows are not attributed to clinicians. These are operational/experience indicators, not clinical competence or outcome evidence. See `session-experience-metric.md`.
- Added v1.14 migration/bootstrap, migration-preservation and fresh-install assertions, English/Amharic/Afaan Oromo provisional UI strings, and focused backend regression assertions. Pure metric tests pass (4/4), Python compile, TypeScript/Vite build, and lint pass; lint retains existing React warnings. Frappe query/migration/browser verification has not run.
- Dependent branch `feat/previous-clinicians` adds a patient-only returning-care query and dashboard cards, limited to the signed-in patient's own completed appointments and clinicians who currently have an approved scope and published schedule. It exposes only the clinician's opaque public profile key and display name; no other patient's history is linked. An integration regression covers patient isolation and clinician denial but is pending a disposable Frappe site.
- The latest source still has no isolated disposable site: `/tmp/tele-tena-pr12-db-admin.json` and `sites/tele-tena-pr12-fresh.localhost` are absent. Frappe migration/integration/browser assertions for this feature have not run. There is no current-source preview URL. The existing port 8017 process is the older Frappe 16 compatibility checkout and is not valid for this branch.
- `docs/operational-screen-map.json` still covers 142 screens/14 journeys; E12 and F12 moved from Designed to Implemented, verification pending. This is not full acceptance. Clinic, couples, laboratory/diagnostics, subscriptions, second opinions, medical tourism, feedback moderation, and other designed screens remain incomplete or externally gated as recorded in the map/tracker.
- No live SMS, physical-device, clinical/native translation, provider settlement, remote Selfmade update, or production-care acceptance is claimed.

## Historical checkpoint — superseded source

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
