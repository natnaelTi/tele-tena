# Verified contact and resumable onboarding

## Contract
Contact verification proves possession of a phone/email, not adult eligibility,
professional approval, service scope, or completion of registration. A new verified
contact has a least-privilege Website User and an incomplete onboarding draft.
Patient access is assigned only after required adult/consent steps are complete.
Clinician submission assigns Applicant only; manual administrator approval and
per-service scopes remain required. Existing development password login remains.

Phone entry and email entry use the same generic request outcome for known and
unknown contacts. Existing accounts are matched only after successful verification;
email matching requires the verified email, never a client-supplied account ID.
No role, enabled flag, account identifier or approval field is accepted at signup.

## Data and state
Additive numbered migration preserves phone challenges/identities and all clinical
and financial tables. Contact challenges store keyed digests, expiry, consumed time,
attempt count and send-once delivery state. Never store plaintext codes. Drafts are
owned by authenticated user and store kind, current step and bounded answers.
States: contact unverified -> verified/draft -> patient complete OR application
submitted -> administrator review. Back/save does not confer roles.

## Permission matrix
Guest: request/verify contact only, with atomic contact/IP quotas and attempt limits.
Verified owner: read/save own draft; complete own patient registration or submit
own clinician application. No generic profile/draft/identity listing.
Patient/clinician: existing command permissions continue unchanged.
Reviewer: existing scoped application/service review commands, no implicit clinical
record access. All authorization remains backend-enforced.

## Email delivery
Backend-only SMTP configuration is a local deployment dependency. Configuration
must use invisible password entry and mode-600 private storage. Require TLS with
certificate verification; bound connect/send timeout. No automatic resend after
an uncertain send. SMTP acceptance is not inbox delivery. Email OTP must not be
written into a persistent Email Queue, errors, logs, or browser configuration.
Automated tests mock delivery; a real inbox test requires configured credentials
and a consenting recipient. The interface must show actionable delivery failure.

## Acceptance
- No account-existence disclosure before contact verification.
- Expired/consumed/wrong codes fail; concurrent verification consumes once.
- Resend/attempt/contact/IP limits survive failed HTTP requests.
- No duplicate delivery for one request ID, including uncertain outcomes.
- Draft resume/Back works; another account cannot read or change it.
- Verification alone creates neither a patient profile nor approved clinician.
- Signup input cannot assign roles or link an unverified claimed account.
- Existing phone and password flows retain regression coverage.

## Implementation boundary
`v1_5_contact_onboarding` adds only identity and draft tables; the existing challenge
and rate-limit tables are reused with distinct purpose/digest namespaces. Generic
DocType APIs cannot expose these command-owned tables. Email matching is performed
only after possession verification. No user-provided account ID is accepted.

Account creation and fixed-role assignment use a private, tightly bounded system
registration context and normal Frappe document permissions (no ignore_permissions).
The original authenticated user is restored in finally; no caller-supplied fields
reach User roles, enabled flags or authority selection. This is a trusted registration
command, not permission granted to Guest on User or profile DocTypes.

Resumable drafts store professional narrative and requested scopes for review;
structured credential uploads and automated credential checks remain unimplemented.
Optional affiliation is stored as an unverified claim and grants no record access.
