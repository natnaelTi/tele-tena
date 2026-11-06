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

> Current provider proof and remaining implementation boundaries:
> [Plan V1 results](live-verification-results-v1.md). Owner Telegram/email receipts
> are confirmed. The settled replay checkpoint is pending; application-wide capture
> remains quarantined. Do not infer production activation from successful fixtures.

# Operations Walkthrough and Sprint 2 Handoff

All Tele Tena Approver users have server-enforced operational super-admin access;
no extra role grant is required. Patients/clinicians see only their own support
reports. This grants no additional clinical/identity-file access. Sensitive support
reads/downloads, config, incident acknowledgement, report export/annotation and
archive access attempts are audited. Never paste private report text into Bugsink.

1. Reviewer: More → Operations Overview. Counts link existing application queues,
   clarification replies and support. Inspect coverage before interpreting zero.
2. System Health: distinguish scheduler enqueue heartbeat from dedicated-worker
   completion. Inspect queue age, notification failure/unknown states and freshness.
   Backup freshness is explicitly unavailable absent trustworthy metadata.
3. User: Help & Tours → Report a Problem. Explicit screenshot only, no automatic
   capture. The current page/draft remains mounted. Follow reference to own history.
4. Reviewer: User Support → report. Triage/assign/priority, separate internal notes
   from reporter-visible replies; resolve. Follow-up channels require user permission.
5. Journey Insights: server outcomes versus browser intents, source/sample/synthetic
   coverage. Saved/incomplete is not presumed confusion or abandonment.
6. Quarterly Reports: calendar quarters in Africa/Nairobi; start inclusive/end
   exclusive. Compile is repeat-safe/versioned, incomplete periods labelled. Export
   JSON and add attributable annotations without changing measured counts.
7. Replay Archive: deliberately unavailable until actual project export, all segments,
   masking and independent sandbox playback are verified. A PostHog link is not an archive.

## Stable Foundations for Sprint 2

`tele_tena.api.operations` exposes reviewer-only `overview`, `health`, `insights`,
`configuration`, `configure`, `archive_list`, `reports_list`, `report_compile`,
`report_detail`, `report_annotate`, `report_export`, `acknowledge`; owner/reviewer-scoped
`support_list/detail/submit/reply/file`; public minimal `liveness` and bounded
`collection`, `events`, `browser_error`. Inspect function signatures before clients
are added. Existing audit/outbox are reused. No competing business state machine.

Native private command tables are versionedv1.53. UI reuses existing workspace,
Dialog, FileUpload, AttachmentPreview, buttons and typography; portal/navigation
expansion is Sprint2. `Operations.tsx`, `SupportDesk.tsx` and operations CSS provide
working baseline screens, not the final exploration UI. All new strings enter the
existing review CSV; no draft translations are approved automatically.

External prerequisites: selected provider projects/scoped credentials, storage and
private player-format proof, owner opt-in receipt test, independent alert launcher,
UptimeRobot account/monitor setup, human language/policy/visual acceptance. No second
browser recorder or invented snapshot converter is authorized as a fallback.

## v1.54 API Handoff

Use existing `tele_tena.api.operations` functions: reviewer `archive_list`,
`archive_retry(id)`, `archive_delete(id)`, `archive_playback(id)`, and
`archive_player(locale)`; authenticated owner `replay_admit(provider_id,window_id)`,
`replay_chunk(id,chunk_id,events,route)`, `replay_loss(id,reason)`,
`replay_close(id)`, `replay_delete(id)`. These are command APIs with server checks,
not generic DocType access. Inspect exact signatures before wiring new controls.
Archive status includes capacity, measured samples, pending/incomplete/retry/loss
and oldest-unarchived timestamps. Never turn null/Unavailable into zero/Healthy.

The client reuses `operations-replay.ts`, strict replay projection and existing
Dialog; the backend reuses runtime/config/audit/storage, native custom queue and
existing notification outbox. No second recorder/provider or competing business
state. Per-tab records deliberately do not reconstruct a cross-tab identity graph.
Sprint2 can consume structured insights/reports/support and these status APIs now;
full portal/heatmaps remain its scope. Raw private replays cannot be public links.

### Investigate a Failed Journey

Inspect server-confirmed outcomes and coverage first; correlate safe attempt/error
references, release/locale/device and actual queue freshness. Open authorized
support context only when needed, keeping internal replies separate. A replay
failure does not invalidate a confirmed business transaction. For an incomplete
archive inspect its safe failure code, chunk loss and export deadline; reviewer
Retry Export is bounded and never restores expired/deleted data. Do not retry
booking/payment commands or adjust balances to repair telemetry. Acknowledge
incidents once, observe deduplicated recovery and keep provider failures distinct
from an application outage. Unconfigured integrations are not healthy integrations.

### V2 Scheduled-Time Handoff

The native gateway has actual provider acceptance/provisional export/player proof.
Use the saved [native resume checkpoint](live-verification-results-v2.md) on/after
8Nov00:28:39EAT; it is not automatically scheduled. Continue native APIs/UI work in
Sprint2 while preserving this exact recording/ledger and disabled production flags.
Do not reuse Completed PlanV1 to create new tests.
