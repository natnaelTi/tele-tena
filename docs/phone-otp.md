# Phase 1: phone verification and onboarding

Status: implemented demonstration flow; provider delivery has not been tested.
Contract recorded before code changes on 2026-10-01.
This work is on `feat/phone-otp` from merged `main` (PR #2 merge); it does not
depend on PR #3. This is an account-access feature, not a phone-OTP claim for
clinical consent or professional verification.

## Agreed product rules

- Phone possession is verified before an account is created or a phone login is
  accepted. OTP does not attest age, identity, qualifications, license, clinic
  affiliation, or clinician approval.
- Public signup can create an adult patient account/profile. A clinician can
  submit an application, but signup cannot grant the privileged clinician role.
  Only the existing authenticated administrator approval command may grant that
  role; service scopes remain separately approved.
- An unverified phone claim cannot be attached to an existing email/password
  account. Existing development accounts keep their normal Frappe password
  login. Linking/recovery for a legacy account needs a separate verified,
  audited procedure.
- Verification material and phone identity mappings are private app data behind
  command APIs. OTP plaintext is transient only; never persist, log, return, or
  include it in audit evidence. Guest endpoints deny by default except the
  narrowly scoped request/verify/signup flow, with Frappe CSRF and generic
  responses that do not disclose whether a phone/account exists.
- The SMS API key is held backend-only in a mode-600 file below the selected
  site's private directory; the setup helper reads it invisibly. A separate
  per-site OTP-HMAC key is generated once by the versioned migration into its
  own mode-600 private file and is never exposed to the browser. The browser
  receives only a generic request result and challenge handle, never either key
  or the OTP.
- SMS provider acceptance is not carrier delivery. The app never labels an
  accepted send as delivered.

## Data model and security material

- `Phone Identity`: unique canonical Ethiopian mobile number, linked Frappe user,
  verified timestamp, and creation timestamp. The number is normalized to E.164
  for storage; provider formatting is a separate adapter concern.
- `OTP Challenge`: opaque random ID, phone, purpose (`patient_signup`,
  `clinician_application`, or `login`), keyed OTP digest, created/expiry times,
  attempt count, single-use timestamp, dispatch state, provider response class,
  and an idempotency digest. It never stores the OTP itself or response bodies
  containing credentials.
- Abuse counters: keyed hashes of normalized phone and trusted client IP, time
  windows, and counters. Do not retain raw IPs in OTP audit records. Forwarded IP
  headers are accepted only when a trusted-proxy contract exists; otherwise use
  the direct request peer.
- OTP verification digest uses HMAC-SHA-256 with a separate random local key,
  binding challenge ID, canonical phone, purpose, and OTP. Compare in constant
  time. Rotate by invalidating active challenges. Challenge rows and phone
  mappings are InnoDB; attempt consumption and counters lock rows transactionally.

## Permissions and flows

| Actor | Request OTP | Verify | Signup/login result |
|---|---|---|---|
| Guest | Allowed only for the three public purposes, under rate limits | Allowed for an active matching challenge | Verified patient receives Patient role/profile; verified new clinician applicant receives no Clinician role; known verified phone may log in as its mapped account |
| Existing email/password account | No phone mapping is inferred from User fields | No phone login until a separate link operation verifies and records the mapping | Existing development login remains available |
| Pending clinician applicant | May access own application/status through authenticated APIs | Cannot publish, book as clinician, or access participant APIs | Manual approval adds the Clinician role; service offering scope needs separate approver action |
| Administrator/Approver | No OTP plaintext or provider credential access through product APIs | Existing manual approval path only | May approve/reject application; approval is auditable and separate from OTP |
| Other account | Cannot read another phone, challenge, attempt counter, or application | Cannot consume another challenge by guessing its ID | No access |

Request flow: the browser gets a CSRF token, submits normalized phone, purpose,
and a random idempotency key. Server applies phone/IP limits and cooldown under
lock, creates one challenge, then makes exactly one provider request for that
challenge. Reusing the same key returns the prior generic result and does not
send again. A timeout or lost response is `uncertain`; it is never automatically
retried. The phone cooldown applies before a later challenge can send. The
provider reference documents no idempotency header, so application-level
idempotency prevents duplicate submissions but cannot promise carrier/provider
exactly-once delivery after an ambiguous network outcome.

Verification flow: require a live challenge, lock it and the rate-limit row,
increment attempts atomically, constant-time compare HMAC, and consume it once.
Expired, consumed, excessive-attempt and wrong-purpose challenges all fail.
After successful verification, create or authenticate only the flow's intended
account. Frappe's normal session cookie/CSRF behavior is used; development email
login is not bypassed or replaced.

## Configurable demonstration defaults (not settled product policy)

- Six decimal digits, five-minute challenge expiry, five verification attempts.
- Sixty-second resend cooldown; at most three sends per phone per 15 minutes and
  ten per direct IP per 15 minutes, at most five sends per phone per day, and
  ten verification attempts per phone / twenty per direct IP per 15 minutes.
- Provider call timeout is bounded and called once per idempotency key. Accepted,
  rejected and uncertain are distinct internal states. No background retry of a
  send whose outcome is unknown.
- These values require security/operations review before a public pilot. Account
  recovery, SIM-swap risk, number changes, retention/deletion, trusted proxy
  configuration, and high-risk velocity policy are not yet agreed.

## SMS Ethiopia reference findings

Inspected the provider's actual public page and API example at
<https://smsethiopia.com/#/api-reference> (the hash route renders the same
single-page reference). It contains conflicting authentication prose: the
overview says `Authorization`, but the displayed executable curl example and
FAQ integration instructions explicitly use `KEY: YOUR_API_KEY`. The adapter
will follow the concrete sample's `KEY` header only; it will never auto-fallback
to a second credential/header after a rejection because that could turn a
configuration error into a duplicate send. Provider confirmation remains needed
before live sending.

The visible send contract is `POST https://smsethiopia.com/api/sms/send`, JSON
`{"msisdn":"251911234567","text":"..."}`, HTTPS, and a 200 body such as
`{"status":"success","message":"Accepted Successfully"}`. Its SDK example
also says “Accepted for delivery.” The shown Ethiopian number is country-code
digits without `+`; canonical storage remains `+251...`, converted to `251...`
at the adapter boundary. The displayed send reference does not mention sender
ID or template fields, provide a delivery-status endpoint/message ID, or specify
template restrictions. These are unresolved provider account/support questions;
the implementation will use only documented fields, keep OTP text generic, and
label 200 as provider-accepted/unknown delivery. The homepage advertises 100 free
test SMS to whitelisted numbers; before any live send the operator must enter the
key through the local helper and name a consenting whitelisted test recipient.
No trial-credit messages are sent by automated tests.

## Local credential setup

On the development Bench, run
`bench --site erp.localhost execute tele_tena.development.configure_sms` in a
terminal. The helper prompts with hidden input and stores only the key in
`sites/erp.localhost/private/tele_tena_sms.json` (mode 600); its output contains
no credential and it does not send a message. Do not put the key in a shell
argument, frontend variable, chat, or repository file. This local helper is
restricted to `erp.localhost` and the Administrator account. Before live testing,
confirm a consenting recipient is on the provider's whitelist; no live send is
part of this checkpoint.

## Acceptance criteria and checkpoint evidence

1. Phone normalization produces one Ethiopian E.164 form from supported local
   and international input; invalid/non-mobile and unsupported numbers fail
   before provider contact. Provider receives country digits without `+`.
2. Provider adapter uses the documented HTTPS endpoint, `KEY` header, exact JSON
   fields and bounded timeout; tests mock it and distinguish accepted/rejected/
   uncertain. No auth fallback, automatic send retry or SMS in tests.
3. OTP is absent from database, API results, audit/logging, Git and exception
   text. HMAC verification is purpose-bound, constant-time, expiring, single-use,
   and attempt counters are atomic under concurrent submissions.
4. Idempotent request replay sends at most once; resend cooldown and phone/IP
   limits reject excess requests. Provider timeout does not trigger a retry and
   becomes an explicit uncertain state.
5. Guest cannot enumerate registered numbers or read challenges; CSRF remains
   enforced. Guessing another phone/challenge does not authenticate or link an
   existing account.
6. Patient signup requires adult attestation and OTP. Clinician application
   requires OTP but grants no Clinician role until manual approval. OTP alone
   grants no service scope. Existing synthetic email/password users still sign in.
7. Focused MariaDB/API concurrency and privacy tests pass; React onboarding uses
   persisted APIs and translation keys for English, Amharic and Afaan Oromo;
   provisional translations are flagged for human review.
8. No live provider test is performed until the user enters credentials locally
   and selects a consenting whitelisted recipient. Migration adds versioned
   schema and preserves all existing profiles, appointments and balances.

Verification on 2026-10-01: `tests/integration.py` passed all 20 MariaDB/API
tests, including the previous booking/privacy concurrency regressions and six
phone-auth/provider tests. `frontend`: `npm run build` and `npm run lint` passed;
`python3 -m compileall -q tele_tena tests scripts` and `git diff --check` passed.
The additive `v1_3_phone_auth` migration and migration-preservation checker passed
on `erp.localhost` before this run. Provider HTTP behavior was mocked; no real
SMS, carrier delivery, sender/template requirement, provider authentication
account, or live whitelist was verified. Fresh-site installation and external
production-like SMS abuse testing remain outstanding.
