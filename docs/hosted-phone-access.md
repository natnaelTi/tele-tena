# Hosted phone access contract

Scope: explicitly bound TeleTena review sites only. Phone OTP, patient registration
and clinician registration are separate site settings, each false by default on a
review site. They do not control simulated funding, Desk/Frappe signup, password
login, LiveKit, review evidence, or the public homepage. The existing review
account credentials continue to work. Original development-site contact flows
remain available for regression testing.

A verified phone maps to one existing user or a new contact-only onboarding draft.
No user existence signal is sent before successful code verification. A new contact
may complete only an enabled patient or clinician onboarding path. Patient status
requires adult attestation and consent; clinician status requires adult attestation,
consent, requested services and a private PDF resume. Application and individual
service scopes need manual review. OTP cannot grant clinical access.

Phone ownership proof does not link an account through a claimed email or profile
name. Conflicting existing identity mappings fail closed after verification.
Disabling registration leaves existing verified accounts able to sign in while
preventing new draft creation and onboarding completion. The remote review site
keeps Frappe's global public signup disabled.

OTP material is keyed HMAC, single-use, five-minute expiry, five code attempts.
The pre-existing per-phone and direct-peer limits/cooldown apply. A new rolling
24-hour, site-wide cap counts **outbound SMS attempts** across both phone APIs,
including provider rejections and uncertain outcomes. Idempotent retries consume
neither additional budget nor another provider call. The site cap is configured
at 1–100 SMS attempts per 24 hours (demonstration default 20). It counts durable
Sending/Accepted/Rejected/Uncertain challenges created within the previous 24
hours under the existing OTP gate lock, requiring no schema migration. Disabling
sends does not clear that history. Contact counters remain in `tt_otp_rate_limit`.
The peer is the WSGI `remote_addr`; arbitrary X-Forwarded-For
is never trusted by TeleTena. A proxy IP may make the limit conservatively
shared among users until the operator confirms trusted real-IP handling.

The adapter makes one bounded POST. Its account-confirmed authentication header
is selected explicitly through a private local helper; it never tries a second
header or retries after an uncertain response. Provider acceptance means an API
request was accepted. Receipt requires the human recipient's confirmation; code
verification is a separate server event. No plaintext OTP, key, request body or
recipient is logged. Review mode stays a demonstration; real payments and clinical
care remain disabled.

Email code sign-in is offered only when a valid private SMTP configuration exists.
The password option remains explicit and always available. Email contact proof
follows the same new-account registration controls. Email delivery is not claimed
until an authorized live test succeeds.

Acceptance: default review denial; independently toggled SMS and both registration
paths; existing-user login and new-user draft/finish; duplicate/racing verification;
wrong/expired/consumed code rejection; phone/peer/site send limits; provider rejected,
uncertain and accepted outcomes without duplicate sends; review password login,
privacy permissions and booking regressions unchanged. Automated delivery is mocked;
any live SMS is an operator-controlled, consenting-number test after private setup.
