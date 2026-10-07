# Clinic registration and clinician affiliations

## Initial state model

Clinic application: `Draft → Submitted → Verified | Rejected`; an authorized
reviewer may later move `Verified → Suspended`. A clinician cannot edit a
submitted application while it is awaiting a decision. A rejected applicant may
correct and resubmit the same registration; the new record links to the
rejected record and neither is overwritten. One submitted, verified or
suspended registration per reference/jurisdiction is enforced under a database
lock. Exact retries of a submitted profile are idempotent. Verification
decisions are restricted to Submitted → Verified/Rejected and
Verified → Suspended; restoring a suspended clinic requires a new explicit
operational review workflow and is not currently available.

Clinician affiliation: `Submitted → Verified | Clarification | Rejected`,
`Clarification → Submitted` on applicant resubmission, and
`Verified → Revoked` by an authorized reviewer. Decisions and reasons are
tracked in Frappe document history and the TeleTena audit stream. An identical
retry while Submitted or Verified returns the existing request.

## Permission boundary

| Actor | Can see | Can change |
|---|---|---|
| Clinician/applicant | Their own clinic submissions and affiliations; public name and jurisdiction of verified clinics | Submit their own clinic profile and affiliation request; edit only their own Draft clinic profile; resubmit their own Clarification affiliation |
| Tele Tena Approver | Clinic registration and affiliation queues, legal registration references, decision history | Record a reasoned clinic or affiliation decision through the command API |
| Patient/other clinician | No clinic application or affiliation evidence | Nothing |

Generic DocType reads and writes use document permission checks, owner query
filters and controller validation. No clinic role is added by these workflows.
Affiliation is not clinical competence and never grants access to patient
records, appointments or consultation notes. It does not create a service-scope
record. No `ignore_permissions` path is used.

Clinic legal names and registration references remain private. The clinician
selector returns only verified clinic names and jurisdictions. Affiliation
summaries must not contain patient information.

### Operational clinic memberships

A verified clinic's submitter or an active Clinic Manager may invite a verified
email address as Clinic Manager, Scheduling, or Billing. The invited account
must verify that exact address before it can see or accept the invitation.
Invitations are in-app only; email delivery is not implemented. Acceptance
records the account and timestamp. A clinic manager can revoke an invitation
or active membership with a reason; audit history is retained. Scheduling and
Billing labels do not yet grant calendar, resource, or billing capabilities.
Clinic Manager permits membership administration only. No role grants patient
record or appointment access; clinic membership is operational identity, not a
clinical encounter grant.

Calendars/resources, clinic billing and encounter access grants remain future
work. This slice does not expose controls for them.

Schema is supplied as additive native DocTypes and installed by normal Frappe
model synchronization. No existing clinic affiliation narrative or appointment
record is rewritten or promoted to verified status.

## Verification status

`tests/presentation.py::test_clinic_registration_and_affiliation_are_separate_from_scope_and_records`
covers idempotent submission, uniqueness within jurisdiction, corrected
resubmission with history, approved clinic and affiliation review, self-review
denial, generic DocType list/document permission checks, cross-clinician denial,
clarification/resubmission, and the invariant that clinic approval creates no
service scope. It passed 22/22 presentation regressions on the disposable
Frappe 15 site after the DocType module paths and permission hooks were fixed.
The actual built `/teletena/` browser journey also passed clinic submission,
separate reviewer decision, affiliation submission and affiliation review.
Screenshots are checked in under `docs/screenshots/clinic-review/`.

On source commit `05115ca5c8027baf99a5049c7e6f5c7250d58466`, the additive
`Tele Tena Clinic Membership` model migrated on the same disposable Frappe 15
site and passed the built-browser path: clinician submits clinic, reviewer
verifies, clinician invites a staff contact, the account with a temporary
synthetic already-verified email fixture accepts, and the manager revokes with
a reason. The fixture row was removed after the browser run. Focused screenshots
are in `docs/screenshots/clinic-membership/`. The screenshots use only a
synthetic `example.invalid` account. The browser checked 320/390/768/1440 CSS
px with no page horizontal overflow and captured the 390/1440 states. Actual
200% zoom, human Amharic/Afaan Oromo review, fresh-site install, and Frappe 16
schema compatibility remain pending.

This was an additive migration onto a site created earlier in the same
checkpoint, followed by Frappe model synchronization; it is not yet a clean
fresh-install proof for the final DocType package. Frappe 16 schema/API
compatibility, actual 200% zoom, and human Amharic/Afaan Oromo review remain
unverified. Responsive overflow checks for the membership route passed at the
four CSS widths above. The separate membership feature is additive and now
has focused database coverage for verified-email visibility/acceptance,
unverified denial, immutable invite identity, non-manager restrictions,
idempotent invite/accept/revoke retries, retained membership history, and the
invariant that a patient membership does not grant clinic or clinical-record
access. Current browser and migration results are recorded in the latest
presentation-readiness report. Private uploads, clinic calendars/resources,
billing and explicit encounter grants remain unimplemented.

Frontend build/lint alone does not establish workflow or visual acceptance.
