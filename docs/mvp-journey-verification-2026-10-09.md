# Active MVP verification —12October2026

PR #44 remains draft and preserves PR #43 ancestry. This is **not** a handover-ready
candidate or owner visual acceptance. `mvp-screen-acceptance.json` is the only
screen/completion matrix; the sections below this active checkpoint are historical.

## Current preview and source

- URL: **http://127.0.0.1:8017/teletena/**; site
  **teletena-mvp-presentation.localhost**; Bench **/home/frappe/frappe/frappe-bench**,
  WSL **Ubuntu-24.04**. The compatibility Bench is not serving this preview.
- Branch **feat/mvp-release-handover**; packaged runtime source
  **a128a7d8bf95fdabe67a757628f28e5e970eff4c**. Later test/report/evidence-only commits
  must have an empty frontend/backend runtime diff from this build.
- Production package, no Vite. Status verifies owned web/scheduler/worker PIDs,
  working directories, selected site and served asset identity. Web at8017,
  isolated queue Redis13917, worker subscribed short/default/long, native site-only
  scheduler. No old financial worker remains after cutover.
- After reboot8017 had no listener; the original Bench did not start this dedicated
  preview. `scripts/local_review.py start/status/stop` restores it without migrations,
  seeds or unrelated signals. Stop/start and Windows `curl.exe`200 passed. See
  [local-preview.md](local-preview.md). No Selfmade/original erp-site change.

## Owner profile photos —13October2026

Current runtime/package `a128a7d8bf95fdabe67a757628f28e5e970eff4c` adds Account
upload/replace/remove for patients, clinicians and reviewers (`/admin/account`).
Four separately AI-generated fictional portraits are assigned to existing seeded
accounts only. Publication is explicit and rechecks clinician eligibility on each
download; patient/reviewer photos are owner-only and never added to encounters,
requests, care records or LiveKit metadata. No original credentials or records
were reset. A site/database/private-files backup preceded the v1.38 table creation.
The existing web alone was HUP-reloaded; worker/queue/scheduler PIDs3044/3029/3038/
3039 status passed and were not otherwise restarted. No background-job execution
claim follows from this status check.

Checks actually run:
- Native Frappe15 test `Presentation.test_profile_photo_owner_visibility_validation_and_revocation`
  passed1/1 in3.129s: owner/other actor/guest denial, current discovery projection,
  withdrawal, replacement invalidation, malformed/SVG/oversized rejection,
  initial table creation and repeat patch preservation.
- `scripts/browser-profile-photos.cjs` passed on this production package with real
  persisted accounts: patient/clinician/reviewer uploads, patient replace/remove/
  reload, invalid upload preserving previous photo, clinician visibility change,
  guest/reviewer download denial and actual discovery photo rendering.
- Account screenshots captured390/768/1440; patient390, clinician1440,
  reviewer1440 and discovery1440 visually inspected. Compact controls follow
  retained Account components. This is an owner-requested reference extension;
  no universal pixel-match or owner approval claimed. Committed evidence:
  `docs/screenshots/mvp-current/a128a7d-profile-photos/`.
- Locked production build/typecheck passed; lint exit0 with pre-existing hook
  warnings; diff whitespace check passed. Served release identity matches above.
- Explicit seed first run added4; repeat added0/preserved4. Repeat patch on
  presentation site retained photos. Neither operation touches funding/approval.

Full fresh-install, Frappe16, hosted media, OTP delivery and financial suites were
not repeated: this focused addition changes no media/auth/funds workflow. Full MVP
acceptance gates remain as recorded below; provisional photo translations require
native review. Photo security/storage/setup details: `profile-photos.md`.

## Guided application/reviewer UX and help island —13October2026

Current package `834ed2d0c6a1600c0a5d0c4d01c97e0f564dda15`. Owner-requested UX
changes keep the same server authorization, rubric, scope decisions and evidence
requirements. General application review is profile -> private documents -> general
decision. Scope review chooses one application, then documents -> credentials ->
assessment -> decision/readiness. Secondary operations/appeals are expandable.
Assessment dimensions open individually and show completion; stage focus and
scroll position follow navigation. Safe feedback identifies incomplete scores,
rationales and findings. Existing mandatory gates and credential provenance are
unchanged. Missing documents are distinguished from an optional unselected reference.

Clinician evidence collection is now inside the experience stage: save a draft,
then attach private documents grouped by selected service. Locked submitted/approved
applications cannot accidentally be included in a new-scope batch; clarification,
renewal and reconsideration retain their existing routes. No automatic scope grant.

Help & tours is one global bottom-right icon for all React routes/roles. Role-aware
workspace tours remain authenticated and server-persisted. The reviewer wiki has
seven sections and the walkthrough has seven steps. Tour launch does not navigate
away from unsaved input or protected calls/sign-in/onboarding/payment steps. The
static offline fallback has a generic help modal, with role-specific tours available
after reconnecting. No private data is cached. Reviewer entries remain in page
memory between steps/queue selections, not localStorage; reload loses unsaved
review fields. Clinician draft persistence is unchanged. See `reviewer-guide.md`.

Actual evidence: two real Frappe tests passed6.205s on the disposable site
(`/tmp/tt-guided-final-backend.log`): clarification/private evidence/resubmission/
credential-provenance/decision, plus resume/privacy and tour preferences/permissions.
Built-browser real-backend inspection passes for guest, patient, clinician and
reviewer at390/768/1440: global icon, role-specific guide, modal focus return,
four-stage scope input preservation, general review stages, clinician evidence
entry, and tour Next/Back. No approval, rejection, file upload or dismissal was
recorded in the presentation browser check. Amharic/Oromo guide layout captures
pass; translations are provisional, not native-approved. Actual Chromium200%
zoom verifies720CSS-pixel width, queue/help keyboard scrolling, close and focus
return (`/tmp/tt-guided-help-zoom.log`, unchanged queue/guide layout from4b6f155).
Offline generic help opens/closes without API actions. Build/typecheck and lint
pass with inherited warnings. Evidence/comparison notes:
`docs/screenshots/mvp-current/834ed2d-guided-review-help/`.

These are explicit owner-authorized composition changes to I03/I04/B07/B09,
not a claim of matching the old single-page prototype or owner visual acceptance.
No schema migration, financial repair, provider send, framework edit, merge or
remote change. Existing consultation media/End source is unchanged; hosted calls,
financial suites, fresh install and physical-device testing were not rerun for
this UX-only workflow presentation change. The wider MVP release gates remain.

## Missing scope-license evidence feedback —13October2026

Package `45159455eaaba103f019a0142481172ccd8d37e6`. Read-only inspection of the
owner-reported Submitted application confirmed no scope evidence documents;
the parent definition is Approved/active. Optional scoring references therefore
have no entries, and mandatory credential provenance cannot select a license.
A general resume is not a scope-specific License or registration document.
The server correctly fails credential_provenance_required; useAction previously
fell back to a generic417 error and concealed that requirement.

Reviewer cards now explain missing license evidence, optional score references,
and Request information -> owner upload/resubmit. Credential provenance/date,
mandatory assessment, score completeness, catalog review and expiry errors have
safe localized messages. An explicit Clear unfinished credential check resets
only the local unsaved source/date/reference/evidence fields and verified flag;
it makes no decision or database change and avoids the existing source-without-
verified-flag rejection when requesting clarification. The reviewer still chooses
Request information and records a meaningful reason; the applicant can upload
only in Draft/Clarification. Approval gates, private evidence access and all
existing records remain unchanged. No automatic verification or approval.

Checks run: existing real Frappe clarification/private evidence/resubmission/
credential-provenance/scope-decision regression passed7.704s on the isolated
fixture site (`/tmp/tt-evidence-review-regression.log`). The actual presentation
reviewer browser verified the missing-evidence explanation, empty license selector
and explicit unfinished-check clearing (`/tmp/tt-scope-missing-evidence.log`);
no Record human decision click or upload was made. Build/typecheck and lint
passed with inherited warnings. No migration, clinical decision, live send or
unrelated financial/call-suite rerun; no private applicant screenshot captured.
Native-language and owner visual approval remain separate pending gates.

## Service-definition booking validation —13October2026

Package `b004f8d75e7866e42731bada6f3fc7bd7f308e48`. The owner-provided grief
form put platform-workflow keys into booking_rules. The same mismatch is
reproduced in a real backend regression: save rejects it without changing the
existing definition. Booking rules accept direct-booking, scheduled and
immediate-request; individual-consultation/private-notes/patient-summary belong
in required_workflows. The former generic error concealed the field distinction.

Booking rules now use labelled checkboxes and a dedicated safe validation error.
Selection does not activate immediate care or grant a clinician scope. Request
clinical review first saves the currently entered draft, then requests review;
a validation failure prevents review and retains the form values. No founder
policy, catalog activation, scope decision, or existing definition was changed
by the agent.

Checks run: the focused typed-catalog Frappe regression passed (11.291s,
`/tmp/tt-booking-rules-backend.log`). Read-only reviewer browser on the actual
presentation grief definition verified checkbox interaction/no old textbox at
390/768/1440 and exact unchanged saved definition (`/tmp/tt-catalog-booking-controls.log`,
reproducible `scripts/browser-catalog-booking-rules.cjs`). A separate loopback
8028 browser on the disposable site created a fictional draft, changed its
professional description after saving, requested review, and verified the new
text persisted and state In review remained inactive (`/tmp/tt-catalog-review-save.log`).
Initial handoff test attempts timed out because an exact nested textarea-label
locator included its populated default text; using the labelled field's textarea
resolved the test locator without removing the persisted-content assertion.
The owned temporary server stopped afterward; no site access flags were changed.
Build/typecheck and lint pass with inherited warnings. Presentation screenshots
at `/tmp/tt-catalog-booking-controls/` were inspected; these focused control checks
are not owner visual acceptance or full MVP release acceptance. No unrelated
call/finance suites or live provider sends were repeated.

## Optional approach selection and ten-scope intake —12October2026

Package `5944566753a323bfa0f9045d47b29b4dc297471c`. The previous scope form
invited arbitrary approach text while its server validator required exact catalog
keys. The presentation catalog has nine Draft approaches and no Active approaches;
no valid selection was available. This was a form/contract mismatch, not a reason
to relax review or approve the draft taxonomy. Service applications may omit approaches.

Private applicant context now supplies Active catalog choices with labels, definitions
and evidence guidance. The free-text key field is replaced by optional checkboxes,
with an explicit empty-catalog explanation and separate training narrative. Previously
saved approaches that are no longer usable are shown with an explicit move-to-training
action; nothing is silently removed or converted into a catalog approval. Server
validation remains authoritative, including retirement after a choice was loaded.

Two focused real Frappe tests passed (6.162s, `/tmp/tt-approach-backend.log`):
Active-only choice projection, optional omission, invalid/Draft/Retired rejection,
stale retirement, and ten-scope atomic draft/submission/retry/privacy with an
above-limit rejection. New registration -> saved claims -> select all ten services
-> draft/reload -> explicitly reselect all ten -> submit ten distinct Submitted
records passed in the real built-browser test (`/tmp/tt-approach-browser.log`).
The browser asserts no obsolete approach textbox, truthful empty-choice guidance,
and all ten submitted states; it uses controlled random-code delivery on the
isolated test site, not a mocked frontend response. Original site settings and
captured-code cleanup verified. Build/typecheck and lint passed with inherited
warnings. No schema migration, live send, financial changes or automatic approval.
No unrelated call/financial suite rerun; full MVP/owner visual acceptance still open.

## Application persistence correction —12October2026

Source/package `c7a62b9ca3a28cb6b46b10350122ebc640aa6ba6` fixes an
owner-reported defect: completed onboarding already stored competencies,
certifications and credential-valid-from, but the private owner/reviewer projection
omitted them. The allowlist now returns all three without exposing them publicly.
Scope editing also previously allowed input before async claims loaded, suppressing
prefill; inputs now await initialization. An existing Draft/Clarification is restored
with its own saved fields on reload. Original completed claims and scope-specific
claims remain distinct; no historical data rewrite or new migration occurred.

Submission now identifies missing profession/qualification/institution, adult-care
confirmation, PDF resume, invalid credential dates and unreviewed treatment approach
keys. The original generic error did not establish which constraint the owner's
attempt violated; these cases now have safe dedicated error codes. Authorization,
clinical-definition review, evidence gates and submitted-content locking remain.

Actual checks: two Frappe/MariaDB regressions passed on the retained disposable site
(`/tmp/tt-professional-claims-check.log`,6.230s): private claim projection to both
owner and reviewer; scope save/read/valid submission/retry; invalid adult confirmation
without partial rows; unrelated patient denial; atomic multi-scope intake/retry.
The built-browser new patient/new clinician recovery and reviewer journey passed
with `TELE_TENA_ONBOARDING_VISUAL=1 TELE_TENA_SCOPE_DRAFT_BROWSER=1` on the
isolated8028 test transport (`/tmp/tt-claims-scope-browser.log`). It asserts all three
initial fields, inherited scope fields, edited Draft save/reload, useful adult-check
error, valid submission, two separate scopes and no clinical role grant. Original
site configuration was restored, loopback test server stopped and captured codes
removed. No live SMS/email sent; wrong/expired codes, returning-user cooldown,
call and financial suites were not repeated for this correction.

Build/typecheck and lint passed (inherited hook warnings and chunk-size warning
remain). Evidence: `docs/screenshots/mvp-current/c7a62b9-application-fields/`.
These checks close this reported private-field persistence defect, not the remaining
MVP handover or owner visual acceptance. Translations are provisional.

## Active clinician intake correction —12October2026 (verification in progress)

The current work corrects draft catalog selection in both contact-verified onboarding
and per-scope intake. Multiple services create distinct atomic applications with private
competencies/certifications/license-validity claims. Identical submitted retries return
the original applications; changed submitted content remains locked for clarification.
A separate reasoned medical-lead catalog decision is required before scope approval;
generic APIs cannot substitute for this action or change approved definition metadata.

The owner selected Medical Lead controls for the existing fictional presentation
reviewer. That site-only, audited role assignment is independent of any approval.
No catalog, rubric or clinician scope has been automatically approved. The named
presentation site was backed up before v1.37 nullable native-field migration.
Existing financial, consultation, availability and notification behavior is unchanged.
Actual checks:
- Five persisted Frappe regressions pass (5.317s): draft multi-scope atomic/private/retry,
  Medical Lead/generic-write authorization, independent scope decisions through offering,
  published schedule/discovery/immediate inbox, clarification and credential expiry.
- Real-backend captured random OTP registration/onboarding plus multi-scope draft/reload/
  resume/submission pass. Focused mode did not repeat wrong/expired/resend checks; prior
  full evidence is retained. No live SMS/SMTP.
- Accepted-offer browser passes while on Account and Requests, deduplicated polling,
  persisted read/reload, authorized consultation link and private projection. Capacity
  UI fault injection is separate from the existing real-backend capacity test.
- Native migration plus two repeat migrations preserve all15 named product/financial/
  catalog/vetting table values. A private presentation backup precedes schema change.
- Current production-build, lint and private-asset/hash scan pass; inherited warnings
  remain. v1.37 fresh installation is still unrun, not covered by the v1.36 result.
- Current patient password/Home/discovery/preview/profile reload/calendar/disclosure-back
  browser passes at390/768/1440 with no booking or balance mutation. The older harness
  hard-coded a clinician name and mislabeled the failing stage; it now asserts the
  selected fictional clinician and retains focus and offering-preservation assertions.

The browser registration/intake and backend reviewer/approval-to-bookable chain are
separate pieces of evidence, not one continuous new-applicant reviewer browser run.
Ten sourced presentation definitions remain Draft pending human clinical requirements
and decisions. Owner-selected reviewer Medical Lead controls exist; nothing was
approved automatically. Current acceptance remains the single existing matrix.

## Current Home/catalog follow-through —12October2026

Current package7daf9c084dcf9982cd1ee622b7cf2c0413417a4d. C01care-record rows now
link only recipient-authorized published summaries/follow-ups through the existing
appointment-detail API. No private text, new records or financial changes.
32068b7browser verifies Home→discovery→preview→selected profile/reload→calendar→
disclosure/back at390/768/1440 and compares record links with authorized backend data.
Only catalog UI/testing and clinical activation validation changed afterward; this
Home evidence is reused. Source/built frontend match before this evidence-only update.

I07/I08 now separate listing/editing, preserve deep links, show loading/unknown/filter
empty states and use compact reference panels and format cards. b280f00read-only
browser passes without application/definition mutations. Actual Chromium200% zoom
(outer1440/inner720/devicePixelRatio2) passes C01/B09/I08 with paired captures.
This proves zoom behavior, not all-state visual acceptance. Current screenshot folders:
`docs/screenshots/mvp-current/32068b7-home-care/`, `32068b7-actual-zoom/`,
`b280f00-catalog/`. DesktopC01 and desktop/mobileI08 compared; remaining differences
are recorded in the single screen matrix. No owner acceptance claimed.

Medical Lead activation now revalidates native back-office definitions: unsupported
formats, reversed durations and couples without consent workflow fail visibly without
activation. Two focused persisted tests pass8.833s, including the valid new clinician
three-scope →bookable offering/published schedule/discovery/immediate inbox chain.
Only the owned8017web master was reloaded; queue13917worker/scheduler remain running.
Current package offline recovery, password/deep-link refresh, guest/unrelated denial,
asset hashes and sensitive-cache exclusion pass. Existing-session *new-build update*
was not repeated in this run; earlier unchanged mechanism evidence remains separate.
No hosted-call repeat: runtime diff of consultation core from the acceptedfde86c3 is empty.

### Reviewer steps for structured applications

1. Existing fictional reviewer has the owner-authorized Medical Lead controls.
   Open Administration→Service catalog→a Draft definition. Complete professional,
   credential, adult consent, jurisdiction, duration, sources and supported workflow
   requirements; Save draft→Request clinical review→record a reasoned decision.
   These are human decisions; ten sourced drafts were not automatically activated.
2. General Applications review remains separate. Newly verified clinician onboarding
   captures private professional claims and CV. An approved clinician opens
   More→Scope applications, selects multiple definitions, supplies qualifications,
   saves/resumes and submits per-scope private evidence.
3. Scope vetting decides each independently: approve, clarify or decline with reasons
   and mandatory rubric/evidence checks. General or catalog approval grants no scope.
4. Only approved scopes allow offerings; publish the schedule explicitly. Discovery
   and immediate requests still require approved exact scope, offering, language,
   format, feasible time and fresh presence. Manual grants remain audited.

Remaining release gates: one continuous new-clinician/reviewer browser mutation chain,
latestv1.37fresh install requiring a scoped disposable DB credential, remaining MVP
state/locale visual comparisons and owner review. Priorv1.36fresh/couples/scheduler/
financial evidence remains named and preserved, not silently promoted to a new pass.
Live SMS/SMTP receipt, physical devices and native-language/clinical approval remain external.

## Desktop consultation-column clarification —12October

The user confirmed the preceding functionality and clarified that the original
media-left / session-details-right composition must remain in both video/audio.
Packagefde86c3132e9af65eb88b437dca7dea2435c23a9 restores that arrangement for
all desktop connected modes while retaining the full-width dark outer canvas.
Compact details/extension spacing, a300px supporting column, and an inline audio
heading keep default contents in view. Mobile retains its existing stacked/details
behavior. Expanded forms, unusually long content and zoom may still use the
accessible internal overflow fallback; no controls/content are removed to fit.

Focused hosted LiveKit Cloud two-role fake-device check passed at1440×960 and
1024×768: visible right column beyond the left media stage; default sidebar content
fits without internal scrolling; no page scrolling; visible Leave; audio-only,
Leave/video rejoin, and clinician End close both views. The first laptop check
caught genuine sidebar overflow; heading/text spacing and audio title row were
corrected and the final unchanged assertions passed. Inspected final audio1024
and video1440 captures. Evidence:`screenshots/consultation-columns-2026-10-12/`.

Production build/typecheck, lint(no errors; inherited warnings), asset hashes and
private credential scan pass. Stable presentation8017HTTP200; owned web/worker/
scheduler remain running. Temporary isolated8028server and copied private LiveKit
configuration removed. No changes to backend authorization, tokens, financial
rules, notes or presentation records; unrelated suites were not rerun. This is
not physical-device testing or renewed cached-token Cloud verification. PR44 stays
draft; overall MVP owner acceptance and previously recorded gates remain open.

## Accepted-offer notification and desktop call delta —12October

Runtime/build42cb041818613aa87dbe5d7a9aceefd23f32297d, stable8017 presentation
preview. Later commits change test harnesses or evidence only. PR44 remains draft.

- An immediate-presence heartbeat revalidates continuous free time. If a new
  reservation removes the last eligible opening, the backend may return
  `no_immediate_capacity`. The shell previously classified it as a generic setup
  update failure. This expected transition now refreshes readiness and displays
  Requests paused / No immediate opening, with availability guidance. It does not
  bypass any eligibility check. Real read-only presentation inspection currently
  finds both clinicians configured=true, ready=false, reasons=[]; the user's
  earlier exact failed response was not captured, so this is not a claim that
  every possible update error has the same cause.
- Clinicians receive a compact accepted-offer popup anywhere in their workspace
  and a Notifications bell with a persisted read state and consultation links.
  Authenticated polling every5seconds; no OS push/background delivery guarantee.
  No forced navigation, booking mutation or interruption of the focused call.
  Requests/owned offer history retain their accepted-consultation handoff.
- New backend projections return only the owning clinician's opaque offer and
  appointment references, acceptance timestamp and read state. Other clinicians,
  patients and guests cannot fetch/acknowledge the clinician's notification.
  No patient name, health narrative, disclosure or competing quote is sent.
- Connected desktop rooms fill viewport width/bottom below the demonstration
  ribbon, with zero outer margin/padding/border. Video stage flexes to available
  height, controls remain visible, and optional details scroll internally.
  Audio-only uses the existing real-track activity surface. This user-requested
  dark connected audio backdrop is an explicit deviation from referenceE08's
  earlier light outer page; preflight/ended/mobile layouts retain existing rules.

Checks actually run:
- Two focused real-DB presentation tests passed: competing private offers,
  insufficient funds, atomic match/retry plus notification ownership/read retries;
  and readiness pausing when a published interval no longer fits the immediate
  window. No new schema/migration or financial write path.
- `check_accepted_offer_notification.py` passed on the isolatedpr12 site: two real
  signed-in browser contexts, patient accepts an offer, clinician Account receives
  popup without refresh, consultation navigation, server-persisted read after
  reload and accepted offer history link (package2784701, unchanged except one
  call CSS border rule in42cb041). Additional capacity-error UI assertion
  uses an explicitly identified fault-injected422response, not mocked booking
  success. Result/screenshot: `screenshots/accepted-offer-room-2026-10-12/`.
- Production build/typecheck passed on42cb041; lint previously passed on the same
  feature with44warnings/no errors. Final runtime delta removes the connected card border; prior notification/permission evidence remains applicable.
  Asset hash/scope/private credential leakage scan passed,7private values checked
  without printing any values. Existing previewHTTP200 and owned site/PIDs verified.
- Focused hosted LiveKit Cloud fake-device two-context browser passed on the
  final package: patient/clinician video viewport fit at1440×960 and1024×768;
  patient audio-only fit at both sizes; controls visible and no desktop page
  scrolling; patient audio Leave, video rejoin and clinician End close both views.
  Inspected the rendered video and audio screenshots, including control placement,
  full-width dark canvas and preserved alias/metadata limits. This is functional
  geometry/rendered evidence for the requested delta, not whole-MVP owner visual
  acceptance. Result: `screenshots/accepted-offer-room-2026-10-12/hosted-focused-result.txt`.
  Temporary private provider configuration and owned8028server removed afterward.
  Cached-token Cloud revocation, physical devices, SMS/email receipt and native
  translation approval are not reverified by a viewport test. Token issuance,
  End/revocation implementation and financial/notes logic are unchanged.

Test harness issues were corrected without relaxing media assertions: current
phone-first/password alternative markup, new AudioStage selector, and selecting
video explicitly before asserting camera-capable rejoin. A colliding diagnostic
fixture attempt was aborted; its owned fixture/server cleaned up. Final runs are
sequential. Presentation data, credentials and original Bench remain untouched.

## Clinician setup report investigation —12October

Current package89631b02d385ef722151f408abb5c6f820b2060d. Read-only actual
presentation second-clinician inspection: one active offering, one Approved scope,
one Draft schedule. Save was succeeding as Draft; Published selector was inside
collapsed advanced rules. Booking-link and request-presence denial were correct.
Moved visibility outside advanced rules, explained Draft/Paused vs Published,
and made success messages state-specific. No automatic publication or record edit.

Professional profile now prominently links to the existing private service application
workflow. Qualifications, license/issuer/jurisdiction/expiry, experience/training and
per-scope evidence exist there, separate from public introduction and private resume.
This site's active catalog contains three Legacy test/Not reviewed/vetting_required0
services and no service open for structured applications. Initial onboarding selections
remain requested interests, not automatically submitted per-scope evidence/decisions.
General approval/direct legacy scope grants do not prove the complete applicant-led
journey is accessible on presentation. Medical-lead-reviewed Active catalog definitions
are required; no auto approval, legacy relabeling or historical rewrite performed.
The presentation applicant-led scope/competency access gate remains open, explicitly.

Real read-only second-clinician browser passes persisted Draft/reload, visible selector
outside advanced settings, disabled unpublished booking link, Account→private scope
application entry and accurate no-open-scopes state. No Save clicked, no credential or
application mutation. Build/typecheck and asset hash/privacy scan pass. Full publishing,
request readiness and per-scope submission/review were not claimed by this check.

## Latest recorded request-outcome correction —12October

Package6ec7d09dc25d3704bb0e0fd1e4ea78bb4cb2ae3e. Request details no longer
say Live request progress after matching/closure. Matched sidebar directs to actual
appointment; live matching instructions appear only while the request remains open.
Real owner browser passes Matched/reload, accepted private offer → loaded authorized
appointment, no duplicate Accept action, unknown-ID isolation and identical requests/
wallet.390/768/1440 inspected; no exact closed-state reference exists, so full active
D04/D09 visual acceptance remains open. Screenshots are explicitly not a paired pass.
Build/typecheck, lint with existing warnings, asset/hash/private-credential scan pass.
Prior1774968 matching/PWA and38ac535 onboarding evidence remains exact-source named;
only recorded-outcome UI changed since1774968. Call/job/financial/authorization code
unchanged; no unnecessary hosted-call or full financial suite replay. Matrix retains
all original gates. Whole-MVP visual/state and final integrated release remain open.

## Latest connected discovery/profile continuation —12October

- Exact package1774968d6899b9b222e9514e27adb9afd2b12f48. C03 matching workspace
  and mobile toolbar/refinement follow actual paired reference. C04 compact approved
  scope/offering rows preserve descriptions through existing View service.
- Fixed real context loss: profile selection previously lived only in navigation state;
  reload chose the first offering. Public opaque service parameter now preserves it,
  while private care query/filters remain RAM-only and clear on full reload.
- Real presentation browser passes filtered discovery, preview Escape/focus, public
  projection excludes private contact/credential fields, SPA filter retention,
  selected profile/booking reload and private request composer handoff. Wallet/profile
  unchanged. No booking/payment mutation. English pairs390/768/1440 inspected.
- Test-harness diagnosis separately fixed exact duplicate-offering selection and
  bounded native-details state waits. Tests intentionally separate SPA retention from
  full reload clearing; no server rule or assertion removed.
- Source38ac535 registration browser and2DB regressions3.745s pass typed/private
  fields, structured finish without duplicate narrative, legacy requirement, resume,
  saved scopes, Pending/no clinician role and retry uniqueness. Configuration restored,
  private captured OTPs removed, temporary8028 server stopped. No provider delivery.
- Latest build/typecheck, lint and asset privacy/hash checks pass with existing warnings.
  No schema/financial/job/call changes; named fresh-install, scheduler and hosted
  consultation evidence retained without unnecessary replay. Final integrated release
  and whole-MVP visual/state/owner gates remain open.
- Safe comparisons: screenshots/mvp-current/1774968-matching and
  screenshots/mvp-current/38ac535-initial-clinician. README notes retain material
  differences; no universal fidelity or all-MVP acceptance claim.

## Historical connected application/reviewer continuation —12October


Package8b5802d5d0e2e54a6d222b0763ad47ceaafd8808; initial application browser
source295ffdd67bb56c9bfaf2685136196671d4efc978. Later difference is reviewer
page/tests/evidence; initial application UI/API unchanged.

- B06/B07 now collect persisted typed private professional metadata, care
  languages and explicitly public introduction. Shared native scope validators
  reject unsupported fields, negative experience, invalid expiry and languages.
  Patient registration rejects clinician fields. Existing unstructured drafts
  remain valid; no migration or inferred qualifications.
- Two real DB regressions passed2.980s: draft/reload, incomplete typed submission
  denial without partial profile, reviewer-only private projection/Guest denial,
  public projection excludes private identifiers, Applicant-only submission and
  repeat completion cannot create a second application; patient privacy unchanged.
- Connected random-code browser passed at295ffdd: both role choices, patient
  background/recovery, clinician B06/B07 typed fields, B09 saved selections,
  private PDF, B10 Pending submission and authorized reviewer. Site config was
  restored; captured codes removed; owned8028 server stopped. Wrong/expiry/resend/
  returning-user/per-scope tests not repeated; prior named evidence retained.
- Reviewer browser initially counted queue rows before async fetch rendered.
  Safe stage reporting identified rows0 after a successful authorized projection.
  Bounded visible-row wait fixed the test; no assertion removed or permission
  changed. A subsequent visual comparison identified a genuine I03 modal/page
  discrepancy. Dedicated page now uses existing opaque public_id and no email
  in its URL; legacy missing identifiers use authenticated navigation state.
- Latest8b5802d read-only reviewer browser passes private fields, opaque refresh,
  filtered queue return, unknown-record recovery, Guest403 and identical records.
  Paired390/768/1440 and actual200% Chromium (outer1440/inner720,DPR2,scale1), plus
  AM/OM320/390/768/1440. No approvals, provider sends or clinical mutations.
- Build/typecheck and lint pass with existing warnings; asset hashes/private
  credential scan pass. PWA/offline/deep-link/password/permission/cache checks
  passed at295ffdd. No actual build-transition flag used in that run; prior
  explicit existing-session Refresh evidence remains separate.
- Owned8017 web master59693 received scoped HUP for API changes; children90877/
  90878 load matching code. Worker59687/scheduler59689/Redis10747 remain unchanged
  because financial/job/call logic is unchanged. Original Bench/Selfmade untouched.
- Safe pairs: `screenshots/mvp-current/295ffdd-initial-clinician/` and
  `screenshots/mvp-current/8b5802d-application-review/`. README comparison notes
  retain material B07 length/evidence-step differences, other states and native
  review/owner gates. No whole-MVP acceptance or new hosted-call replay claimed.

## Historical continuation evidence (exact named sources)

## Prior registration and reviewer fidelity

- Current package/source `bc20f722848a84b7b857284b1599bef0f8b1f451`.
  Matching web/worker/scheduler restarted through the scoped lifecycle at eb670a3;
  subsequent backend API/job code is unchanged. Owned web59693, worker59687,
  scheduler59689, isolated queue Redis10747/13917. HTTP200; no unrelated restart.
- Added missing B04 optional care background through owner-only saved onboarding.
  New patient step4 is inserted before stored ready step3, so historical drafts
  are not reinterpreted. Text length4000, patient only, no implicit sharing,
  no clinical text in browser storage/logs. Two real DB tests passed2.811s:
  owned draft/default privacy/reload-ready completion, oversize/clinician/Guest
  rejection, repeat completion cannot duplicate a profile. No schema change.
- A07 now offers only site-permitted account types after verified contact when
  no intent/draft exists. Patient/clinician CTA intent remains explicit; choosing
  clinician grants no scope or clinical role. Real loopback browser at bc20f72
  exercised both choices, reload, patient Back/background/default-private,
  resume upload and pending clinician submission. Settings restored and random
  captured codes removed. Test-only transport, not SMS receipt. Wrong/expired,
  resend and returning-user checks remain the prior full-run evidence.
- Test failures were diagnosed: populated textarea label → fixed separate label;
  numeric share_history0 versus strict JSfalse → normalized boolean assertion;
  checkbox support description polluting accessible name → shared label/description
  IDs. Source throttle10/15min then blocked a repeated run: preserved counters,
  waited for normal window expiry while doing reviewer work, final pass. No IP,
  phone, daily cap or production authentication rule was bypassed.
- Reviewer browser at bc20f72 passed named queue/search, selected overview-row
  handoff, private résumé download, mobile/desktop dialog scroll, Escape/focus,
  unchanged application projection and wallet403. No decision mutation.
  Fixed max-width CSS collision via existing --dialog-width, and consumed-link
  state after Close so a closed review does not reopen on refresh. Tablet metrics
  retain2columns. Full structured per-scope/rubric/state fidelity remains open.
- Frozen-build invited-review Home→discovery→selected public profile/reload→
  generated calendar→disclosure/review/Back passed at2f3de58, 390/768/1440.
  Later bc20f72 only changes reviewer close context/onboarding primary label and
  test identity guards; patient booking path unchanged. No booking/funds mutation
  in this read-only run. Initial source-before/after assertions prevent mixed
  build evidence. Earlier overlapping-build capture is not the current pass.
- Locked package/TypeScript build, lint(exit0, existing warnings), Python syntax
  and asset hashes/private credential scan passed. No new hosted-call replay:
  call/token/finance/runtime jobs unchanged; reuse named prior evidence.
- Paired evidence: `docs/screenshots/mvp-current/bc20f72-onboarding/` and
  `bc20f72-reviewer/`. Inspected English390/768/1440 compositions; documented
  operational exceptions, missing fuller states and language/actual-zoom gates.
  Visual owner acceptance and whole-MVP completion remain open. Freshv1.36
  installation passed11October; the exact schema/cleanup check is recorded below.

## Current clinician scope-selection continuation —11October

Source/package41b6cf5fc6be1952c5ac36cc38b3d1f30aa3785f. Initial clinician flow now
has five stages, with a separately saved B09 scope-selection step5 before existing
review-step3. Old stored drafts retain their meaning. Patient cannot use clinician
step5; credentials, resume, adult consent and manual approvals remain required.
A populated credential textarea also uses an explicit stable label.

Two Frappe DB tests PASS1.705s (single-use/role injection/new step/patient denial and
optional patient background). Connected real-backend browser PASS at41b6cf5:
patient/clinician contact-proof account choice, draft recovery, private background,
B09 searchable selections/Save/reload, private PDF and Pending submission without
clinical or reviewer privileges. Captured random codes removed, original settings
restored, owned8028 test server stopped. Wrong/expired/resend/returning-user checks
were not repeated; retain prior named evidence. No provider send.

Reviewed B09 desktop/mobile pairs; title/progress/standalone evidence cards and
Review application match the reference. Full initial B06/B07 typed-professional
composition still needs correction; those fields currently live in separate
per-scope vetting. No whole-flow visual acceptance claim. Safe paired evidence in
`docs/screenshots/mvp-current/41b6cf5-clinician-onboarding/`.

Only the validated8017 Gunicorn master59693 received graceful HUP after API change;
its replacement workers74536/74537 load the current source. Isolated scheduler/
financial worker and unrelated Bench services remained untouched. Job/finance/call
logic is unchanged. Build/typecheck, lint(exit0/existing43warnings), asset hash and
private-secret scan passed. No DDL change since the successful v1.36 fresh install.
Previous account/PWA067b450 and profile dc5a582 evidence remains valid for unchanged
components; no redundant hosted-call suite replay.

## Current account correction and recovery —11October

Runtime/build067b450052d11c4ad3fcf83902ab8c5b8de389d4; source after this
checkpoint may differ only by evidence/docs. Backend API/jobs are unchanged from
the matching owned59693web/59687worker/59689scheduler checkout. No service restart,
financial rewrite or remote operation was needed for these frontend corrections.

- Reproduced private-history field’s accessible label changing after populated
  input (exact label count0). Separate explicit label fixes it; draft-only browser
  regression passes with stable count1 and content retained across sections.
- Inspected H01/H03/H04/H05 English paired images. Restored reference card choices,
  primary privacy action, settings order, shared-care row/notice and compact wallet
  amount. Account navigation reveals its selected item horizontally without moving
  the page. Site capability rows replace misleading generic OTP availability.
- `browser-presentation-account.cjs` PASS: real patient/clinician sessions, all
  section routes at390/768/1440, capabilities match server, private draft survives
  section changes, existing profiles/privacy/funds exactly unchanged. This is
  readonly evidence, not new persisted-save coverage.
- `browser-profile-accessibility.cjs` PASS atdc5a582: actual Chrome200% zoom,
  keyboard Introduction→English, provisional Amharic/Afaan Oromo320/390/768/1440
  and Ethiopic font check. Subsequent067b450 changes only wallet typography;
  profile controls/navigation unchanged. No native-language approval.
- `browser-preview-recovery.cjs` PASS on067b450: offline fallback→Try again,
  authenticated deep-link/refresh, guest/unrelated403, exact served asset hashes,
  sensitive cache exclusions. This run did not exercise a build transition;
  prior explicit existing-session Refresh-to-update evidence remains separately
  recorded. No automatic reload during calls.
- Locked production build/typecheck and asset/private-secret scan PASS; lint exit0
  with existing43warnings, large bundle warning remains. Hosted call/financial
  suites were not repeated for this unchanged backend/call path.

Safe pairs/results in `docs/screenshots/mvp-current/067b450-account/` and
`dc5a582-profile-accessibility/`. H04 prototype notification/accessibility settings
and H05 contact/session administration are not represented as working. Global
ribbon/tours/authenticated navigation, unsupported profile fields and remaining
state comparisons are explicit exceptions in the matrix. Whole-MVP visual and
owner acceptance remain open; no acceptance is inferred from captured images.

## Fresh v1.36 completion —11October

Source4a71d2a73b42471f571cf6ad5ef4c58de2a55859, Python3.12.3,
Frappe15.121.2/ERPNext15.121.6. `scripts/check_fresh_install.py` passed on
`teletena-mvp-v136-fresh.localhost`: genuine fresh application installation,
v1.34/v1.35/v1.36 tables/column/PatchLog assertions, native catalog/clinic/roles,
guest denial and disabled funding before explicit setup. Retained erp/pr12
record and private-configuration fingerprints were unchanged. Temporary
localhost administrator, credential file, disposable database/site/user removed;
administrator reauthentication denied. This invocation did **not** run optional
registration browser checks or native repeat migration. Latest existing-site
v1.36 twice-migration preservation and real registration evidence remain separate.
No root authentication, sudoers, presentation records or Selfmade change.

Account continuation reproduced a populated private-history accessible-name
failure and corrected separate labels; matched reference comparisons motivated
privacy card variants, compact section navigation and shared-care notice.
Contact section now queries existing site capabilities rather than suggesting
unavailable OTP methods. Build/browser verification of this latest change is
pending below; it does not close the full H01–H05 visual gate.

## Checks actually run in this continuation

| Gate | Result and exact evidence |
|---|---|
| Existing browser/PWA recovery | `browser-preview-recovery.cjs` passed offline navigation→Try again→online, password session/deep-link refresh, guest403/unrelated-role403, every packaged JS/CSS hash and cache exclusions. Existing session explicitly received48f7da9 through Refresh to update; no automatic active-call reload |
| Shared state model | v1.34 immutable individual consent: original time stays reserved until both adults+clinician agree; decline/expiry/unavailable target preserve booking. Extension agreement never implicitly charges the payer; payer explicitly authorizes after both consent |
| Real DB couples regressions | 11/11 passed4.476s on disposable pr12. Concurrent booking, disclosures, invitation decline, withdrawal/retry/hold, three-party time changes, extension reserve/release and controlled-clock started extension→one earning, separate follow-up draft/idempotency/amendment/recipient isolation. Provider calls mocked in these DB checks |
| Hosted three-person journey | First connection attempt failed at Connected wait; retained appointment/financial records. Direct SDK connection and microphone/camera publication then passed. A bounded retry on the SAME appointment passed at411c293: three-way actual media exchange, Leave cleanup/rejoin, cameras off/audio-only/no extra capture/muted level0, joint extension consent and payer reservation, End releases unused block once, original+app-reissued still-valid tokens rejected directly by Cloud SDK for all3 including departed partner, reload draft/private follow-up/recipient summary/one Pending earning. Fake devices; first transient cause not conclusively established; no natural SDK auto-refresh/physical-device claim |
| Joint rescheduling browser | `browser-shared-reschedule.cjs`: three actual password contexts, generated date/time→proposal→1/3→2/3 with original unchanged→3/3 persisted move; exact wallet and disclosure unchanged. Paired390/768/1440 plus provisionalAmharic/Oromo layouts; actual Chromium zoom via tabs.setZoom2 (outer1440/inner720,DPR2,visual scale1). Old full-page zoom captures were cropped; native viewport replacement must be inspected before image acceptance |
| Follow-up and document browser | `browser-couples-documents.cjs` passed read-only Completed recipient isolation, reload, local amendment/confirmation, unchanged revision, pairedN07/N08 at390/768/1440. N07 now has a separately authorized individual follow-up; no second earning on amendment |
| Reviewer matching | One real-DB permission/projection/pagination-validation test passed2.721s. Browser reviewer200, patient/clinician403, private-field omission, status-filter+reload, actual5request dataset and pairedI10. Visual inspection caught a mobile table hidden by application-only CSS; new matching table retains rows and gets a focused visibility regression |
| Financial preservation | Named presentation-site backup with private/public files, scoped stop retaining queue, native migration throughv1.35. Exact wallets, all legacy events/journals/lines, earnings and reconciliation-values fingerprint unchanged. New tables do not rewrite historical notes/consents. Read-only owner check:3patients,1clinician,6accounts, zero projection/obligation/journal/balance errors |
| Native background jobs | Current scheduler/worker automatically execute release, invitation expiry, request expiry and extension expiry (Scheduled Job Logs Complete), queue contains only intended site jobs. Fixed native scheduler_interval10→60 while keeping tick10: Frappe converted sub-minute All intervals to invalid */0 cron steps. No framework modification. `verify_continuous_processing.py` observed one release posting and a disputed hold; original short policy applies only to its2owned encounters. Prior worker-down enqueue/restart evidence retained |
| Frontend/syntax | Locked package build, TypeScript, lint exit0; existing large-chunk/lint warnings retained. Python syntax checks passed. No full unchanged individual hosted suite repeated |

## Current professional profile and patient handoff — 11 October

This checkpoint closes named defects, not whole-MVP visual or owner acceptance.
Active source/build191762a (latest shared CSS); profile/localization evidence9308b30; API behavior unchanged since467f755 apart from the explicit
presentation seed helper. Web50748, worker50742, native scheduler50744,
loopback queue13917 Redis10747; only presentation services were stopped/restarted.
Original ERP site and Selfmade were not migrated, seeded or restarted.

- **Pending own-profile403:** real valid-name browser save failed because approved
  Clinician role was required for even an existing applicant-owned profile.4371be4
  permits Applicant+existing own clinician profile; cannot create or change kind,
  grant approval/scopes or edit another user. Same-name Save200, roles unchanged,
  direct appointments403 and reload passed390/768/1440. Removed pending Earnings /
  Services / Availability links that led to protected403; applications remain accessible.
- **H02/C04 introduction:** optional2000-character explicit public content, owner
  editable and only approved public clinician query exposes it. No history or
  vetting evidence copied. Omitted field preserves content; empty explicitly clears.
  React renders plain text; other patient/profile fields never publicly returned.
  Separate clinician save/reload and patient context passed. New seed content only
  applies to newly created fictional profiles; setup is not rerun to rewrite records.
- **Four matched-site real DB regressions:**9.029s, owner introduction/validation/
  private-field omission/pending/Guest denial; pending existing profile; original
  booking retry after profile changes; defaults versus booking overrides. Earlier
  retry401 was fixture DBpr12 versus HTTPpresentation8017; corrected owned8028 on
  SAMEpr12, no weakened assertion/credential changes. Temporary server stopped.
- **Two native migrations each, v1.36:** backed up DB/private/public files first;
  compared old columns of ALL54existing command tables:667presentation and3921
  pr12 rows unchanged, no inferred introduction. Initial harness incorrectly used
  DocType column helper on rawtt tables; failed BEFORE migration, corrected to
  SHOW COLUMNS. Native upgrade/repeat then passed. Found/fixed fresh bootstrap
  omissions forv1.34/v1.35. Freshv1.36 subsequently passed on11October; existing-site repeat migration
  and fresh installation remain independently recorded checks.
- **Selected offering lost:** actual390 browser selecting the second individual
  offering failed full-profile selection againstbf3d63c; default was first/couples.
  d82948a carries only opaque PUBLIC offering context via router state, revalidated
  in current authorized services. Full real Home→discovery→preview/focus→profile /
  reload→generated calendar→disclosure/review/Back passes390/768/1440. No booking
  submission/financial mutation in this read-only test. Earlier calendar fixture
  accidentally asserted individual review on first/couples offering; corrected to
  selected individual path, not relaxed couples consent.
- **Paired visuals:** current H02/C04 English390/768/1440 inspected; restored own
  identity summary, icon/description practice links, compact multiple languages,
  expandable private evidence, regular-weight form values. Still different: no
  invented portrait/qualifications/affiliation/ratings; fuller expertise/affiliation,
  shell spacing and remaining state comparisons need work/owner review.
- **Keyboard/languages/zoom:** actual profile Tab order,320/390/768/1440 Amharic and
  Oromo rendered; Noto glyph availability checked. Removed stale dictionary entry
  overriding Amharic Affiliations with Oromo; added Services/pricing translations.
  Real Chromium tabs.setZoom2 outer1440/inner720/DPR2/scale1; native viewport PNG
  width1440. Intro zoom scroll anchors differ and should be improved before final
  paired-image acceptance. Reference is English; local language rendering is not
  same-language reference fidelity or native approval. User-authored intro is not
  automatically translated; no medical text sent to translation services.
- **PWA:** actual existing browser bf3d63c update passed; test originally attempted
  next navigation before controller-change reload and got ERR_ABORTED. Wait for
  real navigation fixed test orchestration; no service-worker assertion removed.
  Offline Try again, password/deep links/refresh, guest/unrelated403, asset hashes /
  sensitive cache exclusion pass. Current9308b30 hash/private scan7passed; no
  Vite or credentials embedded. Build/TypeScript/lint exit0 (existing warnings);
  syntax and3dependency-checks plus worker-cache tests pass. One concurrent local
  build/npm-ci attempt lacked Vite; clean sequential locked packaging then passed.
- **Registration:** c0d911d real two-account contact proof, recovery/private PDF /
  scope draft/reload/resume/repeat-save/submission and initialB10panels. Explicit
  LOOPBACK test cap100 restored original20; no phone/IP/day counters reset, no live
  SMS. Focused result correctly does not claim wrong/expiry/resend/returning repeats;
  unchanged full a001 evidence retained. Historical application/service pointer
  mismatch still preserved and documented; no record deleted or reclassified.

Evidence: `docs/screenshots/mvp-current/9308b30-professional-profile/`,
`9308b30-profile-accessibility/`, `d82948a-patient-profile/`,
`bf3d63c-pending-account/`, `c0d911d-onboarding-review/`, and safe hashes/results in
`docs/verification/mvp-current/`. The single matrix retains ALL99MVP entries.
Latest fresh schema, whole-product visual/state work and integrated candidate
acceptance remain open. Hosted411c293 couples/token evidence retained unchanged;
no full hosted suite repeated for profile-only work. No physical-device/live
SMS/email/native-language/owner/real-money or remote-deployment pass claimed.

Latest shared composition191762a: desktop Help & tours replay now shares the
heading row without absolute overlap; first-visit/mobile invitations retain their
in-flow spacing. Pending role/navigation/save and approved introduction/reload /
public-query checks repeat successfully, matched390/768/1440; desktop pairs
inspected. No consultation or financial logic change. CI on191762a passed all8
runs (Node22/24 frontend and Python3.12/3.14 syntax); this is not freshFrappe16
workflow verification. Feature push initially stalled; one bounded HTTP/1.1
retry confirmed remote191762a, normal fast-forward with no global Git change.

## Public entry, registration and shared-calendar continuation

Packaged source `fb94c293d8f010d8f5775ee0c2d2696bf3fce9d7` includes the following
focused changes. Later documentation/test commits do not require a rebuild when
the frontend/backend runtime diff is empty. Runtime backend is unchanged since
`cc52e8f`; no new migration or financial write was needed for these UI changes.

- **A02/A03**: dedicated public explanation and clinician invitation routes,
  reference hero/cards/header and real access-policy/intent/deep-link checks at
  c09a6d3. Desktop/mobile inspected; 768 also captured. Operational preview does
  not fabricate appointments, patients, credential status or earnings.
- **N01**: approved shared-care catalog, Account/navigation entry, expandable
  retained history and service→generated calendar pass at c09a6d3. Fixed retained
  resource-list rendering multiple plans on one detail route. No records deleted.
- **E03**: three-party generated-slot consent/unchanged financial snapshot passes
  at4553fe4. Corrected tablet/native200% calendar pairing. Actual browser zoom,
  including separately captured scrolled calendar, is not device emulation.
- **A05/B01–03/B05–07/B10**: full real backend transport run at a001e62 proves
  wrong/expired codes, native cooldown/resend, new patient/recovery, same-account
  return, new clinician intent/private PDF/submission without clinical approval.
  Observed premature resend rejection is retained as diagnostic evidence; backend
  limits were correct. Client now computes cooldown from an absolute deadline and
  resets waiting on server cooldown rejection. No throttle was relaxed.
- **fb94c29 focused onboarding**: two real random-code contact proofs, patient and
  clinician draft/reload/submit, searchable scope no-result/reset preserving
  selection, private resume and no privileged roles all pass. This focused rerun
  does **not** repeat cooldown/expiry/returning coverage or prove live delivery.
  Temporary configuration restored, loopback transport stopped, codes removed.
  Paired B05 exposed old global guided width overriding the readiness hero;
  scoped width fixes now render a wide hero and readable mobile stack.

Paired evidence is under `docs/screenshots/mvp-current/` in the named source
folders. Registration screenshots use the isolated technical fixture site;
its service-test wording is not presentation content. English screen comparisons
are recorded individually in the existing matrix, including remaining structured
clinician onboarding composition differences. Native-language approval, all-state
visual acceptance and owner acceptance remain open. Build/typecheck/lint pass;
existing lint and chunk-size warnings remain. No unchanged financial or hosted
consultation suite was repeated for these frontend changes.

## Clinician workspace and detail comparisons — source20172f3

F01 now has one compact schedule surface with distinct actionable/future group
headings and actual readiness icon rows. F13 uses the reference offer-stage rail
and wide detail panel; F14 uses the history heading/panel and truthful persisted
rows. Patient and unrelated-clinician direct offer queries are denied; accepted
own-offer reload/consultation handoff passes. Matched320/390/768/1440 captures,
plus provisionalAmharic/Oromo390 captures, are preserved in the existing matrix.
This does not prove active/expired/withdrawn UI states or native translation review.

`browser-presentation-overview.cjs` passes at390/768/1440 on both roles: keyboard
Today→details, detail reload, real generated alternative slot selected by keyboard,
return without mutation, preserved audit-history keyboard expand/collapse, exact
wallet/earnings queries unchanged during the bounded flow. Its outdated dropdown
expectation was corrected to the dedicated calendar route; reference pages now
explicitly receive the same viewport rather than inheriting the context's1440px.
The app's expanded15-event audit timeline created a very tall page; it now starts
collapsed, retaining every event in an accessible scrolling region. No audit event,
appointment, note or financial record was removed.

Paired F01/E02 English desktop/mobile images were inspected; remaining status,
language/zoom and owner comparisons stay open. Current PWA recovery/hash/auth/cache
check passes at5882b11; later offer/timeline changes do not change service-worker
code, but latest candidate hash checks remain a final integrated gate. A read-only
consistent per-owner audit reports3patients/1clinician/6accounts and zero projection,
obligation, journal-balance or posting mismatches. No balance repair occurred.

## Pending applications and structured scope wizard —11 October continuation

Packaged source `b87d843de0827d3d4d80b8717fe0995d64346ef6`; current preview unchanged. Real pending-applicant
browser passes390/768/1440, profile/reload, no approved-only navigation and direct
appointments403. B11 uses real application/per-scope records in the reference
review-progress/service-decisions panels; unknown review milestones are never
fabricated. Tour invitation now remains in flow and cannot overlap long headings.
Paired pending English desktop/mobile inspected. Rejected/populated decisions,
provisional language layouts, actual zoom and owner acceptance remain pending.

The ungrouped scope form now uses a focused572px reference wizard with Back,
Save draft and a separate review step. At9254a65, the real registration fixture
proved draft→reload→resume→review→repeat save→submit: one application, retained
fields, private resume from onboarding, no clinician approval granted. Settings
restored, local transport stopped and captured codes removed. Current layout
comparison at`b87d843de0827d3d4d80b8717fe0995d64346ef6` is read-only, not a second submission proof.

A subsequent random-code screenshot rerun was rejected before onboarding.
Read-only diagnosis: isolated fixture site20counted24-hour sends/cap20; source
bucket5/10 within900seconds. Controls were not weakened/reset. Existing fixture
password access then passed current screenshots/navigation with exact unchanged
applications. Its old private metadata service pointer differs from its original
owned application; comparison resolves the retained application ID through the
authorized API and records the mismatch, without rewriting metadata or records.
The historical cause of that metadata drift has not been established.

Paired evidence: `docs/screenshots/mvp-current/9254a65-vetting/` (persisted flow),
`b87d843-vetting-layout/` (current read-only layout),
`b87d843-application-progress/` (pending status). Scope-test wording belongs to
the technical fixture site and is not presentation content. Current form width,
typography, progress and review hierarchy compared; initial signup/full inline
upload/reference summary differences remain explicit in the matrix. Technical
fixture's prior role status is unchanged; only new-registration tests prove no
approval granted.

Locked build/typecheck and lint exit0 (existing warnings); packaged hashes,
PWA scope/no maps/config and exact7private-credential scan pass. Python syntax
for the new read-only harness passes. No new backend/schema/financial changes,
no unchanged hosted call suite or financial suite repeated for these UI changes.
No live SMS/email, physical-device or native-language approval claim.

## Remaining release work, not silently dropped

- **Fresh latest schema**: v1.33 fresh install and representative legacy financial
  cutover evidence remain valid. v1.34/v1.35 fresh installation not yet run; temporary
  scoped DB administrator needs local sudo authentication (`sudo -n` fails).
  Harness now checks/fingerprints new shared-consent/follow-up tables as well.
- **Whole-MVP visual fidelity**: existing matrix keeps all99MVP dispositions and
 43post-handover entries. Current matched screenshots do not accept uninspected
 routes/states. Finish remaining screen/state comparisons, actual zoom captures,
 language layouts, mobile dialogs/tours and integrated candidate checks.
- **External/manual**: owner acceptance; physical-device calls/PWA installation;
 live SMS/email received/verified with consenting recipient; native-language review;
 clinical/catalog/rubric/legal approval; actual provider settlement. Current new
 couples code has not been rerun on exactFrappe16. No remote deployment.

Credentials: mode600 private file
`/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private/tele_tena_presentation_accounts.json`.
Use **Use email instead→Use password instead** on invited review; enabled signup
is tested on a separate configuration. No credentials appear in this report.

## Historical evidence retained below

# Historical checkpoint — 10 October 2026

**Historical checkpoint; superseded by the active section above. Its passing evidence remains valid only for named unchanged behavior.**
The runtime below supersedes every earlier site/build/process reference in this report.
The existing `mvp-screen-acceptance.json` remains the sole screen acceptance matrix.

## Current source and working preview

- Branch `feat/mvp-release-handover`; [draft PR #44](https://github.com/natnaelTi/tele-tena/pull/44)
  depends on open PR #43 (`feat/adult-relationship-links`). Ancestor
  `1e8d161468eb8d3563f1b5743982722c749bbcbf` remains included.
- **Built application source `40c608f0de5dd7c9c92faeb11c6e45bbca3c7a49`**;
  later evidence/report commits do not change application code. The packaged
  `tele_tena/public/review/release.json` records this source and asset hashes.
- **http://127.0.0.1:8017/teletena/** now serves **`teletena-mvp-presentation.localhost`**,
  bench `/home/frappe/frappe/frappe-bench`, app `apps/tele_tena`. Production React,
  same-origin Frappe APIs; no Vite server. HTTP 200 checked after packaging.
- Dedicated Gunicorn master 453370 (pidfile `/tmp/teletena-mvp-presentation-web.pid`),
  two workers replaced through a targeted HUP (current IDs are ephemeral); process cwd `sites`, Python path app checkout above,
  observed `TELE_TENA_TEST_SITE=teletena-mvp-presentation.localhost`.
  Old preview master 392014 was stopped only after the new site passed its initial
  journey. The retained `tele-tena-pr12-fresh.localhost` records and credentials,
  `erp.localhost`, unrelated workers and Selfmade were not reset or migrated for this switch.
- Observed local Frappe 15.121.2 / ERPNext 15.121.6, Python 3.12.3, Node 22.23.3.
  These checks are **not** an exact current Frappe 16 rerun.
- **Dedicated native scheduler and worker are active** in `/home/frappe/teletena-mvp-runtime`; queue Redis loopback 13917. Original/shared site configuration keeps scheduler disabled so unrelated Bench services cannot process this site. See current gate table and native-job evidence below.
- Normal preview remains intentionally **invited-review**: phone OTP and both public
  registration flags disabled. Phone-first entry remains visible with an accurate
  unavailable state. Email code delivery is unavailable; explicit password sign-in works.
  Enabled-registration was tested separately with a loopback-only transport and then disabled.

## Current gate reconciliation — source/build40c608f (10 October 2026)

**This table supersedes all older open/missing/disabled claims below.** Earlier
sections are retained as dated evidence, not competing current classifications.
No owner visual acceptance, merge or remote deployment is claimed.

| Gate | Current result | Evidence and remaining boundary |
| --- | --- | --- |
| Registration browser | Closed for listed journeys | `check_registration_recovery.py` + `browser-registration-recovery.cjs`: real backend random-code local transport, wrong/expired code, bounded resend cooldown, patient consent/privacy, returning same phone user, clinician intent/private PDF/app submission, reload recovery passed. Test server stopped, codes deleted, original flags restored. Four HMAC/attempt/concurrency/CSRF/manual-approval tests passed. Live delivery not run |
| Invited review | Closed for existing access | `browser-invited-review.cjs` passes disabled phone/public-registration configuration with explicitly chosen password; no frontend capability mocks or access-policy weakening |
| Practical content | Closed for explicit idempotent seed; coverage partial | Fictional accounts, offerings, approvals through reviewer API, retained patient sessions and actual shared notes/earnings. No fabricated reviews/credentials or reset balances. Historical synthetic test services are not relabelled |
| Individual consultation | Preserved | Previously passing hosted fake-device suite retained; not rerun because subsequent UI-only changes do not affect individual media/security |
| Working couples | Closed for tested core workflow | Latest full hosted three-browser `34641d87cc6b826793482e2963466fd1cd301548`: independent consents, one charge, three-party advancing audio/video, muted/camera-off surfaces, audio-only without extra mic, Leave/rejoin/track cleanup, End and direct SDK rejection of original/app-reissued valid tokens for every identity including departed partner, selected-recipient finalization and one pending earning. DB tests also verify withdrawal/closure retries, unrelated access, concurrent confirmation, fixed-duration extension denial. Separate simultaneous private follow-up field and jointly renewed extensions/rescheduling are not implemented; no silent charge/consent workaround |
| Couples records | Closed for tested routes | `browser-couples-documents.cjs` on 8ba375e: selected partner sees summary after reload, nonrecipient/private-note omission, local amendment/confirmation with unchanged revision. N07/N08 paired 390/768/1440 captures; not owner visual approval |
| Native continuous jobs | Closed for tested release/expiry/restart | Isolated worker 495534 (short/default/long), scheduler 495535, queue Redis 487749 at13917. Native Scheduled Job Logs Complete, exactly one release posting, dispute blocks release through successive cycles, worker-down queue/restart processes invitation expiry. One-minute policy only on two new owned fixtures; clock/global policy unchanged. `docs/verification/mvp-current/tt-continuous-processing-result.json` |
| Current owner reconciliation | Closed on presentation data | Read-only consistent snapshot: 3 patient owners, 1 clinician owner, 6 accounts, zero owner projection/obligation/account/journal mismatches. No repair or balance edit. `tt-presentation-financial-owners.json` |
| Fresh v1.33 | Passed | Exact disposable `teletena-mvp-v133-fresh.localhost`: Frappe+ERPNext+app install, additive couples tables, guest denial, no initial funding, retained-site fingerprints unchanged. Temporary admin/file removed; disposable site retained for upgrade diagnosis. Source51f5759 test-only changes after packaged8ba375e |
| Representative legacy financial cutover | Tested financial-schema path; historical whole-app checkout not tested | Empty named disposable database reconstructed absent v1.7 financial tables with 4 patient owners/2 clinicians, historical completed+booked reservations. Opening/retry preserves records, completed LegacyHold never auto-settles, known post-opening import once, exact-boundary/unknown events remain ReviewRequired. Retained failed-fixture diagnosis checked each owner's exact balances without clearing holds. Unknown kind unit retry test passes. Native `bench --site teletena-mvp-v133-fresh.localhost migrate` and `check_financial_migration.py` passed; full legacy/journal/line/reconciliation-value fingerprint retained. Temporary administrator removed; fixture intentionally retained with unresolved synthetic holds; do not describe this as running every old application version |
| Whole-MVP visual fidelity | Open | Existing single matrix contains exact paired paths and remaining discrepancies. N03/N04 narrow guided forms; N05 focused plan; N06 tiles/activity; N07/N08 recipient/documents corrected. Other pending route/state comparisons, current 200% zoom and language layouts require completion. Screenshots/build are not acceptance |
| External/manual | Pending | Physical devices/PWA installation, native translations, live SMS/SMTP receipt, medical-lead catalog/rubric/credential and clinical/legal review, real payment/provider activation. No current exact Frappe16 rerun of new couples code |

### Subsequent faithful balance/reviewer slice —40c608f

- G01 `/patient/payments`: reference1.7:1 layout, dark balance/reservation card,
  compact icon activity. Five-row pagination preserves access to all events
  returned by the real API; no financial edit. No unsupported external refund
  action is fabricated. Actual balance differs from prototype illustrative values.
- I02 `/admin/applications`: exact title/copy, compact status filter, dark active
  sidebar, link-like Review. Readable mobile Overview/Applications/More navigation;
  scopes remain in More. Tour invitation no longer overlays mobile Review.
  Verified-profession column remains absent from current queue projection; evidence
  and actual application status are truthful operational additions.
- `browser-balance-review-layout.cjs` passed actual backend activity pagination,
  transaction details, Add funds dialog/Escape with unchanged wallet, reviewer
  name/status/empty filters, mobile pointer action, keyboard dialog/focus return,
  reload, private PDF reviewer200/patient403. No mocked frontend or approval writes.
- Paired390/768/1440: `docs/screenshots/mvp-presentation-current/40c608f/`.
  Inspected desktop/mobile comparisons. Not owner visual acceptance, native
  translation approval, all-state or actual200%zoom proof.
- Locked packaging/TypeScript and lint exit0 (existing warnings); three node
  status/grouping/service-worker tests pass. No presentation passwords found in
  packaged public files. Individual call core unchanged; hosted suite not repeated.
- Built40c608f replaces8ba375e after these explicit runtime/UI edits. Later
  evidence-only commits must have empty frontend/backend runtime diff against it.

### Review the current persisted shared record

Open **http://127.0.0.1:8017/teletena/**. Use **Use email instead → Use password
instead** and the mode-600 private file listed below. The file also contains the
second adult's fictional credentials. Clinician: Appointments → completed couples
session → consultation notes → Amend (creates a local draft only until Save).
Partner: Appointments → completed session → shared summary / Book a follow-up.
Payer: the same encounter does **not** show the summary selected only for Partner2.
Patient More → Shared sessions shows consent and appointment links. Reviewer
queues remain logistics/evidence-only, without clinical-record access.

Paired evidence: `docs/screenshots/couples-current/34641d8/` (hosted media),
`34641d8-consent/` (separate guided steps), `8ba375e-documents/` (current N07/N08).
The N07 capture is an amendment, whereas the prototype shows a first draft;
immutable history/earnings labels intentionally differ. The N08 summary-first
composition and right privacy panel were visually inspected at1440 and390; actual
recipient restrictions and demonstration ribbon remain. The separate prototype
individual follow-up field remains a recorded discrepancy, not a pretend control.

The starting 7b866e8 versus d720596 difference was docs only. Later runtime changes
were rebuilt explicitly. The8ba375e document checkpoint was rebuilt explicitly as40c608f after the payment/admin UI corrections above. Subsequent evidence-only commits do not change runtime code.
Production assets are served by dedicated Gunicorn453370, not Vite. No public
ports, original-site migrations or Selfmade changes occurred.

### Focused financial verification and test corrections

- `check_financial_migration.py` now fingerprints reconciliation **values**,
  not dictionary keys, and all legacy/journal/line records rather than only totals.
  It passed on the retained v1.33 disposable site after representative cutover.
- New unknown-kind regression passed (1 test,5.012s): two import retries reject,
  legacy row/balances/journals remain, audit stays ReviewRequired.
- Two existing financial tests initially failed because their artificial Ended
  rooms omitted `room_closed=1`. The newer security guard correctly refused
  finalization. Only those owned fixtures now explicitly represent a closed room;
  no production assertion or authorization changed. Both passed (5.855s).
- New real-connection dispute/release race passed (1 test,7.167s): exactly one terminal outcome, no simultaneous release and open dispute, release retry does not duplicate posting. Concurrent payout test passed in the initial three-test run; the two stale-room
  fixture failures above are preserved in this account rather than claimed passed.
- Retained legacy fixture initially failed when the harness called a financial
  command on its intentionally held wallet. Read-only retained diagnosis verified
  exact balances and held-command denial; no deletion, balance repair or hold
  clearance was used to hide that failure. The corrected harness checks healthy
  owners and held owners separately. This result is a financial-schema fixture,
  not an exact whole historical application installation.

## Historical checkpoints (superseded classifications retained)

## Presentation data and account access

`tele_tena.presentation_data.setup` is an explicitly invoked, exact-site-bound CLI
command, not an installation hook or public endpoint. It creates fictional Selam
Bekele (patient), Hana Tesfaye and Dawit Alemu (applicants), and Mekdes Abebe
(demonstration vetting reviewer), practical Individual counseling / Stress and anxiety
support services, private fictional PDF evidence and an idempotent opening ETB1,000.
Prices are centralized illustrative values, not Ethiopian market-rate claims.
Scope approval is **not** performed by the seed. The ordinary reviewer browser
approved Hana's application and Individual counseling scope for the demonstration;
that is not medical-lead credential verification. Dawit remains Pending with no
clinician privilege. Catalog definitions remain Legacy test / Not reviewed internally;
no finalized clinical taxonomy or verified qualifications/ratings are fabricated.

Private mode-600 account file (never commit or paste its contents):
`/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private/tele_tena_presentation_accounts.json`.
Patient: `patient.presentation@example.invalid`; clinician: `clinician.presentation@example.invalid`;
reviewer: `reviewer.presentation@example.invalid`. Select **Use email instead → Use password instead**.
The earlier review-account file belongs to the retained old site and is not this preview's credentials.

At the earlier presentation setup checkpoint, two actual bookings were retained: one direct calendar booking and one private offer
acceptance, each ETB300. Patient then had ETB400 available / ETB600 reserved; this is not the current wallet.
Repeat setup after those bookings preserves exact owner wallets, schedules, applications,
appointments, legacy events, accounts and journal lines; no duplicate seed or reset.
A cancelled no-supply request and interrupted registration records are retained, not deleted
for screenshots. Complete populated consultation summaries/earnings/clinic scenarios remain pending.

## Actual checks in this checkpoint

| Check | Actual result and boundary |
|---|---|
| Fresh site | `scripts/check_fresh_install.py`, retained dedicated named site: Frappe/ERPNext/TeleTena install, schema/repeat migration checks passed; original site fingerprints preserved. Temporary localhost DB administrator and mode-600 credential removed. This is not full legacy-upgrade reconciliation acceptance |
| Publication chain | Real reviewer application + scope actions; approved clinician offering/schedule commands; patient calendar/disclosure/confirmation/detail/reload; one ETB300 reservation. Earlier harness selector/route mistakes were corrected without repeating the successful booking |
| Private request chain | Separate patient/clinician sessions: scheduled request → authorized inbox → offer → patient receives offer without manual refresh → confirmation → appointment → own accepted offer history; one further ETB300 reservation. Competing clinicians and immediate routing-wave acceptance still need current full coverage |
| No-supply publication | At `ed81ac3`, mobile guided publication opens saved progress automatically, reload preserves it, truthful no-eligible-supply notice, cancel leaves wallet unchanged. No claim of an offer or match where supply is absent |
| Registration | Real backend random OTP with `scripts/presentation_otp_test_wsgi.py` at bounded loopback 8028: wrong-code rejection, patient adult/consent/privacy onboarding, clinician intent, interrupted step recovery, private resume and application submission passed. Applicant has no approved clinician role. Test server stopped, captured codes deleted, public registration flags restored disabled. Expired-code/resend/returning-phone and full abuse/concurrency browser gates remain open; no live SMS/email |
| Patient read-only journey | `scripts/browser-presentation-patient.cjs` at `ffa2392`: real invited password sign-in; Home → discovery → preview/full profile → authoritative calendar selection → disclosure review/back; focus returns after Escape, selected-date hover readable, inputs preserved, no bookings/funds mutated. Paired 390/768/1440 captures |
| Clinician/details | `scripts/browser-presentation-overview.cjs` at `c9c25cd`: compact F01 rows; keyboard link → loaded participant detail; 390/768/1440, reload; compact time-change action opens authoritative slots, selects and cancels without submitting. Exact patient wallet/clinician earnings queries unchanged |
| Layout / zoom | At `904c746`, C02 Amharic and Oromo 390px layout captures; actual Chrome tab zoom 200% (outer1440/CSS720/DPR2), paired reference. Not native-language approval or all-route zoom acceptance |
| Other workspaces | At `ddfe210`, patient/clinician/reviewer real authenticated queries and paired 390/1440 captures; individual actions and visual acceptance are separate |
| Build/privacy | Locked production packaging, TypeScript and frontend lint pass; existing lint warnings and >500KB chunk warning remain. Generated public assets checked for all four presentation passwords: none found. No unchanged broad financial suite rerun claimed |

## Current consultation correction — authoritative evidence

The room/post-session findings below supersede older call-pending claims in this
report for **individual appointments only**. PR #44 remains draft. No merge or
remote deployment occurred. Initial inspection found backend checkout
`e4bc918bf13eca426076afff13a8c0fcb6e574f7` and packaged frontend
`c3e1ff1263eaec2851a1817a1bf54c90f894a40c`. Both now use the corrected application
code described above; later report/test-only commits do not alter that code.

A full database/private-files backup preceded the owned synthetic appointments:
`sites/teletena-mvp-presentation.localhost/private/backups/20261010_111920-*`.
No historical appointment, balance, credential or clinical record was reset.

| Reproduction / state | Exact cause | Correction and evidence |
| --- | --- | --- |
| Approved patient/clinician Join, valid window | Presentation site lacked its private LiveKit configuration; generic connection error hid that distinction | Secure mode-600 site-private setup; safe `consultation_service_unconfigured` category; no browser secrets. Existing development configuration preserved |
| Both joined, clinician received no remote media | Subscription arrived before React mounted the attachment container | Attach existing publications when the ref mounts and on subscription/publication changes. Both actual remote audio/video streams advance in independent browser contexts |
| End with both roles in room | Ended lifecycle left a stale room presentation and misleading Leave/rejoin text | Terminal state stops tracks/connection and presents clinician documentation versus patient completion-pending/detail actions |
| Patient detail open during call | Polling stopped once call state became Open | Poll while appointment remains Booked; patient already-open detail receives End and later published summary without reload |
| End closure pending → finalize | Finalization could mark Completed before room closure succeeded, making End retry unavailable | Server rejects finalization while `room_closed=0`; save draft remains available; visible closure-retry route and disabled Finalize. Controlled local configuration outage followed by real Cloud retry passed |
| Lost draft/finalization responses | Identical saved text could produce a redundant draft revision | Identical draft retry returns current revision; finalized retry returns original result. One consumption posting/earning, no second reservation or earnings release |
| End confirmation inside fullscreen | Portalled dialog lay outside native fullscreen element | Exit native/expanded fullscreen before confirmation; keyboard-aware expanded fallback, normal focus handling |
| Toggle failure / late camera resolution | Control feedback could replace connection feedback; late captures could outlive navigation | Separate control errors, generation guard, room/track disposal and detached-element cleanup. Held asynchronous camera result stopped after navigation |
| Reconnecting | Signaling reconnect event was not handled | Handle LiveKit SignalReconnecting as well as media reconnect. Test closes hosted signaling transport while offline, then restores and observes Connected |
| E08 / E05 / E11 composition | Audio reused full dark video layout; preflight controls preceded the preview; documentation lacked reference facts/hierarchy | E08 light page + centered dark audio card; E05 preview-first device card and readiness sidebar; E11 separate private note/shared summary and compact finalization facts/actions |
| Completed timeline showed two identical finalizations | Completion and documentation-publication audit events used the same label | Preserve both events, label “Consultation completed” and “Documentation published”; retry does not add either event |

### Checks actually run

- Frappe `tests/presentation.py`: three focused tests passed together:
  closure guard/draft idempotency, explicit note sharing/revision preservation,
  encounter privacy/completion/feedback. A combined-run fixture assumption was
  corrected to assert the completed-session/reliability increment relative to
  existing fixture counts; assertions and existing records were preserved.
- Frappe `tests/integration.py`: consultation authorization/window/token/End test
  and concurrent Join/End serialization test **2/2 passed**.
- `scripts/browser-consultation-presentation.cjs`, application
  `0c804ed6795c0629fd630a8d9066ba794aad6e7a`: actual hosted development Cloud,
  independent patient and clinician sessions, fake camera/microphone devices.
  Both receive advancing audio/video; native fullscreen; mute remote-state
  change; camera toggles; audio-only; signaling reconnect; late camera cleanup;
  Leave/rejoin; clinician End/configuration-failure/closure retry; handoffs;
  draft network failure/value retention/retry/reload; preview without saving;
  patient private-note omission; completed list, feedback availability and
  follow-up navigation; repeat finalize; **one Pending earning with recorded
  release time and exact balance increment**. End alone created no earning.
- Cached original and reissued **application** tokens, still unexpired, rejected
  when reconnecting directly with the SDK after End for both opaque identities,
  including the patient who left before End. This is hosted Cloud evidence.
  Automatic SDK/server token refresh was not independently intercepted/tested.
  Self-hosted deletion still cannot invalidate an unexpired reusable JWT.
- `scripts/browser-consultation-review.cjs`, final application
  `d720596e385e9f50c1ed9df256c09fd2e9b4cd13`: guest/reviewer denial, generic
  raw-table API denial, Completed Join rejection, real future-appointment
  out-of-window rejection, disabled Join, local device preparation before the
  window, immediate preview-track stop on mode change and navigation, preserved
  finalized notes after entering/leaving an unsaved amendment, correct timeline.
  320/390/768/1440 views and real Chrome 200% patient-detail zoom passed.
- Locked production packaging / TypeScript build passed. Frontend lint exits 0
  with existing warnings; bundle-size warning remains. Generated assets scanned
  against private presentation passwords and LiveKit key/secret: none found.
  Preview returned HTTP 200. No schema added; no new
  fresh-install, complete OTP/finance or Frappe 16 suite rerun claimed.

### Reference comparison (separate from functional acceptance)

Paired files: `docs/screenshots/consultation-current/`; `evidence.json` records
which source produced each set. Original connected-state pairs use `0c804ed`;
terminal/preflight and unsaved-amendment pairs use `d720596`. Later application
changes after the connected run are preflight/document layout, timeline labels
and device-status copy; no token/media authorization changed.

| Reference | Rendered comparison | Remaining intentional differences / gate |
| --- | --- | --- |
| E05 `#e05` | Preview-first bordered card, stacked device fields, right readiness/join panel, same 1128px content width at desktop | Actual fake device image, truthful clinician/service/time, explicit Check and refresh/window states instead of prototype ready claims; demo ribbon. Human visual approval pending |
| E07 `#room` | Dominant remote stage, self-preview, dark header/sidebar and compact controls; mobile stacks facts below media | Fake green video replaces reference portrait; explicit End versus Leave; booked duration never presented as measured elapsed time. Mobile stage/control proportions require owner review |
| E08 `#e08` | Light page, centered dark card/orb/wave, compact control bar; no black empty video area in audio-only | Quiet/muted activity is flat, not decorative speaking. Actual identity/duration, labeled controls, compact details fold, demo ribbon. Human approval pending |
| E09 `#e09` | Real signaling reconnection status and recovery captured | Signaling-only failure can keep existing RTP media visible; cannot truthfully render a total-media-loss state or claim device/network handover coverage |
| E11 `#e11` | Separate note/summary documents, privacy labels, finalization sidebar | Current comparison includes an **unsaved amendment** to a real finalized encounter, explicitly labeled; original persisted first draft captured on `0c804ed`. Timeline/disclosure accordions and actual booked duration retained; measured connected duration unavailable |
| E13 `#e13` | Role-specific completed detail and actual published summary | Real feedback/dispute/sharing affordances extend prototype. Private clinician document is absent from patient API/DOM; full owner visual acceptance remains pending |

The images were opened and compared at desktop/mobile; screenshot presence or
build success is not treated as acceptance. English layout only in this batch;
new Amharic/Oromo copy is provisional. Actual 200% zoom covers completed patient
detail, not a connected video call.

### Review the connected workflow

1. Open **http://127.0.0.1:8017/teletena/**. Credentials remain in the mode-600
   site-private `tele_tena_presentation_accounts.json`; use separate browser
   profiles for Selam (patient) and Hana (approved clinician), email/password.
2. Completed appointments → the latest Individual counseling encounter:
   patient sees only published summary/feedback/follow-up; clinician sees the
   private note, publication history and optional amendment action. Reload both.
3. Book an eligible generated slot for a fresh call using the patient. The
   booked clinician joins the same appointment from their list. Check devices,
   Join, mute/camera/audio-only, Leave/rejoin, then clinician End for everyone.
4. Clinician Finish the consultation → Save draft → preview → finalize. Patient
   already-open detail updates. Earnings shows Pending with release time; End
   is not payment settlement. Do not reuse completed test rooms for a new call.

### Remaining substantive gates

- **Working two-adult couples is missing**: current appointment/token model has
  one patient and clinician, relationship link is not participant consent,
  three-person authorization or recipient-scoped notes. N01–N08/SH01 remain a
  required MVP blocker; no shared-summary access is granted via relationship.
- Scheduler remains disabled on this presentation site, and no dedicated
  continuous worker/scheduler acceptance was performed here. Pending earnings
  stay pending; no withholding bypass or unrelated service restart occurred.
- Whole-MVP owner visual approval, continuous scheduler, fresh/legacy upgrade
  and exact Frappe 16 release gates remain. Current isolated checks do not prove
  physical devices, live SMS/email, native translations, real payments or
  remote deployment. No Selfmade changes occurred.

## Applicant landing correction — current build

Newly registered/pending clinicians previously reached the approved-clinician
Today dashboard and triggered a denied appointment query, showing misleading
“Unavailable” errors. `1d23e4f` now displays actual application review status and
working professional-review/account links, and skips approved-only queries.
`c3e1ff1` limits applicant navigation to application, professional review and account.
No clinician privilege, service authorization or backend permission was changed.

`scripts/browser-presentation-applicant.cjs` **passed on the current packaged build**:
Pending state, profile navigation/reload, no Requests/Availability links or approved
metrics at 390/768/1440; direct appointment API remains **403**. No role or funds
mutation. Paired B11 captures extend the reference's review panels for a pending-only
application; the reference's illustrative approved/clarification history is not copied
into actual records. Rejected/resubmitted and all review actions still need full
current acceptance. Earlier registration screenshot is historical and visibly shows
this now-corrected landing defect; it is retained as diagnosis, not current acceptance.

## Paired comparison and remaining differences

Evidence: [paired screenshots and capture sources](screenshots/mvp-presentation-current/README.md).
Reference is rendered read-only from the supplied 142-screen source on 8044.

| Reference | Implemented correction / observed comparison | Remaining acceptance |
|---|---|---|
| C01 Home | Compact dark care hero, readable one-row search action, genuine next-session row and wallet composition; mobile global icon inheritance corrected | Mobile Help & tours adds height; no completed care history yet; global demo/language/privacy operations legitimately add elements absent from prototype |
| C02 / popup | Shared grid spacing and hidden-label collision fixed; pill filters, search/private-request entry, description and readable card/preview facts; Escape focus return | Extra supported availability filter; one genuinely approved clinician; initials/no unverified portrait or invented review numbers. All empty/failure states and final composition acceptance pending |
| C04 | Reference heading “Meet your clinician”; approved offering context and truthful trust information | Professional public biography/approach/verified affiliation and corresponding persisted profile depth still incomplete; do not invent credentials |
| C06/C08 | Actual available month/dates/times, timezone, selected-day contrast and disclosure/price review; Back retains input | Dedicated operational booking route differs from prototype wizard; remaining mobile/zoom/composition comparisons pending |
| D01/D03/D04/D05 | Guided privacy publication, dedicated saved progress, scheduled-care explanation separated from immediate three-minute target, actual private offers/acceptance | Full paired populated offers/progress and error/expiry/funding-recovery visual acceptance still pending |
| E02 | Actual loaded two-column appointment facts/preparation/snapshot; compact time-change action rather than always-expanded panel | Ribbon/header offset, truthful initials rather than fictional verified portrait, operational timeline/financial details add height; completed/ended/cancelled comparisons remain pending |
| F01 | Correct “Your day at a glance” / “Up next”; compact icon/time/authorized identity/status rows instead of full detail cards | Presence ribbon and first-visit tour add height; readiness links/verified credential-renewal state differ from prototype; real zero earnings and counts preserved |
| H01/F08/F14/H02/I01/I02/I05 | Current fictional data replaces older test-purpose presentation content; pairs retained for audit | Account city/contact editing, richer professional settings, complete evidence/admin and all role states still require functional and visual acceptance |

**Release blockers:** working two-adult couples (relationship links alone are insufficient),
complete MVP screen/state fidelity and missing profile/journey behavior, continuous
site-bound routing/earnings jobs, representative owner-level legacy reconciliation/
cutover and final installation/migration acceptance, current hosted LiveKit End/token
revocation regression, final integrated permissions/OTP/notes/evidence release checks.
Existing financial/appointment/privacy/PWA work is preserved, not declared reverified
from these UI captures. No merge or deployment. External live delivery, physical-device
calling, native translations and medical-lead catalog approval remain separate gates.

## Short current walkthrough

1. Use the private account file and the exact preview above. Patient Home → Find care →
   Hana's preview → full profile → Choose a time → calendar → disclosure → price review.
   Confirm only if intentionally creating another demonstration booking; existing bookings
   can be reviewed from Appointments without consuming more funds.
2. Patient Post a request → scheduled window → privacy preview → publish. It opens saved
   progress; posting is free. Hana Requests receives only eligible authorized requests,
   chooses an offering/time and sends a private quote. Patient accepts only after exact
   price/sharing review; Hana Your offers → History links to accepted consultation.
3. Clinician Today → compact consultation row; Availability → existing published calendar;
   Services shows its actual approved offering. Do not assume immediate readiness from
   a published working interval alone; presence and applicable policy remain enforced.
4. Reviewer Applications / Service scopes show names and actual decisions. Reviewer
   privileges do not grant clinical notes. Do not treat a fictional demonstration approval
   as a verified professional credential.

---

# Historical evidence below — superseded runtime, retained findings

# Current MVP journey correction — 9 October 2026

**Active checkpoint; not visual acceptance or handover readiness.** This report
supersedes the runtime identity in older checkpoint reports. The screen matrix
keeps visual fidelity and functional journey acceptance independent.

## Historical runtime — 9 October (superseded)

- Branch `feat/mvp-release-handover`, draft PR #44, dependent on draft PR #43.
  The preserved `1e8d161468eb8d3563f1b5743982722c749bbcbf` ancestor remains included.
- Packaged application source **`0eb22ef4e0c988cebabe869b75b042f040bf677f`**.
  Account browser evidence below was captured at `7aa1ea9`; the latest appointment/documentation browser evidence uses this packaged source. Subsequent evidence/documentation commits do not change its application code.
- **http://127.0.0.1:8017/teletena/**; site
  `tele-tena-pr12-fresh.localhost`; bench `/home/frappe/frappe/frappe-bench`.
- Gunicorn master 392014, two site-bound loopback workers; working directory
  `sites`; app checkout above. Targeted HUP reloaded only these web workers after
  backend fixes. Production packaged React, not Vite. `public/review/release.json`
  records the source and asset hashes. Preview HTTP 200 was checked.
- Reference `/home/frappe/teletena-design-reference`, rendered read-only on 8044.
  Actual 142-screen inventory and source remain authoritative.
- Credentials and source ancestry preserved. Earlier fixture cleanup had a broad projection recalculation: the audit and narrow replacement are documented below; blanket historical financial-preservation claims are not established by those earlier runs.
  Additive note-sharing v1.31/v1.32 migrations were applied only to this isolated
  review site after backup; preservation checks are below. No balance repairs,
  retained fixture reseeding, merges or remote deployment.
  Intentional earlier browser deposits/bookings/requests/offers remain recorded.

## Historical account / appointment / native-worker checkpoint

This section records its earlier checkpoint; per-commit findings below are
historical evidence, not an assertion that the entire MVP has passed.

| Reference | Implemented and actual checks | Remaining fidelity / journey gaps |
|---|---|---|
| H01 account overview | Reference two-column personal/settings + dedicated wallet layout. Profile form Enter/save/reload, associated required-name errors, draft retention on aborted save, successful retry; MariaDB values checked | City/contact editing and working shared sessions missing; optional relationship link is not couples acceptance. Actual zero wallet differs from fictional reference amount |
| H02 clinician account | Public name/care languages/private PDF resume and practice/affiliation routes | Reference portrait/introduction and richer profile editing still incomplete; no invented credentials |
| H03 privacy | Global defaults and local disclosure preview; save/reload; no repeated wallet on tab | Reference age/alias controls exceed current name/history model; request override must remain independent |
| H04 preferences | Associated language/timezone selects; persisted UTC; Amharic/Oromo mobile captures | Notification/accessibility preferences absent; native language approval pending |
| E01 appointments | Reference tab geometry/title, booked-local-month/year history, correct public clinician name, status-based filters, view context across detail/Back/reload. Actual pre-start cancellation creates one release | Upcoming date grouping, remaining state/mobile/zoom coverage and coherent presentation content pending |
| E02/E11/E13 | Current owned browser rechecks draft/reload, finalization, explicit note sharing, patient summaries, private amendment/history, route isolation, reviewer denial; one earning/completion posting | Owned Ended fixture is not actual media/End/revocation proof; couples recipients and live call chain pending |

### Exact current checks

- `scripts/check_mvp_account_browser.py` passed against packaged `7aa1ea9`.
  390/768/1440 paired H01–H04 screenshots. Real Chromium **tab zoom** at
  200% (1440 outer width, 720 CSS width, DPR2), paired application/reference.
  The abort-on-save check is controlled transport failure, not proof of a real
  server outage. Profile/defaults/preferences values were checked in MariaDB.
- `scripts/check_mvp_notes_browser.py` passed against packaged `9988610`, then `3b02709` after adding local month/year history grouping, and `0eb22ef` after correcting selected-tab visibility on resize/reload.
  Real owned accounts and backend operations, appointment cancellation,
  persisted notes/publication/amendment, patient and reviewer authorization,
  delayed route isolation, 390/768/1440 paired appointment views.
- `tests/appointment-groups.mjs` passed: no inferred completion, distinct
  clinician documentation tasks, terminal precedence, state-based views.
- `test_appointment_list_cancellation_actor_does_not_unmask_patient`
  passed at `ed28dc2` after reproducing a missing SELECT projection causing
  every clinician name to fall back to “Your clinician”. Cancellation actor
  IDs are retained privately, not returned to unrelated participants.
- Asset/hash/PWA scope scanner passed for `9988610` and `3b02709`, including exact-value scan against four privately stored reviewer passwords; no match. No provider values were configured on this site.
- Locked production build `scripts/build_review.py` passed for `9988610`, `3b02709` and `0eb22ef`.
  Lint exits 0 with existing warnings; build retains >500KB chunk warning.
  These are not visual acceptance.
- Real supported PWA waiting/update flow passed **3bf96b1 → dfe9a2b**, then **9988610 → 3b02709** and **3b02709 → 0eb22ef**:
  old application remained until explicit Refresh; new public bundle loaded;
  no private/API cache paths. Not rerun as a physical-device check or claimed
  as device-level uninterrupted calling or installation.

- Four current `tests/integration.py` methods passed (7.639 seconds): patient phone signup HMAC/single-use/privilege bounds, clinician signup requiring manual approval, guest CSRF/wrong-code durable attempts, concurrent attempt/verification atomicity. Enabled flags and provider transport/login establishment are patched in-process; real persisted backend rules are exercised, but this is not complete HTTP registration-browser acceptance. Preview site policy remains invited-only.
- `scripts/browser-authentication-flow.cjs` passed: real retained patient/clinician password sign-in and disabled phone fallback. Its enabled OTP/error interaction branches mock frontend responses; they are UI evidence only, not registration completion or delivery proof.

### Native worker and preservation evidence

`check_mvp_earnings_worker.py` passed at the `40579e7` checkpoint. Supported
booking/finalization APIs created owned earnings with zero/one-minute policy
snapshots in test-process memory only. The configured site policy, clock and
retained records were not changed. The test waited through the real one-minute
recorded release time, dispatched the installed `Scheduled Job Type` using
`enqueue(force=True)`, and executed it in a separate native RQ worker restricted
to a unique queue. Two executions produced **one** release journal; an open
dispute held the other earning after its release boundary. A repeated payout
request returned the same reservation; no external transfer occurred.

The site's continuous scheduler is **disabled**. Shared worker/scheduler
processes were not restarted, used or drained. This proves native forced
dispatch and RQ execution, **not** a continuous cron tick or complete old-process
cutover. Native Scheduled Job logs/last-execution retain execution evidence.
The private owned queue/job was removed after completion.

A test-harness audit found that inherited `Integration.tearDownClass` globally
recomputed **all** financial account projections after fixture removal. This
could conceal unrelated discrepancies. It has been replaced with subtraction
of only the exact removed fixture journals' signed deltas under account locks.
Unrelated owner values and pre-existing shared-control offsets are left intact.
`check_fixture_financial_preservation.py` passes a rollback-only MariaDB
regression with deliberately inconsistent **test-only** debit/credit/foreign
accounts and retry cleanup. No persisted balance repair was made.

The native worker run now compares exact pre/post row fingerprints for all
12 financial/encounter tables (accounts, journals/lines, wallets/log, earnings,
payouts, disputes, reconciliation, appointments, notes/revisions): **all matched**
after owned cleanup. This is present-run preservation; it cannot retroactively
prove that earlier global-cleanup runs never changed an inconsistent projection.
Full legacy/opening-boundary reconciliation and fresh-site acceptance remain
release gates. Original journals/records have not been rewritten for this fix.

### Paired comparisons and current review steps

Evidence: `docs/screenshots/mvp-connected-journeys/H01–H04-*` (source `7aa1ea9`)
and `E01-{upcoming,completed,cancelled}-*` (source `0eb22ef`). Desktop and mobile pairs were
visually inspected. H01 now follows reference columns, wallet and settings rows;
missing city/verified contact fields and incomplete shared-care workflow remain
explicit differences. E01 follows reference heading/tabs; additional operational
views, fuller facts, tour invitation and generic Upcoming date grouping still differs. A real 390px comparison exposed an off-screen selected tab; the strip now reveals the selected view horizontally without moving page scroll/focus. The capture harness verifies visibility at each width.
**Neither area is declared visually accepted.** No universal pixel-match score.

Open **http://127.0.0.1:8017/teletena/** with existing private reviewer credentials.
Use email → explicitly selected Password on this intentional invited-review site.
Patient: Account → Privacy / Language & timezone; Appointments → view → consultation
→ Back. Clinician: Account → professional details/private resume; Appointments →
ended consultation → draft/preview/publication. Admin review access remains separate
from private care records. Owned browser fixture credentials are temporary and
removed; these tests do not seed a coherent retained presentation dataset.

### Remaining release blockers

All-MVP paired fidelity/state coverage; direct registration in a separate enabled
policy with real backend controlled transport; coherent additive presentation
content; working two-adult couples participant/consent/call/note authorization;
current hosted LiveKit original/refreshed-token End regression; continuous
site-scoped routing/release and safe old-writer cutover; current fresh install /
representative owner-level legacy upgrade/repeat reconciliation. The preview
stays invited-only. Live SMS/SMTP receipt, physical-device media/PWA, native
translation and clinical taxonomy/rubric review remain external validation gaps.
No merges, financial repairs or Selfmade changes in this checkpoint.

## Earlier implemented and verified slices

| Area | Implemented | Verification | Remaining |
|---|---|---|---|
| Home / discovery / preview / profile / service / booking | Search-led dashboard, real wallet, scoped cards and preview, tailored service page, generated monthly calendar | Real password sign-in, popup close/Escape/focus return, profile→service→calendar, selection/Back; actual booking and matching available/reserved delta | Public biography/verified expertise (not private application text), registration-enabled onboarding and coherent presentation dataset |
| Disclosure / price review | Server-produced preview; separate consultation/payment panels; actual available balance and shortfall; funding in new tab retains form; mobile paired facts | Live API preview, review totals, Back retains narrative/time; no mocked success | Explicit insufficient-funds browser recovery on this new review, automatic-confirmation browser capture and manual-confirmation acceptance/expiry lifecycle |
| Patient requests / private offers | Three-step composer, focus-managed reviews, persisted progress/offer workspace, state-driven icons; no three-minute no-offer message when a valid offer exists | Real retained scheduled request→tailored offer→accept→one appointment/reservation→detail/history handoff; concurrency/private-offer regressions | Immediate/routing-worker/reconnect/expiry full current browser acceptance and all reference states |
| Appointments / documentation | E02 conversation/disclosure/preparation composition; E11 private note and summary panels with finalization beside them; E13 clinician document/patient summaries, persisted revisions and amendment; posting-derived reservation status | Actual owned-fixture Frappe browser preview→draft/reload→finalize→patient summary→amendment; reviewer denial, delayed route isolation and exactly one completion journal/earning. Paired 390/768/1440 captures inspected | Full current hosted call/End/feedback/release chain; presentation dataset; remaining language/zoom/couples recipient states |
| Clinician Today / earnings | Actual metrics, upcoming/action priorities, readiness, available/pending/payout composition, real activity filters/table/mobile cards, exact-money payout dialog | Real authenticated responsive pages, activity filters and zero-payout validation; no invented totals | Scheduled-release/cutover/reconciliation release gate and payout browser lifecycle |
| Care records | Table/card route agreement; encounter timeline, original disclosure, explicit private-note boundaries | Real browser directory→record; equal-name patient separation and authorization regression | Remaining filter/date/sort and shared-summary visual states |
| Administrator | Distinct I01 overview, I02 named queue, I03 review dialog; real counts, evidence download action, separate scope authorization | Reviewer real sign-in, queue/review/Escape focus return; responsive captures | Full vetting/scope/resume lifecycle, remaining operational queues and role tours |
| PWA / localization / zoom | Safe explicit update mechanism and provisional translations | Real old-bundle→waiting worker→explicit Refresh→new bundle; no API/private cache paths. Genuine Chrome 200% zoom and Ethiopic font checks | Full translated copy review, key call/calendar zoom, physical-device installation/accessibility |

### Exact findings corrected

1. A routed request selected offering options by **display title equal to parent
   scope label**. Tailored offerings therefore disappeared from the composer.
   The backend now provides this clinician's exact-scope/format published offering
   IDs; submission/acceptance still revalidate authorization, slot and price.
2. Offer-history filtering happened after pagination. Active/History filtering
   now precedes server pagination; closed/expired states remove active disclosure.
3. `Help & tours` inherited `bottom` while desktop positioning added `top`,
   stretching its button over the payment panel. The shared rule clears bottom.
4. Workspace width read global browser `location` rather than router state, so
   navigating from Discovery retained the wrong width. `useLocation` fixes it;
   the browser regression asserts booking is no longer `workspace-wide`.
5. Care records grouped by disclosed name alone. Two different patients using
   the same name could be combined. Grouping and detail selection now also use
   the patient key **only on the server**, without returning that key. Undisclosed
   encounters remain separate; elapsed Booked records do not become future care.

## Latest connected correction checkpoint

- C04 now has a selected published-service booking panel (actual fee, duration,
  format and timezone) and a separate session-experience section. The actual
  preview→profile→service→calendar→disclosure/Back browser journey passed again
  at `0178881`. No private application statement was exposed as a public biography.
- C09 `/patient/booked/:id` loads the authorized persisted appointment after
  booking and refresh. It distinguishes Confirmed from Pending confirmation;
  it shows the actual reservation, sharing identity and response deadline.
  The retained clinician uses manual confirmation. Two initial post-submit
  browser assertions incorrectly expected automatic confirmation, after successful
  HTTP 200 submissions. Those appointments remain intact. Corrected state-aware
  assertions passed pending confirmation, refresh, three-width captures, detail
  handoff and matching available/reserved deltas at `af1bbd0`. This is not proof
  that the pending appointment was subsequently confirmed or its job expired.
- D09 now has the reference's four-stage rail and a separate persisted request
  narrative/facts panel. Stages derive from request/offer state, not elapsed time.
  Matched reference state was prepared only in the static reference; application
  API responses were never mocked.
- F08 offering table/mobile cards and F09 focused editor use server-projected
  **own current approved scopes**. General application approval cannot widen
  authorization. Revoked scopes leave historical offerings visible but unavailable
  for publication. Fixed saved durations, including 50 minutes, remain editable.
  Format/confirmation rules come from actual schedules; unsupported reference
  controls were not presented as functional offering settings.
- F04/F14 `/clinician/offers` and F13 `/clinician/offers/:offerId` separate private
  outcomes from the inbox. Server pagination/filtering and guessed-ID ownership
  enforcement remain authoritative. Accepted details link to the authorized
  consultation. New patient/clinician tour steps introduce requests and offers.
- Resume errors now stay inline. Oversized PDF browser validation resets only the
  file input and made no upload request; backend private-evidence/tour regression
  passed. The first browser selector was ambiguous between an overview shortcut
  and account tab; scoping it to Account settings corrected the test.
- Rendered F09 exposed another shared CSS collision: `.dialog` capped the intended
  editor at 560px. Reusable `size="wide"` with a custom-property base width fixes
  that cause. At `0c69dfc`, the browser asserts desktop width >=900px, saved
  duration, scope immutability, preview, focus return and invalid price preserving
  input with **no publication mutation**. Genuine 200% zoom (720 CSS px/DPR2) and
  320px editor checks passed; save/cancel remained reachable.

## Checks actually run

- Actual MariaDB/Frappe `tests/presentation.py` methods (all passed):
  `test_public_profile_uses_tailored_offerings_and_rechecks_revoked_scope`,
  `test_request_inbox_selects_tailored_offerings_by_scope_not_label` (including
  Active/History and invalid-view assertions),
  `test_discovery_search_metadata_is_catalog_only`,
  `test_private_request_competing_offers_insufficient_funds_and_atomic_match`,
  `test_two_patients_cannot_claim_one_offer_slot_concurrently`,
  `test_care_records_do_not_link_different_patients_with_equal_names`,
  `test_04_notes_privacy_revision_completion_and_encounter_scope`,
  `test_05_private_resume_scope_application_evidence_and_tour_preferences`,
  `test_practice_only_lists_own_current_approved_scopes`.
  The tailored-scope/inbox method was rerun with own-offer detail, another-clinician
  and patient denial assertions. Initial new test failures (wrong publish keyword
  and missing `re` import) were corrected before these passes.
  Tests use owned synthetic fixtures; suppressed fixture enqueue is not job proof.
- `tests/appointment-groups.mjs`, `appointment-status.mjs`, `care-search.mjs`: pass.
- Source `263beca`: actual earnings All/Pending/Payout filters, zero-payout field validation without reservation, tour replay retaining selected booking time/route, and no tour controls on consultation pages passed in a focused browser check. Dismissal preference was persisted; no financial mutation.
- Real backend browser scripts: `browser-mvp-patient-interactions.cjs` (earlier
  checkpoint), `browser-mvp-review-panels.cjs` (current), plus staged local
  preview/profile/booking, retained tailored-offer acceptance and care/request
  read-only capture scripts. No frontend success-response mocking in these flows.
- `python3 scripts/build_review.py`: locked dependencies, TypeScript/Vite and
  packaged source manifest pass. `npm run lint --prefix frontend`: exit 0,
  existing warnings remain (including state-in-effect and Date render warnings).
- `scripts/check_review_assets.py --site-private <isolated-site>/private`: pass;
  artifact hashes/scope/no source maps/config files and exact private-secret scan
  found no credential values. Secret contents were not printed.
- Genuine browser zoom: Chromium extension `chrome.tabs.setZoom(2)`;
  1440 physical viewport → 720 CSS pixels, DPR 2. Home/Discovery/Account/Wallet
  paired captures at source `8f65e84`; Amharic/Afaan Oromo 390px samples and
  loaded Noto Sans Ethiopic. This is not native-language approval.
- PWA: controlled existing browser stayed on `73f7a08` until explicit Refresh,
  then loaded `1442da8`. No automatic reload or sensitive-path cache observed.

Read-only regression helpers now in the repository:
`browser-mvp-offerings.cjs` and `browser-mvp-offer-history.cjs`, guarded to the
isolated review site and private credential files. Both passed actual backend
journeys; neither prints credential material or publishes an offering.

## Paired comparison evidence

Artifacts: `docs/screenshots/mvp-connected-journeys/`. Each ID has
`*-reference-<width>.png` and `*-application-<width>.png`; zoom samples are
`*-zoom200.png`. Source annotations are in the screen matrix.

Manually inspected comparisons: C01/C02/C04/C06/C07/C08, F01/G05, I01/I02 and
care/request states. Paired capture is not a universal pixel-match score.

- C01: reference dark hero, 1.7:1 columns and dedicated wallet restored; actual
  query/private-request controls are necessary operational additions. Still needs
  coherent fictional presentation content and complete state comparisons.
- C04: approved preview size, fact hierarchy, close placement and actions restored.
  Initials replace unsupported portraits; absent verified profession/history/rating
  facts are not fabricated. Fuller source sections remain incomplete.
- C07: focused 660px sharing flow replaces the redundant side summary. Current
  preview includes required free text and whole saved-history sharing; reference
  selected-record sharing is not implemented and must not be implied.
- C08: two panels and paired mobile payment facts follow the reference. Actual
  cancellation policy, amounts and anonymous disclosure differ truthfully; no
  illustrative 12-hour fee was implemented. Registration ribbon/navigation and
  breadcrumb add height; further comparison/review remains required.
- F01: real three metrics, action/upcoming list and readiness/quick-action panels.
  Past records remain accessible through Appointments, not the Today priority list.
- I01: distinct overview restored. Real submitted/pending/evidence-ready counts
  replace unsupported illustrative renewals/concerns; evidence ready means received,
  not credential verification. I02 is now `/admin/applications`.
- Retained Review/Synthetic records in captures are diagnostic fixtures, **not
  accepted presentation content**. No historical records were renamed or hidden.

The initial G05 capture incorrectly used `#g05` and rendered the gallery. It was
excluded and replaced with the actual inventory route `#earnings`. Capture helpers
now resolve reference hashes from `screen-inventory.json`; F02 inbox and F13 offer
detail are distinct mappings.

D09 reference was recaptured in its own in-memory **Matched** state to compare with
the retained matched application request. Only the reference state was prepared;
application responses were not intercepted. The comparison exposes a missing
four-stage rail and separate request narrative/facts panel, corrected at `af1bbd0`.
The reference role-switching demonstration panel is deliberately not a patient control.

Additional comparisons: F08 follows the reference table/primary create action;
F09 is a two-column editor/preview in a focus-managed dialog rather than a separate
prototype page. The screenshot caught and corrected its width collision. Unsupported
format/extension-policy inputs remain absent, not decorative. F13/F14 show only actual
own accepted/closed outcomes, not the reference's invented sample rows. C09 renders
one true appointment state rather than simultaneously showing illustrative confirmed
and manual-confirmation examples. These specific operational exceptions require
review; **none is marked visually accepted**. 200% F09 and H02 resume-error captures
are additional state evidence, not paired reference acceptance.

## Continuation checkpoint: appointment details and documentation

Focused application commits: `3270280` (financial display), `b914087` (E02),
`d3a44e9` (undefined semantic-token aliases), `1ec716a` (finalized note view),
`3b9a010` (unsaved preview/E11), `4b9ffc0` (compact readiness/composition),
`2ddb33c` (appointment-isolated drafts), and `d608dc7` (status-specific headings).
`a05ed13` included the rendered-reference mapping and was that checkpoint’s packaged build. It is superseded by the sharing checkpoint below.
No schema migrations or retained-data repairs were performed.

Observed and corrected:

- A Completed label had incorrectly implied reservation consumption. The query
  now uses immutable Reservation/ReservationRelease/ConsultationFinalized postings
  and identifies LegacyHold as Review required. Read-only detail queries leave
  balances and posting counts unchanged; no historical funds are settled.
- Undefined semantic CSS variables removed avatar backgrounds, field dividers and
  supporting colors. All nine aliases now resolve to the extracted reference palette.
- Finalized private notes were returned to authorized clinicians but disappeared
  from the UI. The document and explicit amendment action are restored. Patient
  APIs continue to omit private notes; published summary history remains visible.
- Preview before saving the first draft previously required a nonexistent revision.
  Entered summaries can now be previewed in a focus-managed dialog without saving
  or publishing. Ended-call and clinician ownership checks remain enforced.
- Appointment-keyed component state prevents old disclosure/note/form/loading state
  crossing to another consultation during a reused route or delayed response.
- E11 now starts with the two note panels and a finalization panel. E13 puts the
  shared/authorized documents before disclosure; follow-up is a real booking link.
  Expandable readiness avoids repeating the full setup warning on every clinician
  screen. Presence heartbeat, expiry, restrictions and failure messages are preserved.

Actual checks in this continuation:

1. `tests/presentation.py Presentation.test_reservation_display_uses_postings_not_completed_status`
   passed, including a fixture with Completed status and a still-reserved LegacyHold.
2. `Presentation.test_02_manual_hold_confirm_cancel_and_expiry_release_once`
   and `Presentation.test_04_notes_privacy_revision_completion_and_encounter_scope`
   each passed with their own fixture invocation. The notes test additionally checks
   unsaved preview, no revision write and patient denial. A combined three-method
   invocation **failed two tests** because class-shared committed fixtures carried
   an extra reservation/completed encounter into later absolute-count assertions.
   Their assertions were not weakened. This combined-harness isolation issue is
   documented; the full suite is not reported as passed in this continuation.
3. `scripts/check_mvp_notes_browser.py`, using bench Python and the explicit isolated
   site: actual password sessions, draft/reload, preview without write, finalization,
   private omission, patient published summary, amendment/reload/history, reviewer
   denial and delayed cross-appointment state isolation passed. After amendment,
   the database has exactly one completion journal and one earning for the owned
   fixture. The harness cleans its random fixture accounts/records and mode-600
   credentials. **Ended call was a synthetic state fixture, not hosted End proof.**
4. Actual retained care/request/detail browser: table/card route agreement, matched
   request→appointment handoff and paired E02 390/768/1440 captures passed.
5. Patient Home→discovery→preview/Escape/focus return→profile→service→calendar→sharing
   Back passed after the shared token correction; no booking was submitted in this
   read-only rerun. Owner offerings/editor and paginated own offer/detail/appointment
   handoff passed on that checkpoint; no clinical/financial mutations.
6. Explicit PWA update passed `4b9ffc0`→`2ddb33c`: existing controlled browser kept
   its old application until Refresh to update, then loaded the new actual packaged
   bundle. No API/private cache paths. Not physical-device installation proof.
7. Production locked build passed; lint exits 0 with existing warnings, and chunks
   over 500 kB remain a build warning. Private asset scan passed with zero exact
   credential matches. No current Frappe 16, fresh installation, migration,
   scheduler release, live SMS, physical-media or native-translation pass is inferred.
8. `browser-consultation-status.cjs` passed on the earlier composition checkpoint.
   It mocks only Ended/documentation response state and is **UI-only evidence**;
   the owned-fixture browser check above is the actual backend documentation evidence.

Paired evidence: `docs/screenshots/mvp-connected-journeys/E02-*`, `E11-*`, and
`E13-{reference,patient-application,clinician-application}-*` at 390/768/1440.
Comparison notes: column proportions, note/document hierarchy, actual reference
40px/32px headings, typography, dividers, icon surfaces and action placement were
inspected. Demo ribbon, authenticated navigation, anonymous initials, join-window
restrictions, booked-vs-connected timing and amendment/history are operational
extensions. Reference portraits/credentials/49-minute duration and prices were not
invented. E11's optional note-sharing gap at this earlier checkpoint is closed
by the explicitly verified sharing checkpoint below. Diagnostic fixture wording remains a presentation-content
gap. No screen is called visually accepted or handover-ready.

All **99 MVP reference routes** were rendered at 1440×1000 for exact headings,
fields, actions and structure. The matrix now identifies flagship `app.js` and
later `request-experience.js` overrides instead of hashing empty `forms` entries.
This is reference mapping, not 99 operational/visual application passes.

## Latest sharing checkpoint — source 53d7ec3

Reference E11's explicit **Share this note with the patient** control is now
operational. v1.31 adds revision-specific publication, default 0 for every old
note. v1.32 stores draft intent separately, also default 0. A selected draft is
never a published note. Finalization requires the treating clinician and explicit
publication; patient APIs return only the published text in
`shared_consultation_notes`, never the `private_note` or draft-intent fields.
Summary publication is independent. Sharing history labels what was shared.
Later private amendments do not retract or overwrite previously shared revisions.
Clinic affiliation, vetting roles and optional partner links grant no note access.
See `consultation-note-sharing.md` for the boundary and migration details.

Verification actually performed:

- Full pre-migration database/config/public/private-file backup succeeded at
  `private/backups/20261009_170359-*` on the isolated site. A separate extra
  row-snapshot command then failed because its working directory was wrong;
  the shell nevertheless launched migration. This ordering error is recorded,
  not presented as a successful pre-snapshot. The prior full backup remained intact.
- Post-migration protected export `20261009_170754-*` was compared with that
  pre-migration backup using parsed SQL-row hashes. **All original rows across
  ten note/appointment/financial tables matched** after excluding only the newly
  default-zero column. No record values were printed. No balancing or row edits.
- A correct private row snapshot then covered repeat migration and the additive
  draft-choice patch. All original note, appointment and owner financial rows
  were unchanged; historical publication/intent stayed 0. Both patches were
  executed twice without resetting populated data. Fresh installation is pending.
- `Presentation.test_explicit_note_sharing_preserves_private_revisions_and_money`
  passed: private first revision, unexposed selected draft, explicit note-only
  publication, invalid flag rejection, later private amendment, prior sharing
  retained, patient/other-clinician/reviewer denial, repeat patch and one financial
  completion/earning. `Presentation.test_04_notes_privacy_revision_completion_and_encounter_scope`
  passed again independently with the new columns.
- `scripts/check_mvp_notes_browser.py` passed on packaged **53d7ec3**: actual
  checkbox/save/reload, selected-draft patient omission, publication and later
  private amendment, in addition to preview/draft/finalization/amendment/route
  isolation. Owned random fixtures and temporary credentials were cleaned up.
  Ended call remains a synthetic fixture; hosted End/media is not inferred.
- Production package/build and lint (existing warnings) passed; private asset
  scan found zero exact credentials. An intermediate compile failed on duplicate
  shared error-message keys; the keys were corrected before the passing build.
  No current Frappe 16/fresh-site/provider/device/native review pass is inferred.

Updated paired E11/E13 captures at 390/768/1440 are in the same evidence directory.
The checkbox now matches the reference interaction. Measured connected time is
still truthfully unavailable, and portraits/reference credentials/fees are not
fabricated. Clean presentation content, complete visual/localization/zoom states
and couples recipient workflows remain release gates. No visual acceptance claim.

## Release gates still open

- Full MVP reference/state/mobile/zoom/tour coverage. No required screen is marked
  visually accepted merely because it renders or its build passes.
- Separate clean/idempotent presentation dataset, respecting clinical catalog and
  human approval rules, without rewriting history or resetting balances.
- Registration-enabled real backend test transport/onboarding on a separate site;
  current preview intentionally remains invited-review. No fixed/public OTP bypass.
- Working two-adult couples appointment consent, participant authorization, three-
  person call and recipient-scoped notes. Relationship links alone are insufficient.
- Current hosted LiveKit media/Leave/rejoin/End and original/refreshed-token rejection;
  inherited evidence remains preserved, not reported as rerun here.
- Current scheduler-driven routing/earnings and legacy financial cutover, owner-level
  reconciliation, representative upgrade, fresh installation and repeat migrations.
  Shared worker 166351 and scheduler 166353 started 6 October and remain untouched.
  Their presence/site scheduler setting do not prove current-code job execution.
- Live SMS/email receipt, physical devices, native translations, clinical catalog/
  rubric/credential review and real-money activation remain separate external gates.

## Reviewer walkthrough

1. Open the URL above. Use privately stored patient credentials; Phone→Email→
   explicitly choose Password in this invited-review configuration.
2. Home→Find care→View profile popup→Full profile→View service→Choose a time.
   Select a real calendar slot, type fictional support text, preview disclosure,
   review actual funds. Back preserves input; confirming creates a real reservation.
3. My requests→guided private request; clinician Requests→eligible inbox→Make an
   offer. Patient review/accept creates one appointment; clinician More→Your offers→History→View offer→Open consultation details links it.
4. Clinician Today→Care records→Table/Cards→record, then Earnings. Current provider
   transfers are disabled; payout requests are demonstration reservations.
5. Reviewer Overview→Applications→Review; scope decisions remain separate. Tour
   targets now use the dedicated application queue. Do not infer record access.

## Acceptance-gate reconciliation — continuation from 7b866e8

`git diff d720596 HEAD -- . ':!docs'` is empty at the starting checkpoint:
only documentation/screenshots differ. No runtime rebuild was required then.

| Earlier gate | Current classification | Precise boundary / evidence |
| --- | --- | --- |
| Registration browsers | Still open | Existing controlled backend patient/clinician registration journeys passed at bounded 8028; returning-phone, expired-code/resend and complete abuse fixtures are not yet a release pass. Invited password access passes on current preview |
| Practical presentation data | Closed for idempotent setup; populated-state coverage open | Actual fictional presentation seed + manual reviewer approvals and retained bookings/notes/earnings; repeat setup preserves balances. Not all required populated/empty screen states compared |
| Individual consultation | Closed for tested paths | Hosted fake-device browser and focused tests in the current correction section; physical devices, automatic SDK refresh and total network handover remain external/unverified |
| Fresh installation | Previous v1.32 evidence retained; next schema gate open | Fresh/repeat install report above is valid for its source, not proof of a future couples schema |
| Legacy financial reconciliation | Still open | Preserved mismatches/holds and focused completion/refund import tests pass; full representative boundary/per-owner/repeat/cutover acceptance still required |
| Couples | Still open | Required two-adult appointment/consent/three-person calls/recipient documentation missing at this baseline; new implementation contract in mvp-release-scope.md |
| Continuous scheduler | Still open | Prior forced native job/RQ execution is not scheduler-daemon acceptance. No dedicated presentation scheduler active at baseline |
| MVP visual fidelity | Still open | Existing single matrix retains each required screen's independent functional/visual status and explicit material differences |
| Physical devices / native languages | External/manual pending | Fake browser devices and layout checks cannot prove these |
| Provider/clinical activation | External pending | Live SMS/SMTP receipt, medical-lead catalog/rubric, credentials, clinical/legal approval and real payments remain separate; no credentials requested in chat |

### Couples implementation checkpoint (in progress, 2026-10-10)

- `fa3de4e` adds v1.33 consent/participant/recipient storage. Three real MariaDB tests on `tele-tena-pr12-fresh.localhost` pass: separately snapshotted consent, one reservation/completion earning and recipient omission; pre-start withdrawal with exactly one release; post-start withdrawal with provider failure/retry and no automatic earnings/refund. Provider calls are mocked in these tests; they are not hosted media evidence.
- Three focused existing private-note/closure/finalization regressions pass after these changes. TypeScript/Vite build passes; lint exits zero with existing warnings.
- Presentation site backed up with database/config/public/private files as `20261010_144217-*` before applying additive v1.33; migration passed. Original development and remote sites were not migrated.
- N02–N05 invitation/consent/payment screens, N06 three-party media and N07 selected recipients are implementation in progress. Actual browser, paired visual, current fresh-install and continuous scheduler gates remain open. Do not describe couples as verified from these API tests.

## Couples and continuous processing — 2026-10-10

This section supersedes the baseline classifications above for the specific
couples and continuous-processing paths tested. Other gates remain open.

- Actual PR44 remains draft and based on PR43's branch. New focused commits:
  `fa3de4e` consent/recipient schema and authorization; `79b2100` connected UI;
  `c84640d` shared-stage layout/consent-safe limitations; `9d148b5` native
  processing harness; `dd0785c` grid sizing/camera-off surfaces; `22373e4`
  matching-state browser capture. No merge or remote deployment.
- Built preview is `http://127.0.0.1:8017/teletena/`, site
  `teletena-mvp-presentation.localhost`, original bench source path. Gunicorn
  master 453370 is the only web process reloaded. Production packaged assets,
  no Vite. Source/build originally d720596 versus 7b866e8 differed only in docs;
  subsequent runtime changes have been rebuilt explicitly.
- At full source `9d148b5b3b15da1cfc43217be222fcfe5e9b9a4c`, the real hosted
  LiveKit browser run passed independent adult consent, one reservation,
  three participants receiving two advancing remote video tracks and audio,
  partner Leave/rejoin, clinician End, and direct SDK rejection of still-valid
  original and application-reissued tokens for all three identities. The
  partner left before End. Opaque subjects, no names/metadata in JWTs. Explicit
  selected-recipient finalization omitted private notes from both patient APIs,
  omitted the summary from the non-recipient, and created one pending earning.
  Automated fake devices; not physical devices or automatic SDK-refresh proof.
- Three couples MariaDB tests rerun: pass (7.226 seconds). Two additional tests
  pass (2.094 seconds): simultaneous confirmation returns the same appointment
  with one reservation; shared extensions refuse without both adults' renewed
  consent. Existing individual extension rules remain intact.
- Paired N06 390/768/1440 screenshots:
  `docs/screenshots/couples-current/9d148b5/`. Actual 1440 pair inspected;
  uneven video-driven grid sizing and missing camera-off identity surfaces
  prompted the next focused correction. These images are evidence, not owner
  visual acceptance. Consent/payment/notes couples comparisons remain open.
- Native scheduler and RQ worker run in `/home/frappe/teletena-mvp-runtime`,
  one real site directory, separate loopback queue Redis 13917, subscribed
  short/default/long. Shared bench sees presentation disable_scheduler=1;
  isolated config sees 0. Native System Settings scheduler enabled. This avoids
  Frappe's long-running cached Redis connection crossing the site queue cutover.
  Read-only original queue inspection found zero presentation jobs across queued,
  running, deferred and scheduled registries; unrelated processes/queues untouched.
- `verify_continuous_processing.py` passed: native scheduler automatically
  enqueued earnings release, worker completed it, one release posting, other
  earning remained Disputed without a release posting. Only two new owned
  synthetic bookings snapshot a one-minute policy; original site policy and
  server clock unchanged. Media/provider mocked during finance fixture setup,
  not presented as a consultation test.
- `verify_worker_recovery.py` passed: stopped only dedicated worker, scheduler
  accumulated site-bound jobs, worker restart processed invitation expiry
  automatically. Schedule restored through API; no booked instants/balances
  changed. Private fixture markers retained, no purge or manual release.
- Current fresh v1.33 installation is pending administrative database-scoped
  access. Existing retained-site additive migration and repeated couples patch
  pass. Four focused legacy/payout tests pass, including exact opening-boundary
  events held for review and preserved original records; this is not yet the
  full representative pre-v1.7 owner-by-owner upgrade acceptance.
- Still open: complete registration returning/expired/resend browsers; remaining
  MVP paired visual/state comparisons; fresh schema and full legacy cutover
  acceptance; final integrated candidate checks. External: physical devices,
  native translations, live SMS/SMTP receipt, clinical/provider activation.
  The MVP is not handover-ready or visually accepted.

The `22373e4` follow-up full hosted couples browser also passed the connected
consent/media/End/reissued-token/documentation chain. Camera-off paired comparison
exposed an additional shared-state bug: a single muted video subscription could
replace the entire remote layout with the audio fallback. Follow-up aggregates
remote camera/microphone state and keeps shared tiles visible unless audio-only
is explicitly selected. Its final rendered verification is pending below;
this discrepancy is not hidden by the passing functional test.
