# Service-scope credential re-verification

## Behavior

An approved clinician can create a separate re-verification application linked
to the exact previously approved scope application. The original application,
credential details, assessment and evidence snapshot remain unchanged. The new
application is a normal human-reviewed scope application, not a self-service
extension of the old decision.

The applicant must save a renewal draft, add fresh private `License or
registration` evidence for that application, and submit updated issuing
authority, jurisdiction and credential details. The submission is immutable
afterward; exact retry returns the same application, while changed payloads use
the clarification or reconsideration workflow. One renewal is allowed per
prior application, preventing duplicate competing renewals. An explicitly
Expired decision can also be re-verified with new evidence; a Suspended or
Rejected decision must first use the appeal/reconsideration path.

If the prior credential remains valid, its approval continues to authorize new
bookings while a renewal is pending. Rejecting renewal evidence does not revoke
that still-valid earlier credential. Explicit suspension or expiry decisions
still revoke the service scope. Once the current approved application has a
credential expiry earlier than the Frappe site date, discovery, offering
publication, matching and booking fail closed. A new renewal only restores
eligibility after a reviewer records a fresh approval with a non-expired date.
Past appointments and their accepted snapshots are unchanged.

When a future booked or pending-confirmation appointment belongs to an
expired, suspended, or otherwise unavailable scope, a once-per-minute server
job records a logistics-only `Tele Tena Scope Appointment Review` item. The
decision path also flags appointments immediately on explicit suspension or
expiry. Appointment plus eligibility-event references prevent duplicate flags
while preserving a later triage episode if another credential expires.
Reviewers see the clinician, service, appointment reference,
scheduled time, and reason code; patient identity, disclosure, requests, and
notes are not included. Acknowledge records triage. Clear requires the scope to
be current again or the appointment to be terminal. The queue does not cancel
or reschedule appointments, alter booking/policy snapshots, release funds, or
grant clinical-record access. The site's scheduler must be enabled for
date-driven expiry flags; explicit reviewer suspension/expiry flags
synchronously.

## Demonstration policy boundary

For this release, the expiry date is compared with `frappe.utils.today()` on the
site. No mapping from each licensing jurisdiction to its local timezone is
configured. A future production policy must define jurisdiction-specific date
semantics, advance reminders, evidence source verification, grace periods, and
the treatment of already-booked consultations when a credential expires. The
UI may offer early renewal, but submission does not create a fixed renewal
notice period or professional-competence claim. Human reviewers must inspect
the new private evidence; the software does not independently verify registries
or scan files for malware.

## Data and access

The existing native `Tele Tena Vetting Scope Application` gains an optional
`reverification_of` reference and a submitted-payload digest. A v1.19 unique
index permits only one child renewal per prior application. These fields are
read-only through generic Frappe APIs; only the audited applicant command can
create them. New renewal evidence remains in the existing private scope-evidence
store and is included in the ordinary immutable assessment snapshot.

No existing application, assessment, scope, appointment or financial record is
rewritten. The patch is additive and repeat-safe.
