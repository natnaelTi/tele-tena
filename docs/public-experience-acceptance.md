# Public Experience Redesign —20 October 2026

Bounded dependent work from PR47/f534f4b; no backend/schema/dependency, provider,
access-switch, seed or private-workspace changes. Written two-mode brief supersedes
A01's simultaneous patient/clinician columns. Inspected `/home/frappe/teletena-design-reference/landing-page-sketch.jpg`: first patient view, manually selected clinician view, scroll cues in both. The image remains outside Git. The written brief supersedes its animated-loading annotation. Local A01/A02/A03/C02/profile components and tokens remain the reference. No fictional UI is presented as live or clinically verified.

| Route/state | Intended composition/actions | Verification |
|---|---|---|
| `/`, guest, Find Care default | Labeled audience tabs, care headline, directory/request CTAs, explicitly illustrative product view, three steps, real public categories, privacy/FAQ/finalCTA | Implementation in progress |
| `/`, For Clinicians selected | Same page changes headline/illustration/steps/benefits/approval/FAQ/CTAs; keyboard tabs; no role/intent mutation | Implementation in progress |
| `/for-clinicians` | Existing professional information entry, clinician-mode landing with application-intent CTA | Implementation in progress |
| `/how-it-works` | Focused patient explanation; existing directory/request routes; no obsolete natural-language search | Implementation in progress |
| `/care`, populated/loading/empty/error | Real grouped offerings/reactive filters; public shell/design; no false availability or invented ratings | Implementation in progress |
| Profile pane and `/care/clinicians/:id` | Public approved projection; focus/Escape/profile links; guest Sign in to Book retains exact service | Implementation in progress |
| `/request` | Existing in-memory private draft/auth return; coherent public framing, no premature broadcast | Implementation in progress |
| `/care/select/:offering` | Existing allowlisted auth return; no new roles or arbitrary return URL | Retain; regression pending |
| `/policies` | Existing versioned draft/review disclosure, readable public surface; no invented approved policy | Implementation in progress |
| Help/contact links | Existing How it works/FAQ and policies; no invented support channel or speculative page | Implementation in progress |
| `/sign-in`, `/onboarding` | Accepted minimal auth shell unchanged; intentional patient/clinician transitions | Retain; regression pending |
| Authenticated home/navigation | Server session destination and curated role links unchanged | Retain; regression pending |
| Invitation entry routes | Existing participant/relationship flows untouched, shared public shell only | Retain |

Acceptance checks:390/768/1440, actual200%zoom, both tab modes/keyboard/reduced
motion, provisional long Amharic/Afaan Oromo labels, real backend guest selection
and auth return, private request draft→auth restoration, application intent,
public loading/empty/error, profile dialog focus, build/lint/privacy/PWA/deep links.
Before evidence: `screenshots/public-experience/before/`. Functional evidence and
visual comparison remain separate; owner acceptance is never inferred from tests.
