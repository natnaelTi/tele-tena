# Next release layout plan

The availability save hotfix is isolated in PR #11. This document covers the
larger presentation and earnings update on `feat/next-design-update`.

| Screen family | Layout/composition change | Primary action and behavior |
|---|---|---|
| Patient and clinician home | Moderate-width content with next appointment and a compact backed balance/earnings summary; remove repeated summary cards | Open the next real action or relevant workspace |
| Clinician availability | Wide calendar workspace, compact configuration and an accessible side editor; mobile becomes date strip + agenda | Create/edit a real persisted time interval; existing bookings remain fixed |
| Patient discovery/booking | Clinician/service context stays visible; useful calendar then time list, disclosure, price and confirm steps | Choose a generated open slot and book with preserved input |
| Appointment lists | Clear patient/clinician groupings, one dominant status, status-aware secondary action | Open details, join only during authorization window, or perform an allowed transition |
| Consultation details | Main column for preparation or notes/summary, compact fact rail and timeline | Prepare/join, document/finalize, or read only published content |
| Consultation room | Navigation reduced; remote stage dominates with self-view, stable control dock and audio participant surface | Join, mute, switch media mode, leave, or clinician-only End |
| Account/privacy/payments | Section overview and focused editors; wallet summary appears once on account overview and fully on payments | Edit one category, inspect available/reserved balance and activity |
| Clinician care | Search/filter table with equivalent card view and encounter-scoped details | Open only records authorized through that clinician's booking disclosures |
| Reviewer/admin | Dense queue with name, scope, evidence and status; resume download remains authorized | Review an application and individual service scopes |
| Sign-in/onboarding | Focused phone/email/code steps and resumable narrow forms | Verify contact, then complete the appropriate role journey |
| PWA, tours and system feedback | Keep offline state distinct from unsaved work; role-aware compact tours and accessible notices | Retry online actions; tours only guide and never mutate |

All copy/layout changes preserve the single demonstration ribbon, existing
English/Amharic/Afaan Oromo locale system, permission checks, private API
omissions and LiveKit token revocation. Mobile verification includes 320, 390,
768 and 1440 CSS-pixel widths and 200% zoom where browser automation supports it.
