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
| PAT-2 | `/patient/discovery` | Approved offerings, clinician cards and filters | Working; matching partial | Price/format/language/category/availability, no invented credentials or ratings; entry to private request when direct options do not fit |
| PAT-2A | `/patient/requests` | Private immediate/scheduled requests, offers, disclosure and acceptance | Implemented in progress; built scheduled request-to-inbox path verified | Same-origin persisted APIs, two-session production-build browser request delivery, and private offer/balance/slot API regressions pass. Immediate UI beyond current service hours is not claimed; scheduler expiry, immediate browser case, concurrency-at-web-layer and full locale review remain |
| PAT-2B | `/patient/clinicians/:opaqueId` | Approved clinician public summary and direct-booking entry | Implemented in progress | Opaque ID, approved services only, no account email; backend privacy checks pass |
| PAT-3 | `/patient/book/:offering` | Calendar/slot, disclosure, review, atomic confirmation | Working | Back without data loss, timezone and price, stale-slot recovery, manual hold status |
| PAT-4 | `/patient/appointments` | Needs action, in progress, upcoming and past groups | Working | Text/semantic badges; clock time does not fabricate completion |
| PAT-5 | `/patient/consultations/:id` · `ConsultationPage.tsx` | Scoped details, timeline, snapshot, permitted summary and follow-up | Working | Upcoming/pending/ended/completed/cancelled states and private-text omission |
| PAT-6 | `/patient/account` · `Account.tsx` | Profile, contact, locale/timezone, privacy, balance and install help | Working; notification/contact edits partial | Focused sections, default-vs-booking sharing, save/error states |
| PAT-7 | `/patient/payments` · `Patient.tsx` | Simulated balance and activity | Working demonstration | Available/reserved distinction; single persistent environment ribbon |
| CLN-1 | `/clinician` · `Clinician.tsx` | Today, upcoming work and approval context | Working | Prioritized schedule, pending actions and honest empty state |
| CLN-2 | `/clinician/appointments` | Same appointment groups with clinician actions | Working | Confirm/decline/cancel, notes-pending and call-state distinctions |
| CLN-3 | `/clinician/availability` | Recurrence, intervals, exceptions, buffers, slot preview | Working; fix also independently reviewable in PR #11 | Built production route passes save/reload/patient booking; timezone-aware desktop week grid and mobile agenda; see current screenshots and limits in `presentation-readiness-verification.md` |
| CLN-4 | `/clinician/services` | Approved-scope offerings and ETB pricing | Working | Publication/approval status, fixed duration and clear save feedback |
| CLN-5 | `/clinician/consultations/:id` | Scoped details and private note draft/finalize | Working | Post-End documentation, patient-visible preview and revision history |
| CLN-6 | `/clinician/care` | Search/filter/sort/paginate encounter-scoped directory | Working | Table/card parity and masked identities throughout |
| CLN-7 | `/clinician/care/:id` | Authorized encounter history and notes | Working | Historical disclosure snapshots; no cross-clinician record link |
| CLN-8 | `/clinician/account` | Professional profile, practice links, resume evidence | Working; settings partial | Approval context, private upload/remove rules, validation |
| CLN-9 | `/clinician/requests` | Explicit expiring availability, private matched requests and own offer | Implemented in progress | Frappe 16 backend scope/language/format/continuous-slot filters and private competing-offer regression pass; separate patient/clinician production-build browser sessions verified scheduled delivery. Immediate readiness now reports missing policy/capacity; hosted realtime, worker expiry outcome, and full locale review remain |
| CLN-10 | `/clinician/earnings` | Pending/available/reserved earnings, snapshotted release time, payout request and cancel | Implemented demonstration | Balanced subledger, retry-safe release, payout reserve/release and owner-only tests; no external transfer or Paid status |
| ADM-1 | `/admin` · `Admin.tsx` | Application queue and authorized resume access | Working | Names first, evidence and requested scopes, approve/reject |
| ADM-2 | `/admin/scopes` | Service catalog and separate scope decisions | Working | Approval/revocation; general approval never grants a service |
| ADM-3 | `/admin/exceptions` | Authorized financial dispute queue | Partial | Financial-only reviewer permission and audited release/refund; no access to clinical notes, and post-release cases remain unsupported |
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
| Clinician pending/available earnings, payout reservations and balanced demo subledger | Implemented for demonstration on this branch; `tt_ledger` remains a separate append-only simulation activity log |
| ERPNext posting/reconciliation and external payout settlement | Not implemented; real-money operations remain disabled |
| Private open requests/offers | Partial; packaged Frappe 16 two-session request→eligible inbox→private offer→acceptance→appointment/reservation journey passed on 2026-10-05. Backend tests cover concurrency and privacy; scheduled waves run on isolated Redis DB 15. Not a pilot-performance or call-to-earnings acceptance. See `vetting-routing-verification.md`. |
| Previous clinicians, natural-language matching/relevance/proximity | Not implemented; direct filtered discovery and editable filters work |
| Mutual rescheduling, couples' individual consent, ratings/reviews, paid or complimentary extensions | Not implemented |
| Actor-specific production cancellation/refund policy, post-release disputes and paid extensions | Not implemented; only explicit pre-start demo release and pre-release dispute holds exist |
| Notification preferences/contact changes and authenticated email summary links | Not implemented |
| Clinic/partner workspace and membership, clinician referral attribution | Not implemented; affiliation conveys no record permission |
| Real payment/withdrawal rails, professional credential verification, clinical safety protocol | Not implemented; review remains demonstration only |
| Live SMS receipt, SMTP delivery on Selfmade, physical-device call quality and native translation review | Validation gaps; do not claim passed or activate during design work |

For each row changed under the next brief, record its route/component ID,
responsive screenshots, locale coverage, connected-flow test, permission check
and any unimplemented dependency in the design verification report. This
inventory is intentionally a starting checklist and does not authorize a
missing backend capability by itself.

## Current feature-branch coverage (`feat/next-design-update`)

This table describes this iteration only. “Intentionally unchanged” means the
existing merged behavior and identity were retained in this focused slice; it
does not mean that the requested whole-product design acceptance is complete.

| Inventory entry | Iteration status | Reason / evidence |
|---|---|---|
| PUB-1, PUB-2 | Intentionally unchanged | Public homepage and clinician invitation were preserved; no current-branch visual review was run. |
| AUTH-1, AUTH-2, AUTH-3 | Intentionally unchanged | Phone, email, password and code flows were not rewritten; current site is invited-review mode. Hosted phone access is not visually reverified here. |
| ONB-1, ONB-2 | Intentionally unchanged | Existing resumable patient and clinician onboarding preserved; no current-branch layout or locale review. |
| PAT-1, PAT-2 | Intentionally unchanged | Home and discovery layout retained. |
| PAT-3 | Verified | Current built browser journey completed slot selection through booking; selection/back-state and all locale variants were not exhaustively reviewed. |
| PAT-4 | Partial | Status grouping copy was refined; a full rendered appointment-state matrix was not captured. |
| PAT-5 | Partial | Primary status and patient-facing “Summary being prepared” wording were refined; all state-specific screenshots remain outstanding. |
| PAT-6 | Partial | Account sections and repeated balance/help/notification cards were reduced; no current-branch rendered review. |
| PAT-7 | Partial | Activity labels now distinguish old simulation log versus demo-subledger source in API output; current payments page visual review remains. |
| CLN-1, CLN-2 | Partial | Appointment state/action hierarchy was refined; full desktop/mobile state matrix remains. |
| CLN-3 | Verified | Built production route save/reload/booking, keyboard field, copy-day and date-only exception paths passed; 390/768/1440 layouts rendered without horizontal overflow. |
| CLN-4 | Intentionally unchanged | Approved service offering flow retained; not visually reverified. |
| CLN-5 | Partial | Ended-call/documentation action wording was refined; note lifecycle regression tests passed, but no current-branch visual capture. |
| CLN-6, CLN-7 | Intentionally unchanged | Encounter-scoped care API and presentation retained; privacy tests passed; visual review remains. |
| CLN-8 | Partial | Professional account section was streamlined; no current-branch visual review. |
| CLN-9 | Partial on dependent `feat/open-requests` | Connected persisted inbox, expiring explicit presence and own offer; API checks pass. A built two-session flow reached persisted acceptance and is documented with screenshots; a reusable clean browser test, background expiry and full locale/render review remain outstanding. |
| CLN-10 | Implemented | Balanced demo journal, earnings lifecycle, holds and payout reservations are server-backed and covered by focused regressions; real settlement and a rendered earnings walkthrough remain out of scope. |
| ADM-1, ADM-2 | Intentionally unchanged | Manual approval and per-service scope controls were preserved; no current-branch visual review. |
| ADM-3 | Partial | Financial event labels were clarified and IDs removed from dispute cards; reviewer workflow and separation from private notes passed API tests, but no current-branch visual review. |
| CALL-1 | Intentionally unchanged | LiveKit authorization and room presentation were not modified. Prior hosted Cloud evidence remains in the earlier report; it was not rerun here. |
| DEV-1 | Intentionally unchanged | Showcase route remains development-only; no updated capture. |
| PWA-1 | Verified (behavior only) | Both service-worker checks passed; visual/offline-install review was not repeated. |
| SYS-1, SYS-2 | Partial | Compact tour invitation and replay duplication were improved; tour layout and all shared feedback components still need full visual review. |
| UI-1, UI-2, UI-5 | Intentionally unchanged | Established shared controls, domain cards and hooks were preserved; this slice adds only calendar copy keys and usage. |
| UI-3 | Partial | Tour invitation composition changed; persistence/route behavior has earlier evidence, but no post-change browser walkthrough. |
| UI-4 | Intentionally unchanged | Call controls were preserved without weakening LiveKit behavior. |
| SYS-3 | Verified (behavior only) | Service-worker privacy/scope regression passed; all-browser visual and install review remains. |

English is the verified language for this iteration's new calendar and finance
copy. Amharic and Afaan Oromo strings remain provisional, and the wider product
contains existing English-only copy. The current design pass is therefore
partial and is not a whole-product visual acceptance.

## PR #12 rendered-route checkpoint (2026-10-03)

The earlier per-feature status table records whether behavior changed; this
checkpoint updates only which production-built routes have current screenshots.
It does not turn a screenshot into proof of permissions or whole-product visual
acceptance. Source and asset SHA: `df845b5b7936a3b696e40c1856f4e48f6148bf75`.
Screens are under
[`docs/screenshots/next-design-update/current-review/`](screenshots/next-design-update/current-review/)
and use synthetic records only.

| Inventory coverage | Render capture | Remaining visual/functional review |
|---|---|---|
| PUB-1, AUTH-1/2 (invited mode) | Homepage and email/password sign-in at 320, 390, 720, 768 and 1440 px | Clinician invitation route; hosted phone entry, OTP, resend and email OTP on an enabled-delivery fixture |
| ONB-1/2 | Not captured in this run | Patient and clinician resumable steps, pending/rejected application and private resume controls |
| PAT-1/2/3 | Patient home, discovery and booking at all five widths | Back-navigation state, disclosure preview, price review and confirmation screens need current screenshots; booking regression did complete the flow |
| PAT-4/5/6/7 | Patient appointments, consultation detail, account and payments at all five widths | Explicit status-state, published summary, privacy-edit, transaction empty/error state review |
| CLN-1/2/3/4 | Clinician Today, appointments, availability and services/pricing at all five widths | Current availability error/editor interactions at mobile and 200% browser zoom; approval-pending state |
| CLN-5/6/7/8/10 | Clinician consultation detail, care directory, account and earnings at all five widths | End-of-call notes, private/shared revision states, care-record detail, resume replace/remove and seeded earnings/payout scenario |
| ADM-1/2/3 | Application queue, service scopes and financial disputes at all five widths | Pending-applicant/resume access and reviewer permission/error states; 200% browser zoom |
| CALL-1/UI-4 | Not part of the five-width route sweep | Preflight permission failure, real video/audio-only layouts, Leave/rejoin and ended state; hosted Cloud token test passed with fake media, physical devices remain untested |
| UI-3 tours | Invitation row appears in authenticated captures | Open/step/replay/dismiss/missing-target states at mobile for patient, clinician and reviewer |
| PWA-1/SYS-1/2/3 | Built sign-in/deep-link/offline flow passed; route screenshots have no page-level overflow | Browser update deferral during an active call and physical HTTPS installation guidance remain unverified |

Twenty direct routes were captured at five CSS viewport widths (320, 390, 720,
768 and 1440 px). The 720 px viewport is a narrow-layout proxy for the CSS
viewport width after 200% zoom on a 1440 px display; it is not an actual browser
zoom/device test. The sweep found patient booking page overflow to 984–992 px at
320/390/768; `.booking-layout` and its children now allow shrinkage, and the
built booking regression plus a repeated route sweep passed without page-level
overflow. Inner date chips remain intentionally horizontally scrollable.

This preview is configured for invited review: the public landing page works,
phone OTP and public registration are disabled, and email/password reviewer
access remains available. The enabled-registration visual/browser configuration
still needs a separate disposable site. No live SMS or SMTP delivery was run.

### Additional authentication/onboarding captures

The 2026-10-03 route evidence also includes:

- `phone-entry-enabled-{320,390,768,1440}.png`: phone access and registration
  switches were enabled only on the isolated preview long enough to render the
  phone-entry UI. No code request was made. The exact invited-review
  `site_config.json` bytes were restored afterward.
- `patient-onboarding-{320,390,768,1440}.png` and
  `clinician-onboarding-{320,390,768,1440}.png`: first step only, using a
  temporary synthetic Website User with verified synthetic email identity and
  no clinician role. The account and private password fixture were removed;
  no onboarding form was submitted.

These captures do not verify SMS delivery, OTP entry, or the later clinician
application stages. Email OTP remains unavailable without a delivery provider.


### Consultation captures from the production-built preview

Current screenshots in `current-review/` cover video call at 390/1440, plus
audio-only, clinician notes after End, and completed consultation detail for
patient and clinician at 320/390/768/1440. They use synthetic records and
fake-media browser sessions. Inspection identified a remaining status conflict
on clinician notes: call status is “Call ended” while appointment status says
“Booked”. A focused built-route regression now verifies “Completion pending” without mutating appointment data; 390/1440 px captures show the corrected display.


### Authentication fallback correction (2026-10-03)

The isolated invited-review page now renders phone-first with an explicit
unavailable notice, then offers email/password because neither SMS nor email OTP
is configured there. Built browser verification passed for the seeded patient
and clinician accounts. With mocked enabled capabilities, the UI preserves the
phone OTP, email OTP and explicit password choice; provider delivery is not
claimed. Wrong credentials and invalid codes have distinct, non-enumerating
messages. Current screenshots are in `current-review/sign-in-invited-*`.
