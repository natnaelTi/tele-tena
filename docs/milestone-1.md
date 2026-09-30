# Milestone 1: synthetic direct booking

Recorded before implementation. Depends on unmerged foundation PR #1.

## Agreed rules and scope decisions
Adults 18+, approved clinicians only, published integer-minor-unit ETB price,
fixed duration, exact request disclosure preview, saved choices, atomic slot and
simulated balance reservation. Affiliations confer no access. No real money,
OTP, diagnosis, calls, recording, notifications or production readiness.
Discovery uses service filters; natural-language suggestions/ranking are deferred.
Direct bookings confirm immediately for this demo. Cancellation/refunds, holds,
offer negotiation, credential verification standards and production safety remain
unresolved/deferred; no fees or policy windows invented. Manual administrator
approval is an attestation, not automated credential verification.

## Data model
Frappe User authentication and Tele Tena Patient/Clinician/Approver roles.
App-owned SQL tables expose only explicit authorized command/query APIs, keeping
private content out of generic DocType list/export/report/file routes. No files
or attachments. Framework Administrator is a trusted infrastructure superuser;
ordinary approvers receive no private patient read API.

- Profile: unique user, patient/clinician kind, display name, adult attestation;
  optional synthetic history and global name/history sharing defaults.
- Application: unique clinician, credential statement, Pending/Approved/Rejected.
- Service: identifier, label, active.
- Offering: unique clinician/service, price minor units, fixed minutes, active.
- Availability: clinician, UTC start/end; nonoverlapping windows.
- Appointment: participants/offering, UTC start/end, Booked, immutable price,
  duration/service/disclosure snapshot, patient-scoped retry key and payload hash.
- Simulated wallet: unique patient, available/reserved integer ETB minor units.
- Immutable simulated ledger: deposits/reservations with unique references;
  no edit/delete, real settlement or production funding route.

## Permission matrix
| Actor | Allowed |
|---|---|
| Guest | Frappe login; no app access |
| Patient | Own profile/defaults, approved discovery/windows, own preview/bookings/wallet; development-only simulated deposit |
| Pending/rejected clinician | Own profile/application; no publication/bookings |
| Approved clinician | Own offering/windows; own bookings with authorized snapshots only |
| Approver | Applications and manual approval; catalog; no patient history/wallet/disclosure API |
| Other accounts | No cross-account private data access |

Identity comes from session; role and profile kind checked. No self approval.
Patients cannot write price, statuses, balances or supplied disclosure snapshots.
No generic table API, clinical caching or permission bypass. POST mutations use
Frappe session CSRF enforcement; token retrieved from authenticated session.

## Workflow and transaction rules
Application Pending -> Approved/Rejected; resubmission -> Pending. Revocation
blocks new bookings; existing participant snapshots remain accessible.
Offering publishes after approval. Booking and balance reservation commit together.
No completion/earnings/cancellation implementation in this milestone.
Patient wallet then clinician locks serialize spending and scheduling across
all offerings. Half-open intervals allow back-to-back sessions. Unique patient/key
makes retries idempotent; changed payload with same key fails. Command exceptions
roll back savepoints; no intermediate commits. Deposits work only on erp.localhost
with explicit tele_tena_simulation_enabled configuration.

## Acceptance criteria
1. Synthetic password accounts traverse persisted profiles, approved discovery,
   exact preview, booking and reserved simulated balance.
2. Pending/rejected clinicians cannot publish/receive bookings, including stale IDs.
3. Clinicians receive only selected snapshot fields; other patient data is denied.
4. Concurrent overlaps yield one booking; concurrent spend never overdraws; retry
   creates one booking and one reservation.
5. Insufficient funds, invalid times, stale approval and injected failure leave
   no partial wallet, appointment or ledger state.
6. English keys and provisional Amharic/Afaan Oromo copy marked for native review.
7. Real MariaDB transactional and authenticated HTTP/CSRF/generic API checks,
   plus frontend build/lint and Python syntax; unrun checks explicitly documented.
