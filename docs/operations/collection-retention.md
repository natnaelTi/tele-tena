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

# Collection and Retention Contract

Version operations-v1. The executable allowlist is `tele_tena/operations/contract.py`;
[event dictionary](event-dictionary.json) is its review export. Browser intent and
server-confirmed outcomes are separate event names. Stable transaction references
are site-keyed HMACs, never raw patient/appointment identifiers. Successful outcomes
are deduplicated in the same transaction; telemetry never retries business actions.
Guest browser analytics is currently **disabled**. No guest-to-account identity graph
is constructed. Authenticated optional browser events require an affirmative stored
preference. Bounded 24-hour attempt UUIDs are nonclinical metadata only. Sign-out/account
change clears the collector's in-memory buffers and changes the actor domain.

| Data | Collection / Access | Retention / Coverage |
| --- | --- | --- |
| Native outcome events | Enumerated properties, reviewer aggregates; no clinical text | 30 days by default, configurable7–90; only delete after aggregation |
| Browser interactions | Explicit preference, safe routes and enums, no autocapture | Same structured-event policy; 100% of eligible attempts before configured sampling/quota |
| Daily aggregates | Safe supported dimensions, exclude labelled synthetic/staff by default | 1,096 days |
| Attempt summaries | Saved/resumed/blocked/completed;24-hour completion window | 365 days; a pause is not abandonment |
| Error envelopes | Opt-in site flag; app filenames/lines and error classes only | 30 days; bounded private spool, no locals/bodies/console |
| Support | Explicit user text/screenshot, owner and reviewer only; private audited reads | No automatic support deletion; policy decision remains outstanding |
| Replay | **Disabled and unavailable** pending project proof; no capture in this release | Desired90days from original capture; synthetic local lifecycle tested only |
| Replay objects/indexes | Dedicated private filesystem; checksum, captured-at, format metadata | Capture-time expiry and durable deletion tombstones; provider deletion not connected |
| Reports and annotations | Reviewer-only, measured counts separate from interpretation | Versioned; retained independently of raw replay |
| Business, clinical, financial and audit records | Existing authorization and retention | Unchanged by telemetry deletion |

Consent notice is a draft operational notice, not approved legal text. Optional
collection failure cannot block care. No private draft, medical content, contact,
filename, receipt reference, evidence, media, cookie, authorization header, query
string or unrestricted request/job payload is permitted in telemetry. Support text
and attachments remain native private data, never analytics/error payloads.

## Limits and Backpressure

Defaults:20,000 events/day;100,000 total raw rows;500 errors/day;500 replay/day
(desired, capture unavailable);1GiB private archive;10MiB/recording;500 export queue;
5 retries;100 alert messages/day. Free disk guard200MB. Export buffer25hours;
provider-specific export and playback remain gated. Events dropped at limits have
visible counters; collection loss is not zero traffic. Server outcomes are minimized
operational data, independent of optional browser preference. Current public replay
and analytics coverage is zero; no full-coverage claim is made.

Raw replay deletion uses original capture time and a private append-only tombstone
journal independent of database restoration. Restore must retain that journal and
rerun retention before enabling exports; provider deletion remains Pending until
credentials/adapter proof. Backup copies expire under the operator's backup policy;
this sprint does not claim immediate erasure from retained backups. Reports do not
extend raw retention. No measured production replay capacity estimate is available:
no actual project recordings exist. Archive status returns null estimates rather
than invented bytes/session. Measure completed masked recordings and publish p50/p95,
compressed bytes/day and90-day projection before enabling capture.

## v1.54 Limits and Restore Rules

Current defaults add5000chunks/day,500pendingchunks and1000chunks/recording;
500recordings/day and10MiB/recording remain independent caps. A recording lease is
bounded to15minutes. Export waits25hours from completion/last-delivery; maximum
20sources/40seconds per attempt, retry budget5, exponential1/2/4/8/16hour delays.
Missing/lost chunks and unsupported formats remain Incomplete, never Verified.
All raw objects expire from original capture+90days; source deletion or owner
withdrawal records tombstones. Aggregate/report/support/business retention is
separate. Consent withdrawal drops unsent chunks, including closed tabs; already
transmitted history requires the explicit deletion lifecycle and cannot be recalled
from a viewer's memory.

Before restoring any database/private backup, preserve the latest deletion journal
and never replace it with an older copy. Merge validated tombstone records, then
run the stopped-site retention recovery command in the deployment guide. Bounded
orphan scans continue in normal jobs. Backup copies require an operator-approved
expiry policy; no claim of immediate physical erasure from retained backups.
