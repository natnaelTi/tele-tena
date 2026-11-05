# Provider Inspection — 5 November 2026

Official sources inspected locally before integration:

- [Bugsink Managed](https://www.bugsink.com/managed/) and
  [pricing](https://www.bugsink.com/): currently15K monthly errors, one user/team,
  retained-event limits apply; selected project's actual limit remains unobserved.
- [Bugsink SDK recommendations](https://www.bugsink.com/docs/sdk-recommendations/):
  errors only, no traces. TeleTena deliberately rejects the optional PII/locals
  recommendation because its collection contract is stricter.
- [Bugsink sourcemaps](https://www.bugsink.com/docs/sourcemaps/): current support
  requires compatible server and private authenticated upload; actual project/API
  token/server compatibility must be observed. Never put maps in public assets.
- [PostHog snapshot API](https://posthog.com/docs/session-replay/snapshot-api):
  metadata is not snapshots; sources/windows must all be fetched, format requires
  post-processing, API is not stable/public. Official guidance says sessions older
  than24hours are safer exports; max20blob keys per request. Exact project contract,
  late data and independent playback remain unverified without selected project.
- [PostHog privacy](https://posthog.com/docs/session-replay/privacy) and
  [JS configuration](https://posthog.com/docs/libraries/js/config): inspect pinned
  implementation/types as well; no unconditional defaults/autocapture/network logs.
- [UptimeRobot Free](https://help.uptimerobot.com/en/articles/11604710-who-should-use-uptimerobot-s-free-plan)
  and [pricing](https://uptimerobot.com/pricing/): current free commercial use,
 50monitors/five-minute checks; HTTP/keyword available. Heartbeat and integration
  entitlement must be checked in the actual selected account, not assumed free.

Historical initial checkpoint: provider credentials were not bound to the local
review site. The owner has since supplied the working private configuration; see
[actual configuration readiness](configuration-readiness.md). It is structurally
valid, including EU PostHog335848 and Bugsink credentials. The site remains unbound;
authorized ingestion/export/monitor/alert verification has not yet occurred.
Public docs do not prove selected-account capability or90-day archive availability.

## Owner Configuration

The owner confirmed a personal alert email and Telegram preference, with no
TeleTena account linkage. Those contact values are stored only in the private
working private configuration, not this repository. All reviewer-role users retain portal access;
that does not subscribe every reviewer to technical alerts. Live tests remain off.
Private source-map token minimum: project-bound `debug-files:upload` where the
selected Bugsink version exposes that capability. Ingestion itself uses only its
project DSN. PostHog snapshot inspection requires `session_recording:read`; deletion
uses a separate `session_recording:write` credential. Verify selected-project API
permissions rather than assuming a token's name proves access.
