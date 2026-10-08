# Vetting, catalog, and routing verification

## Current packaged-preview reproduction — 2026-10-08

This section supersedes the older preview/site references below for the current
request-discovery reproduction. The source and packaged frontend used during
the browser journey were `9385fe6d4301d8ec3ad8fa8b483223fc86ecb52e` on
`feat/request-inbox-eligibility-refresh`. The pushed branch now ends at
`025fa5ff862f363574c47febd9c2340bb4694246`, a documentation-and-evidence-only
commit after that product-code/build SHA. `release.json` still reports the
unchanged frontend source SHA `9385fe6d4301d8ec3ad8fa8b483223fc86ecb52e`. The review URL was
`http://127.0.0.1:8017/teletena/`, served by the production-built Frappe route
on site `tele-tena-pr12-fresh.localhost` in `/home/frappe/frappe/frappe-bench`.
The app was not served by Vite.

### Persisted eligibility findings

Before changing synthetic test configuration, the saved `Review Clinician`
profile had no care languages, the `Review conversation` immediate-care policy
was disabled, and the published `Africa/Addis_Ababa` schedule began at 08:00 on
each weekday. At the observed local time (03:17 EAT), the schedule had no
conflict-free 30-minute start in the next 30 minutes. The presence API returned
`no_immediate_capacity`; the saved presence was not live. The patient fixture
had no prior open request at that point. Thus approval, offering and weekly
availability by themselves did not meet the immediate-request eligibility
rules. The persisted state did not support the earlier assumption that all
request requirements were active. The exact initial empty-inbox state cannot
be reconstructed from an unrecorded earlier browser attempt, but the current
server-side blockers were directly observed rather than inferred from the
availability toggle.

Through the built application only, the synthetic clinician saved English as
a care language, and the reviewer enabled immediate requests for the legacy
review service with a recorded synthetic-only reason. A temporary date-only
replacement interval from 03:30–04:30 EAT was added alongside the existing
08:00–20:00 date interval. Presence then became live with an expiry. A separate
patient browser published a synthetic immediate request while the clinician
session was reachable. The clinician inbox returned that request with a
server-suggested 03:30 EAT start; the clinician submitted an offer at the
published ETB 600 price; the patient reviewed the disclosure and accepted.
Persisted results were one Matched request, one Booked appointment and one
accepted offer. The patient's synthetic wallet moved from ETB 3,151 available /
ETB 1,849 reserved to ETB 2,551 available / ETB 2,449 reserved. The amount was
reserved once. The temporary date exceptions were then removed through the
availability UI; the original daily 08:00–20:00 recurrence remains, and the
accepted appointment remains Booked. No historical data was reset.

The review-service immediate policy and clinician English language are still
saved synthetic fixture configuration. Presence is lease-based and expires
when the clinician session stops renewing it. The schedule was restored to its
original recurring hours; therefore it does not currently offer an immediate
start outside those hours. The accepted appointment is preserved even though
the temporary interval was removed, as required for schedule edits.

Screenshots from the actual packaged UI are in
[`docs/screenshots/request-inbox/current/`](screenshots/request-inbox/current/):
the patient's matched request at 390 px and the clinician's accepted offer
history at 1440 px. They use synthetic copy and accounts.

### Compatibility-site migration and tests

The named disposable site `tele-tena-clinic-access-fresh.localhost` already
existed from a prior fresh-install attempt. The fresh-install harness refused
to overwrite it. Before touching its schema, a full database, config, public-
file and private-file backup was made under that site's private backups. A
site-scoped repeat migration then completed successfully on this branch, and
`tests/presentation.py` passed **33/33** against that site. A second migration
also completed successfully. This is repeat-migration evidence on a retained
isolated site, not a new fresh-install run at the current branch head. The prior
site's synthetic records were preserved. The original `erp.localhost` and
Selfmade were not migrated or changed.

The main bench scheduler flag is enabled, with its `frappe schedule` and worker
processes running. These are bench-wide processes, not a dedicated queue for
the isolated site. This check did not establish execution of a scheduled
routing wave or earnings-release job. No unrelated process was restarted.

GitHub checks for the current PR head `025fa5ff862f363574c47febd9c2340bb4694246`
passed: frontend on Node 22.23.3 and 24.13.0, plus Python syntax on 3.12 and
3.14.2. This documentation-only commit did not alter application code.

### Capacity-state copy follow-up — source `75ef08be1a726b5515584771668a3120b3dc2500`

The clinician shell now says “No complete session fits the next 30 minutes”
when that exact server reason is present and links directly to Availability.
“Go available” remains disabled until the server allows presence. This replaces
the generic “Complete setup” message in the capacity-only state; no matching or
availability checks were loosened. The Amharic and Afaan Oromo action labels
are provisional and still need human review.

`scripts/browser-request-availability-error.cjs` passed against the packaged
`/teletena/` application. It authenticated a real synthetic clinician while
injecting controlled readiness responses for language/policy/capacity states,
verified the capacity-specific copy and route, checked keyboard/mobile
navigation and width overflow at 320/390/768/1440 px in all three locales, and
confirmed authenticated validation errors are not called connection errors.
This script is a UI-state test; the real API capacity response was separately
observed as `ready=false, reasons=[no_immediate_capacity]` for the saved review
clinician, and the rendered real-state screenshot is
[`clinician-paused-no-capacity-1440.png`](screenshots/request-inbox/current/clinician-paused-no-capacity-1440.png).
The production asset build was rebuilt at `75ef08be1a726b5515584771668a3120b3dc2500`
and the identified preview Gunicorn master was HUP-reloaded; `/teletena/`
returned HTTP 200. `npm run lint` and `npm run build` passed before the package
build, with existing lint warnings and the existing large-bundle advisory.

Current evidence proves that a properly configured synthetic clinician can
receive, offer and match an immediate request in the production-built preview.
It does not prove the three-minute pilot target, a new fresh install at this
head, worker-isolated scheduled waves, live SMS, hosted LiveKit behavior,
physical-device calls, native translation approval, or completion of the
broader approved A–I scope. Those remain separate acceptance items.

Historical report context (earlier `feat/vetting-catalog-routing` checkpoint;
not the current branch): the entries below preserve earlier failure analysis
and test results. The packaged-preview reproduction above is the latest
observation. This report separates observed failure causes from broader
requirements that remain incomplete.

## Reproduced inbox failure

Site: isolated `tele-tena-pr2-test.localhost`; no patient narrative, account
identifier, or credential is recorded here. Read-only inspection found:

- The synthetic clinician's general application and exact `Review conversation`
  service scope were Approved.
- A published offering and schedule existed, in video format, with English among
  the clinician's languages. The weekly interval was 09:00–17:00 in
  `Africa/Addis_Ababa`.
- The service's `immediate_care_enabled` policy was false. General approval, an
  approved scope, a published offering, and a presence toggle did not make the
  legacy service eligible for immediate requests.
- The stored presence heartbeat was expired at inspection. It must be renewed
  by an authenticated active session.
- Inspected old patient requests were published before the schedule opened and
  were older than the configured 15-minute request validity. They remained
  stored as Open because no compatibility-site scheduler had been running; the
  request APIs still reject expired requests. They cannot prove a current
  availability failure.
- A fresh eligibility query with complete service projections did not reproduce
  missing `earliest_start` or `latest_start` values. An earlier diagnostic used
  an incomplete projection; it is not evidence of malformed timestamps in
  retained rows.

There was also an independent algorithm defect: immediate matching depended on
a 15-minute direct-booking grid. A complete 30-minute session inside the working
interval could be feasible even when no grid start fell inside the narrow
request window. `scheduling.immediate_start` now finds a continuous valid start
and repeats checks at offer and acceptance. The regression uses a 10:00–10:40
interval and a 10:05–10:35 request window.

The configuration correction is explicit: this legacy review service requires
the site-scoped `tele_tena_demo_immediate_care_enabled` switch before immediate
presence/request use. New catalog services remain inactive until clinical review
and activation. This does not change scheduled-care rules or production defaults.

### Read-only recheck on 2026-10-07

The preserved synthetic site was inspected again without resetting its data.
The site-level demonstration-immediate switch and review-site binding are on, so
the legacy service's false per-record `immediate_care_enabled` value is allowed
through the narrowly scoped legacy-review fallback. It is not the active blocker
on this snapshot. Its existing presence row says `ready=1`, but its expiry is
2026-10-06 13:31:12 UTC; the API correctly treats that as stale. The request table
has no `Open` rows: its immediate requests are already `Expired`, `Cancelled` or
`Matched`, so none can appear in the current inbox. Their date-bound columns are
present. One earlier immediate request has a recipient and a matched state,
showing the existing delivery path has completed successfully at least once.

This read-only snapshot cannot establish what happened in the exact browser
attempt the patient described. It does establish that the currently saved
presence is stale and the currently stored requests are terminal. The next
reproduction must use a newly published request while the clinician's
authenticated workspace is renewing presence, then compare the request's
eligibility/route events and the clinician's scoped inbox response. An open tab
alone is not persisted evidence that presence is still fresh.

## Preview and process boundary

- Review URL: `http://127.0.0.1:8017/teletena/`
- Serving bench: `/home/frappe/teletena-compat/bench`
- Site: `tele-tena-pr2-test.localhost`
- Source branch: `feat/vetting-catalog-routing`, based on
  `feat/open-requests` (`1296682` at branch creation).
- The URL is served by the isolated compatibility WSGI/Gunicorn, not Vite or
  the original development bench.
- Compatibility Redis queue uses database 15. The retained database 0 queue
  was not processed.
- Before release restart, no compatibility worker/scheduler was active. The
  original bench processes were not stopped or restarted.

## Implemented in this branch

- Continuous immediate-start selection in a published interval, including
  duration and conflict validation, rechecked at offer and acceptance.
- Presence now requires a conflict-free full session start inside the next
  30-minute immediate-request window. A published weekly schedule outside that
  current window no longer appears as active ready status; the clinician shell
  gives a `no_immediate_capacity` reason.
- Explicit immediate-service policy and reason-coded clinician readiness.
- Current approval/scope and active-offering checks at discovery, delivery,
  offer submission, and acceptance.
- Bounded progressive private waves with per-site starting delays of 0/30/75
  seconds and a hard total of ten recipients. A one-minute scheduler is the
  reconciliation fallback, so these values are not a latency SLA.
- Separate `NotificationEnqueued` and authenticated `InboxFetched` events; an
  inbox fetch does not prove that a clinician read a notification.
- Patient request CTA beneath discovery search and active-request summary.
- Additive native catalog, service-attribute, scope-application and assessment
  models. New catalog rows remain draft/inactive or explicitly legacy; migration
  does not rewrite historical appointments.
- Applicant draft/resubmission, reviewer assignment, clarification, per-scope
  approve/reject/suspend/expiry actions, and append-only assessment records.
- Proposed rubric v1.0 with mandatory gates. It is not an agreed or medically
  approved rubric.

## Incomplete requirements

- The catalog is a sourced proposal, not a reviewed or exhaustive taxonomy.
  Medical-lead approval is required before activation.
- Applicant scope-specific PDF upload/revision is now implemented on the
  dependent `feat/scope-evidence` branch with private storage and assessment
  references; API permission/state regression tests pass on the retained
  Frappe 15 site. Rendered browser verification for this new workflow is still
  pending. Clinic-affiliation verification, structured interview scoring,
  independent license verification, appeals, reverification,
  expiry automation, and operational review of existing appointments after
  revocation are incomplete.
- The rubric records gating findings but does not implement the requested
  detailed scored assessment engine. The software does not independently verify
  credentials.
- Eligibility does not yet implement every service-specific credential
  restriction, jurisdiction, mandatory accessibility, or dynamic required
  attribute. These must remain non-matches when introduced; they are not inferred.
- Ranking is deterministic by feasible start/exposure, not the requested
  multidimensional expertise/reliability/experience model. No genuine ratings or
  feedback exist; none are fabricated.
- Progressive waves use scheduled jobs. Browser delivery uses authenticated
  polling fallback; enqueue/fetch events are not proof of human notice. No SMS
  request broadcast is implemented.
- The whole journey through call, finalization, feedback, and earnings release
  has not been verified in one pass. Feedback and ratings remain absent.

## Verification checkpoint

- Frappe 16 presentation suite: 20 tests passed, covering continuous immediate
  matching, no-capacity presence state, explicit site-scoped policy, scope approval gates, private offers,
  booking/funds and slot concurrency, and applicant clarification/resubmission.
- Frontend TypeScript/Vite production build passed. Oxlint passed with existing
  React hook/purity warnings.
- Repeat migration on the retained isolated site completed through after-migrate
  hooks; no reseed or record deletion was performed.
- Packaged guest/sign-in/deep-link/reload/sign-out/PWA browser check passed on
  source `ab5ac52e9f849666a3296d2a5fdfe035428860f0`.
- Production-built availability save, reload and generated patient booking
  passed with a newly created synthetic patient.
- Production-built separate patient and clinician sessions published a scheduled
  request and verified it appeared in the authenticated clinician inbox.
- The compatibility scheduler and queue worker ran against isolated Redis DB 15;
  aggregate state inspection confirmed the five stale retained Open requests
  were transitioned to Expired. One new scheduled synthetic request remains
  Open for review. No old queue was consumed.
- A real-time immediate browser dispatch outside the sample clinician's working
  interval was not claimed. Mocked-time Frappe tests cover immediate eligibility,
  continuous starts and capacity gating. The full post-consultation chain, live
  SMS, hosted LiveKit Cloud, physical-device testing and native translation
  review remain unverified in this checkpoint.

## Packaged preview continuation (2026-10-05)

This continuation was run against source `9d239b6d847e7e671fad2026413b92bace5b0ffb`
at `http://127.0.0.1:8017/teletena/`, on the isolated compatibility site and
Redis queue DB 15. The page was the packaged Frappe route; no Vite server served
the preview. The independent compatibility worker and scheduler were running.
The original development bench processes and Redis queue DB 0 were left alone.

The newest test request that appeared to be missing from the clinician inbox
was for Wednesday, 2026-10-07 at 15:00 Addis Ababa time. Read-only inspection
found the retained synthetic clinician's published recurrence on Monday and
Tuesday only. The Wednesday request therefore had no feasible slot and zero
eligible recipients; it was not delivered. This is the exact reason for that
test request's empty inbox. A second packaged UI journey selected Tuesday,
2026-10-06 at 10:00, which is inside the actual published schedule. It produced
one eligible clinician notification; the separate clinician session received
the request, loaded the approved service, and could send an offer only after
selecting a service and start time. The patient reviewed and accepted that
offer. Persisted checks found one Matched request, one Booked appointment, one
legacy reservation event, and one matching reservation journal. These were
synthetic review records and were preserved.

At the inspected local time, the clinician's “Available for requests” status
was Paused because no complete session fit within the next 30 minutes. This is
the intended readiness rule, not evidence that a scheduled request should be
hidden when a later date has a valid published interval. It also explains why a
presence toggle cannot make an immediate request eligible outside current
capacity. The older immediate grid-boundary bug remains separately covered by
the Frappe regression described above.

Additional checks on this exact source/build:

- `tests/presentation.py` on `tele-tena-pr2-test.localhost`: **20/20 passed**.
- `scripts/browser-review-package.cjs`: **passed** guest denial, invited
  password sign-in, protected deep links, consultation reload, sign-out,
  responsive width assertions, PWA scope, offline state, and no Vite server.
- Two-context packaged request journey: **passed** scheduled request
  publication, clinician delivery, offer-input gating, private offer
  submission, patient acceptance, and persisted appointment/reservation.
- A separate ad hoc browser attempt used Wednesday despite the Monday/Tuesday
  recurrence and correctly received no eligible offer. That fixture mismatch
  was diagnosed from the persisted schedule and request bounds; it was not
  treated as a product failure or fixed by broadening eligibility.
- Screenshot evidence is in `/tmp/tele-tena-vetting-review/current/` and the
  prior synthetic offer screenshots remain under `docs/screenshots/open-requests/`.

This does not close the incomplete requirements above. In particular, the
clinician operating inbox is demonstrated, but the complete vetting rubric,
medical catalog approval, multidimensional trust indicators, human response
performance, full call-to-earnings demonstration, native-language approval,
fresh-site installation, live SMS, and physical-device testing remain gaps.

### Patient request-history composition (source `3ff4b0245df83809c01bdb29586382d78ef599d2`)

The synthetic review patient's old request list was dominating the same screen
as the active request composer. Open requests remain directly visible; terminal
requests now sit under a native keyboard-operable “Previous requests” disclosure.
Rows still marked Open after their server expiry are treated as history in the
presentation even if the expiry worker has not reconciled them yet; the server
continues to enforce expiry. No record was deleted or filtered out of the
authenticated API. A packaged 390px browser check matched all 16 API records to
zero unexpired open cards, retained all 16 inside the collapsed disclosure, and
confirmed Enter expands it. Its EN/AM/OM label was added to the dictionary; the
Amharic and Afaan Oromo strings are provisional and need native-language review.
Collapsed and expanded captures are in
`/tmp/tele-tena-vetting-review/current/patient-requests-collapsed-mobile.png` and
`/tmp/tele-tena-vetting-review/current/patient-requests-expanded-mobile.png`.

### Empty immediate-request inbox diagnosis (2026-10-07)

Read-only inspection of the retained synthetic Review Clinician in
`tele-tena-pr12-fresh.localhost` reproduced the reported “toggle is on but no
request arrives” setup. The authenticated `request_presence` query returned
`ready=false`, `configured=false`, with reason codes `language_required` and
`immediate_policy_required`; no unexpired presence lease existed. The saved
calendar and published offering do not by themselves make an account eligible
for immediate requests. The profile must declare the request language, and a
reviewer must enable immediate care for the exact service; only then can an
authenticated session create/renew the short-lived ready presence. The matcher
also excludes a candidate whose language set does not contain the request's
required language. This explains the empty inbox without relaxing either
condition. No profile, approval, offering, schedule, appointment or balance
was changed during this diagnosis.

The clinician workspace now renders each readiness reason as a link to the
relevant account, service, availability or professional-review screen. This
does not enable any policy or bypass the human reviewer. A Frappe regression
asserts that absent languages and disabled immediate-service policy remain
separate readiness reasons. The running packaged browser confirmed the linked
reasons for this seeded synthetic account; screenshot:
`docs/screenshots/mutual-rescheduling/availability-1440.png`.

### Reviewer service-policy workflow (2026-10-08)

The fresh read-only check on the retained `tele-tena-pr12-fresh.localhost`
synthetic account returned `language_required` and `immediate_policy_required`.
The persisted care-language list was empty and the exact service policy was
false; the schedule and approved offering existed. Thus the user's statement
about a matching language in the interface did not match the persisted profile
for this snapshot. Neither cause is inferred from the original screenshot; both
were read from this later server state. No synthetic account or service was
changed to make the diagnosis pass.

The saved schedule is published daily from 08:00 to 20:00 in
`Africa/Addis_Ababa`, for 30-minute sessions. The host clock at this read was
02:24 EAT. That interval supports later scheduled bookings, but no complete
start can fit the immediate request's next-30-minute window at that time. Once
the saved-language and service-policy blockers are addressed, clinician
readiness will still require a current interval with continuous capacity.
“Available for requests” is a presence lease, not a claim that daytime hours
make the clinician immediately ready overnight.

The current dependent branch adds v1.22's audited policy command and a scoped
reviewer control under Administration → Service scopes. Enable/pause requires
an approver role, rationale, eligible catalog lifecycle, and a stable retry key.
Generic DocType saves cannot change the switch. The event and service update
share a transaction; disable is refused while live immediate requests remain.
This controls service policy only: it does not declare the clinician ready.
The clinician must still save supported languages, exact scope approval,
published offering/schedule, and fresh presence with full-session capacity.
Automated backend verification passed on the Frappe 15 isolated site. The
packaged `/teletena/admin/scopes` page was then opened in Chromium using the
existing synthetic reviewer; its service selector and immediate-policy panel
rendered with the explanatory copy. No service was toggled in this browser
check. Capture: `docs/screenshots/immediate-policy/reviewer-services-1440.png`.

## Current packaged preview (2026-10-08)

- URL: `http://127.0.0.1:8017/teletena/`
- Bench/site: `/home/frappe/frappe/frappe-bench` /
  `tele-tena-pr12-fresh.localhost`
- Backend checkout: branch `feat/immediate-service-policy-review`, source
  `00a5f0245fcd2b78e93fcea9b65821e5071977af`; the dedicated loopback Gunicorn
  was gracefully reloaded after migration and build.
- Frontend: production-built Frappe assets, `release.json` source SHA matches
  `00a5f0245fcd2b78e93fcea9b65821e5071977af`; no Vite server serves this URL.
- Scheduler: enabled for this review site; `bench doctor` reports one worker
  online and `show-pending-jobs` reported no pending jobs at this check. This
  does not prove a future request or earnings job has executed.
