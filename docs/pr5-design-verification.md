# Phase 2: React design system and focused journeys

Status: acceptance contract recorded before implementation on 2026-10-01.
Branch `feat/design-system` is based on `feat/phone-otp`; its PR must explicitly
depend on Phase 1 PR #4. It is not a merge or release authorization.

## Agreed design rules

- Build a small reusable React system with named design tokens for color,
  spacing, type, radii, borders, focus, and responsive breakpoints. Keep theme
  values in CSS custom properties, not scattered component styles.
- Use system fonts and language-aware line wrapping that render Latin,
  Amharic (Ge'ez), and Afaan Oromo legibly. Keep text content in translation
  dictionaries. Amharic and Afaan Oromo wording stays marked provisional for
  native human review.
- Shared controls include accessible buttons, labeled fields, cards, dialogs,
  navigation, status labels, and loading, empty, success, and error states.
  Keyboard focus is visible; form errors are associated with their fields or
  announced through a live region; controls have usable touch targets.
- Use responsive layouts from narrow phone view through desktop. Display the
  active timezone explicitly anywhere an appointment time is entered or shown.
- Separate presentation from Frappe transport and domain state. Keep API
  requests same-origin, authenticated commands CSRF-protected, and private data
  in memory only. Do not cache authenticated responses, clinical data, tokens,
  or offline commands.
- Give each authenticated role a focused patient, clinician, or administrator
  journey. Present progressive disclosure, one clear primary action per step,
  plain-language ETB pricing, and explicit simulation labels. Use only APIs
  already implemented; unavailable work must be labeled rather than fabricated.
- Preserve account identity and clinical privacy rules. A privacy preview shows
  exactly the fields selected for a request and does not silently change global
  sharing defaults.

## Journey and component boundaries

- Public access: existing development email/password access; phone access and
  signup backed by Phase 1 APIs, with acceptance/uncertain-delivery copy.
- Patient: profile and global sharing defaults; simulated wallet; discover an
  existing approved offering; select a time with timezone; request-specific
  sharing preview; explicit booking; persisted appointments. Unbuilt marketplace
  workflows remain identified as unavailable.
- Clinician: application/approval status; approved service offering and price;
  availability entry with timezone; persisted appointments. Do not show
  publication or booking controls as usable before approval.
- Administrator: manual clinician approval/rejection and independent service
  scope approval, clearly separated from patient and clinician navigation.
- Shared presentation owns no authorization decisions. Every protected query
  and command continues through the existing server-side API.

## Acceptance criteria

1. Tokens and responsive layouts cover narrow mobile, tablet, and desktop views;
   English, Amharic and Afaan Oromo remain readable and provisional copy remains
   visibly marked for review.
2. Reusable accessible controls cover forms, buttons, dialogs, navigation,
   cards, status, loading, empty, error, and privacy preview states.
3. Role-specific journeys do not present administrator controls to patients or
   privileged clinician actions to applicants. Server APIs remain the source of
   permissions.
4. Patient booking uses persisted discovery, availability, preview, and booking
   APIs; shows explicit timezone and ETB simulation pricing; preview equals the
   saved disclosure. Clinician/admin screens use persisted profile, application,
   service-scope, offering and availability APIs.
5. Request/response data, clinical text and authentication material are never
   written to local storage, service-worker caches, URL parameters, or offline
   queues. API calls use `cache: no-store` for private data.
6. No completed screen implies that clinics, private offers, cancellation,
   extensions, accounting, or LiveKit are implemented when they remain pending
   or blocked in `mvp-delivery-tracker.md`.
7. Build, lint, existing authenticated API/integration tests, and focused
   component/browser checks pass. Manual browser review covers each role and a
   narrow viewport.

## Demonstration policies and open decisions

Existing product rules remain authoritative. The visual token palette, type
scale, spacing scale, breakpoints, and navigation labels are implementation
choices for the demonstration, not user research or final brand policy. No
clinical copy or translations are considered human-reviewed. This phase does
not decide the still-pending marketplace, cancellation, couples, earnings,
withdrawal, accounting, or production policies. Simulated balances remain
simulation only.

## Checkpoint evidence

On 2026-10-01, `npm run build`, `npm run lint`, Python compilation, and
`git diff --check` passed. A mocked API browser check was added at
`scripts/browser-design-system.cjs`, but Chromium could not launch in the local
environment because `libnspr4.so`, `libnss3.so`, `libnssutil3.so`,
`libsmime3.so`, and `libasound.so.2` are unavailable. That check does not claim
backend persistence in any case; real Frappe endpoints are covered by the Phase
1 integration suite. Manual visual review at phone, tablet, and desktop sizes
remains outstanding. Amharic and Afaan Oromo are still provisional.
