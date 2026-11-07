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

# Sprint 1 — Operations & Journey Insights

Requested 5 November 2026. Baseline source de27a6fbd6e2ed8c23d74471d98b8c357178890a,
packaged0d1a3c37e68f4154f96bb809f6a3b60c11acd567. Branch
feat/operations-journey-insights depends on draft PR51. Preserve all existing data,
roles/financial rules/providers and shared Bench; no merge/deployment/reseed.

## Architecture and Collection Contract (Before Implementation)

- Native command tables: allowlisted events, continuous daily aggregates, incidents,
  support reports/replies/private attachment indexes, health/job heartbeats,
  operational configuration, replay archive indexes/deletion tombstones and versioned
  calendar-quarter reports. Existing audit and notification outbox remain authoritative.
- Tele Tena Approver is the operational super-admin, with no additional grant;
  clinical/ID/file permissions remain unchanged. Operational support access, exports,
  replay access and configuration changes are audited server-side.
- Browser intent is separate from durable server outcomes. Transactional successful
  outcomes use deterministic outcome keys; original business transactions are never
  retried by telemetry. Diagnostic failure cannot block care. Safe categories only;
  never request/response bodies, arbitrary strings, raw URLs/query/IDs, filenames,
  contact information, notes, evidence, receipts, tokens or stack locals.
- Authenticated actors use site-keyed pseudonyms; guest attempt UUID is bounded and
  contains no health content. Role/locale/device/release/environment/payment mode
  are enums. Staff/demo are labelled and excluded by default. Attempts have a24-hour
  reporting window; saved/incomplete is not automatically abandonment.
- Browser analytics/replay requires an explicit preference where consent is needed.
  Server operational outcomes are minimized separately. No unrestricted autocapture,
  console/network capture, media/canvas or second recorder. PostHog replay starts
  only after masking and project compatibility verification; full bodies/text/inputs
  masked and all sensitive media/documents/links blocked before transport.
- Bugsink adapter handles sanitized error events only, not tracing/profiling. No
  broad Frappe/Bench SDK initialization. Unexpected app/job failures are grouped;
  expected validation/authorization is counted separately, not a crash.
- Actual providers are currently unconfigured locally (no matching site keys).
  Actual PostHog project/export/playback proof is therefore an explicit external
  gate. Metadata/links are never called an archived recording. Archive remains
  unavailable until complete export and independent safe playback are proven.
- Raw replay expires90days after capture. Deletion tombstones prevent reimport;
  archive blobs are private filesystem/object-adapter objects, never DB blobs.
  Reporting/aggregates survive raw replay expiry. Quotas/backpressure fail safe.
- Native scheduler enqueues a dedicated teletena_ops queue; worker completion is a
  separate heartbeat. Standalone technical health/alert runner avoids dependence on
  application worker delivery. Existing SMTP plus explicitly configured Telegram;
  no unsolicited messages. Critical immediate, recurring grouped/cooldown, ordinary
  daily digest, one recovery, acknowledgement/escalation metadata.
- Quarterly boundaries: Africa/Nairobi calendar quarters, start inclusive/end
  exclusive, stored UTC. Reports are versioned/repeat-safe and label incomplete
  periods. Interpretation/annotations are separate from measured counts/coverage.

## Acceptance Checklist

All statuses start Requested; they are updated with actual evidence, never assumed.

| Area | Status / Gate |
| --- | --- |
| Allowlist, server-confirmed outcome dedupe, bounded browser attempts | Locally verified; optional browser collection only, guest collection disabled |
| Reviewer authorization/audit; patient/clinician denial | Locally verified backend/browser |
| Support ownership, private screenshots, internal/user reply separation | Locally verified backend/browser |
| Overview, health, queue execution/scheduler freshness | Locally verified including dedicated-worker restart |
| Safe errors, incidents, grouped alerts/daily digest/recovery | Controlled tests; no live receipt claimed |
| Analytics/replay controls and pre-transmission canary tests | Safe event/error egress verified; recorder quarantined, actual replay masking awaiting project |
| PostHog actual complete export + independent playback | Credentials present; awaiting authorized project proof and export/player implementation |
| Archive lifecycle/capacity/deletion and restoration safeguards | Synthetic native lifecycle verified; usable archive/provider deletion/capacity proof unavailable |
| Continuous aggregates/quarter reports/test-clock boundaries | Locally verified; partial coverage shown |
| Build/browser/mobile/200%/PWA/localization | Locally verified affected surfaces; human language/owner acceptance pending |
| Fresh/repeat migration and existing state/financial preservation | Frappe16 fresh/populated upgrade + repeat and Frappe15 retained upgrade verified |
| Provider ingestion/live alerts/UptimeRobot setup | Awaiting explicit account configuration/operator test |
| Sprint 2 API/component/operator/update handoff | Prepared; docs/operations/operator-and-sprint2.md |

Provider sources and current limitations are recorded in provider-compatibility.md.

Working-file follow-up: see [actual readiness](configuration-readiness.md). EU335848
and Bugsink credential fields are populated; no successful connectivity is inferred.
Telegram chat discovery found no matching setup message. The single consolidated
[live plan](live-verification-plan-v1.md) awaits approval; no site flags changed.

## Plan V1 Continuation

Selected-provider error/event ingestion, owner alert receipts and the provisional
single-window export/player proof are recorded in
[live results](live-verification-results-v1.md). Application-wide replay remains
quarantined; settled export/deletion is due6November2026 at19:50:28.731UTC. This is
not production activation or completed90-day retention acceptance.
