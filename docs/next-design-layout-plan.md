# Next design update layout plan

This plan records the composition choices before the wider presentation pass.
The calendar save regression is fixed and verified independently before these
layout changes. Existing API authorization, transaction behavior and records
remain authoritative.

| Screen | Layout decision | Primary action and hierarchy | Responsive behavior |
|---|---|---|---|
| Public home and clinician entry | Keep marketing content inside the established 1200 px measure; prioritize headline, care entry, privacy explanation and clinician invitation. | Find care is primary; explain the journey before secondary information. | Stack hero and original illustration; keep the public navigation and footer compact. |
| Phone, email, OTP and password access | Preserve a narrow centered authentication surface and make the selected channel explicit. | One Continue/Send code action; verification replaces entry; password appears only after choosing it. | Keep one field per step and retain visible focus with mobile keyboard open. |
| Patient onboarding | Keep the guided stages short, resumable and separate from discovery. | One or two related questions and a clear Back/Continue action. | Single-column steps; no full-history gate before care discovery. |
| Clinician onboarding and reviewer queues | Separate clinician evidence and requested scopes from reviewer decisions. | Submission is distinct from manual application and scope approval. | Reviewer rows become readable cards on narrow screens; resume access stays authenticated. |
| Patient home and discovery | Give the next real appointment, care search and compact balance summary separate visual weight. | Find care remains the main action; wallet detail stays in Payments. | Cards stack without a wide dashboard grid. |
| Patient booking | Keep clinician/service context visible across date, slot, disclosure, price and confirmation steps. | The selected time leads into privacy preview, then an explicit confirmation. | Day list and date strip replace dense desktop grids; preserve selected input when going back. |
| Clinician availability | Make the timezone-aware week grid the dominant desktop workspace, with schedule configuration in a compact companion panel. | Add/edit a time block; keyboard time fields and explicit Save remain available. | Use a single-day agenda and progressive editor sections on mobile. |
| Appointment groups and detail | Group by one primary appointment state; put preparation or documentation in the main column and compact facts in the side column. | Join, respond, cancel or document only when supported by server state. | Stack details and actions; avoid horizontal table overflow. |
| Consultation room and notes | Focus the call stage during media; after End, use a focused note form with distinct private and patient-visible fields. | Leave differs from clinician End; finalization is explicit. | Keep controls reachable and the remote participant dominant; audio-only replaces blank video with the alias/activity surface. |
| Care directory and record | Use dense filters above a table/cards with encounter-scoped summaries. | Open a permitted record or consultation. | Table becomes cards; preserve masked labels in every rendered surface. |
| Account, Payments and earnings | Use focused sections; show patient available/reserved balance once and clinician balances only from ledger postings. | Add funds, edit a section or request/cancel a demo payout. | Single-column summaries with clear labels and no nested-card stack. |
| Tours and system feedback | Keep a compact dismissible tour invitation and consistent loading, empty, permission and error states. | Retry or continue the current task without forced mutations. | Tour callout becomes a compact mobile sheet and never blocks OTP, calls or note-taking. |
| PWA/offline | Keep the existing public-only static asset cache and honest offline screen. | Explain when a requested action needs a connection. | Installation hints remain secondary; no app data is represented as saved offline. |

The current implementation records the focused availability, appointment-state,
account and financial slices. Remaining screen-by-screen visual verification is
listed in `presentation-readiness-verification.md`; this plan is not evidence of
acceptance on its own.
