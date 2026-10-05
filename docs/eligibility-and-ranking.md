# Request eligibility and ranking specification

## Hard eligibility matrix

| Rule | Immediate request | Scheduled request | Failure code / handling |
|---|---|---|---|
| Enabled clinician account and active manual general approval | Required | Required | `clinician_not_approved`; no recipient |
| Approved active decision for exact service scope; mandatory evidence/credential and restriction checks for catalog-required scopes | Required | Required | `scope_not_approved` / `credential_missing` |
| Active offering under that exact scope and published schedule | Required | Required | `offering_unavailable` |
| Exact required language and supported audio/video format | Required | Required | `language_mismatch` / `format_mismatch` |
| Adult population eligible for this pilot | Required | Required | `population_unsupported` |
| Service location/jurisdiction and practitioner authorization | Required when defined by service | Required when defined | `jurisdiction_mismatch` |
| Full fixed duration plus offering buffers fits an interval, exception, and conflict-free clinician/patient timeline | Feasible start in configured request window | Generated bookable start in requested range and notice/horizon | `no_feasible_time` |
| No conflicting booked or pending reservation across offerings/affiliations | Required | Required | `calendar_conflict` |
| Fresh clinician available-now heartbeat | Required | Not required | `presence_stale` |
| Patient must-have accessibility, format, language, or budget limits | Must match exactly | Must match exactly | Never silently relaxed |

Missing mandatory data is a non-match. Profile preferences/ranking never relax a hard rule. Patient requests do not store inferred diagnoses. Service/topic suggestions are navigation aids only.

## Ranking after eligibility

Sort only the hard-eligible set. Use transparent lexicographic factors: request-specific approved expertise; requested preferences; earliest feasible start; separately reported response reliability and completed-encounter experience with explicit sample counts; then fair exposure for newly approved clinicians. No single quality number is exposed. Reliability uses only requests fetched by an active eligible clinician and separates responsible declines, clinician-caused failures, patient actions and platform failures. New clinicians are not hidden for having no history. Patient satisfaction is never a clinical outcome or credential proxy. Ranking is not purchasable and not proximity-based for remote sessions.

## Explainability and privacy

Applicants see which of their required setup items are missing. Clinicians see their own readiness reason codes and links. Patients see matching progress and constraint-preserving alternatives. Approvers see reason codes and routing history, not additional request narrative unless their operational permission explicitly requires it. Non-selected clinicians cannot enumerate requests/offers. “Enqueued” and “inbox fetched” are separate events; neither proves a human read the notice.
