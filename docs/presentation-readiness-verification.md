# Presentation release verification

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
- Real payments, double-entry accounting, ERPNext posting/reconciliation, withdrawals, clinician earnings, ratings, rescheduling, no-show actions, couples participation, clinic workspaces, natural-language matching and private requests/offers remain unimplemented per the tracker. The configured cancellation/release rules are demonstration policy only.
- Account notifications and contact-change settings are not implemented. Existing appointments without reliable media timing report it unavailable. The PWA installation checklist has not been validated on physical devices/HTTPS hosting.
- This branch is not production clinical readiness. Do not activate real payment or credential-verification claims.

## Presenter walkthrough

1. Open the local development site and sign in through **Use email instead → Use password instead** with a synthetic development patient account. Add demonstration funds from **Payments**.
2. Choose **Find care**, select an approved service, pick one of the returned dates/times in the displayed timezone, review **What you’ll share**, then confirm. Open **Appointments → View consultation** to review the exact snapshot and reservation.
3. In a separate browser session, sign in as an approved synthetic clinician. Show **Today** and the weekly **Availability** editor; edit intervals or a date exception, save and publish. Show that an already booked appointment remains unchanged.
4. For a scheduled synthetic consultation, use the explicit pre-call check and Join in both sessions. Show video, mute/camera/audio-only controls, Leave/rejoin, and the clinician’s **End for everyone** confirmation. Hosted End was separately verified in automation.
5. Open the ended consultation as clinician, save a private draft, preview the patient summary, and explicitly finalize. Sign in as the patient to show only the published summary and follow-up booking link.
6. In the reviewer workspace, inspect the synthetic pending application and private resume, then review the separate service-scope decision. Tours can be replayed with **Help & tours**; no tour submits a mutation.

Do not present the fake-media screenshots as physical-device evidence, and do not
describe the simulation transaction log as accounting or a real payment.
