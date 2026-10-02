# Next design update: route and component inventory

Baseline: merged `main` at `4cc0be9a0a96c3b209d07b47fd5e7c46ab4c31a2`
(PRs #7, #8, #9 and #10). This is the coverage map for the forthcoming design
brief, **not** a claim that the brief has been implemented. Production routes
use the `/teletena` basename; paths below omit that prefix. The public homepage
also resolves at the site's application entry. Keep backend authorization,
booking/reservation idempotency, disclosure snapshots and LiveKit Cloud End
behavior intact when changing presentation.

`Working` means a connected demonstration flow exists. `Partial` identifies a
real but narrower implementation. `Placeholder` is visibly unavailable and
must remain so until backend behavior is built. Every row needs desktop,
tablet, 390 px and 320 px review, 200% zoom, keyboard/focus, loading/empty/error
states and English, Amharic and Afaan Oromo copy review under the forthcoming
brief. Amharic and Afaan Oromo strings remain provisional; some newer copy is
still English. A build does not satisfy rendered visual acceptance.

## Route coverage

| ID | Route / owner | Current behavior | Status | Design coverage to verify |
| --- | --- | --- | --- | --- |
| PUB-1 | `/` · `pages/Homepage.tsx` | Public marketing, services, privacy, clinician invitation links | Working | Header/hero, illustration, category/steps/privacy, footer, language, mobile navigation |
| PUB-2 | `/for-clinicians` · `Homepage.tsx` | Professional invitation and application entry | Working | Clear approval boundary and route to verified contact |
| AUTH-1 | `/sign-in` · `SignIn.tsx` | Phone entry when site-enabled; otherwise email/password | Working | One-field phone, country handling, masked destination, cooldown, provider-error states |
| AUTH-2 | `/sign-in` email mode | Email OTP only with private SMTP; explicit password alternative | Working conditionally | No account enumeration, unavailable-provider message, password path and retry |
| AUTH-3 | `/sign-in` code mode | Phone/email code entry, paste/autofill, verification, resend/change contact | Working conditionally | Six-digit focus, mobile keyboard, expiry/attempt errors; no code/token in screenshots |
| ONB-1 | `/onboarding` · `Onboarding.tsx` patient | Guided alias, adult/consent, language/privacy, finish | Working | Back/resume, validation, no forced history, first-visit tour invitation |
| ONB-2 | `/onboarding` clinician | Identity, requested scopes, resume evidence, application submission | Working | Save/resume, pending approval and no implied permission to publish |
| PAT-1 | `/patient` · `Patient.tsx` | Home, search entry, next appointment and balance | Working | Useful empty state and compact available/reserved summary |
| PAT-2 | `/patient/discovery` | Approved offerings, clinician cards and filters | Working; matching partial | Price/format/language/category/availability, no invented credentials or ratings |
| PAT-3 | `/patient/book/:offering` | Calendar/slot, disclosure, review, atomic confirmation | Working | Back without data loss, timezone and price, stale-slot recovery, manual hold status |
| PAT-4 | `/patient/appointments` | Needs action, in progress, upcoming and past groups | Working | Text/semantic badges; clock time does not fabricate completion |
| PAT-5 | `/patient/consultations/:id` · `ConsultationPage.tsx` | Scoped details, timeline, snapshot, permitted summary and follow-up | Working | Upcoming/pending/ended/completed/cancelled states and private-text omission |
| PAT-6 | `/patient/account` · `Account.tsx` | Profile, contact, locale/timezone, privacy, balance and install help | Working; notification/contact edits partial | Focused sections, default-vs-booking sharing, save/error states |
| PAT-7 | `/patient/payments` · `Patient.tsx` | Simulated balance and activity | Working demonstration | Available/reserved distinction; single persistent environment ribbon |
| CLN-1 | `/clinician` · `Clinician.tsx` | Today, upcoming work and approval context | Working | Prioritized schedule, pending actions and honest empty state |
| CLN-2 | `/clinician/appointments` | Same appointment groups with clinician actions | Working | Confirm/decline/cancel, notes-pending and call-state distinctions |
| CLN-3 | `/clinician/availability` | Recurrence, intervals, exceptions, buffers, slot preview | Working | Desktop week editor; usable mobile day/agenda and explicit timezone |
| CLN-4 | `/clinician/services` | Approved-scope offerings and ETB pricing | Working | Publication/approval status, fixed duration and clear save feedback |
| CLN-5 | `/clinician/consultations/:id` | Scoped details and private note draft/finalize | Working | Post-End documentation, patient-visible preview and revision history |
| CLN-6 | `/clinician/care` | Search/filter/sort/paginate encounter-scoped directory | Working | Table/card parity and masked identities throughout |
| CLN-7 | `/clinician/care/:id` | Authorized encounter history and notes | Working | Historical disclosure snapshots; no cross-clinician record link |
| CLN-8 | `/clinician/account` | Professional profile, practice links, resume evidence | Working; settings partial | Approval context, private upload/remove rules, validation |
| CLN-9 | `/clinician/requests` | Honest pending-feature panel | Placeholder | Private requests/offers require backend implementation before product UI |
| CLN-10 | `/clinician/earnings` | Honest pending-feature panel | Placeholder | No totals, withdrawals or earnings release without accounting backend |
| ADM-1 | `/admin` · `Admin.tsx` | Application queue and authorized resume access | Working | Names first, evidence and requested scopes, approve/reject |
| ADM-2 | `/admin/scopes` | Service catalog and separate scope decisions | Working | Approval/revocation; general approval never grants a service |
| ADM-3 | `/admin/exceptions` | Honest pending-feature panel | Placeholder | No implied patient-record access or fabricated operations queue |
| CALL-1 | `/consultation/:id/room` · `ConsultationPage.tsx` + `features/consultations/Consultation.tsx` | Preflight, two-person video/audio, Leave/rejoin, clinician End | Working demonstration | Focused responsive room, device/permission/reconnect/ended states, opaque aliases |
| DEV-1 | `/showcase` · `Showcase.tsx` | Components/states; development-only | Working in dev only | Every changed component and locale; no public production link |
| PWA-1 | Static offline page and manifest · `frontend/public` | Install metadata and public-static-only offline response | Working demonstration | Honest offline state, no cached API/private data, safe update around calls |
| SYS-1 | Unknown route and role/guest guards · `App.tsx`, `Layouts.tsx` | Redirect, signed-out, loading, service error and permission states | Working | Consistent focus, retry and no private-data flash |

## Shared component and state coverage

| ID | Source | Includes | Required review |
| --- | --- | --- | --- |
| SYS-2 | `components/Brand.tsx`, `layouts/Layouts.tsx` | Brand/illustration, public/auth/workspace shells, demo ribbon, translation notice, responsive navigation | All roles and focused call; ribbon reachable on mobile |
| UI-1 | `components/ui.tsx` | Button/IconButton; Text/Phone/OTP fields; Select/Checkbox/Radio/Switch; Card/Dialog/Tabs; StatusBadge/InlineNotice/Toast; Skeleton/EmptyState | Default/hover/focus/disabled/loading/error/success, keyboard and translated text |
| UI-2 | `components/Domain.tsx` | Clinician/appointment cards, disclosure preview, booking summary, money/date helpers | No unmasked names, exact booking snapshot, timezone/ETB clarity |
| UI-3 | `components/WorkspaceTour.tsx` | Role/version-aware invitation, spotlight steps, replay/dismiss | Patient, clinician/applicant, reviewer; no mutation or call interruption |
| UI-4 | `features/consultations/Consultation.tsx` | Preflight and video/audio-only call controls | Media cleanup, real audio activity, reconnect, Leave versus End |
| UI-5 | `hooks/useSession.tsx`, `useResource.ts`, `useAction.ts`, `useLocale.tsx` | Session/role, async data/action, language | Signed-out versus service failure, retry, pending/success, provisional locales |
| SYS-3 | `frontend/public/sw.js`, `offline.html`, `manifest.webmanifest` | PWA/offline/install states | Public assets only; never save authenticated data offline |

## Capability gaps outside visual completion

The following are **not implemented** or are narrower than the agreed product
contract. A future design may show an honest unavailable state; it must not
present a decorative working control. Scope and policy for implementation must
come from the forthcoming brief and product contract.

| Capability | Current status |
| --- | --- |
| Clinician pending/available earnings, withdrawals, double-entry subledger, ERPNext posting/reconciliation | Not implemented; `tt_ledger` is a simulation transaction log only |
| Private open requests/offers, offer expiry/acceptance, previous clinicians, natural-language matching/relevance/proximity | Not implemented; direct filtered discovery works |
| Mutual rescheduling, couples' individual consent, ratings/reviews, paid or complimentary extensions | Not implemented |
| Actor-specific production cancellation/refund policy, disputes and earnings holds | Not implemented; explicit full-release pre-start demonstration policy exists |
| Notification preferences/contact changes and authenticated email summary links | Not implemented |
| Clinic/partner workspace and membership, clinician referral attribution | Not implemented; affiliation conveys no record permission |
| Real payment/withdrawal rails, professional credential verification, clinical safety protocol | Not implemented; review remains demonstration only |
| Live SMS receipt, SMTP delivery on Selfmade, physical-device call quality and native translation review | Validation gaps; do not claim passed or activate during design work |

For each row changed under the next brief, record its route/component ID,
responsive screenshots, locale coverage, connected-flow test, permission check
and any unimplemented dependency in the design verification report. This
inventory is intentionally a starting checklist and does not authorize a
missing backend capability by itself.
