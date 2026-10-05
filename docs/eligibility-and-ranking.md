# Eligibility and progressive routing

This specification describes the current demonstration implementation and
separately identifies the intended pilot controls. It is not a clinical
credentialing standard or a claim of successful matching.

## Server-enforced eligibility today

| Condition | Current behavior | Gap |
|---|---|---|
| Enabled clinician, general manual approval, exact approved service scope | Required in database eligibility and rechecked before offering/acceptance | Credential evidence and restrictions are not independently validated |
| Active offering and published schedule | Required | Schedule rules do not represent jurisdiction-specific practice authority |
| Exact requested language and audio/video format | Required | Mandatory accessibility needs are not yet modeled |
| Immediate service policy and fresh available-now heartbeat | Required only for immediate requests; legacy review service also requires explicit site setting | Stale heartbeat renewal depends on authenticated app reachability |
| Immediate full duration, buffers, schedule interval, clinician/patient conflicts | Continuous feasible-start calculation; rechecked at offer and acceptance | No in-person location workflow |
| Scheduled request time | Server-generated schedule slots and existing booking checks | Complete patient-selected timezone/filter constraints need broader browser acceptance |
| Adult pilot | Adult patient onboarding/attestation and adult-specific catalog definitions | No independent age verification; the demo attestation is not identity proof |
| Scope policy revocation | Current service-scope check denies new request delivery, offer and acceptance | Existing appointments are not automatically operationally reviewed |

Missing mandatory criteria are not inferred as satisfied. However, service
credential requirements, location/jurisdiction, dynamic required attributes and
accessibility are not fully modeled in this checkpoint, so affected offerings
must stay inactive until their needs are implemented and reviewed.

## Routing behavior

Eligible clinicians are ordered by earliest feasible start, recent exposure
count, then stable identifiers. Request recipients are private, deduplicated,
bounded, and never see competing offers. Configuration defaults begin waves at
0, 30, and 75 seconds with recipient limits 3, 3, and 4 (hard maximum 10).
The one-minute scheduler is the retry path, so those seconds are demonstration
starting values, not timing guarantees. A patient may explicitly request more
options without relaxing any constraint. The 180-second point is a product
fallback, not proof that matching is possible.

`NotificationEnqueued` records availability in the inbox routing path;
`InboxFetched` records an authenticated inbox response. Neither proves a person
saw or read it. Patient APIs poll owner-scoped state for reconnection. No SMS
request broadcast is performed.

## Planned pilot constraints and ranking

Before a pilot, each service definition must explicitly state professional
categories, required and expiry-sensitive credentials, population, participants,
formats, jurisdiction/location, required intake attributes and supported
workflows. Every unmet or absent mandatory item is a non-match. Patient
preferences and ranking can never relax these conditions.

After eligibility, future ranking may use reviewed service-relevant expertise,
request preferences, feasible time, response reliability and completed encounter
experience, with separate metrics and sample counts plus fair exposure for new
clinicians. This multi-dimensional ranking is not implemented here. The current
exposure tie-breaker is not a quality score. There are no fabricated ratings;
authenticated feedback remains pending. Patient satisfaction is not evidence
of credential status or clinical outcome.

The immediate-care business target is measured from successful publication to
appointment creation; time until both participants join is a separate measure.
Unmatched and failed requests remain in outcome reporting. Synthetic data cannot
establish real pilot coverage or performance.
