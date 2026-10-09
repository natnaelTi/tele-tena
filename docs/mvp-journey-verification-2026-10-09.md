# Current MVP journey correction — 9 October 2026

**Active checkpoint; not visual acceptance or handover readiness.** This report
supersedes the runtime identity in older checkpoint reports. The screen matrix
keeps visual fidelity and functional journey acceptance independent.

## Source and preview

- Branch `feat/mvp-release-handover`, draft PR #44, dependent on draft PR #43.
  The preserved `1e8d161468eb8d3563f1b5743982722c749bbcbf` ancestor remains included.
- Packaged application source **`263becaa6b608c805539f487632992b58480b033`**.
  Subsequent evidence/documentation commits do not change its application code.
- **http://127.0.0.1:8017/teletena/**; site
  `tele-tena-pr12-fresh.localhost`; bench `/home/frappe/frappe/frappe-bench`.
- Gunicorn master 392014, two site-bound loopback workers; working directory
  `sites`; app checkout above. Targeted HUP reloaded only these web workers after
  backend fixes. Production packaged React, not Vite. `public/review/release.json`
  records the source and asset hashes. Preview HTTP 200 was checked.
- Reference `/home/frappe/teletena-design-reference`, rendered read-only on 8044.
  Actual 142-screen inventory and source remain authoritative.
- Existing data, credentials, historical records and source ancestry preserved.
  No migrations, balance repairs, fixture reseeding, merges or remote deployment.
  Intentional earlier browser deposits/bookings/requests/offers remain recorded.

## Implemented and verified slices

| Area | Implemented | Verification | Remaining |
|---|---|---|---|
| Home / discovery / preview / profile / service / booking | Search-led dashboard, real wallet, scoped cards and preview, tailored service page, generated monthly calendar | Real password sign-in, popup close/Escape/focus return, profile→service→calendar, selection/Back; actual booking and matching available/reserved delta | Full profile biography/verified expertise presentation, registration-enabled onboarding and coherent presentation dataset |
| Disclosure / price review | Server-produced preview; separate consultation/payment panels; actual available balance and shortfall; funding in new tab retains form; mobile paired facts | Live API preview, review totals, Back retains narrative/time; no mocked success | Explicit insufficient-funds browser recovery on this new review, manual-confirmation review presentation, C09 dedicated confirmation composition |
| Patient requests / private offers | Three-step composer, focus-managed reviews, persisted progress/offer workspace, state-driven icons; no three-minute no-offer message when a valid offer exists | Real retained scheduled request→tailored offer→accept→one appointment/reservation→detail/history handoff; concurrency/private-offer regressions | Immediate/routing-worker/reconnect/expiry full current browser acceptance and all reference states |
| Appointments / documentation | One dominant status, role-specific notes/summary explanation, no elapsed-time completion; cancellation and finalization dialogs | Pure grouping/status regressions and private-note/encounter backend regression | Full current call/End/documentation/feedback journey and all detail-screen visual comparisons |
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

## Checks actually run

- Actual MariaDB/Frappe `tests/presentation.py` methods (all passed):
  `test_public_profile_uses_tailored_offerings_and_rechecks_revoked_scope`,
  `test_request_inbox_selects_tailored_offerings_by_scope_not_label` (including
  Active/History and invalid-view assertions),
  `test_discovery_search_metadata_is_catalog_only`,
  `test_private_request_competing_offers_insufficient_funds_and_atomic_match`,
  `test_two_patients_cannot_claim_one_offer_slot_concurrently`,
  `test_care_records_do_not_link_different_patients_with_equal_names`,
  `test_04_notes_privacy_revision_completion_and_encounter_scope`.
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
four-stage rail and separate request narrative/facts panel, now recorded for correction.
The reference role-switching demonstration panel is deliberately not a patient control.

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
   offer. Patient review/accept creates one appointment; clinician History links it.
4. Clinician Today→Care records→Table/Cards→record, then Earnings. Current provider
   transfers are disabled; payout requests are demonstration reservations.
5. Reviewer Overview→Applications→Review; scope decisions remain separate. Tour
   targets now use the dedicated application queue. Do not infer record access.
