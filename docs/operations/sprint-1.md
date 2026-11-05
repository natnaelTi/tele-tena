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
| Allowlist, server-confirmed outcome dedupe, bounded browser attempts | Requested |
| Reviewer authorization/audit; patient/clinician denial | Requested |
| Support ownership, private screenshots, internal/user reply separation | Requested |
| Overview, health, queue execution/scheduler freshness | Requested |
| Safe errors, incidents, grouped alerts/daily digest/recovery | Requested |
| Analytics/replay controls and pre-transmission canary tests | Requested |
| PostHog actual complete export + independent playback | Awaiting selected project/scoped credentials |
| Archive lifecycle/capacity/deletion and restoration safeguards | Requested; production enablement gated by preceding proof |
| Continuous aggregates/quarter reports/test-clock boundaries | Requested |
| Build/browser/mobile/200%/PWA/localization | Requested |
| Fresh/repeat migration and existing state/financial preservation | Requested |
| Provider ingestion/live alerts/UptimeRobot setup | Awaiting explicit account configuration/operator test |
| Sprint 2 API/component/operator/update handoff | Requested |

Provider sources and current limitations are recorded in provider-compatibility.md.
