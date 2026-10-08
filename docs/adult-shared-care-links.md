# Adult shared-care relationship links

## Purpose and limits

This slice implements an optional, mutually accepted relationship link between
two TeleTena patient accounts. It does not create a couple/family appointment,
share clinical history, give either person access to the other's appointments,
or authorize a multi-participant consultation. Couple, family, and group
offerings remain unavailable until participant-specific booking, disclosure,
call authorization, and note-recipient behavior are implemented and verified.

The link is for adult patients only. Each person gives an explicit adult
attestation at the action they initiate (invite creation or acceptance). This
is an attestation, not independent age or identity verification. Identity
verification remains an external/product-policy decision.

## Workflow

`No link → invitation pending → mutually linked`

- The inviter confirms adult eligibility and creates a short-lived invitation.
- A high-entropy, single-use token is returned once and is shared manually. No
  SMS/email is sent and no invitation URL is placed in an API query string.
- The token is held in the browser URL fragment, removed from browser history
  before the authenticated acceptance request, and stored server-side only as a
  digest. It grants no access before sign-in and acceptance.
- The invitee previews the inviter's chosen display name, confirms adult
  eligibility, and accepts or declines. The server records both consent times
  and the consent-text version.
- Either linked patient can revoke the link. Revocation is audited and
  immediately removes the relationship from active-link queries.
- Expired, revoked, declined and superseded invitations cannot be accepted.
  Reusing the same submission key rotates the bearer token on the existing
  invitation instead of creating a duplicate.

## Permission boundary

Only a `Tele Tena Patient` with a patient profile may create, preview, accept,
decline, list or revoke these links. The invitee must present the original
high-entropy token and authenticate as a patient. Clinicians, clinic staff,
administrators and unrelated accounts cannot list or operate on a patient's
relationship state. The token is never a substitute for authentication.

Each participant may see the other participant's current profile display name
after mutual acceptance. No email, phone, history, account ID, appointment,
disclosure snapshot, note, balance, or call-room information is exposed. A
relationship link does not create or imply any record grant.

## Demonstration defaults and acceptance

- Invitation validity: 72 hours, configurable by site setting within 24–168
  hours.
- At most five invitation creations per patient are allowed in a rolling day;
  declined, expired, and withdrawn invitations still count. Retrying the same
  idempotency key returns the original active invitation without consuming
  another creation.
- The invitation text and consent version are versioned in the application.
- Database uniqueness and a transaction gate prevent reciprocal racing invites
  from creating duplicate active relationships.

Acceptance tests cover adult attestation, patient-only access, token
single-use, duplicate retries, expiration, decline, revoke, privacy-minimized
responses, reciprocal concurrent acceptance, and proof that the link does not
grant appointment or clinical-record access. Couples/family offering, booking,
multi-party LiveKit, private intake and recipient-scoped documentation remain
pending.

## Human review

The English consent wording is product copy and Amharic/Afaan Oromo
translations remain provisional. Medical/legal review of the relationship
consent text and of age-assurance requirements is still required before any
real-care use.
