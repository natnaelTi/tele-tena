# Open patient requests and clinician offers

Status: implemented in progress on `feat/open-requests`, dependent on draft PR #12. The persisted APIs and patient/clinician UI are connected. The Frappe 16 backend regression exercises competing offers, privacy, insufficient-funds retry, atomic reservation, idempotency and two-patient concurrent slot claims. A two-session production-built browser walkthrough reached persisted acceptance; the ad hoc runner’s final assertion was wrong, so a reusable passing browser test remains outstanding. Scheduler execution, provider-backed realtime delivery and full translation review remain outstanding. “Implemented” here does not mean release-accepted.

## Agreed product rules

Patients can publish a private request without a funded balance. “As soon as possible” requests seek a clinician with fresh explicit available-now presence; “Schedule for later” requests seek a future proposed appointment. Matching is deterministic and eligibility-first: active clinician approval, approved service scope, language, format and a conflict-free time must all match. A request is not an emergency response service and category suggestions are not diagnoses. The three-minute match target is measured, never promised.

Only the patient who owns a request and a clinician explicitly selected for bounded delivery may read its minimum necessary disclosure. An offer is visible only to that patient and its author. Other clinicians cannot enumerate requests, responders, prices or accepted matches. The disclosure snapshot is immutable. Text entered by the patient is disclosed to recipients and can contain identifying details even when profile fields are masked.

The published request has one final disclosure snapshot. Global privacy preferences initialize it; the patient can override before publication. On offer acceptance the patient reviews the appointment disclosure and exact price. The accepted snapshot is copied to the appointment. Posting and offers never reserve funds. Acceptance locks the shared booking gate, request, offer, clinician schedule and patient wallet; validates current approval/scope, presence where applicable, offer validity, booking slot, patient funds and request state; and creates the appointment and reservation atomically. A successful retry returns the same appointment. Insufficient funds leave the request and offer unchanged so the patient can add funds and retry, subject to offer expiry.

## State model

Request: `Open -> Matched | Cancelled | Expired`. An open request is private and has a server expiry. Closing it revokes ordinary clinician access; restricted audit events retain timestamps and actor references only. Offers are `Active -> Accepted | Declined | Withdrawn | Expired | Superseded`. A clinician may withdraw an active offer; it does not hold a calendar slot. Acceptance supersedes competing offers without disclosing the winning quote to their authors. Eligibility is rechecked at acceptance; approval revocation, stale presence, expiry, changed scope and slot conflicts fail without partial writes.

Clinician readiness is a separate, explicit presence record with heartbeat and server expiry. An open tab is not presence. Clinicians may pause immediately. The configurable default presence TTL is 90 seconds; the configurable request and offer validity demonstration defaults are 15 minutes. They are product demonstration defaults, not agreed commercial service levels. Immediate requests are delivered to a bounded eligible set and then expanded in bounded rounds; there is no public feed or SMS broadcast. Authenticated, owner-scoped polling is the implemented update mechanism and reconnect path; notification payloads omit request text, identity and clinical details. Provider-backed realtime delivery is not implemented.

Limits are configurable per site and enforced server-side: at most 3 active requests per patient, 5 request publications per rolling hour per patient, 10 offer notices per request per delivery round, and 10 offers per request total. Limits return an actionable result without exposing whether other patients or clinicians are present.

## Measurement and pilot assumptions

Record request publication, first eligible notification, first valid offer, appointment acceptance/creation and participant joins as privacy-preserving timestamps. Report all immediate requests, including unmatched, expired, cancelled and failed acceptances: eligible supply at publication; percentage confirmed within 3 minutes; median and p90 first-offer and confirmed-match times; and unmatched, expired, cancelled and failed-acceptance rates. Label synthetic demonstration data separately from pilot evidence. Participant join latency is measured separately and does not count a future booking as an immediate match.

The under-three-minute outcome needs enough currently approved, scoped, language/format-compatible clinicians with fresh presence and available conflict-free slots. It also depends on clinicians responding and patients having sufficient funds at acceptance. No target is supportable without measured coverage and pilot evidence.

## Acceptance criteria

- Separate patient and clinician sessions publish, notify, offer and accept a request through authenticated backend APIs and persisted records. `tests/presentation.py` passes the real backend acceptance slice; a built two-session walkthrough reached persisted acceptance, with captured states in `docs/screenshots/open-requests/`. The reusable browser assertion remains pending.
- Patient sees only eligible offers; clinicians see only their own offers and only the authorized request disclosure. Non-selected and unrelated accounts cannot retrieve the request, offer, patient identity, appointment or notes.
- Two competing clinician offers remain mutually private; a losing offer is superseded on match without exposing the winner's price.
- Immediate presence expires server-side; pausing, disapproval, scope changes, language/format mismatch, offer expiry and slot conflict prevent acceptance.
- Insufficient funds preserve request/offer selection; funding and retry revalidate the offer and atomically reserve funds and create one appointment.
- Duplicate/concurrent acceptance creates at most one appointment and one reservation. Two patients cannot claim one slot. Cancellation, expiry and reconnect/polling work without duplicate messages or broadened disclosure.
- No-response fallback offers continue waiting, schedule later or browse care without changing constraints. No SMS broadcasts, fake responders, fabricated availability, clinical diagnosis, price auction, real settlement, or guaranteed-match language.
- The complete synthetic journey is tested through the real backend and production-built local preview; UI mocks alone do not satisfy acceptance.

## Unresolved product decisions

The immediate-request service category taxonomy, commercial response SLA, recipient expansion cadence and production request-retention period require pilot/operator agreement. The implementation uses named, configurable demo defaults above; these must not be represented as settled commercial policies. Clinical escalation/safety policies remain outside this matching feature.
