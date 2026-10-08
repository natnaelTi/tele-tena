# Patient-shared clinic calendar

This slice adds a staff calendar over the existing patient-consented
`Scheduling coordination` grants. It does not create clinic-wide appointment
visibility, resource scheduling, booking authority, billing, or access to
completed clinical records. Clinic membership by itself is not sufficient.

## Acceptance

- Only a verified clinic owner, active Clinic Manager, or active Scheduling
  member may query the clinic calendar. Care Coordination and Billing members,
  patients, clinicians without the relevant clinic permission, and unrelated
  accounts are denied by the server.
- Results include only future Booked appointments for which the patient created
  an active, unexpired scheduling grant to a currently verified clinic linked
  to the treating clinician through a verified affiliation.
- Results contain the booking disclosure alias (or “Private patient”), service,
  appointment instant, duration, format, timezone and status. They omit account
  email/phone, medical history, request narrative, private notes, price, and
  appointment/grant identifiers.
- The calendar requests a single seven-day local-date range. The server
  validates the IANA display timezone and Monday week boundary and converts
  local midnights to UTC correctly across daylight-saving transitions.
- Desktop uses seven weekday columns. Narrow layouts use a vertically readable
  agenda. Every event remains keyboard-readable and usable without hover.
- Previous/next week, Today, timezone change, empty, loading, retry/error and
  server-persisted data are verified in the built Frappe application.

## Deliberate limits

This is a read-only schedule projection, not an authoritative clinic calendar.
There are no clinic resources, room allocation, staff-shift rules, clinic-level
availability, patient directory, bulk export, or clinic booking actions. The
existing individual clinician appointment remains authoritative. A patient
revoking the sharing grant removes the appointment from later clinic queries.
No migration is required because the feature reuses the existing grant and
appointment records.
