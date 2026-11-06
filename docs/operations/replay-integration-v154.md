# Application Replay Continuation — Implementation Plan

6 November2026. Starting source2f80119; runtime79fcebd. This is additivev1.54,
within Sprint1, before implementation. Provider collection stays disabled.

## One Capture Path

Use the existing pinned PostHog recorder, with no second recorder. Its snapshot
callback feeds a bounded TeleTena gateway after a strict masking projection; it
never sends directly to a provider from the browser. Native admission requires
site flags, matching project proof, a private explicit activation certificate and
individual consent. Guests remain ineligible without an approved anonymous-consent
protocol; public-route capture can run only for an otherwise eligible signed-in
user. Show this coverage gap explicitly rather than treating it as zero traffic.

Each tab gets an independent memory-only recording/window ID. Authentication scope
is checked on admission and every chunk. Logout, actor/role changes, offline,
pagehide and cross-tab invalidation stop capture and clear buffers. Reload starts
a new recording; no raw snapshots or secrets persist in browser storage.

## Privacy Projection

All DOM text/input values are masked. Attributes are reconstructed from explicit
safe types, known public CSS class names and bounded layout numbers. Captured
CSS/URLs/filenames/links/IDs and arbitrary payload fields are discarded. Only owned
release CSS (without URL/import rules) is injected by the server. Documents,
receipts, profile media, clinical notes and consultation media are blocked. SDK
network/console/autocapture/canvas recording is disabled. Unknown formats fail
closed. Server repeats structural validation; no request body enters analytics.

## Gateway, Archive and Lifecycle

Add private capture and chunk indexes (not replay blobs) with authentication scope,
original capture time, expiry, deterministic retry keys and byte/quota counters.
Private bounded files hold only projected snapshots. An operations worker sends
accepted chunks asynchronously through the existing provider adapter. Unknown
outcomes reuse stable insert IDs; capture never retries a business operation.
The archive index is created at admission, so exports do not rely on broad provider
search. Recording leases close after inactivity/max duration; exports wait25hours
from completion and fetch every source with manifest/integrity checks.

Capture admission is separate from archive quota and90-day retention. Storage
failure, missing proof, opt-out, stale session or worker delay reduces coverage
visibly and cannot block care. Raw spool/archives expire from capture time;
provider deletion, tombstones and restore denial remain audited/retryable. Reviewer
playback stays gated until actual selected-project settled proof passes. Existing
structured aggregates/reports persist independently of raw recordings.

## Acceptance

Before marking complete: network-free actual-route canaries, consent/role/tab/PWA
lifecycle, server ownership/idempotency/quota tests, retry/deletion/integrity tests,
fresh/repeat/additive preservation, production build/asset checks, quarterly
boundaries and all original Sprint1 requirements reconciled. Live PlanV1 ledger is
unchanged; settled checkpoint only at/after19:50:28.731UTC. No further notifications.

## Completed Local Evidence — 6 November 2026

Production build source: `47cd8f899e3026d5fc3c80e1c851e0ced5f43387`. Retained preview8017 serves this exact
release. It is deliberately unbound to the private provider file; no collection or
financial/access/provider switch was changed. The private test WSGI gate is confined
to a disposable clone and cannot activate the presentation site.

-14/14 real Frappe16 capture/lifecycle tests,19/19 operations tests and30/30
 communications tests pass sequentially. Additional network-free checks cover
 strict format/export, budgets, restored deletion journal, private checkpoint TAR
 integrity and credential-corrected known403 retry. Unknown I/O is never resent.
-Actual production-built patient/clinician/reviewer routes send projected chunks
 through real authenticated native admission and spool APIs. Dynamic content,
 dialog canaries and SPA transitions are masked; SDK/controller tests separately
 cover sign-out/account changes, distinct tabs, offline/pagehide/reload and sensitive
 browser-storage denial. The SDK's own transport sends nothing. No live egress.
-Three actual-route **local/mock-transport** archives measure134418,134106 and
 133886 compressed bytes. This is a short synthetic sample, not a production
 average:1GiB fits roughly8000 similarly sized recordings before overhead, about89
 per day across90days. The default500/day is a limit, not a promise of retention
 capacity. Measure duration/device distribution, p50/p95 and storage headroom before
 activation; backpressure must remain visible.
-Native enqueued dedicated-worker processing completed; transport was mocked.
 Quotas, bounded spool/index growth, retries/backoff, per-record expiry, provider
 failure, corrupt/missing segments, tombstones, restored/orphan object deletion and
 denied playback were checked. Continuous aggregates and Nairobi quarter boundaries,
 repeat-safe report versions and synthetic/sample/partial-period labels pass the
 operations suite; this does not infer frustration or clinical competence.
-Archive dialog at390/768/1440 and actual Chromium200% zoom (1440physical,
 720CSS/DPR2): Play/Pause, keyboard Escape inside sandbox, focus restoration,
 scrollable content and no private-file requests pass. Rendered compositions were
 inspected: shared cards, typography and dialog remain coherent; masked content is
 intentionally obscured, not a representation of original clinical text. Owner
 visual acceptance remains separate. Screenshots are linked below.
-Built PWA controller/update check, API/private cache denial, offline fallback then
 online deep-link recovery pass. Existing service-worker static-only policy remains.
-Exact final combinedv1.54 Frappe16 fresh installation and repeat native migration
 pass on `teletena-ops-v154-release.localhost`, provider flags off. Populated compatible
 upgrade/repeat preserves original122tables/18984rows; main additive/repeat preserves
 122tables/19311rows plus credential/config/private hashes. Final quiescent populated repeat additionally preserves124tables/19133rows after
 synthetic replay tests. Later capture indexes are additive, with latest
 fresh/repeat and main repeat coverage. No resets.
-Financial reconciliation11patients/2clinicians/22accounts has zero projection,
 obligation, journal or posting mismatches. Build/lint and asset hashes/private
 credential scan pass. No private source maps shipped.

A daemon restart interrupted isolated MariaDB/Redis and one fresh/test attempt.
Only owned isolated processes were recovered, then the failed checks reran and
passed; this was an environment failure, not a weakened assertion. Main development
Bench and the compatible Bench are separate environments.

Private logs and raw synthetic/session artifacts stay outside Git under
`/home/frappe/teletena-operations-proof/`; public-safe screenshots are at
[masked archive screenshots](../screenshots/operations-v154/README.md).

## Actual Provider Checkpoint

After2026-11-06T19:50:28.731Z, original PlanV1 recording export retrieved its complete
source manifest:1source,72events,4061compressed bytes. Independent playback applied
all events, sought both ends and made zero network requests. DELETE returned403;
the owner confirmed changing the same token's permissions, and one explicitly
recorded retry also returned403. Exact readbacks still return200. Both failed
attempts remain charged; no counters/timestamps were reset, no new recording or
notification was sent. No project-proof certificate is issued/bound while cleanup
fails. This is an observed authorization failure, not an unimplemented exporter or
an assertion that PostHog cannot archive.

The new native SDK→gateway→worker path is implemented and locally checked, but the
original fixture does not establish its live-provider compatibility. See the
[bounded amendment proposal](live-verification-amendment-v2-proposal.md).
The third deletion slot is now the last remaining one; successful original cleanup
would consume it. Any subsequent live gateway proof must therefore explicitly
amend deletion/confirmation caps rather than quietly reuse/reset them.
