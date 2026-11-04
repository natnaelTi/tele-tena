# Application Workflow Revision — Requested Scope

Owner direction: make scope applications a tracker and focused detail journey;
replace repeat full-form clarification with typed requested-information dialogs;
provide audited reviewer-assisted entry using clinician email authorization.
No automatic service approval, identity-reviewer expansion, consent fabrication,
new clinical modules or remote deployment.

| Role / Route | Required Behavior | Acceptance |
| --- | --- | --- |
| Clinician /clinician/vetting | Tracker, statuses, search, current/history, new application entry | Requested |
| Clinician /clinician/vetting/:id | Focused claims, typed documents, feedback/timeline | Requested |
| Clinician detail / response dialog | Only explicitly requested fields/files; save errors retained, retry-safe resubmission, acknowledgement channels | Requested |
| Reviewer /admin/vetting | Primary navigation, searchable status queue | Requested |
| Reviewer /admin/vetting/:id | One application, grouped facts, current typed evidence, human decision | Requested |
| Reviewer Request Information | Choose requested fields/documents; reason; immutable request history | Requested |
| Onboarding / assisted entry | Save existing progress, select preferred scopes, request email assistance | Requested |
| Reviewer /admin/assisted/:case | Recorded email authorization, full private claims/evidence, declared languages, audited assisted submission; then separate general/scope/language decisions | Requested |

Clinician: Tracker → Application Details → Requested Information → focused dialog
→ Submitted for Review → updated tracker/acknowledgement.
Reviewer: Scope Applications → one detail → read current grouped evidence → decide
or request specific items → receive resubmission with current files in their typed
fields and preserved historical snapshots.
Assistance: verified clinician requests help → supplies email authorization/details
→ reviewer records private authorization source and received date → enters claims
and evidence → submits with explicit email-based declaration/policy provenance →
normal separate human decisions. Owner selected reviewer submission with recorded
email authorization; no forged clinician UI clicks or automatic approvals.
