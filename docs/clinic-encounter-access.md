# Patient-authorized clinic encounter access

## Purpose-specific grants

Clinic membership, clinic verification and clinician affiliation never expose
patient information by themselves. Two separately consented purposes are
supported; granting one does not imply the other.

**Scheduling coordination** shares one future confirmed appointment's service,
time/timezone, delivery format, booked duration, status and the identity label
already permitted by the booking disclosure snapshot. It does not expose notes,
summaries, request text, saved history, feedback, balances or other encounters.
Active Clinic Manager and Scheduling memberships, plus the verified clinic
owner's operational workspace, may read these minimized details. Billing and
Care Coordination roles do not receive scheduling access through this grant.
Access ends after the appointment is no longer actively booked, the seven-day
post-session window expires, the patient revokes, or clinic verification is
removed.

**Patient-shared summary** shares only summaries that the treating clinician
explicitly published for one completed encounter. Before sharing, the patient
selects a verified clinic and consents to sharing all patient-visible summary
revisions for that encounter. This includes later revisions the clinician
chooses to publish while the grant remains active. It excludes private notes,
unpublished drafts, request text, profile history, contact information,
feedback, balances and other encounters. The UI explains that revocation stops
future access but cannot undo prior viewing.

Only an active **Care Coordination** membership at the selected clinic can read
these summaries. Clinic Manager, Scheduling, Billing, clinic ownership and
clinician affiliation do not imply summary access. Care Coordination is an
operational role; it is not clinician credential verification, service-scope
approval or authorization to practice. A member may access only the summaries
the patient shared for that clinic and encounter while the clinic, treating
clinician's clinic affiliation and membership remain active/verified.

The API returns the encounter-scoped identity label from the immutable booking
disclosure snapshot, service/date, published summary text, revision and
publication time. It never returns an account email/phone, raw disclosure JSON,
private clinician note or arbitrary appointment lookup capability. The patient
may revoke either grant at any time; grant history is retained, and a later
profile edit does not change earlier encounter identity.

## Workflow and acceptance

1. For scheduling, the patient chooses a clinic with a current verified
   affiliation for the treating clinician and confirms the narrow disclosure.
2. For summaries, the patient can choose a clinic only after the encounter is
   completed and at least one summary is published. The consent explicitly
   identifies the purpose and ongoing revision scope.
3. Each grant is an immutable purpose-specific record. Identical active retries
   are idempotent; revocation is actor/time/reason audited and idempotent.
4. Purpose-built endpoints enforce appointment ownership, clinic verification,
   current clinician affiliation and exact active membership role. Generic
   DocType reads/writes do not enumerate or mutate grants.
5. Scheduling access is read-only and expires. Summary access is read-only and
   remains until patient revocation or a relevant clinic, affiliation or
   membership state is no longer eligible.

Automated tests use synthetic consultations and text only. Native Amharic and
Afaan Oromo translations remain provisional, and local demonstration consent
wording is not a jurisdiction-specific legal/privacy review.
