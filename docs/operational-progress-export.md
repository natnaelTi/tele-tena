# TeleTena operational progress export

Sanitized local checkpoint for roadmap updates. It is not a merge, deployment,
real-patient-readiness, real-money, or market-performance claim.

## Current source and preview — 2026-10-07

- Current branch: `feat/mutual-rescheduling`, draft PR #22 against
  `feat/clinic-staff-workspace` (PR #21); no merge or remote deployment.
- Backend source is the PR branch checkout. The latest packaged frontend source
  SHA is `b627c8ba7518acb3a923e03607e9ea0317e99ccd`.
- Review URL: `http://127.0.0.1:8017/teletena/`, site
  `tele-tena-pr12-fresh.localhost`, Bench
  `/home/frappe/frappe/frappe-bench`. Frappe 15.121.2 / ERPNext 15.121.6 /
  Python 3.12.3 / Node 22.23.3. This is the built Frappe application, not Vite.
- The isolated review scheduler is disabled. Do not claim scheduled request
  routing or earnings release ran through workers. The original development
  site and Selfmade installation were not modified.
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
