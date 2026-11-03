# Onboarding Scope Submission and Manual Review — 3 November 2026

## Cause and Correction

Onboarding persisted `requested_services` in the general application but did not
create any `Tele Tena Vetting Scope Application` rows. The review queue correctly
reads those independent rows, so an apparently successful application omitted its
service reviews. New final submissions now create both atomically, link each scope
to the exact professional submission, and snapshot only that submission's selected
safe license PDFs. IDs are never copied into the service evidence channel. The
ordinary private professional submission still exposes its other evidence through
existing permission checks. Selected image licenses remain professional evidence;
this existing scope-verification flow requires a license PDF and honestly requests
clarification when one is absent. No document is deemed verified by copying it.

The old Service Scopes button called the direct-grant command even for services
requiring structured vetting. Its `scope_vetting_required` error was obscured by a
generic message. The corrected reviewer flow asks for an audited reason, opens an
existing scope review or initiates one using submitted professional claims, then
requires the normal individual evidence/credential/rubric/decision steps. Draft
service definitions can receive applications but cannot be approved until their
independent medical-lead review passes. Existing applicant drafts are not forced
into submission by reviewers. Explicit legacy services without vetting retain a
working audited direct-grant path. There is no new override of approval guards.

The general application shows individual scope states and exact review links.
Recording a scope decision now also renders the existing success notice. General
approval, each service decision and each language decision remain separate.
Applicants receive existing scope status/reasons/clarification feedback in their
Service Applications workspace.

## Recovery and Preservation

Versioned patch `v1_50_onboarding_scope_intake` creates only missing explicitly
selected, open structured requests. It does not edit existing applications, manual
scope decisions, assessments, files, approvals, names, credentials or financial
records. The original request time is retained separately from the new creation
and recovery-audit time; no historical human approval/consent is fabricated.
Duplicate migrations create no duplicate applications/evidence. Legacy incomplete
claims or missing CVs are not invented: the requested service remains visible with
an explanation and the reviewer/applicant must supply the missing details. Closed
or legacy service definitions retain their existing rules.

No schema columns, package dependencies, provider settings, access switches,
payment-mode settings, passwords, balances or shared framework/Amazon code change.
Fresh bootstrap includes the patch. Evidence copies retain content hashes and
source submission/evidence references in private audit history. Failed completion
rolls back the general application and all scope work in the same request.

## Candidate and Evidence

- Runtime/build/install pin: `d400cb5d9e68d35a2b602f11497f76ce3441a58e`.
- Branch `feat/offline-telebirr-mvp`, draft [PR50](https://github.com/natnaelTi/tele-tena/pull/50), retaining PR49 ancestry.
- Preview: http://127.0.0.1:8017/teletena/ ; `teletena-mvp-presentation.localhost`.
- Primary preview Frappe15.121.2; actual compatibility tests Frappe16.2.1,
  ERPNext16.1.0, Python3.14.2 on the isolated compatibility Bench.
- Private logs/backups/browser fixtures: `/home/frappe/teletena-scope-intake-release/`.

| Requirement | Actual Result |
| --- | --- |
| Full registration creates two independent scope submissions | Built browser with private random email OTP transport; persisted Applicant role, two Submitted scopes and selected license PDFs |
| Scope authorization, decision separation, rollback and manual review | Five real Frappe16 tests pass: owner/reviewer/guest/cross-role file boundaries; separate clarification/rejection; mandatory-criteria denial; manual structured approval with complete synthetic evidence/assessment; legacy grant; retry and failed-completion rollback |
| Professional evidence regressions | Nine pass;100 original protected tables unchanged by repeated existing professional migration |
| Upgrade/repeat preservation | Quiescent restored Frappe16 clone:102 protected tables,18,112 original rows, private/config files preserved;2 omitted requests recovered; repeat migration strictly identical; clone removed, original site not restored/reset |
| Local presentation migration | Complete verified database/public/private/config backup;102 protected tables/18,810 original rows/25 private/config files preserved; strict repeat migration passes |
| Preservation guard tools | Four retained tests pass; new integration test verifies only the expected recovery additions, with original rows unchanged |
| Built reviewer handoff | Two scope links, private license evidence, one clarification/one Submitted, separate general approval and manual third-service initiation pass;390/768/1440 and actual200%, zero page errors |
| Localization | Five exchange tests pass; source delta in `localization/scope-intake-delta.csv`; no approved dictionary changes or invented approvals |
| Build/lint/assets | Locked production build, lint (existing nonblocking warnings), exact asset hashes and private credential scan pass |

A first non-quiescent compatibility verification correctly rejected a concurrent
browser OTP write. It is not counted as preservation evidence. The independent
restored-clone test above replaces that inconclusive attempt without resetting or
altering any original site's records or weakening the guard.

Rendered reviewer states/screenshots and browser outcomes are in
[screenshots/scope-intake](screenshots/scope-intake/README.md). Automated review is
separate from owner/native-language acceptance. No live SMS/email, physical-device
call or real transfer was performed. Unchanged consultation/payment suites are not
rerun for this isolated intake/reviewer correction.

## Selfmade Operator Handoff

This is a **local correction**, not a remote deployment. Selfmade will continue
showing the defect until the update and target-site migration are applied.
Owner-site financial reconciliation checks11 patients/2 clinicians/22 accounts with zero projection, obligation, journal or balance mismatches.

Use the checkpointed [incremental update guide](selfmade-translation-update.md),
now pinned to the runtime above. Observe the actual installed SHA/services first.
This incremental verification targets an existing v1.49 release containing553a619;
older/unrelated releases require a baseline-specific plan. Do not force checkout.
The v1.50 preservation option permits only missing selected requests, their license
snapshots and explicit recovery audits; every original row/file remains exact.
Use strict preservation for the second migration. Do not run a seed, password
reset, payment-mode cutover, provider change or dependency repair. Preserve the
existing Nginx exception, Amazon patch, framework commits and reviewed lock delta.

Reviewer walkthrough after migration:

1. Applications → the clinician → Requested Service Scopes. Each recovered/new
   request has its own status and **Review This Scope** link.
2. Approve/reject the general application independently.
3. Open each scope, review its submitted claims/evidence and complete the normal
   human assessment; approve, decline or request information with reasons.
4. To initiate another review: Service Scopes → approved clinician → service →
   Reason for Manual Review → Continue to Service-Scope Review. This does not grant
   a structured service until that assessment passes. Legacy direct grants remain
   limited to services configured without vetting.
5. Clinician → Service Applications: review individual outcomes and respond to
   clarification through the existing correction/resubmission path. Approved
   scopes still require approved care languages, offerings and published schedules.
