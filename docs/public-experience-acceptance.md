# Public Experience Redesign — Historical 2067a34 Checkpoint

Current owner-directed atmospheric/contact/policy work and packaged identity are
recorded in [public-atmosphere-verification.md](public-atmosphere-verification.md).
The evidence below is retained for before/after comparison, not the current build.

This is the bounded public overlay of the existing MVP matrix, not a new MVP
tracker. PR47/f534f4ba950969319a5a313f011d4b30ce5129e8 remains its parent.
No backend, schema, dependency, provider/access setting, seed or private-workspace
workflow changed. The prior Selfmade release pin and deployment reports remain
historical and unchanged. This work has not been deployed remotely.

## Candidate and environment

- Branch: `feat/public-experience`, dependent on `feat/guest-first-mvp` (draft PR47,
  itself dependent on PR46). No merge or force push.
- Packaged runtime: `2067a34951c0c6f687584526b56104814f902064`.
  Subsequent acceptance/screenshots commit contains no runtime changes.
- URL: <http://127.0.0.1:8017/teletena/>, production build, not Vite.
- Site: `teletena-mvp-presentation.localhost`.
- Bench/backend source: `/home/frappe/frappe/frappe-bench`, this branch;
  Frappe15.121.2, ERPNext15.121.6, Python3.12.3. Backend is byte-identical to PR47.
- Separate compatibility tests: `/home/frappe/teletena-compat/bench`, Frappe16.2.1,
  ERPNext16.1.0, Python3.14.2; unchanged backend checkout d8f11c8, named disposable
  `teletena-guest-first-test.localhost`. These are focused backend checks, not a
  claim that this frontend was served from the Frappe16 bench.
- Node24.13.0 locked production build; frontend lock SHA256:
  `a5f7a16b739627b44fcb73fb348f6c71a7974a55fec90a0d3c3caa4d6345e696`.
- Served JS: `assets/index-CNgstPFV.js`, SHA256
  `7fc2da4edffb2263dacb87bf29bb11aa222c6960cfb3fae4aee9823ff0bc1bbf`.
- Served CSS: `assets/index-BD2S5Unk.css`, SHA256
  `d22a12746d03127ae3aaaa46777d1ee8ba2496b5953dcea274e9a960be5081db`.
- `release.json` records all41 artifact hashes; every served artifact was fetched
  and matched. Web277161, queue Redis1999, worker277150, scheduler277157 observed
  running. No process/service changes were necessary for this frontend revision.

## Reference and visual comparison

Inspected the original sketch at
`/home/frappe/teletena-design-reference/landing-page-sketch.jpg` before continuing.
It remains outside Git. Its first patient view/manual clinician selection and
scroll indicators are implemented; the written no-loading/no-carousel brief
supersedes the sketch's animated-loading annotation. Existing A01/#welcome,
A02/A03 authentication and C02/profile components inform the shared visual
language. The explicit new two-mode brief supersedes A01's simultaneous columns.
No universal pixel-match percentage or owner acceptance is claimed.

Compared rendered before/after images at matching1440 and390 widths and inspected
new tablet768 layouts. Both modes have hero copy/CTA left, labeled product view
right at desktop, with copy before the illustration on mobile. The previous
stacked headline and competing audience cards are replaced by one clear selected
purpose. The logo, Inter/Noto fonts, blue–teal palette, outline icons, controls and
demonstration ribbon remain. Fictional product views are labeled illustrations;
actual service links come from the public API, not fabricated catalog content.

The header uses existing role-specific links with a compact mobile dialog; footer
has Care, Clinicians and Information groups. Directory cards retain the existing
approved public hierarchy, real fees/status/trust data and service grouping;
spacing, request entry and filter surfaces now share the public composition.
Profile pane and full profile retain the existing booking/identity rules. The
narrow pane scrolls to its actions rather than clipping content. Help uses the
same three-step/FAQ components; policy layout preserves the review-mode warning.
No contact route/channel exists in the app: Help & FAQ resolves to the existing
explanation, rather than inventing a contact page or provider details.

At390, all sections become single column except compact two-column footer groups;
at768, hero and steps remain readable without horizontal clipping. Actual200%
Chromium zoom (outer1440, inner720, DPR2, visualViewport scale1) was inspected,
including reachable hero CTA, menu, directory and profile booking action.
Amharic and Afaan Oromo long labels/glyphs wrap without truncation in both modes;
translations are provisional, and some existing footer/catalog copy remains
English. Native-language approval is pending. Reduced-motion removes animation.
No material layout defect remains known in this bounded scope; owner visual
acceptance remains pending.

## Route/state acceptance

“Visual inspected” means Codex compared composition and states; it does not mean
owner approval. All route paths below are under `/teletena/`.

| Route/state | Reference/expected action | Functional result | Visual result/evidence |
|---|---|---|---|
| `/`, guest Find Care default | Sketch first view + revised A01; exact headline, directory/request CTAs, illustration,3steps, actual services, privacy, FAQ, finalCTA | Passed real backend categories and navigation; loading/failure retry separately injected | Visually inspected390/768/1440 and200%; `after/landing-patient-*` |
| `/`, For Clinicians tab | Sketch second view; tailored headline, practice view/steps/benefits/approval/FAQ/CTAs | Passed keyboard arrows/Home, selected states, application intent; no role/return-intent mutation | Visually inspected same widths/zoom; `after/landing-clinician-*` |
| `/for-clinicians` | Same public experience, clinician mode initially | Passed application CTA→clinician-intent registration, no account chooser | Shared clinician-mode comparison |
| `/how-it-works` and `#public-faq` | Existing explanation destination; shared steps/FAQ, no deferred search instructions | Passed route/links; browser-native scrolling | Visually inspected `after/how-*` |
| `/care`, populated/refining | C02 plus accepted service-grouped directory; View Profile only for guests | Passed real filter/reset responses and profile navigation | Visually inspected `after/directory-390/768/1440.png` |
| `/care`, empty/error/stale | Same controls, truthful status, retry/reset | UI-only injected empty/error; retry fetches real backend | `after/directory-empty-390.png`, `directory-error-390.png` |
| Profile pane | Existing profile popup, public details, Sign in to Book | Passed focus return/Escape/full-profile/selected-offering link | Visually inspected `after/profile-pane-*`; mobile action-scroll capture included |
| `/care/clinicians/:id` | Existing full public professional profile and offering selector | Passed real public data, guest booking labels/return | Visually inspected `after/profile-390/768/1440.png` |
| `/care/select/:offering`→`/sign-in`→calendar | Accepted safe opaque return; minimal A02/A03 shell | Real existing password login returns to exact selected offering; reload retains its calendar | Existing auth layout retained; no marketing shell added |
| `/request`→auth→`/patient/requests` | Existing memory-only guest draft, no premature publication | Real draft survives navigation, mode change and sign-in; no publication or text in persistent browser storage/URL | Visually inspected `after/request-*`; current service-load feedback verified |
| `/policies` | Existing review-only content; no invented approved policy | Passed real versions and explicitly injected failure/retry | Visually inspected `after/policies-*`, `policy-error-1440.png` |
| Signed-in home/public navigation | Existing server-session role destination | Patient/clinician/reviewer redirect+reload, role links, account/Escape and logout session invalidation pass | Headers fit390/768/1440; narrow names truncate visually with full accessible name |
| Mobile menu/FAQ/focus/motion | Labeled dialog, native details, visible focus, interruptible motion | Escape/focus/link dismissal pass; actual200% and reduced-motion checks pass | Inspected shared public controls; no scroll hijacking |
| Invitation/onboarding/private workspaces | Existing supported flows; public shell only where inherited | No underlying implementation changes; prior47 evidence retained, not rerun in full | No new visual acceptance claim for private routes |

## Before/after evidence

All paths below are relative to `docs/screenshots/public-experience/`:

| Surface | Before | After |
|---|---|---|
| Patient landing desktop | `before/landing-1440.png` | `after/landing-patient-1440.png` |
| Patient landing mobile | `before/landing-390.png` | `after/landing-patient-390.png` |
| Clinician entry | `before/clinicians-1440.png` | `after/landing-clinician-1440.png` |
| Directory | `before/directory-1440.png` | `after/directory-1440.png` |
| Profile preview | `before/profile-pane-1440.png` | `after/profile-pane-1440.png` |
| Full profile | `before/profile-1440.png` | `after/profile-1440.png` |
| How it works | `before/how-1440.png` | `after/how-1440.png` |
| Policies | `before/policies-1440.png` | `after/policies-1440.png` |

Before source f534f4b; after runtime2067a34. Additional after images cover tablet,
mobile, actual200%, long translated labels and explicitly injected UI failures.
Only existing fictional public profile data appears in screenshots. The sketch,
private account manifests, provider configuration and logs are not committed.

## Concrete defects found and fixed

1. Guest request returning from audience navigation could submit before its
   service options finished loading. Native required-select validation then
   stopped navigation without useful load feedback. Wait for a currently valid
   offering catalog, disable premature submission, keep draft fields and expose
   retry/stale-selection messages. Reproduced through the real auth return.
2. Global small-screen CSS wrapped public navigation into a second row. Scope
   public flex sizing and provide the compact menu instead.
3. A mobile `a.button` rule overrode desktop-link hiding for signed-in Home,
   overflowing the header alongside bell/menu/account. Exclude desktop links
   from that guest Sign-in rule. Patient/clinician/reviewer regression passes.

## Executed verification

- Production locked build (TypeScript+Vite) and lint: pass. Existing lint hook
  warnings and large-bundle warning remain; no new dependency or broad refactor.
- `scripts/browser-public-experience.cjs`: pass on2067a34, real retained backend.
  Modes/keyboard, real filters, profile focus, exact offering login/reload, guest
  draft/login/no publication/no persistent text, clinician intent, info/policy,
  widths/locales/reduced motion.
- `scripts/browser-role-navigation.cjs`: pass on2067a34, three real roles,
 390/768/1440, redirects, curated navigation, Account/Escape and invalidated
  authenticated session after logout.
- `scripts/browser-public-states.cjs`: pass on2067a34; explicitly simulated
  loading/empty/error, real retry recovery. This is resilience evidence only.
- `scripts/browser-public-zoom.cjs`: pass on2067a34 with actual Chromium200% zoom.
- Existing-browser PWA transition5cecef2→0fb892e: pass; new build notice, explicit
  refresh, changed module, static-only cache, offline/online recovery. SW code is
  unchanged through2067a34. No clinical/authenticated API caching added.
- Frappe16 focused real-backend tests:4/4 pass: public projection/composable
  filters; publication withdrawal/private photo denial; presence/capacity/expiry;
  history owner-only/grant/revoke. Backend code identical to candidate.
-7 production deep links return packaged app; all41 served artifact hashes match.
- Asset/privacy checker: pass, including20 exact private credential values checked
  without printing them. No source maps/config/private manifests in public build.
- Retained site configuration and24 original private/provider/key/manifest files
  match previous private preservation snapshot byte-for-byte. No seed, setting,
  balance, clinical record or credential reset occurred.
- No schema/Python/package-lock changes: fresh installation, migrations, full
  finance/couples/hosted-call suites were not repeated for this public-only task.
  Inherited evidence remains in `guest-first-release-readiness.md`; no new claim
  of live delivery, physical calling or final policy approval.

Reproduction commands, from repository root (existing private fictional accounts
are read locally, never printed):

```bash
export NODE_PATH=/home/frappe/teletena-browser-tools/node_modules
export TELE_TENA_REVIEW_SITE_PATH=/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost
node scripts/browser-public-experience.cjs
node scripts/browser-role-navigation.cjs
node scripts/browser-public-states.cjs
node scripts/browser-public-zoom.cjs
npm --prefix frontend run lint
/home/frappe/frappe/frappe-bench/env/bin/python scripts/check_review_assets.py \
  --site-private "$TELE_TENA_REVIEW_SITE_PATH/private"
```

Detailed local execution logs remain under
`/home/frappe/teletena-public-experience/` (not public artifacts).

## Owner walkthrough and limitations

1. Open the review URL signed out. Switch Find Care/For Clinicians; use keyboard
   arrows; inspect the tailored steps/FAQ and scroll cue. No auto-transition.
2. Find Care→filter→View Profile→full profile→Sign in to Book. Existing patient
   credentials return to that exact offering's calendar. No booking is created
   by browsing or authentication.
3. In a separate signed-out tab, Request a Consultation→enter a fictional draft
   and service→navigate home/toggle audience/return→sign in. The draft resumes in
   Requests, still unpublished until the existing publication action/consent.
   A full refresh intentionally loses the anonymous in-memory draft.
4. For Clinicians→Apply opens clinician-intent authentication; it never grants
   approval. Existing signed-in accounts opening home return to their workspace.
5. Narrow the browser/open the menu; Escape returns focus. Inspect policy review
   labels, honest catalog availability and the global demonstration ribbon.

Local lifecycle remains `env/bin/python apps/tele_tena/scripts/local_review.py
status|start|stop --keep-queue` from the identified Bench. Do not start a Vite
preview or the separate compatibility site to review this build.

Owner visual acceptance, native translation review, assistive technology/physical
mobile review and live SMS/email receipt remain separate. No external delivery or
physical call test was performed here. Existing production Terms/Privacy approval
remains pending. No universal conversion/performance result is claimed.
