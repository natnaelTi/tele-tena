# TeleTena operational progress export

## Current local checkpoint — financial transaction details — 2026-10-08

- Draft PR #32, branch `feat/financial-transaction-details`, depends on PR #31
  and targets its feature branch to preserve ancestry. It remains unmerged and
  no hosted installation was changed.
- The exact source commit is the value in the served `release.json` manifest;
  this report is updated before each final packaging pass.
- Preview: `http://127.0.0.1:8017/teletena/`, site
  `tele-tena-pr12-fresh.localhost`, Frappe app production build (no Vite).
  The packaged release manifest matches the source commit. Gunicorn master
  287561 was reloaded and serves workers on the isolated review bench.
- Patient payment activity now opens an owner-scoped persisted detail route;
  clinician earnings/payout rows have corresponding owner-scoped routes. The
  presentation suite passed 36/36 after correcting the new test fixture to keep
  wallet and subledger projections aligned.
- Built browser acceptance passed for a patient account: visible email/password
  alternative → existing payment reservation → detail → reload → generic
  unknown-ID denial. Responsive screenshots at 390, 768 and 1440 CSS px are in
  `docs/screenshots/financial-activity/`. 320px, 200% zoom, clinician-route
  browser coverage and native-language review remain pending.
- This is one incremental presentation slice. It does not complete the larger
  operational design scope, enable real payments, verify provider delivery,
  prove physical-device calls, or establish clinical/legal readiness.

Sanitized local checkpoint for roadmap updates. It is not a merge, deployment,
real-patient-readiness, real-money, or market-performance claim.

## Current source and preview — patient offer detail — 2026-10-08

- Current feature branch: `feat/patient-request-offer-detail`, draft PR #31,
  dependent on draft PR #30 → #29 → #28. No merge or remote deployment.
- Current feature branch head is tracked on PR #31; the built frontend manifest
  source is `f9d01703a3e46edbf80fe674f3fd4753256f22b5`.
- The review URL is `http://127.0.0.1:8017/teletena/`, site
  `tele-tena-pr12-fresh.localhost`, bench
  `/home/frappe/frappe/frappe-bench`; the frontend is a built Frappe app. The
  new route is `/teletena/patient/requests/:requestId/offers/:offerId` and
  reuses the patient-owner request query and existing atomic offer acceptance.
  Gunicorn master PID 287561 and worker PIDs 326665/326666 serve this build.
- Browser rendering and reload of a persisted accepted offer passed; the page
  showed its timezone, duration, format, price, exact request disclosure and
  appointment link. The existing browser journey also covered direct request
  access, return to list, entry from the list, and generic unknown-request
  handling. No active-offer Accept click was made because the available
  synthetic offer was already accepted. Amharic/Afaan Oromo text is provisional.
- Screenshots: `docs/screenshots/request-details/offer-detail-390.png` and
  `offer-detail-1440.png`. Layout overflow checks passed at 320/390/768/1440px.
  `npm run build` passed, `npm run lint` exited 0 with existing warnings, and
  the dependent Frappe presentation suite passed 34/34 on the prior code slice.
- Existing review data was preserved. There was no schema migration, reseed,
  live SMS, physical-device test, hosted deployment or remote site change.
- The service worker/update behavior was not separately exercised for this new
  route in this slice. Scheduled release/routing execution and the remaining
  designed/verification-pending screens stay outstanding in the map.

## Current source and preview — 2026-10-08

- Current branch: `feat/patient-request-detail-route`, head
  `29d267de5f510799f44db9506d91b4412a519a23`; draft PR #30 targets the open
  PR #29 branch `feat/request-inbox-eligibility-refresh`, which depends on #28.
  No merge or remote deployment occurred.
- Preview URL `http://127.0.0.1:8017/teletena/`, site
  `tele-tena-pr12-fresh.localhost`, Bench
  `/home/frappe/frappe/frappe-bench`. The packaged production app is served by
  Gunicorn at loopback, not Vite. Asset manifest source is
  `662d5ec6ae869a568a0105285cd36ad23a03315f`; backend request-detail code was
  introduced at `1a9eeeaa9a83808e4725150aa9e6bdae64354832`. The identified
  master is PID 287561 with two workers. No migrations, reseeding or changes to
  `erp.localhost` or Selfmade were made for this route slice.
- Patient request detail was verified against the persisted synthetic request:
  Frappe presentation suite 34/34; browser sign-in, direct route, reload,
  return to list, list-link navigation and generic unknown-ID state passed.
  Responsive checks passed at 320/390/768/1440 CSS px; Amharic and Afaan Oromo
  headings rendered. Screenshots are in `docs/screenshots/request-details/`.
  PR #30 CI passed on Node 22.23.3/24.13.0 and Python syntax 3.12/3.14.2.
- Bench scheduler and a shared worker are running, but scheduled earnings
  release and progressive routing-wave execution remain unverified for this
  checkout; no claim is made that a worker has processed either job. The
  retained synthetic review site was not reseeded.

## Historical source and preview — 2026-10-07

- Current branch: `feat/mutual-rescheduling`, draft PR #22 against
  `feat/clinic-staff-workspace` (PR #21); no merge or remote deployment.
- Backend source is the PR branch checkout. The latest packaged frontend source
  SHA is `b627c8ba7518acb3a923e03607e9ea0317e99ccd`.
- Review URL: `http://127.0.0.1:8017/teletena/`, site
  `tele-tena-pr12-fresh.localhost`, Bench
  `/home/frappe/frappe/frappe-bench`. Frappe 15.121.2 / ERPNext 15.121.6 /
  Python 3.12.3 / Node 22.23.3. This is the built Frappe application, not Vite.
- The isolated review site has its scheduler enabled. The bench scheduler and
  its shared worker processes serve the bench; only this site's scheduler
  flag was changed. Scheduled request expiry ran through the Frappe scheduler
  and worker. There were no due earnings to release, so scheduled earnings
  release remains unverified. No unrelated bench service was restarted.
  The original development site and Selfmade installation were not modified.
- The named disposable fresh site `tele-tena-clinic-access-fresh.localhost`
  remains available; its temporary scoped database administrator and
  credential file were removed after use.

## Latest verified work

- The patient-registration completion regression was fixed: an authorized role
  grant temporarily switching to Administrator had overwritten the user's Frappe
  session state. The code now restores the complete session snapshot. The
  presentation suite passed 27/27, including the session-preservation case.
- Fresh-site installation/schema checks and repeat migration passed. A
  production-built browser journey passed in enabled-registration mode; an
  independent invited-review check passed with phone/public registration off
  and password access retained. No live SMS or email was sent. Local MariaDB
  10.11.14 is not evidence of exact Frappe 16/Selfmade compatibility.
- The seeded review clinician's authenticated readiness query currently reports
  `language_required` and `immediate_policy_required`; no fresh presence lease
  exists. The real built UI shows those requirements and keeps “Go available”
  disabled. The account/profile and service policy were not changed. A focused
  fault-injection browser test confirms server rejection is not mislabeled as a
  network outage. Screenshots across English, Amharic and Afaan Oromo at 390px
  and 1440px are under
  `/tmp/tele-tena-presentation-review/request-readiness/`.
- The clinician workspace now uses three focused mobile shortcuts plus a
  keyboard-accessible “More workspace links” dialog. Browser coverage verified
  role-specific routes, Escape dismissal, and focus restoration. The
  readiness/error journey was rerun at 320/390/768/1440px in all three locales
  with no horizontal document overflow. Latest screenshots include
  `blocked-{en,am,om}-{320,390,768,1440}.png` and `mobile-more-menu.png` in the
  directory above. Amharic and Afaan Oromo remain provisional, not natively
  approved.
- The packaged Frappe browser check returned HTTP 200 at `/teletena/`, and its
  service worker controlled the canonical `/teletena/` scope after reload.
- After confirming there were no due pending earnings or pending-confirmation
  holds, the scheduler was enabled only for `tele-tena-pr12-fresh.localhost`.
  The site-specific `Scheduled Job Type` rows for request expiry, pending
  appointment expiry, earnings release and reschedule expiry recorded a run;
  two overdue open synthetic requests transitioned to `Expired`, and no due
  earning or appointment hold remained. `bench doctor` showed an online worker
  processing queues. The default queue also contains an old global failed-job
  registry; failures were not attributed to TeleTena. The short check did not
  create an eligible request or a due earning, so it does not prove a successful
  routing wave or financial release.
- Frontend TypeScript/Vite production build passed; lint exited 0 with existing
  React warnings. Asset hash/scope/secrets validation passed. PR CI passed on
  Node 22.23.3/24.13.0 and Python 3.12/3.14.2.

## Scope still in progress

The approved 142-screen map and batches A–I remain the controlling scope;
current work is incremental, not full operational acceptance. Human-led
vetting/catalog approval, verified routing through successful presence and
offers, the live worker/scheduler path, complete trust indicators, extensions,
clinic operations and multi-party consent, labs, subscriptions, second opinions,
medical tourism, complete administration, and whole-product visual acceptance
remain partial or pending. Details and per-screen states are in
`docs/mvp-delivery-tracker.md` and `docs/operational-screen-map.json`.

External gaps remain: live SMS delivery, physical-device calling, native-language
approval, clinical/legal approval, partner integrations, real custody/payment
settlement, remote installation of this branch, and Frappe 16 compatibility for
the latest local changes. Synthetic routing metrics are not pilot evidence, and
the three-minute match target is not guaranteed.
