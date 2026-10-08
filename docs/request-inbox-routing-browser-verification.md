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

The patient zero-supply browser journey and screenshot are documented in
[`open-request-no-supply-verification.md`](open-request-no-supply-verification.md).
The due-wave widening outcome, rendered clinician-card assertion/screenshot,
offer submission, patient acceptance, call join and completion-to-earnings chain
remain pending. This synthetic run is not pilot performance evidence.
