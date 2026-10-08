# Patient-approved sharing of a published consultation summary

## Scope

This adds one explicit sharing purpose alongside the existing scheduling-only
clinic grant. A patient may share only a completed encounter's already-published
patient summary with a currently verified clinic affiliated with the treating
clinician. It does not expose private clinician notes, intake/request text,
unpublished drafts, profile history, balances, feedback, or other encounters.

The new `Care Coordination` clinic membership role is separate from Manager,
Scheduling, and Billing. Only an active Care Coordination member can fetch
patient-approved summaries. Clinic ownership and manager status confer no such
access. A clinic invitation is not clinical credential verification and does
not authorize clinical practice.

The patient selects a clinic and sees a disclosure notice before granting
access. The grant references one appointment and one purpose, is repeat-safe,
and remains active until the patient revokes it or the clinic membership/clinic
verification is no longer valid. Revocation removes subsequent API access;
the audit trail retains that sharing occurred. Previously viewed content cannot
be made unseen.

Only revisions that the treating clinician explicitly published for the patient
are eligible. If later revisions are published, those patient-visible
revisions may appear under the same active grant. The clinic response returns
only the encounter-scoped disclosure alias, service/date, published summary,
revision and publication time. It never returns account email, phone, private
note, raw appointment disclosure, or arbitrary appointment lookup capability.

## Acceptance

- Patient sees eligible clinics only for their own completed appointment with
  at least one published summary and a current verified clinician affiliation.
- Patient grant is idempotent; revoke is idempotent and stops subsequent reads.
- Care Coordination sees only summaries explicitly shared to its clinic and
  only while its membership is active and the clinic is verified.
- Billing, Scheduling, Manager, clinic owner, other clinicians, other patients,
  generic DocType APIs, and guessed IDs do not grant access to summary content.
- Patient API never includes private notes in this workflow.
- Tests use synthetic consultations and summaries only.

This is a local demonstration workflow, not a legal determination of clinic
record-controller status or a substitute for jurisdiction-specific consent,
retention, or professional review.
