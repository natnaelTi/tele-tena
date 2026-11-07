# Bounded Provider Verification Plan V1 — Awaiting Owner Authorization

No provider call in this plan has been executed. `live_test_authorized` remains
false. The only live call already authorized/performed was one Telegram getUpdates
retrieval; zero matching private setup chats, no changes, no sends.

## Boundaries and Destinations

Use only new synthetic test data in an isolated proof fixture, never existing
patient, clinician, support, receipt or professional-application data. No production
collection/activation, Selfmade change, account creation/linkage, reseed, payment,
provider setting change, webhook change or public sharing link.

- PostHog EU project335848: ingestion `https://eu.i.posthog.com`; administrative
  requests only `https://eu.posthog.com`. Keys remain server/private-runner-only,
  except the project's nonadministrative ingestion key required by the isolated SDK.
- Bugsink: the HTTPS host and project already in the private working configuration;
  exact nonsecret host/project endpoint manifest is private alongside that file.
  No complete DSN or token is included in this document.
- Telegram: `https://api.telegram.org`, stored dedicated bot and the uniquely
  discovered/owner-confirmed private chat. No message without that prerequisite.
- SMTP: existing private TeleTena SMTP configuration; destination is exactly
  `owner_alert_email` in the working file, unlinked to an account. Do not substitute
  demo reviewer addresses. SMTP completeness is checked locally first; no SMTP
  credential or sender change.
- UptimeRobot: **no calls or monitor creation** under this plan. Separate operator setup.

A private manifest at
`/home/frappe/teletena-operations-config/live-verification-plan-v1.json` records
actual destination metadata without credentials, the cap counters and these message
bodies. Its approval must refer to V1. Credential presence proves no scopes or access.

## Phase 1 — Restricted Connectivity and Synthetic Error/Event Proof

1. Inspect selected Bugsink canonical schema/capabilities using at most4 GETs. Do not
   list other projects or alter alert rules. If automatic provider notifications would
   create additional unbounded emails, stop before ingestion and report the dependency.
2. Send at most **12 allowlisted synthetic analytics events** (including retry/dedupe
   probes) to PostHog capture. All use new pseudonymous test IDs, synthetic=yes and
   review environment; no accounts or captured real pages. Confirm durable readback
   through at most6 tightly filtered project queries. No broad event exports: use the
   new test insert IDs only. If the read key lacks the required query permission,
   report it; do not obtain broader scopes or list unrelated activity automatically.
3. Send at most **5 synthetic errors** to the configured Bugsink project: browser,
   backend and background-job categories, one grouping/retry probe, one optional
   source-map probe. Maximum10 ingestion HTTP attempts total; no blind resend of an
   ambiguous event. Safe fixed messages/classes/release/route templates only.
4. Bugsink readback: at most10 GETs, filtered to the new test group/event IDs. Inspect
   grouping and sanitized payloads in memory; persist only allowlisted results/counts.
   SDK flush/HTTP acceptance alone does not establish stored ingestion.

No quota/billing plan changes. Twelve is a custom-event ceiling, not a claim about
all provider-internal billable SDK events. No mass cleanup of analytics/error history;
label these synthetic records and retain their test-ID manifest. Do not delete an
issue that could contain another event.

## Phase 2 — Masked Replay Feasibility (Not Yet Implemented/Verified)

Prepare an isolated loopback fixture at
`http://127.0.0.1:8127/ops-proof-v1/`, using the pinned existing PostHog SDK, not a
second recorder. This is a synthetic page, not a production route, and holds no real
session cookies, profiles or business records. No production replay flag changes.

Capture at most **3 recordings**, at most90seconds each (270seconds total), with
at most300 snapshot-upload HTTP requests and30MiB total transmitted recording data.
Stop rather than increase these limits. Exercise:

- Public/directory → onboarding/booking/Requests layouts and dynamic dialogs.
- Synthetic filename, document-preview, error-message, identity, receipt and clinical
  canaries; all entered/displayed values masked, private visual elements blocked.
- Consultation placeholders only: no microphone, camera, canvas or real call/media.
- Reviewer fixture, SPA navigation, sign-out/reset, separate synthetic user/tab and
  offline recovery. Stop if a new unexpected recording would exceed the3-ID cap.

Intercept/decode outgoing requests **before egress** and block on any canary, raw
query, filename, private URL, cookie/token or unapproved automatic property. An
undecodable payload is a failure and must be blocked. No raw console/network bodies,
performance tracing, unrestricted autocapture or media capture. Content must remain
usable if capture fails. Existing quarantined policy is not called a working recorder;
a reviewed fixture-specific adapter is required before any replay transmission.

Administrative replay operations: at most **60 GETs total** across the three known
new recording IDs, including metadata, complete source/window manifests and every
required blob/segment; max20 blob keys/request. No unrelated recording list/download.
Cap10MiB compressed per recording and30MiB private proof storage. Respect429/backoff;
no busy polling. If completeness requires more requests/bytes, stop and report it.

Export early for a provisional proof, then repeat source/completeness inspection
at least25hours after original capture (official guidance recommends older than24h).
Do not falsify capture timestamps or claim the initial export is settled. The
approved request budget covers this delayed recheck without another authorization.

Normalize the actual format behind the versioned provider adapter; reject missing,
malformed, duplicate or unsupported segments. Verify checksums and masking. Prove
playback with all provider/network access blocked, source recording unavailable and
private application routes unreachable. No scripts, forms, live authenticated actions,
private file access or remote asset fetching. Record required format/player versions.
Metadata or a PostHog link is a failure, not archive success.

Only if export + independent playback pass may the project-specific implementation
be considered locally verified. Production archive enablement remains a separate
acceptance decision. If format support is missing, continue code/testing inside this
scope while remaining visibly unavailable; do not claim a provider limitation before
observing one.

## Phase 3 — Source Maps, If Supported

At most **one isolated synthetic bundle/map pair**, total5MiB, at most12 standard
Sentry-compatible upload/discovery HTTP requests. Verify selected Bugsink version,
token debug-files capability and standard upload schema first. Use a private pinned,
checksum-verified tool in isolated staging; no shared dependency installation.
Inject matching debug IDs in the isolated proof bundle only. No maps in public assets,
no modification of the running preview package. Use the fifth error from Phase1 to
prove mapped source/line resolution. If current browser-envelope wiring lacks the
required frames/debug metadata, implement/test that locally before this probe; an
uploaded map alone is not a working frontend source-map integration. No tool/API
compatibility assumption or extra upload when the budget is exhausted.

## Phase 4 — Owner Alert and Recovery Receipt

Prerequisites: unique confirmed private Telegram chat; SMTP ready; owner's approval
of this plan. Fresh isolated operations state contains only the synthetic incident
`synthetic_verification_no_real_incident`. Use the existing adapters and durable
claim/dedupe logic. Do not enable alerts on the populated presentation site.

Maximum **2 Telegram messages and2 emails** (one alert plus one recovery), to the
private chat and owner_alert_email only. Repeat processing should produce zero
additional sends. Unknown outcomes are not blindly retried.

Exact plain-text bodies, identical on both channels:

> TeleTena Alert: synthetic verification no real incident. Open your authenticated Operations Overview.

> TeleTena Recovery: synthetic verification no real incident. Open your authenticated Operations Overview.

Email subject for both: **TeleTena Update**. Existing branded HTML wraps the same
neutral text; no receipt, clinical, profile or support content. Telegram API/SMTP
acceptance is recorded separately from the owner's actual receipt confirmation.
No SMS, daily digest or additional provider-generated test alerts are authorized.

## Cleanup, Limits and Restoration

After successful independent playback, delete only the **up to3 newly generated test
recordings** identified by the private manifest (maximum3 DELETEs plus3 exact-ID
GETs to check absence). No project-wide deletion, source-account deletion or public
share changes. Stop on an unexpected ID or unclear permissions. Test local capture+
90day expiry and restore tombstones through the isolated clock, never by changing
production/provider timestamps. Remove only new proof replay objects after checks;
retain nonsecret manifests/checksums and native audit/report evidence.

After approval, temporarily set only `live_test_authorized` true for the bounded
runner, bind credentials only inside the isolated proof environment and restore false
in finally/cleanup (including between capture and the25h recheck). Preserve every
other populated value, owner_account empty,600/700 permissions and original site flags.
No global capture/alert/export switch changes. Stop isolated fixture processes and
restore their temporary settings. Retain the protected working configuration;
never copy the template over it.

Record actual event/recording/byte/request counts and failures. On401/403, unexpected
host/redirect, canary failure, insufficient scopes, unsupported format or exhausted
budget, stop that phase; continue independent local fixes. Additional destinations,
recipients, scope expansion or higher quotas require a materially revised plan.

## Current Decision

**Awaiting owner approval of Plan V1.** No provider result, delivery receipt, raw
archive availability, capacity estimate, source-map compatibility or UptimeRobot
configuration is verified by credential presence. No calls under Phases1–4 have run.
