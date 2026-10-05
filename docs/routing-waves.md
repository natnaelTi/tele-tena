# Progressive request routing policy

Status: configurable demonstration defaults, not pilot commitments or a validated optimum.

- Wave 1: at publication, notify up to 3 highest-ranked eligible clinicians.
- Wave 2: at 30 seconds without a valid offer, add up to 3 new eligible clinicians.
- Wave 3: at 75 seconds without a valid offer, add up to 4 new eligible clinicians.
- At 180 seconds, show the patient continued-waiting, scheduled-care and browse alternatives. Keep the existing request and constraints unchanged.

A valid offer stops automatic widening so the patient can compare it without notification pressure. The patient may explicitly select “Find more options” to invite the next eligible group. All recipients are deduplicated per request, waves are bounded, and a request/clinician pair is notified at most once. Widening never weakens clinical scope, language, mandatory format/accessibility, disclosure, age or explicit budget requirements. Newly approved clinicians receive fair tie-break exposure without overtaking better request suitability.

Each wave is an idempotent delayed job plus a scheduler reconciliation fallback. The job checks the request lock/state, valid offers, current eligible supply, prior recipients and limits. Enqueue timestamp means a job/notice was queued; inbox-fetch timestamp means the authenticated clinician inbox API returned it. Neither means it was read. Patient/browser closure does not stop routing. API polling remains authorized and scoped; realtime remains optional and cannot carry request text in push previews.

For immediate requests, the business target clock starts at successful publication. Confirmed match ends at atomic appointment creation. Time until both participants join is a separate measure. All published requests, including unmatched/expired/cancelled/failed, remain in the denominator. Synthetic fixture metrics are never combined with pilot data.
