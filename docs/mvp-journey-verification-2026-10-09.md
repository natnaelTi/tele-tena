# Current MVP journey correction — 9 October 2026

**Active checkpoint; not visual acceptance or handover readiness.** This report
supersedes the runtime identity in older checkpoint reports. The screen matrix
keeps visual fidelity and functional journey acceptance independent.

## Source and preview

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

## Current account / appointment / native-worker checkpoint

This section is the current checkpoint; earlier per-commit findings below are
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
