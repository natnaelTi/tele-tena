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
