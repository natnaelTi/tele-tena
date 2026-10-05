# Vetting, catalog, and routing verification

Status: local dependent feature work on `feat/vetting-catalog-routing`; not
merged or deployed. This report separates observed failure causes from broader
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
- Applicant evidence-by-scope, clinic-affiliation verification, structured
  interview scoring, independent license verification, appeals, reverification,
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
- Packaged asset refresh, request-inbox browser journey, scheduler execution,
  full post-consultation chain, live SMS, and physical-device testing remain
  pending at this checkpoint.
