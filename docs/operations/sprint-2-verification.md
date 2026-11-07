# Reviewer Operations Portal — Local Review Candidate

Verified 7 November 2026. This completes the bounded portal implementation for owner
review; it does **not** close Sprint 1 or establish production collection/90-day archival.

Installation / production-build source:
`39816601c9d21d59f8758a08efbdda4c723069e4`.
Later source commits contain documentation, screenshots and test-harness corrections
only. The runtime source matches this pin. Both previews serve the same build.
Release JSON SHA256:
`d69c77ba54f0eedf43fb4c3a5b691677843f38daba907b804da4f78af6e1e70e`.
Frontend lock and reviewed translation dictionary are unchanged from PR #52. Schema
remains v1.54 / app 0.1.0: no DDL, patch-list or dependency change in this sprint.

- Main: http://127.0.0.1:8017/teletena/admin/operations
- Isolated populated scenario: http://localhost:8023/teletena/admin/operations
- Scenario uses `localhost` deliberately, separating its cookies from main 127.0.0.1.
- Existing main reviewer credentials remain in the existing protected presentation
  account manifest. No password or account reset.
- Scenario credentials: `/home/frappe/teletena-compat/bench/sites/teletena-ops-v154-release.localhost/private/operations-portal-review.json`, `accounts.reviewer` (600).
  OTP transports are intentionally disabled there; use its email/password entry.

## Sprint 1 Reconciliation

See [actual web/worker observations and badge explanation](sprint-1-runtime-reconciliation.md).
The populated provider test file is valid but **not bound to the presentation site**.
Stored analytics/errors/alerts are on in review; effective delivery is inactive
without credentials. Replay/archive are off. Do not conflate these observations with
all switches being off or all provider projects being absent. A completed read-only
probe on the actual dedicated worker confirmed the same configuration as the web.

The UI now separates configuration, saved enablement, effective eligibility, measured
outcomes and dated verification scope. Source maps are unverified for this application
build even though a synthetic pair was verified. Mobile effective eligibility also
requires the enabled Telegram channel and an owner destination. No page load tests a
provider. **Disable/review saved external switches before any separately approved
credential binding**, including binding a file to supply backup metadata.

## Implemented and Verified in the Running Main Preview

- Coherent desktop sidebar, compact styled native section selector on mobile/tablet;
  Applications/Service Applications remain visible. All seven original URLs retained.
- Overview separates professional and submitted/resubmitted service-scope counts,
  including clarification replies and open assistance requests; it prioritizes current-queue window and processing
  freshness; detailed diagnostics moved to Health and expandable sections.
- Server-filtered journey/period/locale/device/payment/source/synthetic scope with
  explicit attempt denominators, sample/coverage, descriptive state bars and events.
  No eligible cohort yields no completion percentage. Stage counts are independent
  events, not unique people or a fabricated conversion funnel. The completion
  definition is visible for each family. Saved/interrupted is not abandonment.
- Health separates database readiness, executed-job observations, queue visibility,
  backup sources, notification outcomes and integration evidence. Missing execution
  is Not Observed; old execution is Stale. Known zero backlog has no queued-job age;
  unavailable queue visibility is not zero. ProviderAccepted is not receipt.
- Archive states, readable sizes, expiry, bounded server search/pagination, capacity
  and qualified coverage; existing authorized sandbox playback/retry mechanisms.
- Quarterly dates in Nairobi, partial labeling, measured attempts/events/support,
  supported-period comparison, coverage limitations, annotations and audited export.
- Grouped collection/alerts/storage/advanced settings preserve optimistic revision
  checks; saved preferences remain distinct from effective runtime capability.
- Support queue filters/ownership/age/priority and detail triage, notes versus replies.
  Assigning/status changes have audit records. Visible replies reuse existing outbox
  and preferences. No general clinical/evidence permission was added.

Main actual-state checks are read-only, including real empty/disabled/unconfigured
states and actual reviewer access plus guest/patient/clinician denials. No main
support record, setting, private preference or financial transaction was changed.

## Verified in Isolated Real-Backend / Controlled Tests

The persisted scenario is on `teletena-ops-v154-release.localhost`, separate database
and private files, served by a fixed loopback-only WSGI harness. Four journey families
have20 bounded synthetic attempts in total, with completed/interrupted/saved/resumed
states; application cohort8, completed within24h5, descriptive62.5%, small-sample warning.
There are4 real native support cases, stale scheduler/worker observations, partial
coverage/drop counters and partial/completed synthetic quarterly reports. The
reviewer can use real APIs to assign, reply, resolve, compare and export.

The scenario explicitly marks synthetic data and defaults Insights to include it;
main defaults to exclusion. Synthetic report compilation is server-restricted to an
explicitly marked isolated site and cannot relabel production metrics. No booking,
clinician approval, wallet money, receipt or actual consultation is manufactured.

One **locally generated**, two-event masked replay object exercises the existing
sandbox. It is not a browser/provider recording or selected-project export proof.
The local harness substitutes only its playback gate, blocks every provider
transport and cannot activate capture. All receipt/evidence access remains real
authorization. The initial fixture incorrectly used an event digest for its compressed
object; the existing integrity check rejected it. Only that new local fixture was
corrected to its actual compressed-byte digest; no integrity guard or V2 record changed.

A browser pass found a real support race: remounting triage controls on every reply's
modified timestamp discarded a just-selected status. The form now remains mounted;
older detail responses cannot overwrite newer versions. A delayed900ms real response
regression verifies resolution through this race. Concurrent reviewer triage changes
are rejected using expected saved values; explicit Reload Saved Triage preserves the
response draft. Reply submission preserves triage atomically under the existing lock.

Focused results:
- Frappe16.2.1/ERPNext16.1.0/Python3.14.2:9new portal tests and19operations regressions.
- Localization exchange5 + extraction2; approved dictionary unchanged.9412source rows,
  5094missing per locale; no human approvals/imports invented. New strings and source
  hashes are in `localization/operations-portal-delta.csv` and full exchange CSV.
- Production build, TypeScript and lint pass (zero errors; pre-existing warnings).
-311packaged artifact hashes verified; exact20private site credential scan plus the
  actual private operations-provider tokens/DSN scan passed without printing values.
- Full built browser: seven click/deep-link/refresh/Back/Forward routes, delayed
  Insights, filter changes/collapse, controlled HTTP/render recovery, real role denial,
  triage/reply/resolution race, owner/internal-note separation, report comparison/export,
  disabled/empty states and isolated playback. No external provider requests.
-390/768/1440px, keyboard native section selection, reduced motion; English/Amharic/
  Afaan Oromo rendering and long-label stress. New copy has truthful English fallback,
  not native-language approval. Screenshots visually inspected against the existing
  TeleTena tokens/components; owner visual acceptance remains pending.
- Actual Chromium200%:1440physical/720CSS/DPR2, all seven sections, reachable settings,
  sandbox Escape/focus restoration. Additional long-label stress measured195CSSpx.
  This is automated desktop browser evidence, not physical-device acceptance.
- Existing Terms browser regression passes: old acknowledgements/cookies/dismissal do
  not enable replay; guests unrecorded, no extra popup/button, sign-out/role denials.
- Built PWA controller/update/obsolete-cache eviction, API/private-cache denial,
  offline fallback and online deep-link recovery pass on the isolated transport.

## Preservation and Reused Evidence

Read-only comparison:12protected file/table hashes unchanged, including private
provider configs/credentials, appointments, policy acceptances, collection preferences,
Ops settings, wallets, accounts and journal lines. Presentation payment mode remains
Offline.11patient/2clinician/22financial-account reconciliation: zero mismatches or
unbalanced journals. No scenario reseed or setting/mode changes on the presentation
site. The new fixture is idempotent; repeats retain its accounts/dates/history.

No schema change: fresh/repeatv1.54 and populated-upgrade evidence is inherited from
Sprint 1. Unchanged individual/couples/media/end/consent/financial journeys, extensive
masking/retention clock/provider proofs are reused transparently from Sprint 1. This
sprint did not repeat physical calls, live OTP/delivery or the complete clinical suite.
Main observed runtime is Frappe15.121.2/ERPNext15.121.6/Python3.12.3/Node22.23.3;
compatibility backend checks use the separate Frappe16 environment.

## Remaining Launch Prerequisites — Not Closed by This Portal

- V2 remains AwaitingSettledRecheck; original V1 is closed. Due8Nov2026 at00:28:39.095385
  Africa/Nairobi. No recheck/cleanup ran early and none is automatically scheduled.
  Use only the saved command/ledger after inspecting its state at the due time:
  [V2 results and exact resume](live-verification-results-v2.md).
- No new live events/errors/recordings/maps/messages, credential changes or production
  activation. Prior provider proof/confirmed receipts are inherited, not re-sent.
- Approved production archive volume/capacity/backup-expiry policy and explicit activation;
  a configured90-day policy and local fixture do not establish operational90days.
- UptimeRobot HTTPS checks and approved persistent independent alert/Operations worker
  launcher; actual monitoring/heartbeat entitlements must be checked in the account.
- Recurring verified backup-source pointer. Unavailable is correct without one.
- Owner visual/assistive-technology/physical-device acceptance, genuine language review,
  approved policy wording/consent model. Guests without an acknowledgement remain off.
- Public heatmaps unavailable: there is no approved public coordinate dataset. Private
  screens remain out of scope; this sprint adds no capture to manufacture heatmaps.

## Short Reviewer Walkthrough

1. Open main Overview: inspect window/freshness and queues; visit System Health's
   integration cards to distinguish unbound site configuration from past test proof.
2. Sign into the isolated URL with its protected reviewer entry. Overview shows actual
   synthetic support counts and stale processing. Application/service queues keep
   their existing destinations; they are not fabricated applications in this scenario.
3. Insights: application 8 starts / 5 completions; expand Advanced Filters, choose locale or another family,
   switch scope to exclude synthetic and see the honest empty state. Collapse retains
   filters. Completion means submission here, not clinician approval.
4. Support: filter/assign a case, save triage, add a Private Reviewer Note, then choose
   Reply Visible to the Reporter. Resolve and reload. Fixture follow-up is off and
   transports disabled, so this does not send live email/SMS.
5. Reports: open2026-Q4, inspect Partial Quarter and measured findings/attempts, compare
   Q3 with its different coverage, export; add nonclinical interpretation separately.
6. Archive: inspect disabled capture/capacity; play the local masked object, seek and
   close with Escape. This does not run the V2 provider experiment.
7. Settings: inspect groups/effective status; use the isolated site for trial changes.
   Do not enable production capture or bind the provider file on main during review.

[Acceptance matrix](sprint-2-acceptance.json) · [screenshots](../screenshots/operations-portal/README.md)
· [configuration/operator guide](configuration.md) · [future Selfmade checkpoints](../selfmade-operations-portal-update.md).

## Local Restart and Recovery

From the repository, use `../../env/bin/python scripts/local_review.py status` and `../../env/bin/python scripts/local_review.py start` for the owned main preview. Do not start a second Bench or change shared services.

The isolated scenario retains its private database and account manifest. If port 8023 is stopped, run `/home/frappe/teletena-compat/bench/env/bin/python /home/frappe/teletena-operations-proof/sprint2/start-scenario.py`. This guarded local helper refuses an occupied port and does not reseed. Preserve its existing manifest and database.
