# Plan V1 — Actual Results and Pending Settled Check

5 November 2026. This supplements the immutable approved
[Plan V1](live-verification-plan-v1.md); the plan itself is unchanged.
Private counters and exact destination references remain in
`/home/frappe/teletena-operations-config/live-verification-plan-v1.json`.
No credentials, raw provider responses or replay payloads are included here.

## Verified Against the Selected Providers

- Telegram discovery found exactly one private chat with the authorized setup
  message; saved its ID without changing any other configuration. Two synthetic
  Alert/Recovery messages were API-accepted and **owner receipt is confirmed**.
- Two original email sends were SMTP-accepted. The owner corrected the recipient
  and explicitly approved a separate two-email amendment. Both amended messages
  were SMTP-accepted and **owner receipt is confirmed**. No more messages are
  authorized. The subscription remains unlinked to any application account.
- A plain-string email subject bug failed locally before SMTP. It was reproduced
  with a mock transport, fixed and regression-tested. The private ledger retains
  those local failures separately from the four actual sends; no unknown SMTP
  outcome was blindly resent.
- PostHog EU project335848 accepted two safe synthetic native events; the exact-ID
  query found both after the owner corrected Query Read permission. No clinical
  records, user identities or arbitrary request bodies were transmitted.
- Bugsink2.6.2 accepted five synthetic errors. Exact SDK-ID lookups verified all
  five and the duplicate-backend grouping probe. Four initial canonical event
  URL lookups returned404 because that API expects an internal ID; lookup by SDK
  ID resolved this without sending replacement errors. Earlier403 and diagnostic
  calls remain charged to the ledger.
- One private synthetic JavaScript/source-map pair was uploaded using pinned
  sentry-cli3.8.2. CLI binary SHA256:
  `c958865f9d4000183509ea21b1f04925d5390de6d8d87386b9e69f2b305070c3`.
  Numeric project ID assembly failed400; the actual project slug supplied by the
  owner resolved it. The fifth browser error maps to the original TypeScript
  filename and **line2**. The owner authorized exactly one additional read to
  assert that line; it succeeded and is now exhausted. No production application
  source maps were published or uploaded by this proof.

## Replay Feasibility — Provisional, Not Final

The pinned PostHog1.446.0 SDK captured one short isolated synthetic session, with
one accepted snapshot upload /37,064 request bytes. Pre-egress interception
expanded compressed snapshots, enforced an automatic-property allowlist and
checked text/input/dialog/document/URL canaries. All fixture text and input values
were masked; document/media elements were blocked. This fixture contains no
existing patient, clinician, support, application or payment data.

Actual export retrieved one blob-v2 source and72 normalized events. It rechecked
an unchanged source manifest, recorded hashes, and produced a4,061-byte compressed
private archive. Independent playback loaded those actual exported events in an
opaque sandbox with zero provider/private network requests. Play/pause/timeline
and malicious captured-script/URL/media tests are separate local checks. The
screenshot in this report is of masked synthetic content only.

This establishes provisional export and independent rendering for the observed
**single-window web blob-v2 format**. It does not establish settled completeness,
production-wide masking, multi-user/multi-tab coverage or a usable90-day service.
Unsupported incremental variants and multiple windows are rejected, not silently
merged or omitted. These are current implementation boundaries, not an asserted
PostHog provider limitation.

### Required 25-Hour Checkpoint

Due **2026-11-06T19:50:28.731000+00:00**
(**6 November2026,22:50:28.731 Africa/Nairobi**).
It has **not run**. Running this command early prints Pending and makes no request:

```bash
cd /home/frappe/frappe/frappe-bench/apps/tele_tena
PYTHONPATH="$PWD" ../../env/bin/python scripts/operations_proof/recheck.py \
  --root /home/frappe/teletena-operations-config \
  --output /home/frappe/teletena-operations-proof \
  --delete-verified-tests
```

The retained manifest must be used; do not initialize a new budget or recording.
This command re-exports all listed sources, checks their stability, renders the
settled artifact independently, then deletes **only this run's newly registered
recording** and verifies404 by exact ID. Failure does not create a success
certificate or blindly resend an unknown deletion. Success writes a private,
player-hash-bound certificate without binding it to any site; removes only this
run's raw proof copies and closes the one-run authorization. Remaining counters
expire48hours after the recheck deadline. No system scheduler/cron was added.

The immediate phase is closed: no more analytics, errors, source maps, recordings
or notifications can be sent by this ledger. The only remaining permitted actions
are the capped settled read/export/deletion checkpoint after its deadline.
`live_test_authorized` is false outside each individual bounded request.

### Budget at Immediate Checkpoint

| Category | Used | Authorized cap |
| --- | ---: | ---: |
| Custom analytics events |2|12|
| Synthetic errors |5|5|
| Recordings |1|3|
| Snapshot uploads |1|300|
| Snapshot bytes |37,064|31,457,280|
| PostHog administrative reads |7|60|
| PostHog exact readback queries |2|6|
| Bugsink schema/inspection reads |3|4|
| Bugsink event reads |10|10|
| Extra original-line read amendment |1|1|
| Error ingest attempts |5|10|
| Source-map protocol requests |6|12|
| Source-map pair bytes |985|5,242,880|
| New test recording deletions |0|3|
| Deletion confirmation reads |0|3|
| Telegram sends |2|2|
| Original email sends |2|2|
| Amended email sends |2|2|

The exact durable ledger remains authoritative if a later checkpoint consumes
additional approved reads. Unused immediate allowances are closed, not permission
for further tests.

## Measured Capacity and Lifecycle Boundaries

One synthetic archive measured4,061 compressed bytes. For arithmetic illustration,
1,000 equally sized recordings would occupy4,061,000bytes; this is **not** a
representative production average or capacity promise. Real route/duration/device
samples and overhead must be measured before choosing production quotas.

Native90-day capture-time expiry, retained deletion journal/restore denial and
bounded storage tests passed on the isolated backend. Provider deletion and the
settled export are pending the checkpoint above; no90-day archive availability is
claimed. Continuous aggregate/quarter reports and prior native lifecycle tests
remain separate from this provider proof.

## Remaining Implementation and Operator Gates

- Full application replay remains quarantined. The synthetic capture adapter is
  not a production application capture pipeline. Application-wide consent/quota
  admission, actor/sign-out/multi-tab lifecycle and all-route masking coverage
  must be implemented and checked after selected-format acceptance. Do not remove
  the gate merely because the project contains a recording.
- Archive export/deletion and sandbox playback adapters are implemented and
  locally tested behind the project-proof gate. No proof certificate is bound,
  site replay/archive flags remain disabled, and capture activation is not
  authorized by Plan V1.
- Production-bundle private source-map generation/upload remains an explicit
  release workflow; only the single synthetic pair was authorized here.
- Bugsink automatic email/chat/webhook alerts were confirmed disabled by the owner
  for this test. The owner must restore the intended provider alert configuration
  deliberately before activation; this task did not change provider settings.
- UptimeRobot account/HTTPS monitor setup remains a separate manual operation.
- Owner UI acceptance, native-language/policy approvals and production activation
  remain separate. No physical-device call, live patient notification, real
  payment or remote deployment was performed.

Native operations/support functionality and the prior build's preservation,
financial and scheduler evidence are retained. This report supersedes older
statements that all projects are absent or that no provider calls have occurred.

## Local Regression Evidence for This Continuation

-19/19 isolated real Frappe16 operations tests;30/30 communications tests.
-7 private-preflight,6 durable-budget/amendment/phase tests,3 strict replay-format,
  2 complete-export,2 trusted-frame and2 email-composition tests.
-5 localization exchange and2 extraction tests. Source-only export now8,990 rows;
  approved reviewed dictionary is unchanged, with zero invented approvals. Archive
  dialog/player labels use the same reviewed-only fallback mechanism.
-Independent playback applies all72 actual exported events, seeks to both ends,
  and makes zero network requests. Separate hostile synthetic markup test denies
  captured scripts, private URLs, media and active account controls. A translated label cannot close the trusted player script.
-Frontend production compilation passes. Lint retains existing warnings with zero
  errors. Fresh/upgrade/repeat-migration and financial preservation evidence from
  the unchangedv1.53 schema is reused; this continuation adds no schema migration,
  provider binding, balances or business-data mutation.

[Masked synthetic playback screenshot](../screenshots/operations-provider-proof/README.md).
