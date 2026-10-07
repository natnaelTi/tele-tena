# Session-experience feedback

The patient may submit one structured 1–5 session-experience rating after a
booked consultation is ended and explicitly finalized by its treating clinician.
The rating records the patient's experience of that encounter; it is not a
measure of clinical competence, treatment effectiveness, or a clinical outcome.
There is no public free-text comment in this release, so this path does not
claim to provide comment moderation.

The `tt_session_feedback` row is private and encounter-scoped. It records the
patient, treating clinician, completed appointment, rating, server timestamp,
and `session-experience-v1` metric version. Generic DocType access is not
provided. The patient may read their own submitted rating through their
authorized appointment detail. Clinicians and administrators cannot read
individual patient ratings through this API.

The public profile indicator is computed on read from ratings received by the
clinician in the preceding 365 days. The source event is a persisted, eligible,
finalized encounter rating. The formula is the arithmetic mean, rounded to one
decimal for display. Counts are shown. Fewer than five responses hide the mean:
zero is “New to TeleTena”; one through four is “More feedback needed”. At five
or more, the mean and sample count appear. Missing history is not scored as
zero. The metric version, observation window, and minimum sample are returned
with the query result; values update on each profile read.

Responsiveness and appointment reliability are distinct trust dimensions.
Response behavior counts an immediate request only after the authenticated
clinician inbox returns it and the client acknowledges the card while the
clinician's available-now presence remains fresh. Its numerator is distinct
presented request IDs with a clinician offer created after that inbox fetch;
its denominator is presented immediate requests. The observation window is 90
days. It displays the rate and numerator/denominator only at five presented
requests or more; smaller samples show the evidence count and a suppression
label. An enqueued notification alone is not counted. The metric describes
offers, not clinical ability.

Appointment reliability counts only confirmed consultations that ended in
explicit completion or a clinician-attributed cancellation within 365 days.
Its rate is clinician-attributed cancellations divided by completed plus
clinician-cancelled sessions. Patient cancellations and expired unconfirmed
holds are excluded, not attributed to the clinician. The rate and numerator /
denominator are hidden below five observations, while the evidence count and
suppression label remain visible. No-show attribution is not implemented and
is not included in this metric. The source is the appointment's persisted
confirmed/completed/cancelled actor and timestamp state. This is an operational
indicator, not clinical competence.

No single overall clinician score is calculated. Credential review and approved
service scopes remain separate human decisions; patient experience never
grants or implies a scope.

The English strings are implemented. Amharic and Afaan Oromo strings are
provisional and require native-language review. Frappe migration, direct API
permissions, metric queries, profile rendering, and connected browser behavior
remain pending until the isolated current-source site is available.
