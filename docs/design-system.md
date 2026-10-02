# DESIGN SPECIFICATION — TELETENA

Authoritative user brief, recorded 2026-10-01. This replaces the rejected PR #5
product-facing design. Follow this document and `design-acceptance.md` for all
frontend changes. Preserve historical verification reports separately.

## Naming
- User-facing product: **TeleTena**. Repository: `tele-tena`. Frappe: `tele_tena`.
- Do not rename technical identifiers, tables or migration history for branding.

## Design direction
Calm, human, precise. Warm neutral surfaces, deep ink typography, distinctive teal
accents, restrained original illustrations and generous but purposeful spacing.
Reference Headspace for approachable care presentation and Linear for hierarchy
and restrained interface density. Inspect their public pages; borrow principles,
not logos, assets, exact layouts or copy. Avoid generic giant cards, excessively
wide forms, repeated banners, decorative gradients everywhere, and a dashboard
made from one long form.

## Brand and logo
Create an original SVG mark using two rounded opposing forms suggesting
conversation and a subtle lowercase t. Pair with **TeleTena**. Refine optically at
small sizes; no generic medical-cross/heartbeat clip art. Deliver horizontal,
symbol-only, monochrome, reversed and favicon variants. Define clear space and
minimum sizes; verify 16, 24 and 32 px. Keep assets local and reusable.

## Color tokens
| Token | Value |
|---|---|
| brand.primary | #126B64 |
| brand.hover | #0D5751 |
| text.primary | #182B2A |
| text.secondary | #526561 |
| surface.canvas | #FAF9F6 |
| surface.card | #FFFFFF |
| surface.subtle | #EAF2EE |
| border.default | #D7E2DC |
| accent.apricot | #F2BC97 |
Define semantic success, warning, danger, information and focus tokens. Verify
actual foreground/background contrast. Apricot is decorative, never small text.
Status never relies on color alone.

## Typography
Self-host properly licensed **Manrope** (English and Afaan Oromo) and **Noto Sans
Ethiopic** (Amharic), with fallbacks. Body 16 px at 1.5–1.65 line height; normal
supporting copy at least 14 px. Scale 14 / 16 / 20 / 24 / 32 / 48 / 64 px.
Marketing headline responsive 36–64 px; application title 28–32 px. Weights
400/500/600/700 purposefully. Verify Ethiopian-script wrapping, line height and
baseline alignment.

## Geometry and layout
Spacing: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 px. Marketing max 1200 px;
authentication max 440 px; guided form max 640 px; desktop sidebar about 240 px.
Gutters 16 px mobile, 24 px tablet, 32 px desktop. Controls 48 px high; touch
targets at least 44×44 px. Radius 12 px controls, 20 px cards, 24 px dialogs.
Subtle borders/restrained shadows; avoid nested cards. No fixed heights truncating
translations. Compact screens must remain usable with a mobile keyboard open.

## Component system
Document variants and implement Button, IconButton, TextField, PhoneField,
OTPInput, Select, Checkbox, RadioGroup, Switch, Card, Dialog, Drawer, Tabs,
navigation, StatusBadge, InlineNotice, Toast, Skeleton, EmptyState, clinician
card, appointment card, disclosure preview, booking summary and call controls.
Define default/hover/focus/pressed/disabled/loading/error/success states where
applicable. Use one outline icon family (Lucide), 20 px standard and 24 px
prominent; no emoji icons. Icon buttons require accessible names/tooltips.
Provide a development showcase with all states and languages. Use accessible
primitives for focus management and keyboard interaction.

## Tone and disclosures
Short, reassuring, direct: “Find care”, “Continue”, “Send code”, “Verify and
continue”, “Change number”, “Choose a time”, “What you’ll share”, “Join
consultation”, “Leave”, “End for everyone”. No developer-facing copy such as
“Refresh persisted data”, “authenticated development account”, “create an adult
patient account”, or “minor units”. Do not promise anonymity, guaranteed outcomes,
unsupported credentials or unimplemented capabilities.
Use one compact persistent **“Demonstration environment — no real payments or
clinical care”** indicator, also present in focused/mobile layouts. Use ordinary
labels such as **Balance**, **Payments** and **Add funds**; identify demo deposits,
reservations and releases in activity detail. Translation review is an accessible
secondary notice.
No repeated large warnings; genuine errors stay visible and actionable.

## Public homepage — /
Header: logo, How it works, For clinicians, language, Sign in.
Headline: “Find someone you feel comfortable talking to.”
Supporting copy: “Explore mental health and relationship support. Choose your
clinician, your time, and what you share.” Primary Find care; secondary Explore
how it works. Original restrained conversation illustration. Service categories,
three-step explanation, privacy explanation, clinician invitation, concise footer.
No invented testimonials, ratings, clinician counts, success claims, or decorative
marketing forms collecting personal data.

## Authentication — /sign-in
Centered, phone-first and simple: compact brand, short welcome, **one phone field**
with clear country code, **one Continue button**, secondary **Use email instead**.
No password, role dropdown, profile form or signup questionnaire on first screen.
After requesting, **replace** it with heading, masked destination, one accessible
code input supporting paste/autofill, Verify and continue, Change number and
resend with cooldown/clear failures.
Email selection reveals only email field. Email OTP is default; reveal password
only after **Use password instead**. Implement real email verification and local
delivery configuration; no pretend working OTP route. Expected guests are signed
out, not load errors. Do not disclose account existence before contact ownership.
On a hosted review site, offer email OTP only when its private SMTP configuration
exists. Otherwise the email alternative opens password entry directly. Phone
remains the single-field first step when SMS access is enabled. Distinguish SMS
provider acceptance from receipt in the code step. New Amharic and Afaan Oromo
sign-in labels are provisional pending native review.
Existing verified users enter workspace; new users enter onboarding. Verified
contact is distinct from completed onboarding. Preserve development password
accounts; signup never grants clinician approval.

## Patient onboarding
Small resumable steps with Back/progress: (1) preferred name/alias, (2) adult
eligibility/required consent, (3) preferred language/privacy defaults, (4) Find
care. At most one/two related questions per step. No full medical history required
to discover care; explain later relevant collection. Incomplete onboarding stays
distinct from completed patient registration.

## Clinician onboarding
Separate For clinicians entry. Contact verification, professional identity,
credentials/service scope, optional clinic affiliations, review/submission.
Save/resume and approval status. Signup never grants approval/unrestricted scope.

## Patient workspace
Default Home/Find care, never profile maintenance. Navigation Home, Find care,
Appointments, Account. Desktop sidebar; mobile labeled icon navigation. Home:
prominent “What would you like help with?” field, next appointment, previously
consulted clinicians when available. Discovery: useful clinician cards, editable
category/language/format/availability filters, clear prices/verification meaning.
Booking: time → sharing preview → price/policy review → confirm. Wallet in
Account/payment, not above discovery. Helpful empty states; no fabricated records.

## Clinician workspace
Default Today; upcoming consultations, pending requests, required actions.
Separate appointments/requests, availability, services/pricing, care records,
earnings, profile. Permission-scoped patient information. Understandable time
selection; enter/display prices in ETB without minor-unit jargon.

## Administration
Focused application, service-scope and operational-exception queues. Clear
status/evidence/actions. Administrative workflow roles imply no patient access.

## LiveKit
Integrate PR #3 in dedicated routes/components. Preflight: camera preview,
microphone/device controls, audio-only, appointment information, explicit Join.
Call: dominant remote area, self-preview, connection state, stable accessible
controls. Microphone, camera, audio-only behavior, Leave. Clinician-only **End for
everyone**, visually distinct, confirms intent. Understandable ending,
disconnection/retry/rejoin. No profile/wallet forms beside calls. Preserve token
authorization, privacy, cleanup/revocation. No recording/transcription or charges
inferred from connection duration.

## Accessibility and architecture
Verify 390/768/1440 px and 320 px; semantic structure, keyboard, visible focus,
associated errors, reduced motion, 200% zoom, no horizontal overflow. Essential
actions never hover-only. Contrast/readability in all three languages.
Use routes/layouts/feature components/hooks, not monolithic App.tsx. Separate
server state, form state and UI state. Secrets/authorization stay backend-only.
Never weaken tests or permissions for visual results. No clinical/API offline cache.

## Presentation release additions

Scheduling, appointment/call/note states, cancellation defaults, privacy scopes
and accepted demo timing values are defined in [presentation-release-model.md](presentation-release-model.md).
The schedule editor is a weekly recurrence with timezone, multiple intervals,
date exceptions, breaks, notice/horizon, buffers, duration and confirmation mode.
Desktop uses a week calendar beside its editor; mobile uses agenda and compact
editing steps. Time entry remains accessible without drag. Patient slot choice
uses real server-generated slots and preserves the disclosure -> price -> confirm
sequence.

Use status labels for `Upcoming`, `Needs action`, `In progress` and `Past` with
explicit appointment/call/documentation badges. No badge is inferred as a database
transition from the clock alone. The consultation detail view is state-aware; the
LiveKit room is a focused route. Audio-only replaces video with a permitted alias
surface and activity derived from the existing participant audio track only.

Consultation notes have separate private clinician and patient-visible fields.
They are server-persisted, revisioned and never cached in local storage. Patient
responses contain only published summary revisions. A persistent share history
explains if a prior revision was visible. Resume upload is private PDF only, at
most 5 MiB, and is evidence for review, never proof of a credential.

The installable PWA caches public, versioned static assets and the generic offline
page only. `/api/`, private files, consultation routes and authenticated responses
are network-only. Updates wait for existing clients to close; an active consultation
is never reloaded by the service worker. Offline UI never claims a mutation saved.

Guided walkthroughs are versioned, per-user/per-role server preferences with a
replayable Help & tours entry. They do not submit, approve, book, disclose or pay.
Steps use stable target identifiers, support missing-target recovery and do not
start during OTP, calls or note editing. English, Amharic and Afaan Oromo copy is
required; provisional strings are marked for review.

## Acceptance and integration gates
Install/fix browser dependencies with installed Playwright's supported setup.
Inspect actual rendered mobile/tablet/desktop screens and capture homepage,
phone entry, OTP, email, onboarding, patient home/discovery, clinician Today and
call screenshots without credentials/personal data. Verify working flows, not
just components. Resolve complete hosted Leave/rejoin/End and cached-token
rejection before merging calls; do not discard assertions. Keep reviewable
integration/authentication/branding/pages/verification commits. Preserve all data,
credentials, security fixes, source branches and verification evidence. Source PRs
must be merged or explicitly superseded after accounting for their changes.
Merge only after integration checks pass; never deploy to production. Report
unimplemented screens/backend dependencies explicitly. Build/lint are not visual
acceptance.

## Reference inspection
Inspected https://www.headspace.com/ and https://linear.app/ on 2026-10-01.
Take approachable task-oriented care navigation from the former; compact hierarchy
and disciplined content grouping from the latter. All brand art and layouts here
are original. No third-party marks, illustrations, metrics or testimonials copied.

## Brand implementation
Local `frontend/public/brand/` contains symbol, horizontal lockup, monochrome,
reversed and favicon SVGs. Two opposed rounded speech forms share a vertical
negative-space rhythm that suggests a lowercase t. Minimum symbol size 16 px;
preferred interface size 32–40 px. Clear space is one quarter of symbol height.
Use the React Brand component for the locally typeset Manrope wordmark. SVG
lockups use the same font with a sans-serif fallback; no external asset requests.
Manrope and Noto Sans Ethiopic are distributed locally through their Fontsource
packages with included SIL Open Font License files. No Google Fonts runtime calls.

### Review deployment URL

The packaged release runs at `/teletena/` with the existing design and persistent
demonstration ribbon. Use router links within its basename and `BASE_URL` for
public assets; do not hardcode development hosts or expose provider secrets.
