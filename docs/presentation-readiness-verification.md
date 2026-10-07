# Presentation release verification

## Latest local clinic/auth checkpoint — 2026-10-07

- Review URL: `http://127.0.0.1:8017/teletena/` (production-built Frappe app,
  not Vite). Bench `/home/frappe/frappe/frappe-bench`; site
  `tele-tena-pr12-fresh.localhost`; branch `feat/clinic-affiliation-review`;
  backend checkout and packaged source SHA
  `57c4a4842a1a26d1b6cd4e10b6701a8ace3d9324`.
- Environment: Frappe 15.121.2 / ERPNext 15.121.6, Python 3.12.3, Node
  22.23.3. The review WSGI process is Gunicorn on loopback 8017. This site is
  configured for invited password review; its public phone and registration
  flags remain off. Its synthetic account file is private under that site's
  `private` directory; credentials are intentionally omitted here.
- `tests/presentation.py`: 22/22 passed, including clinic registration and
  affiliation state, ownership, generic DocType permissions and no implied
  scope/record access.
- `tests/contact_auth.py`: 7/7 passed. These tests exercise enabled-registration
  OTP state using a mocked email provider and a test-only enabled policy; they
  did not change the invited site's configuration and did not send email.
- `tests/integration.py`: 24/24 passed against the same built Frappe preview.
  The run used a scoped, temporary setting change on this disposable site to
  exercise enabled phone/patient/clinician registration, restored the original
  site config in a `finally` cleanup, and reloaded only this isolated Gunicorn.
  SMS transport and OTP-key access were mocked in tests; no SMS was sent. The
  HTTP regressions used `http://127.0.0.1:8017`, not the obsolete Vite default
  on port 5173. After the run the preview is back in invited-review mode.
- `scripts/browser-clinic-registration.cjs`: passed a real browser journey
  through the built React package and Frappe APIs: applicant submission →
  reviewer verification → affiliation request → separate reviewer decision.
  Synthetic screenshots: `docs/screenshots/clinic-review/`.
- The earlier frontend build, lint and packaged review/auth/PWA checks passed
  at this source checkpoint. Existing lint warnings and large LiveKit bundle
  warning remain.
- The fresh schema path was synchronized on a disposable site that had been
  created before the final DocType directory correction. This is not claimed as
  a clean fresh-install test of the final package. Frappe 16 compatibility for
  the new clinic DocTypes, clinic/admin responsive visual review, actual
  browser zoom, live email/SMS, physical-device calling, and native language
  approval remain unverified.
- This checkpoint does not complete the 142-screen/product scope. The accurate
  per-screen status remains in `operational-screen-map.json`; clinics still
  lack staff membership, calendars/resources, billing and encounter grants.

## Current integrated local preview — 2026-10-05

- Review URL: `http://127.0.0.1:8017/teletena/` (built Frappe application,
  not Vite).
- Bench/site: `/home/frappe/teletena-compat/bench`,
  `tele-tena-pr2-test.localhost`.
- Source branch: `feat/vetting-catalog-routing`; latest frontend/product-code
  commit `4a78f483ff4915e7a9db2744ecc27a5abc73fe46`. The exact source SHA for
  this packaged React build is recorded in `tele_tena/public/review/release.json`.
  The documentation changes that follow this build do not change app assets or
  Python behavior.
- The current web process is the isolated compatibility WSGI/Gunicorn and serves
  the packaged React app, not Vite.
- Isolated `bench worker --queue default,short,long` and `bench schedule` are
  running against this compatibility bench's Redis queue database 15. The old
  Redis DB 0 queue and the original development bench processes were not
  processed or restarted. The intended review site has its scheduler enabled.
- A separate synthetic patient/clinician browser journey against the packaged
  `/teletena/` build published a scheduled request and showed it in the
  clinician's authenticated inbox. The packaged availability test saved and
  reloaded a schedule and booked a generated slot. The package guest/sign-in,
  deep-link/reload, sign-out, responsive consultation detail, PWA scope and
  offline checks also passed on this build.
- Immediate requests are configured for the legacy synthetic review service on
  this site only. The current wall clock was outside the sample clinician's
  weekly interval, so an actual immediate browser dispatch was not claimed;
  mocked-time Frappe regressions cover continuous start selection and policy
  enforcement. At this time the clinician shell reports no immediate capacity
  instead of implying ready status.
- A packaged two-session scheduled request journey on 2026-10-05 delivered one
  eligible request to the clinician, created a private offer, and accepted it
  into one appointment with one reservation journal. An intentionally
  out-of-schedule Wednesday request correctly received no recipient; the actual
  retained recurrence is Monday/Tuesday only. Full evidence and limitations are
  in `vetting-routing-verification.md`.
- Patient request history is keyboard-expandable and collapsed by default. The
  390px regression retained all 16 previous cards in that section and opened it
  with Enter. Screenshot: `/tmp/tele-tena-vetting-review/current/patient-request-history-mobile.png`.
- This does not validate live SMS, hosted LiveKit Cloud in this run, physical
  devices, native translation quality or Selfmade deployment.

Older snapshots below describe their dated branches and commits. They are
historical evidence, not the current preview source or release manifest.

## PR #12 local preview checkpoint (2026-10-03)

The correct review preview is `http://127.0.0.1:8017/teletena/` (availability:
`http://127.0.0.1:8017/teletena/clinician/availability`). It is served by
`/home/frappe/teletena-compat/bench`, site
`tele-tena-pr2-test.localhost`, branch `feat/next-design-update`; the running Gunicorn backend loaded product
code at `3d806d03bb5a25fcb2bad7ecce3f154d3147f85f`. Current PR head
`ac7f827995053e8b5605d2896c3712907c25c8d7` adds only screenshots, docs and the
focused browser regression. The built asset manifest reports the product-code
SHA `3d806d03bb5a25fcb2bad7ecce3f154d3147f85f`. Gunicorn runs
from this bench's Python 3.14.2 environment and loads its `./apps/tele_tena`
checkout. This is the production React build behind Frappe's `/teletena/` route,
not Vite. The old Vite process at `127.0.0.1:5173` loads
`/home/frappe/frappe/frappe-bench/apps/tele_tena/frontend` and belongs to the
original development bench; it is not the preview URL to use. Its backend is
the separate original bench on port 8000. Neither original-bench process, site
nor data was changed. Use the synthetic approved clinician account for
availability and synthetic patient account for booking; credentials remain in
the site's mode-600 local review-account file and are not recorded here.

Availability was exercised through the built `/teletena/` route. The approved
synthetic clinician opened the calendar, an end-before-start interval showed a
field-level error and retained its value, a valid weekly schedule saved with
HTTP 200, survived reload, and generated a patient-bookable slot. The regression
also followed the opaque patient booking link through sign-in and booking. A
new synthetic patient with ETB 1,000 was created for this run, so previous test
spending did not alter existing balances. The server route returned
`Cache-Control: no-store, private`.

Rerun evidence on 2026-10-03: production-built availability save/request/reload/
booking and booking-link navigation **passed**. Invalid end-before-start input
showed a field-specific error and remained editable. The browser harness now
waits for the sign-out response before following the patient link, removing a
race that could keep the clinician session active. Built-package guest redirect,
password session, consultation deep-link/reload, sign-out, PWA scope, sensitive-
cache exclusion and offline-state checks **passed**; invited-review auth policy
**passed**. Twenty routes rendered at 320, 390, 720, 768 and 1440 CSS px with no
page-level horizontal overflow. The invited-review email/password entry and the
enabled phone-entry screen were both captured; patient and clinician onboarding
step one was captured at 320/390/768/1440 after creating and cleaning up a
short-lived synthetic verified-contact account. 720 px is a narrow-layout proxy for 200% zoom on
a 1440 px display, not an actual browser-zoom test. Asset hash/scope/privacy scan
**passed**. The latest bundled source SHA is `3d806d03bb5a25fcb2bad7ecce3f154d3147f85f`; the earlier route sweep bundles were `0fce298eedaa4ad93243d3f24086f023e068c1d3` and `df845b5b7936a3b696e40c1856f4e48f6148bf75`.
Presentation regressions passed 14 cases; lint passed with existing warnings.

The first integration rerun stopped on a fixture mismatch: it used the
invited-review site, where phone OTP and public registration are disabled, and
an HTTP fixture targeting Vite. This is not a code pass or an app regression.
An enabled-registration fixture still needs its own browser/API run. A fresh
v1.8 installation passed schema/role/patch-log/guest-denial checks earlier, but
its combined browser run stopped on an obsolete root-manifest assertion. That
assertion is fixed and the browser package passed against the retained site; a
fresh install plus full browser suite has not yet been repeated. The temporary
database-admin credential is currently absent, so a new disposable install
needs the operator setup step. The hosted LiveKit regression **passed against the development LiveKit Cloud
project** after its mode-600 private configuration was copied only to this
isolated site and removed in cleanup. Two independent Chromium contexts
exchanged fake-device audio/video, Leave/rejoin passed, End closed the room,
and Cloud rejected original/refreshed cached tokens for both identities,
including a participant who left before End. This is automated fake-media
evidence, not physical-device testing.

The retained compatibility site ran v1.8 reconciliation: 15 post-opening
legacy rows (10 deposits and five reservations) were imported into balanced
journals without rewriting legacy events, appointments, reservations or wallet
projections. A read-only audit now finds the Review Patient wallet at 120,000
available / 480,000 reserved minor units (ETB 1,200 / ETB 4,800), exactly equal
to journal projections; current difference is zero. The earlier mismatch was
60,000 / 540,000 in the legacy wallet versus opening journals of 260,000 /
240,000. The 15 missing post-opening rows explain it and v1.8 imported them
once. This does not identify which process originally wrote the legacy rows.
The cutover guide requires stopping every old writer before new code is active.

Current route screenshots are under
`docs/screenshots/next-design-update/current-review/`: 20 public and authenticated
patient, clinician and reviewer routes at 320/390/720/768/1440 px. The audit
found patient booking overflow to 984–992 px at 320/390/768; `.booking-layout`
and its children now shrink, and the production route test plus repeated sweep
show no page-level overflow. Short booking blocks display the permitted alias
without clipped secondary text and retain a full accessible name. Visual acceptance remains incomplete: OTP entry/resend, later clinician onboarding and
pending/rejected application states, open tours, Amharic/Afaan Oromo rendering,
actual 200% browser zoom and several empty/error states still need visual review.
Current production-build screenshots now cover video call (390/1440), audio-only,
clinician end-of-call notes, and completed consultation detail for both roles
(320/390/768/1440), using fake media and synthetic records. Inspection found a
remaining clinician detail mismatch: the page can show “Call ended” while its
appropriate appointment-state field still says “Booked”; lifecycle status
presentation needs a focused fix and regression before visual acceptance.

## Update for `feat/next-design-update` (2026-10-02)

This section supersedes the earlier PR #7 snapshot where it conflicts with the
v1.7 earnings work or the availability follow-up. It records checks actually
run against the current feature branch on the isolated Frappe 16.2.1 / ERPNext
16.1.0 bench. The site and browser accounts are synthetic. Nothing was deployed
to Selfmade.

| Requirement | Current branch status | Evidence and remaining work |
|---|---|---|
| 1. Availability and patient booking | Implemented; focused browser verification passed | Production-built `/teletena/` clinician schedule save, request values, reload persistence, then a patient booking passed on 2026-10-02. Calendar edit/copy/date-only exception interaction passed. `tests/presentation.py` passed 12 cases for recurrence, DST, exceptions, conflicts, timezone snapshots and invalid-save atomicity. Rendered/inspected at 390, 768 and 1440 px. See [availability hotfix](availability-save-hotfix.md). |
| 2. Appointment, call and documentation states | Implemented in API; presentation partially updated | 12 presentation and 18 selected integration regressions passed, covering explicit completion, exact-once reservations/releases and call lifecycle authorization. Appointment grouping and status copy changed on this branch. Full status-state screenshot matrix was not rerun. |
| 3. Post-consultation notes | Implemented in the merged baseline; regression subset passed | The 12 presentation tests include private/shared note access and revisions; the 18 integration tests exercise consultation authorization. This branch did not change note persistence or privacy APIs. No new note-screen screenshot was captured here. |
| 4. Consultation room | Intentionally unchanged | LiveKit media, Leave/rejoin and Cloud token revocation were verified in the prior hosted report with two fake-media browser contexts. The hosted Cloud run was not repeated on this branch; physical-device testing remains outstanding. |
| 5. Consultation details | Partial presentation refinement | Changed dominant status and patient/clinician action wording. Backend snapshot and private-note access regressions passed. The full status-specific detail screenshot matrix was not rerun. |
| 6. Product copy | Partial | Account, activity and payment labels were refined; the add-funds success copy now says “balance.” Some flows still contain repeated demo implementation language and newer copy is not consistently translated. |
| 7. Care directory and patient record | Intentionally unchanged | Encounter authorization and privacy tests were part of the 12 presentation cases. No current-branch visual browser pass was run for this route. |
| 8. Account and wallet summaries | Partial | Removed repeated wallet/help/notification placeholder cards from account tabs and limited the patient wallet summary to the account overview. No current-branch browser screenshot pass was run. |
| 9. Admin review | Partial | Existing application review remains; financial activity now uses readable event labels and does not expose appointment IDs in dispute cards. Full current-branch admin browser verification was not run. |
| 10. Private resume evidence | Intentionally unchanged | Private evidence authorization is covered by existing presentation tests. No upload/download visual or fresh-install test was repeated on this branch. |
| 11. Mobile/PWA | Partial | `tests/service_worker.mjs` passed for both development and packaged modes. Calendar screenshots at 390/768/1440 have no horizontal page overflow. Other routes, 320 px and 200% zoom were not rerun. |
| 12. Role tours | Partial | Invitation is now a compact single row and is hidden while the replay entry is available, reducing duplicated prompts. No post-change visual/accessibility browser pass was run. |
| Earnings and payout lifecycle | Implemented as demonstration behavior; not real-money readiness | `tests/presentation.py` passed exact arithmetic, fee/window snapshot, dispute/release ordering and concurrent payout regressions. `tt_journal` is a balanced simulated subledger separate from `tt_ledger`; no ERPNext posting or real settlement. |

### Current-branch checks

- `frontend`: `npm run build` passed. Vite reports the LiveKit SDK chunk is
  above 500 kB.
- `frontend`: `npm run lint` exited successfully with React hook, Fast Refresh
  and render-purity warnings; no lint errors.
- `env/bin/python -m compileall -q tele_tena tests scripts` passed.
- `node tests/service_worker.mjs` passed for packaged and development worker
  scope and sensitive-endpoint exclusions.
- `tests/presentation.py` — **12 passed** against the existing disposable site.
  The test-process `frappe.enqueue` was a no-op because the local Redis queue
  was already overloaded; no application code or worker configuration changed.
- `tests/integration.py` selected cases 01–17 — **18 passed**, including
  permission/scope, privacy, idempotency, transactional rollback, concurrent
  booking/overspend, LiveKit authorization and end/join serialization. This
  was not the full suite: legacy phone-auth cases were excluded because this
  site deliberately disables them.
- `scripts/check_migration.py` — passed twice through the migration path and
  verified exact snapshots of old records, nine numbered patches, presentation
  and financial tables, journals, journal lines and payout/earning/dispute
  rows. This establishes repeat-migration preservation of the current records,
  including the mismatch described below; it does not establish that the seeded
  wallet projection reconciles.
- `scripts/browser-availability-regression.cjs` passed on the production-built
  Frappe route using a new synthetic patient with a fresh balanced demo wallet.
- `scripts/browser-availability-calendar.cjs` passed date-only edit and
  accessible field focus/copy interactions on the production-built route.
- `scripts/check_redesign_browser.py` was attempted as a wider browser sweep but
  stopped during synthetic fixture setup, before Chromium launch: its applicant
  onboarding fixture called the registration endpoint while the site correctly
  had public registration disabled. No registration setting was changed and no
  browser result is claimed from that attempt.
- `scripts/build_review.py` passed and produced the packaged Frappe assets; the
  exact source SHA is in the generated `release.json`. The packaged artifact
  hash/scope/privacy check passed. PR #12's eight frontend/Python CI jobs passed.
- `git diff --check` passed.
- Before the v1.8 reconciliation, the seeded synthetic account had 60,000
  available / 540,000 reserved in `tt_wallet`, versus 260,000 / 240,000 in its
  v1.7 opening journals. The append-only log showed 10 post-opening deposits
  totalling 100,000 and five reservations totalling 300,000 with no matching
  journals. The records do not identify which process wrote those entries.
  The new versioned v1.8 patch imported those 15 known events into balanced,
  idempotent journals. Wallets, legacy event rows and appointments were left
  unchanged. The mismatch count is now zero.
- `scripts/check_financial_migration.py` passed after reconciliation and on a
  second migration, preserving wallet balances, the legacy log, earning rows
  and balanced journals. `tests/presentation.py` now passes 13 cases, including
  a savepoint-isolated post-snapshot legacy-event reconciliation/idempotency
  case. The migration refuses unknown legacy event kinds.
- A fresh install of v1.7/v1.8 has not yet run: the existing compatibility site
  contains synthetic records that must be retained. A separate site named
  `tele-tena-pr12-fresh.localhost` and its narrowly scoped temporary DB admin
  are prepared in `scripts/prepare_fresh_install_db_admin.py`; operator setup
  is still required before that one-time check. The existing preview site is
  not dropped or reseeded.
- The hosted LiveKit Cloud revocation browser regression, the fresh v1.7/v1.8
  site installation, configuration-matched invited/enabled-registration
  browser suites, complete contact-auth suite and all-route visual review are
  still outstanding for the current source head. Hosted SMS delivery and
  physical-device results remain unverified.

### Current screenshot evidence

Rendered from the built React bundle served at `/teletena/`, synthetic clinician
account, on 2026-10-02; screenshots were visually inspected:

- [Availability, 390 px](screenshots/next-design-update/availability-390.png)
- [Availability, 1440 px](screenshots/next-design-update/availability-1440.png)
- [Date-specific exception editor, 1440 px](screenshots/next-design-update/date-exception-edit-1440.png)

The 768 px screenshot was rendered and its `scrollWidth` equaled its viewport
width, but it was not retained. At 390 and 768 px the agenda view is used; at
1440 px the week grid is shown. The screenshot still includes a synthetic
appointment and the demonstration ribbon. It is not evidence of a phone/device
test or a complete visual acceptance pass.

### Availability root cause and exact target state

The previously reported save failure is a frontend/API payload mismatch, not a
timezone or service-scope failure. The production-built editor sends
`start_local` and `end_local`, while the original validator read `start` and
`end`; the API therefore rejected populated time fields as missing. The focused
compatibility mapping is in PR #11 and is also present in this feature branch.
Current browser verification confirms save, reload, booking and visible date
exception editing. Invalid interval saves fail before partial writes and remain
covered by the presentation API regression.

Selfmade was last operator-reported with app checkout SHA
`8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6`; an earlier report named installed
release SHA `bba5ed9f15bd0b140967618ed2bd982c31a76c1b`. These observations differ
and no new remote check was performed. Do not prepare a deployment command from
either value until the operator confirms the active installed commit. This
branch and PR are not deployed.

## Earlier PR #7 verification snapshot

Verification run on `feat/presentation-ready-release`, based on merged main
`7222836` (PR #6); review PR: [#7](https://github.com/natnaelTi/tele-tena/pull/7).
Screenshots use synthetic fixtures and are stored outside Git
at `/tmp/tele-tena-presentation-review/`. Automated fake-media is identified
separately from human/device testing.

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| 1. Recurring availability and patient booking | implemented | IANA-zone weekly schedules, multiple intervals, copy-day editor, date overrides/breaks, notice/horizon/buffers, server-generated slots and global clinician/patient conflict checks. `tests/presentation.py` covers recurrence, DST, exceptions, conflicts and timezone snapshots; integration covers atomic booking/balance/idempotency. `check_redesign_browser.py` completes a real persisted discovery → slot → disclosure → confirm flow. Availability/calendar screenshots are in the directory above at 320/390/768/1440. |
| 2. Appointment, call and documentation states | implemented | State projection remains separate from persisted transitions; manual holds expire and decline/cancel releases exactly once; completion requires clinician finalization after End. Covered by presentation and integration regressions. Demonstration cancellation is full release before start under the immutable `demo-full-release-before-start-v1` policy. |
| 3. Post-consultation notes | implemented | Private clinician note and patient summary are separately stored and revisioned; patient API omits private text; previews do not publish; finalization is explicit; same-clinician follow-up uses normal availability. API regressions and hosted browser test cover draft, preview, finalization and patient-visible summary. Screenshot: `end-of-call-notes-*`, `completed-consultation-clinician-*`, `completed-consultation-patient-*`. |
| 4. Consultation room | implemented | Focused route uses the locale dictionary, responsive video/audio-only layouts, media activity from the existing remote track, and existing cleanup/authorization controls. Hosted LiveKit Cloud test passed with two independent Chromium contexts and fake microphone/camera: media exchange, Leave/rejoin, clinician End, then Cloud rejection of original and refreshed cached tokens for both participant identities, including the participant who left before End. Screenshots: `call-preflight-screen-*`, `video-call-*`, `audio-only-*`. |
| 5. Status-aware consultation details | implemented | Patient/clinician details expose the accepted disclosure snapshot, scheduled timezone, booked duration, price/reservation and timeline; call timing is explicitly unavailable where not recorded. Ended sessions show notes action; patients see published revisions only. Browser captures include detail and both completed views. |
| 6. Professional product copy | implemented | A single accessible persistent ribbon says “Demonstration environment — no real payments or clinical care.” User-facing totals say “Balance” and “Payments”; feature gaps remain clear. Internal transaction records remain simulation-only. |
| 7. Clinician care directory | implemented | Search, service/status/date filters, table/card display and pagination use encounter-scoped API results. Only encounters for the same treating clinician with the exact same explicitly shared alias are grouped; masked encounters remain separate and no account identifiers are returned. Direct API/privacy regressions and `clinician-care-*` screenshots. |
| 8. Account and wallet summaries | implemented | Focused profile, contact, language/timezone, privacy, practice/resume and payments sections use persisted preferences and available/reserved wallet values. There are no fabricated clinician earnings. Notification preferences and contact changes are identified as unavailable. Screenshots: account/privacy and payments. |
| 9. Admin approval usability | implemented | Queue shows professional name, status, submission date, requested service labels, evidence completeness and authenticated resume action. Reviewer flow does not grant care-record access. Browser evidence uses a newly submitted synthetic applicant; only that fixture is returned to the screenshot session. |
| 10. Private resume evidence | implemented | Server validates PDF extension, size (5 MiB) and PDF signature/ending; evidence stays in private DB storage and authenticated download is restricted to owner/reviewer. Upload, replace/remove-before-submit, ownership and reviewer permission regressions pass. Fresh install includes v1.6 tables. |
| 11. Mobile and PWA | implemented | Manifest, local app/maskable icons, HTTPS-compatible install guidance and generic offline state are present. Browser check activated the service worker and reached the offline page with network disabled. `tests/service_worker.mjs` confirms authenticated APIs, Authorization requests and private paths are excluded from cache. Responsive journeys include 320/390/768/1440 and a 200%-equivalent narrow layout check. |
| 12. Role-specific walkthroughs | implemented | Persisted by account/role/tour version; patient, clinician, applicant and reviewer steps are permission-aware, replayable, dismissible, non-mutating and localized in English, Amharic and Afaan Oromo (provisional). Browser verifies patient route transitions, Back, dismissal persistence, replay, missing-target recovery and captures patient/clinician/reviewer tours. Screenshots: `tour-patient-*`, `tour-clinician-*`, `tour-administrator-*`. |

## Checks run

- `./env/bin/python apps/tele_tena/tests/integration.py` — **24 passed**. Includes OTP/scope approval, privacy defaults/booking overrides, idempotent replay, rollback, concurrent booking/overspend/repeated submission, token authorization, and Cloud close cutoffs.
- `./env/bin/python apps/tele_tena/tests/presentation.py` — **5 passed**. Includes recurrence/DST/exceptions, manual holds and exact-once release, global conflicts/timezone snapshots, private notes/revisions/care scopes, resume permissions and tour persistence.
- `./env/bin/python apps/tele_tena/tests/contact_auth.py` — **7 passed**.
- `node apps/tele_tena/tests/service_worker.mjs` — **passed**; public static/offline caching only.
- `./env/bin/python apps/tele_tena/scripts/check_migration.py` — **passed**; repeat migration preserved the exact pre-existing development records and DocType scope records.
- `./env/bin/python apps/tele_tena/scripts/check_fresh_install.py` — **passed** on disposable `tele-tena-pr2-test.localhost`, installing Frappe, ERPNext and TeleTena and verifying all eight patch-log entries, native DocTypes, new presentation tables/columns, guest denial and disabled simulation. The retained development-site record fingerprint matched. Cleanup **passed**: disposable site/database/site user, temporary admin, mode-600 credential file and mode-600 install log removed; temporary admin authentication was denied afterward.
- `./env/bin/python apps/tele_tena/scripts/check_redesign_browser.py` — **passed**; persisted synthetic patient onboarding, discovery and booking; clinician/admin workspaces; privacy defaults, payments, tours, service-worker install/offline behavior, keyboard dialog, Ethiopian-script showcase and no horizontal overflow at 320/390/768/1440. No SMS or email was sent.
- `./env/bin/python apps/tele_tena/scripts/check_hosted_livekit_revocation.py` — **passed against the configured LiveKit Cloud project**. Two independent Chromium sessions used automated fake microphone/camera media; this is not human or physical-device validation.
- `./env/bin/python -m compileall -q apps/tele_tena/tele_tena apps/tele_tena/tests apps/tele_tena/scripts` — **passed**.
- `cd frontend && npm run build` — **passed**. Vite reports the LiveKit SDK chunk exceeds 500 kB.
- `cd frontend && npm run lint` — **passed with warnings** for React Fast Refresh, effect dependencies/state-in-effect and render purity; no lint errors.
- `git diff --check` — **passed**.

## Screenshot locations

All names below are PNGs in `/tmp/tele-tena-presentation-review/`:

- `availability-editor-{320,390,768,1440}.png`, `booking-preview-{320,390,768,1440}.png`
- `appointments-{320,390,768,1440}.png`, `consultation-detail-*`, `call-preflight-screen-*`
- `end-of-call-notes-*`, `completed-consultation-clinician-*`, `completed-consultation-patient-*`
- `video-call-{width}-{patient,clinician}.png`, `audio-only-{320,390,768,1440}.png`
- `clinician-care-*`, `care-record-*`, `payments-*`, `administrator-review-*`
- `tour-patient-*`, `tour-clinician-*`, `tour-administrator-*`, `offline-state-390.png`
- `homepage-*`, `phone-entry-*`, `code-entry-*`, `email-alternative-*`, onboarding, profile and language showcase captures.

## Remaining limits

- No human participant or physical iOS/Android device test was performed. Hosted media verification used fake devices; it proves Cloud token revocation and browser media-track exchange, not room quality, clinical suitability or mobile background continuity.
- SMS and SMTP providers were not live-tested; phone possession OTP does not verify adult age or clinician credentials. Amharic/Afaan Oromo strings remain provisional pending human review.
- Real payments and external withdrawal settlement remain disabled. Balanced demonstration subledger postings, clinician earnings, dispute holds and payout reservations are implemented and tested; ERPNext posting remains unimplemented. Ratings, rescheduling, no-show actions, couples participation, clinic workspaces, natural-language matching and private requests/offers remain unimplemented per the tracker. Cancellation/release rules are demonstration policy only.
- Account notifications and contact-change settings are not implemented. Existing appointments without reliable media timing report it unavailable. The PWA installation checklist has not been validated on physical devices/HTTPS hosting.
- This branch is not production clinical readiness. Do not activate real payment or credential-verification claims.

## Presenter walkthrough

1. Open `http://127.0.0.1:8017/teletena/` on the compatibility bench and sign in with a synthetic patient account in invited-review email/password mode. The separate original Vite preview at port 5173 is not this release. Add demonstration funds from **Payments**.
2. Choose **Find care**, select an approved service, pick one of the returned dates/times in the displayed timezone, review **What you’ll share**, then confirm. Open **Appointments → View consultation** to review the exact snapshot and reservation.
3. In a separate browser session, sign in as an approved synthetic clinician. Show **Today** and the weekly **Availability** editor; edit intervals or a date exception, save and publish. Show that an already booked appointment remains unchanged.
4. For a scheduled synthetic consultation, use the explicit pre-call check and Join in both sessions. Show video, mute/camera/audio-only controls, Leave/rejoin, and the clinician’s **End for everyone** confirmation. Hosted End was separately verified in automation.
5. Open the ended consultation as clinician, save a private draft, preview the patient summary, and explicitly finalize. Sign in as the patient to show only the published summary and follow-up booking link.
6. In the reviewer workspace, inspect the synthetic pending application and private resume, then review the separate service-scope decision. Tours can be replayed with **Help & tours**; no tour submits a mutation.

Do not present the fake-media screenshots as physical-device evidence, and do not
describe the simulation transaction log as accounting or a real payment.


### Current consultation visuals (2026-10-03)

From the running built app at `http://127.0.0.1:8017/teletena/`, the hosted
LiveKit browser regression captured video call at 390 and 1440 px, and
audio-only, clinician end-of-call notes, and completed details for clinician and
patient at 320/390/768/1440 px. The test exchanges fake audio/video between two
independent browser contexts; this is not physical-device evidence. Example
files: `current-review/video-call-390-patient.png`,
`current-review/audio-only-390.png`,
`current-review/end-of-call-notes-1440.png`, and
`current-review/completed-consultation-patient-390.png`. The earlier clinician-notes capture showed “Booked” alongside “Call ended”. A focused UI regression now mocks a synthetic booked appointment with an ended call, verifies the visible “Completion pending” state, and captures 390/1440 px; the stored appointment and accounting state remain unchanged.


The local preview was restarted after its isolated MariaDB service had stopped.
Compatibility MariaDB now uses its separate socket/data directory, and the
loopback web process serves the built Frappe route without starting compatibility
workers. Current package/deep-link and availability save/reload/book browser
checks pass against that same URL. No old worker is writing to the v1.8 site.


## Local authentication repair (2026-10-03)

The invited-review site reports SMS OTP, email OTP and public registration
disabled. The sign-in UI now remains phone-first and clearly marks phone-code
access unavailable on this site; the user can choose email/password. When site
capabilities report OTP delivery available, SMS remains the first route, email
OTP is available as the alternative, and password is an explicit email option.
No provider or site authentication setting was enabled for this check.

The local protected review credential file and active User records were checked
without printing credentials. Patient and clinician password sign-in both passed
through the built browser UI. A wrong-password browser case now shows a
non-enumerating email/password message. UI-only mocked capabilities exercised
phone OTP -> email OTP -> password choice and an invalid/expired-code message;
no SMS/email was sent and this does not verify delivery.

`Sign in` and fallback states were rendered and visually inspected at 390 and
1440 px. Captures are `current-review/sign-in-invited-phone-390.png`,
`sign-in-invited-phone-1440.png`, `sign-in-invited-email-password-390.png` and
`sign-in-invited-email-password-1440.png`. These show the invited-site fallback,
not the hosted SMS-enabled configuration.

Checks: `npm run build`, `npm run lint` (existing warnings),
`python3 scripts/build_review.py`, `python3 scripts/check_review_assets.py`, and
`node scripts/browser-authentication-flow.cjs` all passed. Packaged frontend
source SHA: `c9f098814e7aab9e3ab5df7a19a760da6148b33b`.

## Historical continuation checkpoint — local open-request integration (2026-10-04)

This records the state on 2026-10-04 and is superseded by the 2026-10-05 local continuation above and in `vetting-routing-verification.md`. The integrated local branch at that time was `feat/open-requests`, based on the PR #12 draft head. The request/offer code remains unmerged and has not been deployed to Selfmade.

- Compatibility site: `tele-tena-pr2-test.localhost` on the isolated Frappe 16 bench at `/home/frappe/teletena-compat/bench`; original development bench and Selfmade were not changed.
- `bench migrate --site tele-tena-pr2-test.localhost --skip-search-index` passed, including `v1_10_request_public_identity`. The migration adds an opaque profile ID and timezone snapshot column; no reseed/reset was run.
- `tests/presentation.py`: **15 tests passed** on Frappe 16. This includes the persisted private competing-offer scenario, other-patient denial, clinician-to-clinician offer privacy, insufficient-funds then fund/retry acceptance, one appointment/reservation, repeat acceptance, immediate publication retry idempotency, and clinician discovery/profile email exclusion. The local harness replaces `frappe.enqueue` with a no-op because the isolated bench has no compatible request worker; database commands and transaction paths still execute. Thus this does not verify scheduler expiry or queued dispatch.
- `frontend && npm run build`: **passed** with Vite 8.3.1; the existing LiveKit chunk-size advisory remains. This is a frontend compile/build result only; built-asset deployment and browser request journey have not yet been rerun for this continuation source.
- Patient open requests poll the authenticated owner-scoped API for reconnect; provider realtime notifications are not implemented. Request/offer expiry is enforced at endpoints and by a one-minute scheduler hook, but the compatibility site's scheduler/worker path is not currently running.
- Translation strings for several request labels were added to the existing Amharic and Afaan Oromo dictionary and integrated into the patient composer and clinician page title/actions. Most request copy remains English; translation coverage and native-language review are incomplete.
- Open-request code captures anonymous outcome timestamps, including participant joins through the signed LiveKit webhook. No hosted webhook delivery assertion was rerun during this continuation.

Remaining release gaps include a production-built, two-browser request-to-offer acceptance flow on this same preview; a concurrent two-patient claim of one clinician slot; scheduler-driven expiry/dispatch execution; seeded populated earnings screenshot flow; full inventory screenshots and route-by-route visual checks at 320/390/768/1440 px and actual 200% zoom; enabled-registration backend test on its separate policy fixture; fresh v1.10 installation and representative migration reconciliation; and current hosted LiveKit End/token revocation rerun. Live SMS receipt, native translation sign-off and physical-device calling remain external validation gaps. Keep PR #12 and the dependent request change draft until these substantive acceptance gaps are closed.

### Request/offer continuation evidence and current preview source (2026-10-04)

The current source branch is `feat/open-requests`; the final source SHA is the value in `tele_tena/public/review/release.json` after the final clean rebuild. The previous clean package was built from `8eb632038f7b6e6c65c4a4688c8ce7af19ce3104`; it included the policy-aware sign-in change and predates the later browser-test timing correction. The final clean package rebuild follows the current report commit.

The built `/teletena/` preview was restarted with `TELE_TENA_TEST_SITE=tele-tena-pr2-test.localhost` and is running at `http://127.0.0.1:8017/teletena/`. It serves the isolated Frappe 16 compatibility checkout, not Vite. The invited-review policy remains configured: phone OTP and both registration paths are disabled, with email/password reviewer access available. The browser now waits for site policy before rendering the default auth method; both `browser-invited-review.cjs` and `browser-review-package.cjs` passed after this fix. The latter covered guest deep-link redirect, password sign-in, protected detail reload, sign-out, responsive detail capture, `/teletena/` PWA scope, static-only cache and offline page.

A two-context Playwright session against this same built preview exercised the request flow with the stored synthetic review accounts: clinician care-language setup, patient scheduled-request publication, clinician inbox receipt and offer submission, then patient offer review/acceptance. The accepted request and appointment were persisted; the patient’s authenticated request API and a fresh rendered page showed `Matched` plus an `Accepted` offer. Screenshots in `docs/screenshots/open-requests/` show the patient waiting state, clinician’s private offer and patient’s persisted request history. No external SMS was sent. The first ad hoc runner had an incorrect terminal-state assertion; the rendered/API state was inspected separately after that assertion, so do not treat this as a clean reusable end-to-end test script.

`tests/presentation.py` now passes **16/16** on the isolated Frappe 16 review site, including a two-thread, two-patient attempt to accept the same clinician slot; exactly one offer books and the other conflicts. The earlier full `tests/integration.py` run on the invited-review site passed 19 tests but had 5 OTP errors: those cases call the deliberately disabled legacy `phone_auth` endpoints (`legacy=True`) rather than the current site-scoped `contact_auth` routes. This is a fixture/API mismatch, not grounds to enable those legacy endpoints. The enabled-registration and legacy OTP suite still needs its own explicit enabled-policy fixture and corrected route coverage.

Frontend production build passed (`npm run build`, Vite 8.3.1); `npm run lint` completed with existing React-hook/purity warnings and no lint errors. `build_review.py` passed; `check_review_assets.py` passed with no embedded secrets/config. `bench migrate --skip-search-index` passed through v1.10, and the repeat financial migration checker passed. The financial checker remains a limited aggregate verifier: fresh v1.10 installation and per-owner legacy reconciliation (including opening timestamp equality and all historical account projections) are not proven. The compatibility preview has no scheduler or background worker active; request expiry/dispatch scheduling and scheduled earnings release were not run by workers.

Still outstanding for presentation release acceptance: clean automated enabled-registration/contact-auth suite on a separate site fixture; a reusable passing Playwright request/offer script; live concurrent web requests (database concurrency is covered); scheduler/worker execution; fresh v1.10 installation and per-patient/per-clinician migration reconciliation; hosted LiveKit Cloud revocation rerun; complete earnings lifecycle screenshots; and route-by-route visual inspection at all requested widths, 200% browser zoom and all languages. Current language strings in new request screens are only partially localized and remain provisional. SMS delivery, native-language approval, physical-device call quality, remote installation and deployment are untested.
