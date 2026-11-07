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

Backend policy/guest, native backup/status and browser checks are recorded after
implementation. Before screenshot/first exception are retained privately under
`/home/frappe/teletena-operations-proof/terms-navigation/`. Only synthetic/public
screenshots may be committed. No raw support, identity, payment or clinical content.
The saved V2 recording/authorization remain unchanged; its checkpoint is due
8November2026,00:28:39Africa/Nairobi and has not been run early or scheduled.
