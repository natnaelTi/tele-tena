# Immediate request routing browser verification

On the isolated Frappe 15 site, two independent Chromium contexts used the
seeded synthetic Review Clinician and Review Patient through the production
`/teletena/` app. At the time of the run the Review Clinician's published
08:00 Africa/Addis_Ababa interval was within the 30-minute immediate-start
window. The clinician enabled request presence in the workspace; the patient
published a synthetic immediate video request using the approved Review
conversation scope.

Persisted evidence for that request showed `eligible_supply=1`, one recipient
for the Review Clinician, and both `NotificationEnqueued` and `InboxFetched`
route events. The browser loaded the clinician inbox and acknowledged the
request fetch. A later Playwright assertion timed out because the test selected
`.clinician-request[data-request-id]`, while inbox cards do not render that
attribute. The run did not capture a card screenshot or assert visible card
text; this is not yet full rendered-inbox acceptance. The test cleanup cancelled
the synthetic request, and a separate authenticated UI check confirmed clinician
presence was paused afterward. No offer, appointment or financial event was
created by this run.

The earlier empty-inbox report is explained by the actual schedule at the time
of that request: the first interval began outside the immediate window. The
current capacity calculation and persisted recipient evidence confirm a request
is routed when the same clinician's full session fits the immediate window and
fresh presence is enabled.

## Rendered inbox acceptance — 2026-10-08

The earlier selector failure was in the browser assertion, not the product: the
inbox card has class `.clinician-request` but does not expose
`data-request-id`. A new two-context Playwright flow uses rendered request text
as its locator and passed against the production-built Frappe app at
`http://127.0.0.1:8017/teletena/`.

With the Review Clinician inside the published 08:00 Africa/Addis_Ababa
interval and fresh presence active, the Review Patient published an immediate
video request through the UI. Publication recorded one eligible clinician; the
clinician inbox API returned the request, and the actual `.clinician-request`
card rendered “As soon as possible · Review conversation”, the patient's
authorized request text, language, format, and the earliest feasible start.
The card omitted the patient's account email. Database audit showed one
recipient, one `NotificationEnqueued`, and one `InboxFetched` event.

The test cancelled the synthetic request, created no offer/appointment or
financial posting, and restored the clinician's original availability state.
It captured screenshots at 390, 768, and 1440 CSS px with no horizontal
overflow:

- `docs/screenshots/open-request-routed/review-clinician-390.png`
- `docs/screenshots/open-request-routed/review-clinician-768.png`
- `docs/screenshots/open-request-routed/review-clinician-1440.png`

This resolves the visible-inbox assertion gap for a clinician who is actually
within the immediate capacity window. The earlier report remains the root cause
for the user's original empty inbox: at that request's publication time, the
clinician's 08:00 interval had not begun, so the full session could not fit in
the immediate-start window. This is a synthetic acceptance scenario, not pilot
performance evidence. Due-wave widening, offer submission, patient acceptance,
call join, and completion-to-earnings remain pending.
