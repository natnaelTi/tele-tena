# Proposed Native-Gateway Live Amendment — Not Authorized or Executed

This is one consolidated request, after local preparation. It does not activate
production collection or reset PlanV1 counters. Preserve its completed receipts,
errors, events, destinations and original recording reference.

Purpose: verify the new native snapshot gateway against the selected EU PostHog
project335848, ingestion eu.i.posthog.com / administrative API eu.posthog.com.
The earlier live session used an isolated fixture; actual app routes now have
network-free real-backend coverage, but the new gateway needs its own live proof.

If approved, append an explicit one-time scope amendment to the existing private
ledger, leaving original usage/caps intact. Do not execute before approval.

- One new synthetic recording, each at most90seconds: a newly created synthetic
  patient account with role-appropriate synthetic route transitions on a disposable local site. Account,
  onboarding, Requests and support-dialog layouts only; no existing user data.
- SDK→native gateway→bounded operations worker→PostHog snapshot ingestion. Before
  egress inspect masked payloads for synthetic text/input/file/receipt/URL canaries.
- Maximum6snapshot POSTs and5MiB combined snapshot bytes; record before every
  request. Total recordings, including originalPlanV1, must remain≤3.
- Maximum16project-scoped metadata/snapshot/source/readback GETs, including
  provisional exports and each new recording's separate25hour completeness check.
  Keep total administrative reads≤60. No custom analytics events or query calls.
- Independent private playback with all segments, integrity and zero-network
  checks. Delete only this one new recording after settled verification, plus1exact
  confirmation GETs. Original cleanup now used2/3delete/readback slots and still fails403. Completing it would consume the third slot; this proposal explicitly requests one additional delete and one confirmation for only the new recording (overall caps4each). No other cap increases.
- Bugsink errors/readbacks/uploads:0. Telegram/email/SMS:0. No new source maps,
  billing settings, monitors, provider destinations or existing-record deletion.
- Temporarily enable only this disposable site's capture/consent path. Keep the
  presentation/Selfmade sites unbound and disabled. Native site records/certificates
  used for transport tests must be explicitly labelled synthetic and cannot enable
  production. Restore the disposable site's flags and stop its owned processes.
- Preserve original capture timestamps; record new exact due times. No day-long
  sleep or assertion that a recheck is scheduled. Retain the same durable budgets
  across failures; no blind retries of unknown outcomes. If remaining caps cannot
  cover a complete export, stop and report that exact discrepancy.

No notifications are requested; all four confirmed owner receipts stay complete.
This proposal does not authorize production activation, real payments, deployment,
merging, capture of existing records or future permanent live testing.
