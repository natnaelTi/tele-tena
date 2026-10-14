# Portable fictional MVP dataset v2

Explicit CLI only; no installation/migration seed or public endpoint. The site
must already be explicitly bound to review mode, with developer mode/CSRF bypass
off. Real-money/payment/payout flags cause refusal. This command never configures
SMS/SMTP/LiveKit, enrollment, funding switches, framework settings or real transfers.
It adds a separate namespace `tt-demo-mvp-v2` alongside existing records. It never
adopts an existing conflicting account or service. No cleanup command is provided;
financial and clinical audit records must be retained.

Run as the normal Bench user, with `Administrator` supplied by Bench execute:

```bash
bench --site SITE execute tele_tena.demo_dataset.setup
# Expected dry_run:true, changes:false; read the preflight before continuing.
bench --site SITE execute tele_tena.demo_dataset.setup --kwargs '{"dry_run":False}'
```

Bench15/16 interpret kwargs as a Python literal: uppercase `False`, not JSON
`false`. This is a built-in command argument, not a secret. No password argument.
Passwords are random and saved only in the site's private mode600 file:
`sites/SITE/private/tt-demo-mvp-v2-accounts.json`. Role names, account mapping,
record IDs, scenario links, illustrative prices and operation checkpoints are in
`sites/SITE/private/tt-demo-mvp-v2-records.json`, also mode600. Do not publish either.
Restore both with database/private-files backups if a setup was interrupted.

## Connected contents

Ten fictional accounts: five adult patients (English, Amharic, Afaan Oromo;
masked/name-sharing choices; two separate couples identities), three approved
clinicians with complementary counseling, psychotherapy/relationship and
psychiatric scopes, a pending applicant, and an Approver/Medical Lead reviewer.
Names are coherent fictional identities, not real professionals. Seven distinct
structured demonstration definitions cover individual counseling, stress/anxiety,
grief/loss, psychotherapy, couples, premarital and psychiatric consultation.
Existing catalog drafts and historical services/decisions are untouched. These
new definitions and scope assessments record explicitly fictional review exercises;
they are **not** medical-lead approval for real clinical practice. License/resume
PDFs visibly state FICTIONAL/NOT VALID and use ordinary private evidence APIs.
The pending applicant has Submitted, Clarification and Rejected scopes; general
approval is still Pending. Approved accounts have separate recorded scope
assessments, published offerings and schedules. One fictional clinic affiliation
is submitted/reviewed separately from scope competence.

Five patient wallets are funded through the existing demonstration deposit API.
Upcoming, pre-start-cancelled/full-release, completed/private-note/shared-summary,
pending/disputed/released earnings, Requested and Cancelled payout, confirmed
couples, open/comparing/accepted/cancelled requests and withdrawn/accepted offer
history are created through domain commands. The single existing feedback API
has a clearly fictional verified-encounter rating; no public text review is
invented. Payout Processing/Paid/external transfer are not fabricated when no
operator/provider settlement exists.

Schedules include date exceptions. Twenty-four-hour intervals are deliberately
**fictional review availability**, allowing an operator in any timezone to test;
this does not claim real clinician supply. Clinicians start paused and must
explicitly enable presence in their active browser. Recurring bookings start
relative to the first run. Offers expire normally. No supply/three-minute result
is guaranteed. First-run dates and accepted policy snapshots stay unchanged on
repeat; use the UI to post a new request or book a new slot when old fixtures
expire. A repeated seed does not reopen requests, move appointments, renew
presence, overwrite edited schedules, reapprove scopes or deposit again.

## Financial and session simulation boundary

All deposits, reservations, cancellation releases, finalization, dispute holds,
release and payout reservations use balanced immutable application postings.
The historical released fixture uses an explicitly synthetic, process-local
clock earlier than the configured dispute window; no server clock or persisted
policy setting changes. Pending/held fixtures use separate controlled times.
The offline room adapter exists only inside this non-HTTP CLI context, uses
throwaway credentials/tokens discarded in memory, and closes a fictional room
that never existed at LiveKit. It is not a production authentication bypass or
proof of media exchange/revocation. `FictionalSession` audit records explicitly
state actual_media:false. Real calls for new bookings continue through the
unaltered hosted LiveKit authorization/closure implementation.

Release is restricted to the dataset's due historical appointment; the seed
cannot release unrelated eligible earnings. Every patient projection and each
clinician's pending/available/payout obligations are checked against the ledger;
unbalanced/mismatched records stop visibly and remain intact. The ordinary
scheduler still runs the unchanged bounded all-eligible scan independently.

## Short presenter script

Open the private record manifest locally to find role/account mapping; never copy
passwords into reports. Use email → Use password instead.

1. Patient Mahi: Find care → inspect Sara/Michael → calendar → disclosure → book.
   Compare available/reserved wallet activity and appointment detail.
2. Mahi: Requests → inspect the open scheduled request and two mutually private
   offers. Choose one, confirm its total and sharing; funds reserve once.
3. Sara: Requests/Your offers → own Active/Accepted/Withdrawn history; accepted
   consultation link. Enable Available for requests for a new immediate test.
4. Private patient Aster: completed session → shared summary; private clinician
   note is absent. Sara: care record → private note and shared summary.
5. Sara: Earnings → pending, dispute hold, available and payout-reserved buckets.
   Cancel a Requested payout to release its reservation; no external payment.
6. Liya/ Yonatan in separate sessions: shared appointment → each adult's own
   consent/disclosure. Use a new shared booking for actual configured LiveKit calls.
7. Reviewer Meron: Netsanet's general Pending application and three different
   scope states, private fictional evidence and the review guide. Existing
   unrelated reviewer accounts and decisions are not modified.

Portable data does not verify live SMS/SMTP delivery, physical-device calls,
real clinical competence, native translations or external financial settlement.
