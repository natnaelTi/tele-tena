# Transactional Communications and Fictional Service Readiness

## Candidate

Runtime/install pin `02ed9209589732e9d4e3e3750c07c49592c2a327`, branch
`feat/offline-telebirr-mvp`, draft [PR50](https://github.com/natnaelTi/tele-tena/pull/50)
dependent on PR49. Later report-only commits do not change runtime. Preview:
http://127.0.0.1:8017/teletena/ on `teletena-mvp-presentation.localhost`.
The primary preview is Frappe15.121.2/ERPNext15.121.6/Python3.12.3. Changed backend
behavior is also tested on actual Frappe16.2.1/ERPNext16.1.0/Python3.14.2.

## Corrections

Previously the durable transport outbox principally covered appointments/payments.
Application and request/offer events did not consistently enter it; receipt events
notified only one side. Applicants also lacked the workspace bell. These events
now share durable idempotent outbox rows and after-commit enqueueing, backed by the
minute scheduler. A failed enqueue cannot undo an application, booking or payment.
The existing accepted-offer system event remains the single source for its popup.

A real scheduled-worker test exposed an additional defect: UTC appointment/request
expiry values were compared with Frappe's site-local clock at sending time. The
send checks now consistently use UTC; a timezone-offset regression protects this.
No appointment time, financial rule or original record is rewritten by this fix.

| Durable Event | Recipients and Channels | State / Privacy |
| --- | --- | --- |
| Application submitted / resubmitted | Applicant: system, email, SMS | Acknowledges under review and an update within24hours; if still pending a once-only scheduled24hour status update follows, not fabricated approval |
| General application decision | Applicant: all three | Neutral outcome/secure link; individual service/language approval remains separate |
| Scope decision, clarification, suspension, appeal; care-language decision | Affected clinician: all three | Per-decision keys; private rationale/evidence stays behind authentication |
| New eligible open request | Each actual eligible recipient: all three | Recipient authorization rechecked; closed/expired requests do not generate stale external sends; no clinical text in messages |
| Clinician submits offer | Owning patient: all three | Secure request link, no other patient's data |
| Offer selected / explicitly declined / competing offer not selected | Owning clinician: all three | One accepted system event, separate external channels; no competing prices or private offers disclosed |
| Direct booking created | Patient and clinician: external plus existing durable appointment/payment system activity | Accurate payment/confirmation-pending language; never calls unpaid appointment confirmed |
| Payment submitted / verified | Patient and clinician: all three | Durable activity receipts survive fast subsequent transitions; payment verification remains separate from appointment acceptance |
| Confirmed / awaiting acceptance / cancelled / expired | Existing authorized participants: all three | Existing policy, independent couples consent and historical payment mode retained |
| Five-minute reminder | Confirmed appointment participants: all three | Minute scheduler, within five-minute window, unique per current start time; rescheduling/End invalidates stale sends |

Email and SMS remain subject to saved preferences, verified contacts, site/provider
switches, Ethiopian-only SMS support and caps. Disabled preferences are preserved.
Account → Notifications now shows verified contacts and delivery activity. An
owner can verify a missing email/mobile using the existing random, expiring OTP
transport without creating another account, switching identity, replacing an
existing contact or granting roles. Unknown provider outcomes are not blindly
resent. Explicit safe retry is limited; Provider Accepted is **not** Delivered.

Emails now use an escaped responsive TeleTena HTML composition, bilingual brand,
neutral authenticated CTA, privacy footer and the existing demonstration ribbon,
with a plain-text alternative. OTP emails use the same visual system. No tracking
pixel, external imagery, permanent authentication token or clinical data is added.

## Ready-to-Use Fictional Services

Explicit additive command, separate from full dataset seeding:

```bash
bench --site SITE execute tele_tena.demo_readiness.setup --kwargs '{"dry_run":true}'
bench --site SITE execute tele_tena.demo_readiness.setup --kwargs '{"dry_run":false}'
```

Use the current external Bench CLI on Selfmade; see the updated deployment guide.
This CLI-only Administrator operation requires a review-enabled, non-real-money
site and the matching existing `tt-demo-mvp-v2` ownership/account manifests. It
refuses unrelated clinicians, missing datasets and conflicting existing decisions.
It never enables access/providers, seeds accounts, refreshes appointments, adds
funds, resets passwords or revises historical transactions. Protected identity,
configuration and financial hashes are checked inside its transaction. External
fixture notices are suppressed, so readiness creates no bulk email/SMS sends.

All ten shipped adult demo definitions now have an approved fictional provider,
individual scope evidence/decision, approved care languages, published offering,
receiving-number readiness and published calendar on the local presentation site:
initial/ongoing psychotherapy, individual counseling, stress/adjustment, grief,
relationship, premarital, separation, psychiatric assessment/follow-up. Normal
profession eligibility and individual versus couples rules remain authoritative.
Prices are centrally defined illustrative values in `demo_readiness.SERVICES`.
Approval/source/audit text explicitly identifies a fictional demonstration exercise;
it makes no real licensing, external-verification or clinical-readiness claim.
New applicants still need their own human general/scope/language reviews. Fresh
request presence still requires an authenticated active clinician workspace.

The setup was run twice on the existing presentation site: ten ready services,
no duplicate approvals/offerings/schedules and no credential/financial changes.
It does not overwrite existing published schedules or extend their dates on every
run. Existing real/manual decisions are preserved; ambiguous ownership stops
rather than adopting records. Nothing was applied to Selfmade.

## Verification Performed

Private logs, fixtures, verified backups and unsanitized synthetic browser captures:
`/home/frappe/teletena-communications-release/` (outside Git).

- `final-backend.log`:30 real-database tests pass (21 retained Direct Payment plus9
  communication/readiness regressions). Includes state/privacy, explicit decline,
  accepted/superseded offers, retries, once-only reminders, offset clocks, MIME
  escaping, and twice-run protected-state readiness. Outbound adapters are mocked.
- `final-contacts.log`:5 pass: account-bound OTP, cross-account/public-login denial,
  wrong/expired/single-use/resend guards, existing identity/roles preserved, Ethiopian
  SMS restriction. `legacy-notifications.log`:10 retained tests pass against current
  source, with current language eligibility explicitly established in fixtures.
- Built browser: new seven-section clinician registration/submission and two scope
  requests; private attachments/reload; independent reviewer clarification and
  general approval; actual verified-contact addition; persisted preferences,
  owner-only activity, notification dialog, Escape/focus restoration.
- Built browser: guest directory/profile → exact offering/auth return → calendar →
  direct receipt submission → separate clinician verification → confirmed appointment
  → ledgers. Also guest request/auth/draft → publication → two private clinician
  offers → patient acceptance → receipt → verified confirmed appointment.
- Native isolated Frappe scheduler and subscribed worker automatically enqueue and
  execute dispatch/reminder jobs, including after worker restart. A newly created
  browser appointment alone receives controlled test timing. Two once-only in-app
  reminders and two test-accepted emails result. Its accounts lack verified mobile
  contacts, correctly producing Unavailable with zero SMS attempts. A separately
  OTP-verified applicant receives test-accepted email **and** SMS for submission,
  general approval and scope clarification. A second current-build Requests browser
  verifies both contacts for its isolated accounts: new request, received offers,
  selected and not-selected outcomes all reach test-accepted email and SMS exactly
  once (`request-worker-outcomes.json`). No live provider sends occur.
- Additive upgrade/repeat: restored Frappe16 clone preserves102 original protected
  tables/18,112 original rows/private/config files; earlier v1.50 recovery adds only
  two omitted selected scopes. Strict repeat passes. Retained sites untouched.
- Primary presentation: complete database/public/private/config backup, migration
  and repeat preserve102 tables/18,810 original rows/25 private/config files.
  Read-only owner reconciliation after readiness checks11 patient owners,2 clinician
  owners,22 accounts: zero projection/obligation/journal errors. The compatibility
  dataset's previously known legacy discrepancy is preserved, not silently repaired.
- Locked production build, lint (existing nonblocking warnings), asset hashes/private
  credential scan,5 localization exchange and2 extraction checks pass. No dependency
  or framework/Amazon changes. The final asset check compared20 privately stored
  credential values without printing any value; none appears in public assets. New schema is only additive v1.51 outbox context and
  OTP account binding; no wallet/ledger or provider-setting changes.
- Responsive screenshots390/768/1440 and actual Chromium200% zoom (1440 physical,
  720CSSpx,DPR2,visualViewport1), keyboard dismissal and reduced motion inspected.
  Existing grouped settings/bell/dialog language is reused; email composition
  inspected in a browser, not claimed tested in physical mail clients.

Existing hosted individual/couples media, notes/recipient isolation, immutable
finance and wider permission suites are inherited unchanged from their named MVP
reports; they were not all rerun for this communication-only revision. Current
payment/browser tests cover the changed notification boundaries. Fresh bootstrap
includes v1.51, but a brand-new native site install was not repeated for this patch.

## Review and Remaining External Work

1. Use existing private account manifest; no password changed. Account → Notifications:
   check both preferences, verify missing contacts, expand delivery status.
2. New clinician submits; check bell acknowledgement. Reviewer records general and
   individual scope/language decisions; clinician receives neutral linked updates.
3. Create request with a freshly present eligible clinician; submit/accept or decline
   an offer. Follow direct payment and clinician verification; inspect both bells.
4. With consenting actual recipients, test configured SMTP/SMS separately. Inspect
   provider outcomes and handset/inbox receipt, not merely API acceptance. SMS remains
   Ethiopian-only. Five-minute reminders require a confirmed future appointment and
   running subscribed workers/scheduler.
5. Browse the local directory; demo services are ready without another catalog-review
   exercise. Clinician still opens their workspace to establish fresh presence.

Owner visual acceptance, native-language approval, physical-device calling, live
message receipt and production clinical/legal approval remain separate. Translation
reviewed hash remains `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356`;
no draft or invented human approval was imported. Full UTF-8 CSV and communications
source delta are in `localization/`; genuine per-locale approval remains outstanding.

See [screenshots](screenshots/communications/README.md) and
[incremental update/backup/rollback](selfmade-translation-update.md). No merge,
remote deployment, payment-mode change or public roadmap website update occurred.
