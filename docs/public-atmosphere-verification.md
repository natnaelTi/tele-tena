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
