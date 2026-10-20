# Final Stage and Shared Layout Pass — 20 October 2026

This is the current bounded follow-up. Earlier sections below are historical;
their source pins must not be confused with the build now served.

- Preview: <http://127.0.0.1:8017/teletena/>. Site
  `teletena-mvp-presentation.localhost`, Bench `/home/frappe/frappe/frappe-bench`.
- Branch `feat/public-experience`, draft [PR48](https://github.com/natnaelTi/tele-tena/pull/48),
  dependent on draft PR47 (`feat/guest-first-mvp`). Earlier ancestry preserved.
- **Packaged runtime f679e6ce8a1a8169b9bba16626a2880e5e212a75**. Subsequent evidence-only commits do not change runtime.
  Frappe15.121.2, ERPNext15.121.6, Python3.12.3; build Node24.13.0.
  The separate Frappe16 compatibility Bench is not the preview and was untouched.
-49 HTTP-served artifact hashes match `release.json`. JS
  `assets/index-r5bd3fIg.js` SHA256
  `ed3cb437f489aa1488cfc6a7cb88c889aac099a82f6449eec18aa65037dfd0cb`;
  CSS hash is recorded in [release identity](screenshots/final-polish/release.json).
- Scoped local web, Redis, worker and scheduler remained running. No restart,
  migration, seed, provider/access switch, framework or shared dependency change.

## Concrete Visual Corrections

The owner annotation `/home/frappe/teletena-design-reference/stage-correction.png`
was opened and visually inspected; it remains outside the repository. Green
marks require the complete projecting wooden corner; yellow marks require the
rug to continue to its own complete corner. These supersede the earlier cropped
stage images, while the accepted composition and hero colors remain.

| Requirement | Implemented / visually inspected | Paired evidence |
|---|---|---|
| Full patient stage | Complete V-shaped wood fascia and rug corner, transparent margin; no mask or clipped foreground. Desktop scene keeps its scale and bleeds over the wave boundary. | [Before](screenshots/public-stage-v3/patient-1440.png) / [after](screenshots/final-polish/hero/patient-1440.png) |
| Full clinician stage | Complete floor/rug and transparent surroundings. Phone/hologram SVG motion remapped to the new asset; no new live media. | [Before](screenshots/public-stage-v3/clinician-1440.png) / [after](screenshots/final-polish/hero/clinician-1440.png); [detail](screenshots/final-polish/scene-detail.png) |
| Shared role navigation | Logo left, bilingual wordmark left-aligned, role links/account/language/notifications right. Header visible on ordinary routes. Patient/clinician/reviewer/Medical Lead use the same masthead and mobile More navigation. Only homepage hero retains initial conceal. | [Patient before](screenshots/final-polish/before/patient-patient-account-1440.png) / [after](screenshots/final-polish/after/patient-patient-account-1440.png); [reviewer before](screenshots/final-polish/before/reviewer-admin-applications-1440.png) / [after](screenshots/final-polish/after/reviewer-admin-applications-1440.png) |
| Cohesive surfaces | Blue-gray canvas, blue heading hierarchy, subtle borders/shadows, consistent cards, readable controls and focus. Low-specificity shared rules retain page-specific wallet, calendar and call patterns. | [Services](screenshots/final-polish/after/counselor-clinician-services-768.png), [earnings](screenshots/final-polish/after/counselor-clinician-earnings-1440.png), [review queue](screenshots/final-polish/after/reviewer-admin-vetting-1440.png) |
| Mobile directory | Removed duplicate workspace gutters, full-width request action, one disclosure arrow. Initial final-pass render still constrained the action to35%; computed-style inspection found the inherited max-width and corrected it. | [Before](screenshots/final-polish/before/patient-patient-discovery-390.png) / [after](screenshots/final-polish/after/patient-patient-discovery-390.png) |
| Responsive content | All46 route/actor views rendered at390/768/1440. Entire mobile survey inspected; key desktop/tablet compositions and full-page hero images inspected. Actual200% browser zoom tested independently. Tables and tabs retain intentional accessible scrolling rather than clipping content. | [Route-by-route evidence](screenshots/final-polish/after/route-survey.json); [availability390](screenshots/final-polish/after/counselor-clinician-availability-390.png); [patient requests390](screenshots/final-polish/after/patient-patient-requests-390.png) |

The original task images touched the canvas bottom and were rejected. Final RGBA
assets have real transparent space below their lowest corners. At1440/1920 the
complete floor may extend beyond the hero; on mobile the image fits available
width. No page overflow is hidden to obtain a pass. The reference annotation is
composition guidance, not an automated universal pixel-match claim.

## Focused Functional Results and Provenance

| Check | Result / source |
|---|---|
| Production build | Pass on f679e6ce8a1a8169b9bba16626a2880e5e212a75; clean runtime checkout, locked dependencies. Existing large-chunk warning remains. |
| Route/actor survey | Pass46 actual backend views ×3 widths on f679e6ce8a1a8169b9bba16626a2880e5e212a75. Guest/public/auth; patient, clinician, applicant, reviewer, couples partner; existing patient/clinician consultation details. `/clinician/offers` intentionally redirects to the accepted consolidated Requests workspace. Read-only navigation does not prove every underlying operation. |
| Hero/state suite | Pass on81085a4f61eeb31052ca0e6bc0aa732f1428986c: both modes390/768/1440/1920; four screen waveforms/five figure layers, no mask, guide accordion, styled language picker, reduced motion, no media/protected writes. Later changes only remove duplicate directory gutters/arrows and widen its mobile action. |
| Real backend public journeys | Pass on81085a: reactive filters/profile focus, password sign-in→exact selected offering/reload, guest draft→authentication→Requests without publication/storage, clinician application intent, public information/policies, provisional locale/mobile states. No request/booking/finance API changes. |
| Navigation and sign-out | Pass on81085a: patient/clinician/reviewer home redirects, role menus,390/768/1440 headers, Account/Escape focus and server-session invalidation. Later directory-only styles leave this behavior unchanged. |
| Language and keyboard | Pass on81085a: real-role native picker1440/390, keyboard open/Escape/focus return; existing locales retained. |
| Actual200% browser zoom | Pass9 authenticated views on81085a: patient Account/Requests/Appointments; clinician Availability/Requests/Account; reviewer Applications/Vetting/Catalog. Chromium tabs.setZoom(2), inner720/outer1440/DPR2. Public hero/directory/profile/application guide pass on98c7d84; final change only removes private directory action max-width. [Zoom evidence](screenshots/final-polish/zoom/), [public zoom](screenshots/final-polish/zoom-public/). |
| Lint | Pass; existing warnings only. No new lint errors. |
| Asset/privacy | Pass on f679e6ce8a1a8169b9bba16626a2880e5e212a75: all49 HTTP-served hashes verified; exact20 private credential values absent from packaged artifacts; no maps/config/environment files. |
| Preservation | Site configuration and24 original private manifests/provider/key files remain byte-identical. No data reseed/reset, balances/credentials/consent changes or private upload modifications. |

Commands: `scripts/browser-mvp-polish.cjs`, `browser-mvp-polish-zoom.cjs`,
`browser-public-stage.cjs`, `browser-public-experience.cjs`,
`browser-role-navigation.cjs`, `browser-private-language.cjs`,
`browser-public-zoom.cjs`, `scripts/check_review_assets.py`, locked production build
and frontend lint. Browser scripts use private local manifests, never output passwords.
[Served identity](screenshots/final-polish/release.json) records the current asset hashes.

No backend/schema/dependency or consultation-core change: inherited financial,
couples, migration and hosted-call evidence remains in the authoritative MVP
matrix. Those expensive suites were not repeated for these visual-only changes.
The active consultation keeps its accepted dark focused header and media-left /
details-right layout; marketing navigation is not inserted into an active room.

## Reviewer Walkthrough and Remaining Limits

Open the stable preview, compare both hero modes and the complete front stage
corners. Scroll down/up to exercise homepage nav. Open Directory→View Profile→Sign
in to Book. Sign in using the existing private account manifest and inspect
patient/clinician/reviewer header, Account, Requests, calendar, care records and
review forms; on mobile use More and Escape/backdrop dismissal. Existing credentials
remain in the site's private `tt-demo-mvp-v2-accounts.json`.

Codex visual inspection is recorded separately from owner acceptance. Owner
review is pending; no claim of owner approval. Native Amharic/Afaan Oromo review,
physical-device calls and live SMS/email delivery remain external validation;
this styling pass does not change or newly verify them. No remote deploy or merge.

---

# Clinician Stage, Public Composition and Application Guide —20October2026

This is the current follow-up to the owner-reviewed hero correction below. The
preceding crop/feathered clinician image is superseded by the complete stage.
The single MVP matrix retains the earlier evidence and records this revision.

## Current Preview and Identity

- <http://127.0.0.1:8017/teletena/>; site
  `teletena-mvp-presentation.localhost`, Bench `/home/frappe/frappe/frappe-bench`.
  Observed Frappe15.121.2/ERPNext15.121.6/Python3.12.3; Node24.13.0 build.
- Branch `feat/public-experience`, draft [PR48](https://github.com/natnaelTi/tele-tena/pull/48),
  still dependent on PR47. No merge/deploy/reseed or environment repair.
- Exact packaged runtime `151d178eb8dc7fb21a1fabdb71a6341f1f2faf73`.
  Later test/evidence commits do not change application runtime or assets.
-47 HTTP-served artifacts match `release.json`; JS `assets/index-C9Cxch6n.js`
  SHA256 `0ad2335485a6799e1fdb747fa25e070de9da88239fa0df6d8ca7947614db9bbd`;
  CSS `assets/index-CPhKWpYa.css`
  `ec4e3491c305639de28b7658282ae8002554cf7c787c9c903fd54074e695d3cd`.
- Scoped web314550/Redis1999/worker314529/scheduler314544 remain running;
  HTTP200, production-built Frappe route, no Vite. No service restart/migration.

## Requirement and Visual Comparison

The owner's new written direction supersedes the earlier annotated clinician
crop. The patient stage remains unchanged. The current two-mode public design,
shared tokens and accepted private workspaces are preserved.

| Requirement / route | Implemented behavior | Functional / visual evidence |
| --- | --- | --- |
| Clinician hero `/for-clinicians` or clinician tab | Genuine transparent left/right walls; clinician, gown/stethoscope, furniture, window and complete rug enclosed by an uncut raised wood stage. No oval crop or whole-scene fading. Phone shows a TeleTena consultation with a faceless patient and media controls. | [Before](screenshots/hero-correction/after/hero-clinician-1440.png) / [after](screenshots/public-stage-v3/clinician-1440.png); also [390](screenshots/public-stage-v3/clinician-390.png), [768](screenshots/public-stage-v3/clinician-768.png), [1920](screenshots/public-stage-v3/clinician-1920.png). Visually inspected by Codex; awaiting owner acceptance. |
| Illustrative screen activity | Three holograms and phone have screen-aligned audio bars with varied durations/delays; clipped image layers add gentle character motion, including the clinician. SVG coordinates scale with the image, not viewport offsets. No media capture, live audio or real participant activity is claimed. | Four waveform groups,20 bars and5 character layers; actual computed waveform motion checked. Static reduced-motion and Help motion-off inherited; [reduced-motion](screenshots/public-stage-v3/reduced-motion-390.png). |
| Wave boundary and supporting homepage | Hero no longer clips its wave SVG. White closing layer extends below colored layers to avoid a flat colored strip. Steps, service/benefit surfaces, privacy/approval panel, FAQ and final CTA reuse the blue–teal hierarchy. | [Patient before](screenshots/hero-correction/after/hero-patient-1440.png) / [after](screenshots/public-stage-v3/patient-1440.png). First v3 render exposed a bottom strip; it was rejected and corrected before final screenshots. Natural vertical scrolling retained. |
| Hero brand/language/nav | Both wordmark lines align left; Amharic words no longer spread apart. Native language selector sits beside Sign In. Header conceals with transform/opacity first and delayed visibility, remaining inert during conceal. | Keyboard locale selection; reveal/retract timing and responsive screenshots pass. Native dropdown styling shared with public/authenticated navigation. |
| How It Works tour | Coherent illustrative personas Mekdes Abebe/Samuel Tadesse, generated portraits, readable service/time/price/request/call content. One introductory disclosure replaces repeated Example/Fictional labels. Local interactions remain isolated from booking, finance, roles and media. | [Patient](screenshots/public-stage-v3/tour-patient-1440.png) / [clinician](screenshots/public-stage-v3/tour-clinician-1440.png), full tour click-through with zero protected writes. These personas/photos are not public directory or clinical data. |
| Clinician application questions | Read the Application Questions opens `/how-it-works#clinician-application`, with six keyboard-native accordions: profile, credentials, scopes, affiliations, individual human review and approval-to-publication readiness. Explains private evidence, separate scope decisions, requests for information and resubmission. | [1440](screenshots/public-stage-v3/application-guide-1440.png), [768](screenshots/public-stage-v3/application-guide-768.png), [390](screenshots/public-stage-v3/application-guide-390.png), [actual200%](screenshots/public-stage-v3/application-guide-200-percent.png). Deep link, scroll position, clinician tour intent and keyboard expansion pass. |
| Shared language picker | Existing native select now reuses the established field-picker radius, chevron, hover/focus, selected option and popup surface. Chromium base-select enhancement; other browsers retain native keyboard controls. No new dropdown dependency. | Real-role sign-in and popup/Escape/focus checks at1440/390: [patient](screenshots/public-stage-v3/language-patient-390.png), [clinician](screenshots/public-stage-v3/language-counselor-390.png), [reviewer](screenshots/public-stage-v3/language-reviewer-1440.png). Locale choices unchanged. |
| Terms & Privacy | Removed review-environment suffix from link/heading in all current public locations and translations. Policy body/version draft notice remains truthful. | Policy route and public/internal content boundary pass; no policy versions or prior acceptance records changed. |

Paired screenshots were opened and inspected for composition, stage edges, text
clearance, picker states and responsive wrapping. No universal pixel score or owner
acceptance is claimed. At tablet/mobile widths the image follows the copy; the
stage remains fully visible. Actual200% uses browser zoom and scrolling, not CSS
zoom or clipping. Long text/Amharic/Afaan Oromo layout samples passed, but new guide
body copy has English fallback and still needs translation/native-language review.

## Actual Checks and Evidence Reuse

- Production TypeScript/Vite build and lint pass; existing warnings/bundle-size
  advisory remain. No dependency/lockfile/backend/schema changes.
- Final runtime: `browser-public-stage.cjs` passes both modes390/768/1440/1920,
  actual image decoding, left brand, hero language keyboard, animated nav retract,
  waves overflow, screen activity, guide link/keyboard, coherent tour, policy
  label/draft notice and reduced motion with no media/protected writes.
- `browser-private-language.cjs` passes real patient/clinician/reviewer sign-in,
  shared picker appearance, keyboard open/Escape/focus return and no locale change.
  Initial test selected a detached auth-header control during routing; the test
  now waits for the actual workspace, without relaxing style/focus assertions.
- Final actual Chromium200%: both modes, CTA focus, mobile navigation, directory,
  profile booking action and guide keyboard accordion pass. Screenshot capture
  waits for the bounded transition to finish so evidence shows usable content.
- Real-backend `browser-public-experience.cjs` and `browser-role-navigation.cjs`
  pass on bff32b9 (same application except three wave-path closure coordinates):
  filters/profile, exact offering return and reload, guest draft→auth→Requests
  without publication/persistent health text, clinician intent, role redirects,
  mobile curated navigation and session-invalidating sign-out. These tests were
  not repeated after the wave-only fix.
- `browser-public-atmosphere.cjs` passes the full updated tour click-through,
  Help motion preference, caption focus/Escape, Contact safety and policy boundary.
- Explicitly injected loading/empty/error/retry tests pass on the final runtime;
  these verify UI resilience, not real-backend matching behavior.
- Asset/privacy scan passes:47 artifacts, no source maps/config and exact scan
  against20 private values. Retained configuration and24 original private
  manifests/provider/key files remain byte-identical.
- Public-only SW cache, current built deep links, offline fallback and online
  recovery pass. Full old-browser→new-build update evidence remains inherited
  because service-worker/update logic is unchanged.
- Unchanged finance/couples/LiveKit/OTP/provider/fresh-install suites are inherited,
  not rerun or claimed as new UI-patch evidence. No outbound notifications or
  real-money/provider operations occurred.

## Owner Walkthrough and Remaining External Review

1. Open the preview signed out. Try the hero language selector and both modes.
   Inspect the complete stage, phone and holograms; hover/focus the illustration
   for its disclosure. Help & Tours can disable decorative motion.
2. Scroll through the supporting sections, then back up: the navigation should
   retract smoothly and the wave edge should have no straight colored strip.
3. In clinician mode, Read the Application Questions opens the dedicated guide.
   Expand its sections with mouse or keyboard. Apply preserves clinician intent.
4. Try both How It Works tours: real-looking illustrative personas, schedule,
   sharing/offer/call states; no real booking or media is created by the tour.
5. Use existing privately stored review accounts for each role's language menu.
   The existing profile/booking/Requests journeys and account credentials remain.

Owner visual acceptance remains pending. Native translations, assistive technology
and physical devices are separate review; no live SMS/email/clinical or real-money
claims are made. No remote change or merge. [Asset provenance and prompts](public-atmosphere-assets.md).

---

## Historical Hero Composition Checkpoint

# Hero Composition Correction — 20 October 2026

This is the current follow-up in the existing public-experience acceptance matrix.
The earlier atmosphere/content checkpoint below is historical; its visible Pause
Motion button, image breathing and oval image treatment have been superseded.

## Current Local Candidate

- Branch `feat/public-experience`, draft [PR48](https://github.com/natnaelTi/tele-tena/pull/48)
  still depends on PR47. No merge or remote deployment.
- Packaged runtime: `69f33ae628201fbf2bc7f8c1e91ed9fb09659d2b`.
  Later evidence/test-only commits are not a different application build.
- <http://127.0.0.1:8017/teletena/> — site
  `teletena-mvp-presentation.localhost`, Bench `/home/frappe/frappe/frappe-bench`.
  Observed Frappe15.121.2 / ERPNext15.121.6 / Python3.12.3; Node24.13.0 build.
  The separate Frappe16 compatibility Bench is not serving this URL.
- Scoped preview status: web314550, Redis1999, worker314529, scheduler314544;
  HTTP200. No service restart, migration or setting change was needed.
-45 HTTP-served artifacts match every SHA256 in `release.json`.
  CSS `index-71HdNKoa.css`:
  `00e9e7b8540a19f5ed9ee4f75d3e89fa407bd3be4f3831510a7b15fb80889dfc`.
  JS `index-BSawgYdA.js`:
  `81bcf885600c37e25500f8788d5aa6a910c2c55335c3dd160d490a420ab4010a`.
  Frontend dependency lock unchanged:
  `a5f7a16b739627b44fcb73fb348f6c71a7974a55fec90a0d3c3caa4d6345e696`.

## Direction, Implementation and Paired Inspection

Reference: the owner's local `hero-section-correction-direction.png`, visually
inspected outside Git. It contains browser chrome and is intentionally not copied
into this repository. This approved annotation supersedes the old gallery hero
composition; it does not change private workspaces.

| Route/state | Before | Current | Comparison result |
| --- | --- | --- | --- |
| `/`, Find Care,1440 | [Before](screenshots/hero-correction/before/hero-patient-1440.png) | [After](screenshots/hero-correction/after/hero-patient-1440.png), [viewport](screenshots/hero-correction/after/viewport-patient-1440.png) | Removed blurry foreground plant and opaque wall. Décor/furniture retained as a transparent room diorama. Entire rug inside raised wood stage; front/right edges visible and uncut. Hero gradient serves as wall; scene reaches the right edge. |
| `/`, For Clinicians,1440 | [Before](screenshots/hero-correction/before/hero-clinician-1440.png) | [After](screenshots/hero-correction/after/hero-clinician-1440.png), [viewport](screenshots/hero-correction/after/viewport-clinician-1440.png) | Existing clinician/phone/screens/office concept retained; white gown and teal stethoscope added to viewer-right armrest. Wall extracted; narrow edge feather blends existing crop into blue. No replacement stage or new scene. |
| Image explanation | Inline caption | [Keyboard tooltip](screenshots/hero-correction/after/hero-tooltip-1440.png) | Hidden normally; hover, focus or touch reveals; Escape/blur dismisses. Concept/facility/hologram disclosure retained. |
| Responsive room | Earlier small masked scene | [390](screenshots/hero-correction/after/hero-patient-390.png), [768](screenshots/hero-correction/after/hero-patient-768.png), [1920](screenshots/hero-correction/after/hero-patient-1920.png) | CTAs first, image stacks at tablet widths, complete stage stays visible; desktop copy and image occupy separate regions. |
| Responsive practice | Earlier small masked scene | [390](screenshots/hero-correction/after/hero-clinician-390.png), [768](screenshots/hero-correction/after/hero-clinician-768.png), [1920](screenshots/hero-correction/after/hero-clinician-1920.png) | Readable headings/actions, larger scene, gown/stethoscope visible, no page-width clipping. |
| Motion/access | Prominent hero play/pause | Help & Tours → Motion Preferences | Removed hero button as requested. Optional decorative motion remains stoppable, memory-only. OS reduced-motion always wins. Three independent wave layers have varied durations/delays and crossing vertical motion. |

Manually inspected these paired compositions, not just overflow assertions.
The first enlarged render overlapped copy; it was rejected and corrected before
this evidence. Natural image proportions and all patient stage edges take priority
over stretching an image vertically. At narrower widths the scene follows the
copy instead of overlapping it. The clinician image is an AI-assisted edit and
has small generative detail variations; no claim of pixel-identical preservation.
Its original framing/crop is blended, whereas the patient's newly bounded stage
is not faded away. These are illustrations, not a real facility or practitioner.

## Actual Checks on This Runtime

- Production TypeScript/Vite build and frontend lint pass (existing lint warnings
  and existing bundle-size advisory remain; no new dependency).
- `browser-public-atmosphere.cjs`: pass; both modes390/768/1440/1920, separate
  desktop text/image regions, image decoding, hidden caption/focus/Escape,
  removed hero button, Help motion preference, independently animated waves,
  reduced motion, bounded loader, navigation threshold, pointer gradients,
  Contact mock safety, patient/clinician tour without operational writes,
  public/internal policy visibility.
- `browser-public-experience.cjs`: pass against the real retained backend;
  reactive directory filters, profile focus return, password sign-in to the exact
  selected offering, reload, guest draft → authentication → Requests without
  publication or browser-persistent health text; clinician application intent,
  mobile menu dismissal, provisional Amharic/Afaan Oromo samples and reduced motion.
  No live OTP, booking publication or financial fixture writes.
- `browser-public-zoom.cjs`: pass at actual Chromium200% (`tabs.setZoom(2)`,
  inner720/outer1440/DPR2/visualViewport1), both modes, CTA keyboard focus,
  navigation, directory and profile booking action. Scroll remains available;
  [patient](screenshots/hero-correction/after/landing-patient-200-percent.png) /
  [clinician](screenshots/hero-correction/after/landing-clinician-200-percent.png).
- `check_review_assets.py`: pass; artifact hashes, scope, no source maps/config,
  exact scan of20 private credential values without printing them.
- Retained-site preservation: configuration values and24 original private
  manifests/provider/key files byte-identical; no reseed/access/provider changes.
- Diff from preceding `fe702a4` has no backend, schema, dependency-lock or build-
  helper changes. Unchanged financial/couples/hosted-call/fresh-install suites
  were not repeated for this image/CSS/public-motion patch; prior evidence below
  remains inherited, not newly asserted on this UI correction.

## Remaining Review

Owner visual acceptance is pending. Native-language review, assistive technology,
physical devices and live SMS/email receipt are not established by these checks.
This patch does not approve production policies, enable real money, alter clinical
records, or change Selfmade. Asset prompts/hashes: [provenance](public-atmosphere-assets.md).

---

## Historical Atmosphere / Editable Content Checkpoint

# Public Atmosphere and Editable Review Content — 20 October 2026

Current evidence addendum to the single `mvp-screen-acceptance.json` matrix.
The earlier `public-experience-acceptance.md` documents the preceding2067a34
public checkpoint; its screenshots remain the before comparison here.

## Review Candidate

- Draft PR48, branch `feat/public-experience`, dependent on unmerged PR47; earlier
  ancestry remains intact. No merge, remote deployment or shared repair.
- Source/packaged runtime: `4e5483b2643c0e329bfd09eb26d1d24b3042d75e`.
  Later test/evidence-only commits do not change runtime files.
- Production-built URL: <http://127.0.0.1:8017/teletena/>.
- Site: `teletena-mvp-presentation.localhost`; Bench/backend source:
  `/home/frappe/frappe/frappe-bench` (Frappe15.121.2/ERPNext15.121.6/Python3.12.3).
  No Vite process serves this URL.
- Node24.13.0 locked build, unchanged frontend dependency lock hash
  `a5f7a16b739627b44fcb73fb348f6c71a7974a55fec90a0d3c3caa4d6345e696`.
-43 served artifacts match their `release.json` hashes. JS `index-Dq9jHhBi.js`:
  `bd616e2bcfaa96ca42e00cd2d02d54b4f643cf175f92930f75004ef7774a9b1c`;
  CSS `index-BOmApCP8.css`:
  `7aad776e5a110432aba7deb929af2fde052f6e835308c12852735780e0598897`.

## Implemented Direction and Visual Inspection

The new owner direction supersedes the previous white hero/product-card
illustration. The external sketch remains outside Git. The hero now uses bold
layered blue/teal gradients, restrained pointer-responsive lighting and two
photorealistic AI-created concepts: an Ethiopian-inspired private room and an
anonymous clinician managing a conceptual connected practice. Both are visibly
identified as illustrations, not actual facilities, practitioners or hologram
features. Supplied logo, established fonts, palette and controls remain.

Manual audience selection changes copy, image, actions and supporting sections;
it never changes account roles or pending booking/request intent. The bilingual
public wordmark places TeleTena and ቴሌ ጤና on separate aligned lines beside the
existing icon. Private workspace branding/composition remains unchanged.

A CSS dimensional stethoscope mark appears in a non-intercepting800ms initial
transition; public route changes use420ms. Its final position tracks the public
logo, including a delayed hero render after session lookup. This is decorative,
not a false progress percentage or a wait for all network requests. It never
blocks input, extends to private consultations, or waits indefinitely. Reduced
motion removes the overlay and motion. No WebGL/new animation dependency.

Hero navigation is hidden/inert initially, then drops into view beyond75% of the
hero. Logo, Sign In and both audience options remain available in the hero.
Session-check errors retain visible navigation and a usable retry. Contact
replaces For Clinicians in public navigation; the clinician selector, CTA,
information route and footer remain discoverable. Every homepage section has an
ID; native smooth anchors/scroll padding, a working skip target, standard page
entry, restrained section motion, layered waves and a mouse scroll cue are used.
Ambient smoke, lighting and image breathing pause through Pause Motion. Reduced
motion makes them static. Nothing is hidden to force a no-scroll layout.

Inspected rendered1440/768/390 images, comparing the preceding public layout and
current approved written direction. Desktop has dominant copy left and a blended
room image right; mobile stacks copy/CTAs before the image. Text retains contrast
outside the viewport rather than dimming sections. Header, footer, Contact and
review-document layouts stay cohesive; contact cards collapse on mobile. Actual
200% Chromium zoom remains usable with scrolling. Amharic/Afaan Oromo rendering
and long labels were checked; new editor/tour/policy copy has English fallback
and still needs translation/native approval. No owner acceptance is inferred.

How It Works contains a full interactive workspace tour with patient/clinician
selection, page navigation and working local micro-flows: service/time/sharing
selection, appointment preview, readiness toggle, example hours, offer preview
and consultation explanation. All data is explicitly fictional and in memory.
The tour never accesses devices or creates accounts/bookings/payments/requests.
Real actions remain linked to the existing authenticated product. This is a
learning surface, not evidence that a visitor booked care without authentication.

## Reviewer Contact and Policy Management

Reviewer Account → **Public Contact and Policies** supports:

1. Select Contact Details or one of eight documents.
2. Edit, Save Draft and reload; drafts do not change public content.
3. Inspect Preview and Version History.
4. Explicitly Publish Review Version; prior revisions and acceptances remain.

Contact fields: organization, support/privacy email, phone, address, hours and
fictional-data flag. Initial reserved `.example` addresses and a fictional office
are conspicuously labeled; no mock mailto or message-sending form exists. A
reviewer can configure real contact details later; that does not configure SMTP,
SMS or authorize outbound delivery. Invalid emails and stale-reviewer conflicts
produce safe actionable feedback. Form labels remain correctly associated with
controls. Switching sections cannot save the previously selected document into
the next one.

Public boilerplate documents: Terms of Service, Privacy Policy, Teleconsultation
and Sharing Information, Booking/Cancellation/Demonstration Payments,
Support/Complaints/Safety, and Clinician Conduct/Scope Standards. Internal-only:
Records Retention/Access Procedure and Security Incident/Safeguarding Procedure.
All remain **review drafts**, with local legal/clinical/operator decisions clearly
unresolved. Editing or publishing a review version is not legal approval, a
regulatory claim, a change to operative financial rules, or retrospective consent.
This is an editable initial document inventory, not a determination that every
jurisdiction's necessary legal instrument has been completed.

Drafting context: [Ethiopian Ministry of Justice publication](https://justice.gov.et/en/law/personal-data-protection-proclamation/)
and [WHO ethical/data-protection principles](https://smart.who.int/trust/ethical_principles.html).
These sources are reviewer context only. Templates primarily describe implemented
TeleTena behavior; they do not select lawful grounds, retention periods, statutory
deadlines, dispute jurisdiction, liability provisions or provider agreements.

## Backend, Migration and Preservation

Additive patch `v1_43_public_content` creates app-owned revision, head and audit-event
tables. Stable boilerplate IDs plus INSERT IGNORE preserve reviewer edits on repeat
migration. Draft writes create immutable versions, with optimistic revisions and
row locks; publication records an actor/time event. Only Tele Tena Approver may
manage content. Guest/patient/clinician access is denied server-side. Public
projection contains published contact/public documents only; internal documents,
drafts and author metadata are excluded. Plain-text rendering uses React escaping,
not executable HTML. Generic DocType access does not expose these command tables.

Terms/Privacy acceptance records store current published version IDs; stale versions
are rejected. Existing acceptance rows are not rewritten. Policy head locks keep
acceptance validation consistent with publication. No patient preferences, selected
files, booking snapshots, credentials, provider switches, funds or existing demo
records are reset. This patch adds boilerplate content only, not a demonstration
scenario reseed.

Before the native site's migration, the existing backup helper created and verified
its database, public files, private files and configuration at private local path
`/home/frappe/teletena-public-experience/before-v143` (not Git/public assets).
The native site migration passed. Only the owned preview processes were stopped
and restarted; shared/unrelated Bench services were untouched. Use the existing
scoped `scripts/local_review.py status|start|stop --keep-queue` lifecycle as before.
No production installation is authorized by this report.

Separate Frappe16.2.1/ERPNext16.1.0/Python3.14.2 tests ran current backend source
against `teletena-guest-first-test.localhost` in the compatibility Bench. First
creation and repeat execution of the new patch passed. Full-row hashes of11
preexisting profile, appointment, consent, history and financial tables remained
identical. Four persisted content tests pass: authorization/public allowlist,
draft/publication/validation/audit, immutable versions/conflicting edits/internal
visibility, and stale/current/idempotent policy acceptance. Tests rollback their
fixture changes. No outbound provider calls.

The current-source guest-first suite also passed17 tests on that compatible site,
including policy acceptance/no role escalation, defaults/opt-outs, public eligibility,
file ownership/grants, booking constraints, notices and request presence. This is
not a fresh whole-site installation claim. Full calls/couples/finance and fresh
installation were not repeated for unchanged workflows; previous release evidence
remains historical in `guest-first-release-readiness.md`.

## Executed Browser and Build Checks

On packaged runtime4e5483b:

- `browser-public-atmosphere.cjs`: bounded transition, hidden/revealed header,
  pointer gradients, pause/reduced motion, bilingual brand, mock Contact safety,
  both interactive tour flows with zero operational writes, public/internal
  policy separation, screenshots390/768/1440: pass.
- `browser-public-experience.cjs`: real public API filters/profile/focus,
  exact-offering password return/reload, memory-only guest draft→authentication→
  restored Requests without publication, clinician intent, locale samples: pass.
- `browser-reviewer-content.cjs`: real backend invalid-email rejection, identical
  mock-contact save/reload/publication and internal editor, three widths: pass.
  It adds content versions/events but changes no contact values or policy text.
- `browser-role-navigation.cjs`: real patient/clinician/reviewer redirects, curated
  menus, mobile fit and session-invalidating logout: pass.
- `browser-public-states.cjs`: explicitly injected session/catalog/policy
  loading/failure/empty states and real retry recovery: pass. Initial test failures
  incorrectly matched alert text without its nested retry button; assertions now
  target the same required message within the alert. No guard/assertion removed.
- `browser-public-zoom.cjs`: actual200% browser zoom, both modes, menu/CTA and
  profile booking action reachable: pass. This is not CSS zoom emulation.
- Production TypeScript/Vite build and lint: pass; existing lint/bundle warnings
  remain.8 production deep routes (including Contact) and all43 served hashes pass.
- Asset/privacy scan: pass, including20 exact private credential values without
  printing them. Site configuration and24 original private/provider/manifest files
  remain byte-identical to the preservation snapshot.
- Current real service-worker control, static-only cache inspection, offline
  fallback and online recovery: pass. Worker unit checks pass. The earlier explicit
  controlled-browser update proof is inherited; worker/update implementation is
  unchanged. An existing owner tab may use Refresh to Update, not cache deletion.

Logs remain privately under `/home/frappe/teletena-public-experience/`.

## Screenshots and Owner Walkthrough

Before/after pairs are under `docs/screenshots/public-atmosphere/`:

- `before/landing-patient-1440.png` vs `after/hero-patient-1440.png`.
- `before/landing-patient-390.png` vs `after/hero-patient-390.png`.
- `before/landing-clinician-1440.png` vs `after/hero-clinician-1440.png`.
- `before/how-1440.png` vs `after/tour-patient-1440.png` and
  `after/tour-clinician-1440.png`.
- `before/policies-1440.png` vs `after/policies-1440.png`.
- New Contact and reviewer content images at390/768/1440; public zoom, locale,
  reduced-motion and failure-state evidence included. Captures were visually
  inspected; screenshot existence alone is not acceptance.

Open the preview signed out, switch audiences, move the pointer and pause motion.
Scroll past most of the hero to reveal navigation. Open How It Works and try the
patient and clinician workspace pages. Contact shows fictional configured entries;
Policies shows the public review library. Sign in as the existing fictional reviewer,
open Account → Public Contact and Policies, save a draft, inspect it and explicitly
publish its review version. Internal documents never appear in the public library.
Real booking/request actions continue through their existing authenticated paths.

The new images, prompts and provenance are recorded in `public-atmosphere-assets.md`.
Owner visual acceptance, native translation, real contact/legal/operator approval,
physical-device/assistive-technology review and live delivery remain separate.
No remote deployment, merge, real-money activation or claim of legal approval.
