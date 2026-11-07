# Sprint 2 — Reviewer Operations Portal

Requested 7 November 2026. Based on Sprint 1 source cf53c4f / build 4e5b126,
draft PR52→51. No activation, provider tests, remote deployment or business-data
mutation is part of this sprint. V1 is closed; V2 remains separately bounded and
time-gated. Preserve Terms acknowledgement and unrecorded guests.

## Implementation Checklist (Requested Until Verified)

- Reconcile site binding, enabled preferences, scoped historical proof and measured
  runtime health. Never infer current ingestion or delivery from credentials/proof.
- Shared desktop sidebar / responsive navigation for all seven destinations,
  plus Applications and Service Applications. Preserve resource isolation/recovery.
- Overview actionable queues; environment, observation time and freshness first.
- Bounded server-filtered journey/period/locale/device/payment/source data, attempts
  with explicit denominators, completion window and coverage; no invented heatmaps.
- Health separates readiness/execution/queues/backup/providers/notification states.
- Replay search/state/capacity/expiry; verified-only existing private playback.
- Readable quarterly dates/partial periods/measured findings/comparison/annotations/export.
- Grouped settings explain saved versus effective state and prerequisites.
- Support scan/filter/assign/priority/status and explicit private versus visible replies.
- Persisted synthetic review data only on isolated site; no provider traffic or
  changes to existing presentation users/records. Real empty/disabled/error states.
- Server authorization/audits, backend and production browser regressions, responsive
  390/768/1440 and actual 200% zoom, localization/PWA/assets, financial preservation.

## State and Data Contract

Zero is an observed count; no eligible data is not zero-percent completion. Insufficient
sample is not abandonment. Saved/resumed/blocked/completed are separate bounded
attempt states. Browser interactions and confirmed outcomes stay separate; counts
are not unique people. Unknown, disabled, unconfigured, stale and error are distinct.
Retain raw event identifiers and private report text server-side. No new capture,
heatmap data, telemetry provider, chart dependency or credential UI is authorized.

The existing native operations tables, report compiler, support/outbox/audit,
archive player and site configuration remain authoritative. Additive query APIs
project safe reviewer summaries; no competing state machine. Synthetic review is
explicitly labelled and excluded from production analytics, not silently substituted
for live results. No new database tables are expected for this UI/query sprint.

## Evidence

Pending implementation and focused checks. See Sprint 1 matrix for inherited
coverage and operator/policy/storage/UptimeRobot prerequisites, which this redesign
does not close.
