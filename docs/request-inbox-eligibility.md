# Immediate request inbox revalidation

Clinician delivery rows record that a bounded notification was enqueued. They
are routing/audit records, not a lasting authorization to read the patient
disclosure. Every inbox query therefore rechecks active clinician approval and,
for immediate requests, the exact requested language, service policy, fresh
server-side available-now lease, current approved service scope and a feasible
full-duration start with its buffers and conflicts. A request is omitted when
any gate is no longer true; the routing record remains for restricted audit.
Offer submission and patient acceptance continue to revalidate independently.

This distinction matters for the retained synthetic Review Clinician. On
2026-10-08 its authenticated readiness query returned `language_required` and
`immediate_policy_required`; `ready` was false. A clinician's approved service
scope and published offering do not by themselves enable the administrator-
controlled immediate-care policy for that service. The service inbox toggle
also does not persist a lease when setup validation fails. No existing account,
request, service policy or appointment was changed to manufacture an eligible
scenario. These observed conditions explain why this retained fixture cannot
receive an immediate request as currently configured; they do not prove the
user's separate browser configuration has the same state.

## Verification

`TELE_TENA_TEST_SITE=tele-tena-clinic-access-fresh.localhost ../../env/bin/python
tests/presentation.py` passed 33/33 on Frappe 15. The immediate-request case
now verifies a routed request disappears from inbox reads after the clinician
loses its matching language or its presence lease expires, and reappears after
both are restored. Other tests cover exact-scope/policy checks, continuous
availability between grid boundaries, privacy of the recipient payload, offer
submission and atomic acceptance. Existing request-recipient audit rows remain
untouched by inbox reads.

The packaged `http://127.0.0.1:8017/teletena/` browser check on source/build
`e5acea215be9948b538c138cc04f43e9918bcb88` authenticated as the retained Review
Clinician and observed the actual readiness response: `ready=false`,
`language_required`, and `immediate_policy_required`. The page now says that
service-scope approval alone does not enable immediate requests, links directly
to the missing care-language setting, and no longer links this reviewer-only
policy gate to the clinician's scope-application page. The inbox correctly
shows its empty state. Screenshot:
`docs/screenshots/request-inbox/review-clinician-readiness-1440.png`. This is
diagnosis and clear recovery guidance, not a successful request delivery test.
Frontend lint and production build pass with existing warnings and the
large-chunk advisory.
