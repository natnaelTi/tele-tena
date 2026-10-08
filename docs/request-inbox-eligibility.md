# Immediate request inbox revalidation

Clinician delivery rows record that a bounded notification was enqueued. They
are routing/audit records, not a lasting authorization to read the patient
disclosure. Every inbox query therefore rechecks active clinician approval and,
for immediate requests, the exact requested language, service policy, fresh
server-side available-now lease, current approved service scope and a feasible
full-duration start with its buffers and conflicts. A request is omitted when
any gate is no longer true; the routing record remains for restricted audit.
Offer submission and patient acceptance continue to revalidate independently.

Earlier verification on this page reported missing language and reviewer policy
for the retained synthetic Review Clinician. That finding is historical and no
longer describes the subsequently configured review account. On 2026-10-08 we
inspected the persisted request and routing records after the user reported an
empty inbox despite enabling request availability. The patient's latest request
was already `Matched`: another eligible clinician received and submitted the
accepted offer, while the Review Clinician had no recipient record. At
publication time (03:24 Addis Ababa), the Review Clinician's published interval
began at 08:00. The service required 30 continuous minutes, so no feasible start
fit the immediate window. This is why it correctly did not appear in that
clinician's inbox; the availability toggle alone cannot make an out-of-hours
clinician eligible.

This investigation also found that the readiness response could continue to
show an unexpired presence lease as “Available” after the clinician's schedule
changed and no longer fit the immediate window. The lease is now presented as
paused whenever live setup validation fails. Readiness and request publication
share the same site-configurable immediate start window (bounded to 5–60 minutes,
30-minute default), and the patient response includes the window used. A
published interval can qualify between generated booking-grid start times when
it fits the complete duration and buffers; normal scheduled-booking notice
rules remain separate. The matching algorithm still rechecks capacity when an
offer is submitted and accepted.

## Verification

`TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost /home/frappe/frappe/frappe-bench/env/bin/python
tests/presentation.py` passed 38/38 on the isolated Frappe 15 review site. The new regression keeps a presence lease live, moves the schedule outside the start window, and verifies readiness is paused and a new patient request is not routed to that clinician. Existing immediate-request cases also verify a valid full-duration start between booking-grid points and revalidation at offer submission/acceptance. The immediate-request case
now verifies a routed request disappears from inbox reads after the clinician
loses its matching language or its presence lease expires, and reappears after
both are restored. Other tests cover exact-scope/policy checks, continuous
availability between grid boundaries, privacy of the recipient payload, offer
submission and atomic acceptance. Existing request-recipient audit rows remain
untouched by inbox reads.

The retained synthetic account's persisted request was matched to a different
eligible clinician; it was not a failed delivery to the Review Clinician. The
Review Clinician's next immediate readiness is schedule-dependent: the stored
recurring schedule begins at 08:00 Addis time, so it will not be ready before
then even with the toggle enabled. The focused regression passed on the same
isolated site. Full browser verification of the patient-side no-supply recovery
copy and an end-to-end request specifically routed to the Review Clinician are
still pending. No schedule, booking, balance or account was edited to force that
journey. The built preview remains `http://127.0.0.1:8017/teletena/`; build
source SHA and browser check are recorded in the current delivery checkpoint.
Frontend lint completes with existing warnings; the build retains its existing
large-chunk advisory.

## Isolated scheduler and worker status

On `tele-tena-pr12-fresh.localhost`, `bench --site … scheduler status` reports
enabled and `show-pending-jobs` reports no queued jobs. The shared Bench's
existing `frappe schedule` process and a worker are running. The worker log
records successful site-qualified runs of both
`tele_tena.api.open_requests.expire_requests` and
`tele_tena.accounting.release_eligible_earnings` on 2026-10-08. The former
invokes the idempotent due-wave dispatcher; this confirms handler execution,
not that a specific due wave delivered to additional eligible clinicians.
That outcome still needs a controlled eligible-supply scenario.

## Subsequent real two-session routing check

At a later local time, when the 08:00 clinician schedule fell inside the
immediate window, an authenticated clinician session enabled request presence
and an independent synthetic patient session published an immediate video
request. The persisted publication metric recorded one eligible clinician; a
recipient row belonged to the Review Clinician, and the routing audit recorded
both notification enqueue and clinician inbox fetch. The UI acknowledged that
fetch. The test's final visible-card assertion used a nonexistent DOM attribute,
so there is no captured inbox screenshot or verified rendered-card assertion
yet. The synthetic request was cancelled and clinician presence was paused.
Detailed evidence is in `request-inbox-routing-browser-verification.md`.
