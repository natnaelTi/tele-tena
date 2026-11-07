# Terms, Operations Navigation and Backup Freshness — 7 November 2026

Baseline: sourceff700c04 / packagedfbd3b09d, draftPR52→51. Preserve PlanV1 Completed
and V2 AwaitingSettledRecheck. No provider calls, new provider recordings, alerts,
activation, merge or deployment in this continuation.

## Requested Route/State Checklist

- Public `/policies`: version-bound draft replay disclosure in Terms, provider and
  distinct proposed archive retention in Privacy; no consent inferred from reading.
- Existing authenticated onboarding Terms section: same disclosure before the
  existing acknowledgements; changed source/addendum versions clear old checked
  draft values. Existing immutable acceptance records are never rewritten.
- Guests: **no anonymous Terms acceptance point exists**. Keep them unrecorded,
  including refusal/withdrawal attempts and transitions. No new popup, acceptance
  button, cookie, anonymous identifier or clinical draft store. Account replay
  preferences remain separate and optional; Terms acceptance alone does not enable.
- Reviewer Operations: Overview→Insights first exception, all seven click/deep-link/
  refresh/history transitions; delayed, empty, disabled, unavailable and error states.
  Navigation remains mounted during request/render errors. Patient/clinician/guest
  API denials remain server-enforced.
- Backup freshness: protected complete native-backup metadata only; Current/Stale
  from capture-start age; Unknown for invalid/incomplete/changed source, Unavailable
  when unconfigured. No arbitrary file-mtime inference or privileged scanning.

## Root Cause and Implementation

Production-built8017 reproduced `TypeError: Cannot read properties of undefined
(reading 'reduce')` in Insights. No network or asset failure occurred. `useResource`
retained Overview data while the route selected Insights; the latter synchronously
read `data.events.reduce` on the wrong response shape. Each Operations method now
owns a keyed request/component lifetime. Shared navigation stays outside a local
recovery boundary. HTTP failures show Retry without unmounting valid current data;
unexpected render failures reset only the affected tab. User Support reuses the
navigation and resets list/detail resources by record, with local recovery too.
No cache clear or blanket optional-array fallback conceals an invalid response.

The draft policy addendum is application-owned and versioned alongside the
reviewer-edited immutable source version. The effective Terms/Privacy IDs hash
both original version and disclosure content. Published body/source records remain
intact; current and historic acceptances remain attributable. There is no guest
choice to persist because no guest acceptance step exists. This is an explicit
coverage limitation, not implementation of anonymous guest recording or legal approval.

BackupGenerator's existing complete-backup helper now emits a private
`backup-observation.json` only after all four artifacts pass gzip/TAR/config/SHA
verification. Read-only health verifies site identity, private ownership, manifest
and unchanged file statistics, with age from original backup start (not receipt
mtime or re-verification). It does not hash large archives on web requests. A changed
or incomplete source is Unknown, never zero-age healthy. The operator configures
`verified_backup_directory` and optional `backup_max_age_hours` (default24,1–168).
No source was bound or provider configuration changed on the presentation site.

## Evidence

New focused verification:19Frappe16 rollback operations tests;6Terms/guest tests;
3policy-localization regressions;6complete-backup/status tests;7provider preflight;
localization exchange5/extraction2; frontend lint zero errors and production build.
Actual disposable Frappe16 backup included DB/public/private/config, all integrity
checks and reviewer health Current; Guest detailed health denied. Main remains
Unavailable without configuration. Financial audit is read-only:11patient owners,
2clinician owners,22accounts, zero projection/obligation/journal mismatches.

Real reviewer8017 browser covers all7sections click/direct/reload/back-forward,
delayed first Insights response, recoverable HTTP503 and malformed-response render
failure, empty Insights/support, disabled replay controls and unavailable backup.
Guest/patient/clinician real backend denials pass. No failed assets or unexpected
browser exceptions. No external/replay requests. Terms browser checks390/768/1440,
fake guest acceptance cookies/dismissal still off, real sign-in/out and authorization.
The **onboarding draft response/profile absence/access-switch responses alone are
synthetic**, to display an unfinished account without modifying presentation accounts
or registration switches; current Terms API and old-version validation are real.
No application submitted and no real acceptance/preferences overwritten.

Actual Chromium200% zoom (1440physical/720CSS/DPR2) tested Insights/Terms and keyboard
navigation of7tabs, no page overflow. Screenshots were visually inspected; responsive
navigation wraps, text remains readable and content scrolls. A long effective-version
summary wrapped incorrectly at390; applying existing policy-version wrapping fixed it.
Policy anchors retain heading space below sticky navigation.

The final built PWA test also passed: controller/update and obsolete-cache eviction,
API/private cache denial, offline fallback and online deep-link recovery on the
isolated site, with no provider traffic.

Unchanged application-wide replay canary/lifecycle, quarter-clock/reporting,
retention/deletion/restore, fresh/repeatv1.54 migration and business journeys reuse
[earlier evidence](replay-integration-v154.md); they were not all rerun for these
route/policy/read-only metadata changes. No new DDL/dependencies, financial mode,
provider setting or historical record changes. No new provider ingestion, native
language/legal approval, physical devices or live delivery are claimed.

Private screenshots/logs are retained; a safe public/synthetic subset is linked in
[the verification report](verification.md). Before screenshot/first exception are retained privately under
`/home/frappe/teletena-operations-proof/terms-navigation/`. Only synthetic/public
screenshots may be committed. No raw support, identity, payment or clinical content.
The saved V2 recording/authorization remain unchanged; its checkpoint is due
8November2026,00:28:39Africa/Nairobi and has not been run early or scheduled.
