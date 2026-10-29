# Direct Payment Navigation — 28 October 2026

Runtime/build: `ec94719809961bf54671baf4d52eb434b4f07a3e`, branch
`feat/offline-telebirr-mvp`, draft PR50 dependent on PR49. The retained preview is
http://127.0.0.1:8017/teletena/ on `teletena-mvp-presentation.localhost`.

## Delivered Behavior

- Both payer submission and clinician review use standalone payment pages.
  Desktop: form/status left, payment-only timeline right, with View Appointment
  and Next Steps at its end. Mobile/zoom stacks those sections with normal scrolling.
  Receipt verification stays on the payment page; appointment details contain a
  compact status/action link, never the receipt form or payment history.
- Payment notifications route to the exact authorized payment, including an
  extension's additional receipt. In-app duplicate projections of the same durable
  event are deduplicated. External notices use the same authenticated destination;
  their neutral copy contains no transaction ID, receipt or health text.
- Clinician Appointments and Requests poll a bounded owned pending-review queue
  every15seconds. Submitted claims and unresolved unverified evidence have direct
  Review Payment actions. Labels use the encounter disclosure and time, never a
  later patient-profile identity. Appointment details and accepted-offer cards
  also expose the relevant payment status/link. No new confirmation popup replaces
  the accepted-offer popup or presence/capacity behavior.
- The explicit new owner decision makes financial configuration a default for
  Tele Tena Approver accounts. v1.48 grants it to existing reviewers and audits
  the backfill; authorized administrator assignment of a new reviewer supplies
  it automatically. Explicit later removal is not silently undone on profile save.
  Clinicians/patients receive no such default. This supersedes the earlier
  separate-opt-in reviewer default, not the server permission check.

Receipt verification, appointment acceptance, End and clinical completion remain
separate facts. The API still denies unrelated clinicians, reviewers, partners
and guests access to a private receipt/payment; reviewer financial configuration
does not confer party access. No wallet entries, provider credentials, consent or
payment-mode selection were changed by this implementation.

## Verification

| Check | Result |
|---|---|
|Payment backend|19/19 real-MariaDB rollback-isolated tests, including notification destination/deduplication, pending ownership, exact extension-payment destination, private receipt denial, retry/concurrency-related state invariants and prior payment/finance cases|
|Reviewer defaults|3/3 native User/migration tests: new reviewer default, clinician exclusion, explicit removal respected, repeat-safe existing-reviewer backfill with payment config/journal preservation|
|Fresh target|New disposable `teletena-payments-v148-fresh.localhost`, Frappe16.2.1/ERPNext16.1.0/Python3.14.2; fresh install and two native migrations passed; new reviewer default verified; access/provider switches remain off; transient test reviewer rolled back|
|Existing review site|Owned preview writers stopped; verified complete database/public/private/config backup before migration; nativev1.48 migration passed; both reviewer accounts now have financial configuration; site configuration values unchanged. No demo reseed or accounting-company setup|
|Connected browser|Real Frappe16 backend and separate existing synthetic payer/clinician sessions: guest profile→auth/calendar→payment submission→already-open Requests updates through polling→Appointments review section→single notification directly opens receipt→Requests review action→human verification→standalone page retained→appointment status/link only→payer reload/private-receipt denial|
|Responsive|Production-built payer/clinician screens captured at390/768/1440. Actual Chromium200% zoom on both payment roles, verified720CSS-pixel viewport/DPR2 at1440physical pixels; timeline next-step action remains accessible by scrolling|
|Other checks|Production build, lint (existing warnings), Python syntax,4 localization exchange tests, service-worker tests, built asset hashes/private-credential scan passed. No new dependencies or framework edits|

Reproduction: `scripts/browser-payment-navigation.cjs` and
`scripts/browser-payment-pages-zoom.cjs` use only the isolated8021 test transport,
private test manifest and synthetic documents. They are not remote deployment
entrypoints. Native preview migration backup/logs and test logs remain under the
restricted `/home/frappe/teletena-offline-sprint` directory.

Rendered evidence is in `docs/screenshots/payment-navigation`. Codex inspected the
new two-column composition, timeline hierarchy, labels, wrapped mobile controls
and actual zoom captures. C08/D06/H01/H02 shared patterns are retained; this new
owner-approved direct-payment composition supersedes the old embedded form and
has no literal wallet-only reference equivalent. Owner acceptance remains pending.

The actual server privacy/notification destination checks are separate from
provider receipt/delivery: no real Telebirr transfer, live SMS/email receipt or
physical-device call was tested. The accepted consultation media layout and
hosted call core were not changed. Policy/translation/clinical review gates remain
as recorded in the prior sprint report.

## Review Walkthrough

1. Reload8017 (use Refresh to Update if offered). Reviewer Account should show
   Payment Mode and Timing without a separate grant. Default permission alone
   does not change the mode. Native ERPNext setup is unnecessary for this page.
2. Submit proof for a new Offline booking. The payment page has only payment
   details/actions and the timeline. It does not append appointment details.
3. Clinician: remain on Requests, or open Appointments. Within bounded polling the
   pending-payment section provides Review Payment; the notification opens the
   same exact receipt page. Counterparty identity respects the encounter snapshot.
4. Verify receipt in the appropriate account. Stay on the standalone payment
   page, then use View Appointment and Next Steps. Manual appointment acceptance
   remains a separate action where configured. Payment history stays on its page.
5. Check the existing accepted-offer notification, availability card and clinical
   workflow remain available. No historical data needs reseeding or resetting.

The [Selfmade guide](selfmade-offline-telebirr-update.md) now pins this runtime and
documents the intentional reviewer permission default. No remote deployment or
merge has been performed.
