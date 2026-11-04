# Direct Payment Live Updates — 28 October 2026

Runtime/source/build: `cd89a9ff82484233caa4a8353341cde6c3b4a182`.
Branch `feat/offline-telebirr-mvp`, draft PR50 dependent on PR49.
Preview http://127.0.0.1:8017/teletena/; retained site
`teletena-mvp-presentation.localhost`. Later evidence-only commits do not change runtime.

## Behavior and Root Causes

The payment form previously remained editable after submission and used a slower
refresh. It now displays submitted amount, reference and authorized private receipt
read-only, polls every five seconds, and refreshes on focus/payment events. The
server rejects replacement proof during review; explicit correction/rejection
reopens submission without erasing history. Initial late proof remains supported.

Existing bells held payment events but only accepted offers had a workspace popup.
A separate nonmodal payment activity alert now runs for authenticated patients and
clinicians across routes, including the call route. It neither replaces accepted-offer
alerts nor navigates automatically. Seen events are deduplicated in memory; dismissal
persists read status in the authorized inbox. New popups concern activities while the
session is open; older unread activity stays in the bell. No browser-persistent
clinical data, receipt, transaction reference or contact details enter the alert.

The worker previously superseded a queued submission notice if verification had
already changed payment state. Submission and verification now validate their
immutable source events, so both activities can be notified even when processed
later. Messages explicitly direct users to current status. Preferences, verified
contacts, country/provider switches, caps and idempotent outbox claiming still apply.
Reminders remain state-bound. No SMS/email receipt or delivery claim is made.

## Checks Actually Run

- Frappe16.2.1/ERPNext16.1.0/Python3.14 real database: `tests/direct_payments.py`,
  **21/21 passed**, rollback isolated. New tests cover pending-proof rejection,
  identical retries, correction/resubmission, fast confirmation before dispatch,
  opposite email/SMS preferences, two adapter acceptances and repeat dispatch with
  no duplicate sends. Transports and SMS enable/cap preconditions were mocked;
  this is not live delivery evidence. Existing permission, financial, late-proof,
  duplicate-reference, extension and mode tests passed unchanged.
- `scripts/browser-payment-live.cjs`: two separate browser contexts on the isolated
  real-backend Frappe16 site/port8021. Actual calendar booking and receipt upload;
  patient form disappears; clinician on Account receives popup and exact receipt
  link; clinician verifies; patient status and popup update without page reload.
  A same-document probe survived. Read persistence and no repeated popup verified
  over additional polling. One verification event, zero browser errors.
- Desktop1440, tablet768, mobile390 screenshots captured; submitted desktop,
  clinician Account alert, verified tablet/mobile inspected visually. Standalone
  timeline retained; mobile stacks with normal scrolling; alert remains dismissible.
- Actual Chromium200% zoom for both payment roles passed via
  `scripts/browser-payment-pages-zoom.cjs`; controls/next-step link remain reachable.
- Production build and lint passed (existing warnings retained). Artifact/hash and
  privacy scan passed. Localization export and **4/4** CSV exchange tests passed.
- Retained preview production shell/deep links returned200 and release.json matched
  the runtime above. Guest payment detail denied. The hosted HTTPS-only URL checker
  was not applicable to HTTP localhost; direct local HTTP assertions were used.

## Evidence and Review

See [submitted desktop](screenshots/payment-live/payment-live-submitted-1440.png),
[clinician on Account](screenshots/payment-live/payment-live-clinician-alert.png),
[verified mobile](screenshots/payment-live/payment-live-verified-390.png),
[verified tablet](screenshots/payment-live/payment-live-verified-768.png), and
[actual 200% viewport](screenshots/payment-live/payment-patient-200-percent-viewport.png).

Owner walkthrough: open patient payment instructions and clinician Account in
separate signed-in browsers; submit proof; follow clinician popup to Review Payment;
confirm receipt; watch patient status/alert change without refreshing. Receipt
verification remains distinct from appointment acceptance. Only verify synthetic
payments during demonstration.

No schema/dependency/provider/access/mode changes, data reset or reseeding in this
revision. Inherit v148 fresh/repeat-migration and actual scheduler processing evidence
from `payment-navigation-verification-2026-10-28.md`; no schedule interval or job
registration changed here. No need to repeat hosted calling or unchanged migration
suites. Live email/SMS receipt, physical devices and owner visual acceptance remain
external/manual. No remote deployment or merge.
