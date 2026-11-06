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
