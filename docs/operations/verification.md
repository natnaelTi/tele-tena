## Current Reviewer Portal — Sprint 2

[Full current evidence, source/build, screenshots and walkthrough](sprint-2-verification.md)
and [actual runtime reconciliation](sprint-1-runtime-reconciliation.md).
Sprint1 remains open at its settled V2/operator/policy gates. No new live tests,
production activation, merge or deployment. Earlier package pins below are historical.

## Terms, Navigation and Backup Follow-Up — 7 November 2026

Verified installation/build: `4e5b12613eb7702ca7c2844716605a094d558ef6`. Preview
http://127.0.0.1:8017/teletena/ serves this exact production package; later commits
contain documentation/evidence only. Release JSON SHA256:
`3227445b9b7d88d352869a224243a22c77fda3427c58d4a7555ac8af1aa37e75`.
No dependency, schema or patch-list change in this continuation.

[Exact new checks and inherited evidence](terms-navigation-followup.md),
[current requirement matrix](acceptance-matrix.json),
[source configuration](configuration.md#read-only-backup-freshness-source).
Built final browser checks passed all7tabs click/direct/reload/history, local
HTTP/render recovery, empty/disabled/unavailable states, server role denials and
Terms old-version/non-consent boundaries. Responsive390/768/1440 and actual200%
zoom/keyboard screenshots inspected. Backend6Terms +19operations,6backup,
3policy-localization,7preflight and localization5+2 pass. Production build/lint
(zero errors; existing warnings) and311artifact hashes/private credential scan pass.
Read-only11patient/2clinician/22account reconciliation has zero mismatches.
Final built PWA update/cache-denial/offline-to-online deep-link recovery also passed
on the isolated site, without provider traffic.

Safe rendered evidence:
[Before: first Insights crash](../screenshots/operations/terms-navigation/before-navigation-1440.png),
[After: Insights](../screenshots/operations/terms-navigation/after-insights-1440.png),
[Mobile Operations](../screenshots/operations/terms-navigation/after-archive-390.png),
[Public Terms mobile](../screenshots/operations/terms-navigation/public-terms-390.png),
[Existing acknowledgement section](../screenshots/operations/terms-navigation/onboarding-terms-panel.png),
[Actual200% Operations](../screenshots/operations/terms-navigation/insights-200-percent-screen.png),
[Actual200% Terms](../screenshots/operations/terms-navigation/terms-200-percent-screen.png).
Screenshots contain public copy or fictional presentation identities only.

Guests remain unrecorded because the current guest flow has no Terms acceptance
point. Draft wording/consent model approval remains pending; production stays off.
V1 remains closed; V2 ledger still AwaitingSettledRecheck with unchanged usage and
8Nov2026,00:28:39Africa/Nairobi due time. No new provider operation or automatic
schedule. UptimeRobot, production storage/expiry, independent launcher and recurring
backup-source setup remain operator prerequisites. No merge or remote deployment.

## Historical Evidence (Superseded Where Noted Above)

## Final Local Package — 6 November2026

Installation/build: `fbd3b09d5ff64bfb7e1f57c0deb4a5d489b373ce`. Preview8017 serves this exact release; later
documentation/evidence changes do not change runtime assets/backend.
v1.54 fresh/repeat and populated preservation pass;16capture,19operations and
30communications tests,8budget,6cleanup-retry,5native-budget,1due-time guard,
localization5+2, build/lint and exact private-asset/hash scans pass. Current frontend
lint retains existing warnings, zero errors. The strengthened built PWA check
verifies obsolete public-cache eviction as well as API/private denial and
offline→online recovery. Restart uses only owned preview processes; final financial
reconciliation11patients/2clinicians/22accounts has zero mismatches.

[Current matrix](acceptance-matrix.json), [actual V2/due command](live-verification-results-v2.md),
[remaining gaps](implementation-gaps.md), [Selfmade guide](../selfmade-operations-update.md)
and [Sprint2 handoff](operator-and-sprint2.md) are authoritative over historical
status descriptions below. Sprint1/operational90day archive are not complete.

> **Latest V2 status:** actual native SDK→gateway→worker ingestion and provisional
> export/playback pass. Its settled native archive/cleanup checkpoint is due
> **8November2026,00:28:39Africa/Nairobi**, not scheduled or passed.
> Original PlanV1 settled proof/cleanup is complete and closed. Production remains
> disabled. See [exact results and resume command](live-verification-results-v2.md).

> **Current continuation — 6 November 2026:** v1.54 native replay admission,
> masking, private spooling/export, independent player and retention are implemented
> and locally verified. The original live recording passed its settled25-hour
> export/playback; deletion was accepted204 after corrected permissions, and a
> separately approved follow-up read returned404. PlanV1 is closed. The actual new native gateway has no
> live ingestion proof yet. Production capture/export remain disabled.
> [Current requirement matrix](acceptance-matrix.json),
> [implementation gaps](implementation-gaps.md) and
> [v1.54 evidence](replay-integration-v154.md) supersede older status statements below.

> Current Plan V1 results supersede the historical provider status below: see
> [actual live results, receipt confirmation and pending 25-hour checkpoint](live-verification-results-v1.md).
> Production collection remains disabled; no 90-day archive claim is made.

## Working Provider Configuration Follow-Up

The owner supplied a populated `providers.json`; credentials and optional capability
fields are present and local validation passes. Telegram chat is unresolved after
one authorized exact-message lookup found zero matches. Owner subscription stays
unlinked/live tests false, site binding unchanged. No ingestion or delivery claimed.
See [current readiness/gaps](configuration-readiness.md) and
[bounded approval plan](live-verification-plan-v1.md). The earlier evidence below
remains historical; references to missing projects are superseded by this follow-up.

# Operations Sprint 1 — Verification and Remaining Gates

Verified5November2026. This is a **native operations review candidate**, not final
launch acceptance. Baseline de27a6f / built0d1a3c3, dependent draft PR51/50 ancestry
retained. Production build pin is recorded in the final handover below. No remote
site or provider project was modified. Main presentation data was not reseeded.

## Observed Environments

| Environment | Observation |
| --- | --- |
| Retained preview | `/home/frappe/frappe/frappe-bench`, Frappe15.121.2 / ERPNext15.121.6, Python3.12.3, Node22.23.3; site `teletena-mvp-presentation.localhost`, port8017 |
| Compatibility | `/home/frappe/teletena-compat/bench`, Frappe16.2.1 / ERPNext16.1.0, Python3.14.2; isolated MariaDB10.6 / Redis6.0.16 |
| Browser integration | Private clone `teletena-payments-v147-fresh.localhost`, separate DB/Redis/port8021, same production-built static application; synthetic accounts and private transport only |
| Error SDK | Existing sentry-sdk1.45.1 on both environments; no Python dependency changes |
| Frontend | Locked posthog-js1.446.0 addition, quarantined; no runtime recorder start or draft translation import |

## New Evidence

- **16/16** real Frappe16 rollback-isolated operations tests: strict event/source/
  property schema, duplicate outcomes, role denials, support ownership/internal-note
  separation/private screenshots, quota failure without appointment mutation,
  sanitized errors/timeout, actual Sentry Client with in-memory transport, report
  quarter boundaries/repeat/synthetic exclusion, private90-day test-clock deletion
  and restore tombstones, unavailable export proof, stale/current health, alert
  grouping/cooldown/single recovery under mocked channels, preferences and fresh-site
  HMAC key without framework credential changes.
- **17/17** existing application-flow and **21/21** direct-payment regressions rerun
  sequentially because central command hooks changed; no financial reset. Localization
  exchange5/5 and extraction2/2 pass. Lint has existing warnings and zero errors.
  Production locked build passes (existing bundle-size warning retained); asset/
  privacy/hash check passes, no public source maps/configuration/private files.
- Real production-built browser: patient problem submission, reference, reviewer
  triage/internal note/user-visible reply/resolution, patient refresh and internal
  note denial. Explicit synthetic screenshot preview, close/reopen/Escape/focus
  restoration and guest download denial. Patient operational configuration denied.
- Browser report compile/repeat/annotation and rendered report. Consented safe event
  transport and controlled browser-error canary: raw error text/email/token canary
  absent from outgoing error/event payloads. No live provider transport. This is
  **not** a verified PostHog replay-masking claim: recording remains disabled.
- Rendered Overview/Health/archive unavailable/support at390/768/1440px, actual
  Chromium200% zoom (1440physical/720CSS/DPR2) on Overview/Support/Reports, reduced
  motion, keyboard dialog Escape/focus. Screens visually inspected against the
  current shared reviewer typography/cards/dialog language. There is no previously
  approved dedicated Operations screen; owner visual acceptance remains required.
- Actual native scheduler → default worker scheduled method → `teletena_ops` worker
  completion/retention/aggregate/report heartbeats, independently observed. Initial
  custom-queue validation exposed missing queue registration; fixed native registry,
  restarted only owned clone processes and proved processing. Dedicated worker
  stop/start recovery and repeat-start PID stability pass. No direct invocation is
  substituted for enqueue/execution evidence.
- Main local lifecycle stop/start passes,8017HTTP200 with its dedicated operations
  worker. Financial owner reconciliation11patients/2clinicians/22accounts: zero
  projection, obligation, journal or balanced-posting mismatches.

## Migration and Preservation

Native Frappe16 populated clone upgrade + repeat preserved106original tables and
18,795original rows, private-file/config hashes and credential values. Main
Frappe15 upgrade + repeat preserved106original tables and19,301original rows and
private/config values. The local log's generic script label says Frappe16; the main
actual interpreter/framework was15 as recorded above. Complete native backup before
main migration includes verified database/public/private/config archives (600/700).

Fresh native Frappe16 + ERPNext16 installation on
`teletena-ops-v153-fresh.localhost` and repeat migration pass with empty operational
records and disabled external flags; existing Wallet/access defaults unchanged.
The first attempt stopped because isolated Redis was not running; resumed native
TeleTena install after restoring that owned Redis, without resetting the site.
v1.53 tables were unchanged by subsequent UI/service/HMAC fixes. New HMAC test covers
fresh sites without an existing encryption key. No framework source modified.

## Explicitly Reused Evidence

Individual/couples hosted calls, End/revocation/media isolation, historical earnings,
full registration/scope/language and prior payment communication suites retain their
existing reports. They were not rerun as expensive complete hosted suites. This
sprint adds safe hooks/metrics, not call/session/financial state changes; targeted
application/payment regressions above exercise the affected command boundary.
No new physical-device, live OTP/SMS/email receipt or real payment evidence.

## External and Human Gates

| Capability | Accurate state / Required resolution |
| --- | --- |
| Bugsink | Sanitized controlled SDK transport tested; working project/DSN present; authorized ingestion readback and opt-in alerts unverified |
| Private source maps | Not uploaded or verified; selected Bugsink endpoint/debug-ID compatibility and scoped token required |
| PostHog analytics | Server adapter/control tests only; EU335848 credentials present; project ingestion not verified |
| Masked replay | Quarantined, disabled; actual canary/SPA/account-switch/document masking proof outstanding |
| Replay archive/playback | **Unavailable**; complete raw export/all segments/player independence/missing segments must pass on selected project before implementation can be enabled |
| Capacity | No actual compressed recording samples; no fabricated production estimate; measure once export/player proof exists |
| Provider/user replay deletion | Native tombstone/local object lifecycle tested; provider deletion remains Pending, not connected |
| Owner alerts | Recipient private/unlinked; Telegram token present/chat unresolved; live email receipt unverified, no unsolicited tests |
| External uptime | Exact setup instructions prepared; no account/monitor created, entitlement/receipt needs operator validation |
| Policies/localization | Draft notice and existing fallbacks; no human translation/policy approval invented |
| Owner acceptance | New native screens await owner review; full launch still depends on these gates and Sprint2 |

All authorized independent native work is packaged. The actual PostHog project is
a specific blocker to claiming a working90-day archive or Sprint1 provider acceptance,
not a reason to fake a player or activate unrestricted capture.

## Evidence Locations and Reproduction

Private raw logs/browser sessions/synthetic evidence:
`/home/frappe/teletena-operations-sprint` (outside Git). Do not publish session files,
account manifests or private backup bundles. Selected synthetic screenshots are in
`docs/screenshots/operations-sprint-1/`.

Backend reproduction uses the existing isolated synthetic site, runs sequentially:
`PYTHONPATH=$PWD /home/frappe/teletena-compat/bench/env/bin/python -c "import sys,runpy,tele_tena;sys.path.insert(0,'tests');runpy.run_path('tests/operations.py',run_name='__main__')"`.
Browser reproduction: `tests/operations_browser.cjs` requires private
`TELE_TENA_OPS_ACCOUNTS` and `TELE_TENA_OPS_EVIDENCE`, plus Playwright via the retained
browser-tools NODE_PATH; loopback8021 only, existing isolated synthetic users. Never
point tests at Selfmade/presentation data. New operations files/rows are separate
from immutable clinical and financial history.

## Current Handover Identity

Immutable installation/packaged source: `79fcebde6a940d3c12e9b5df7be2eb03ab788ac7`.
Branch `feat/operations-journey-insights`, draft PR52 → PR51 → PR50 ancestry retained.
Later source commits contain evidence/guide updates only. The latest continuation
adds gated adapters and trusted browser frames, without schema/dependency changes.

See [actual provider results and exact pending checkpoint](live-verification-results-v1.md),
[release metadata/checksums](release-evidence.json) and
[copyable incremental update/recovery procedure](../selfmade-operations-update.md).

Preview: http://127.0.0.1:8017/teletena/ — reviewer More → Operations Overview /
User Support. Provider bindings and site replay/analytics/alert settings stay unchanged.
This is a native review candidate; unfinished capture integration and settled
proof gates prevent claiming Sprint1 fully complete or90-day archive availability.
