# Offline Telebirr MVP: Local Verification — 28 October 2026

Runtime/build pin: **d553253d8dc24681ceaa5cd71c9bc6881fe46483**.
Branch `feat/offline-telebirr-mvp`, dependent on draft PR49 at
`24baa364c65d666db7c4f35e69ef3a35ee4e8a56`. Later evidence/guide-only commits
do not change the packaged runtime. No merge or remote deployment occurred.

## Environments and Preservation

| Environment | Observed Configuration | Result |
|---|---|---|
|Retained review|`/home/frappe/frappe/frappe-bench`, site `teletena-mvp-presentation.localhost`, Frappe15.121.2/ERPNext15.121.6, Python3.12.3, production-built port8017|HTTP200; scoped web/worker/scheduler recovery; original payment mode remains Wallet|
|Target-compatible|`/home/frappe/teletena-compat/bench`, Frappe16.2.1/ERPNext16.1.0, Python3.14.2, Node24.13.0, MariaDB10.6.22, Redis6.0.16|Native install/migrate and real-backend browser tests; no framework/shared package repair|
|Disposable browser|`teletena-payments-v147-fresh.localhost`, loopback8021, latest packaged assets|Separate synthetic accounts, private random OTP and notice transports; both payment modes exercised|
|Fresh combined schema|`teletena-payments-v147-candidate.localhost` before subsequent clone reuse|Fresh install and two native migrations;630 languages/78 domains; payment mode Wallet, registration/provider switches off, evidence/payment tables empty; couples language column present|
|Populated upgrade clone|Same named candidate, restored only after verified empty-site check from preserved pre-upgrade fixture backup|69 original tables/1,225 rows/7 private-config files unchanged by hashes; repeat migration87 tables/17,425 rows/7 files unchanged|
|Retained presentation migration|Writers stopped; complete native SQL/public/private/config backup|87 protected tables/18,431 original rows/25 private-config files unchanged, including credentials/preferences/financial history|

Fresh installation evidence predates the final copy/submission fixes; no schema
changed afterward. Those runtime changes were checked separately. Native Frappe
`migrate` ran with the current app imported, not the older compatibility checkout.
The final clone and presentation checks compare original column/row hashes and
private-file/config hashes without printing values. No original demo account was
reseeded, no balances/passwords reset, and no provider/access switch was changed
on the retained preview. Existing language declarations become Pending claims;
reviewer approval is a deliberate cutover prerequisite, not fabricated migration.

## Executed Checks

| Check | Actual Evidence and Result |
|---|---|
|Direct-payment backend|`tests/direct_payments.py`:17/17. Both modes, stale revision/admin denial, historical transition plan, private/unknown/foreign receipt denial, late/mismatched proof, immutable correction, reused transaction, refund acknowledgements, individual finalization, couples payer/consent/language isolation, extra extension payment, reminder idempotency. Real MariaDB; per-case rollback. Provider/media dependencies mocked where stated.|
|Professional records|`tests/professional_onboarding.py`:9/9; identity assignment/access, credential evidence/history, directory paging/Other/deduplication, required validation; repeat/additive migration99 original tables unchanged by hashes.|
|Concurrent connections|Independent database connections: competing booking retry → one appointment/intent; competing proof → one receipt/event; competing verification → one receipt decision; no Wallet postings for direct payment. Private `concurrency-result.json`.|
|Direct booking browser|Guest directory/profile → exact selected offering after password sign-in → saved Amharic consultation preference → backend calendar → Offline instructions → private receipt → separate clinician verification/manual acceptance where applicable → Booked → payer reload/ledgers. Guest receipt denied. Captured390/768/1440. Repeated on final runtime.|
|Open-request browser|Guest draft → sign-in → preserved request/publication → two fresh eligible clinician inboxes → mutually private offers/foreign-offer denial → patient selection → receipt → clinician verification → Booked/reload. Ran on2c783d2; later changes concern onboarding and copy, not request/payment logic.|
|Retained Wallet browser|Current built app: shortfall disables confirmation; supported demonstration deposit; Check Balance Again; reservation and automatic booking; reload. Historical Offline activity remains readable across the audited mode transition. No real funding.|
|Full clinician onboarding|`scripts/browser-offline-onboarding.cjs`: new random email OTP; profile/private Passport/CV, language self-assessment, qualification/issuer/Other authority, credential retry, date validation, competency rating without uploader, pending clinic, declaration/scopes, reload and completed application. Applicant role only; no general/scope/language approval invented.390/768/1440.|
|Onboarding sign-out|Private random OTP; signup has no password alternative; saved draft→sign-out→server session invalidated/protected Back denied→same-user sign-in resumes; explicit discard preserves the earlier saved value. Failed upload/save retains entered data in full onboarding.|
|Automatic jobs|Actual one-site native scheduler and subscribed default/short/long RQ worker on isolated Redis16680. Controlled owned fixture clocks only. Payment midpoint, verification midpoint, expiry and dispatch executed automatically; no direct invocation substituted for scheduler acceptance.|
|Worker recovery|Stop only owned worker; native scheduler queued11 jobs with0 workers; restart → original pending work processed; one PaymentReminder per final intent and one provider-accepted email attempt. Existing reminder not duplicated. Separate verification reminder also one. See [sanitized job evidence](offline-telebirr-scheduled-evidence.json).|
|Financial reconciliation|Retained synthetic financial site:20 Wallet owners,0 owner-projection differences,0 unbalanced journals,0 financial-account/journal projection differences;8 owners with historical reserved balances preserved. Offline browser payments add no Wallet custody/earning; receipt finalization does not post a second credit.|
|Localization|4/4 source-only exchange tests: Unicode/newline/formula round-trip, duplicate/unknown/stale/hash/placeholder rejection, provisional import exclusion, reviewed version history/rollback. Deterministic export;8,607 owned-source entries;4,271 missing per non-English locale;0 marked human-approved. No database/user records exported.|
|Build/lint/assets|Production build and lint exit0. Existing lint warnings and large-chunk build warning remain; no new framework dependency. Narrow Vite8.3.1→8.3.3 security patch; no other locked frontend package version changed; npm audit0 known vulnerabilities at build. Asset hashes/scope/private credential scan pass (20 private values checked, none exposed). Python compileall and service-worker tests pass.|
|Responsive/zoom|Affected patient, clinician, reviewer and authorized financial configuration pages at390/768/1440; actual Chromium200% zoom (`innerWidth=720`,DPR2,visual viewport scale1 at1440 physical pixels), keyboard-compatible native/select/details controls and retained scrolling. CDP viewport captures used because ordinary Playwright screenshot clipping misrepresents real browser zoom.|

Private full logs, generated OTPs, receipts, sessions and manifests remain under
`/home/frappe/teletena-offline-sprint` (restricted). None are committed. Only
synthetic rendered UI and sanitized aggregate state evidence are in Git.

Reproducible browser harnesses are committed as `scripts/browser-offline-*.cjs`.
They target only loopback8021 and read the private isolated test manifest; never
point them at a hosted site. `prepare_offline_test_site.py` refuses a nonempty
profile dataset. The Wallet harness requires its explicit, audited local mode
transition; it must not toggle a presentation/hosted site implicitly. Tests that
share a fixture database ran sequentially. Provider transport interception is
restricted to the dedicated site/test domains and is not a deployment entrypoint.

## Defects Found and Fixed During Verification

- Initial direct-payment intents emitted booking-style status too early. They now
  emit payment intent facts, with no confirmation timestamp/charge implication.
- Manual appointment acceptance now starts its timer at verified payment, and
  remains separate from the receipt decision. Repeated decisions do not add events.
- Cross-tab identical proof is deduplicated even with a different client nonce;
  deliberate correction resubmission still creates immutable evidence history.
- Legacy mixed-collation joins use exact binary identities where necessary;
  private/unknown receipt access returns the same denial boundary.
- Unpaid expiry no longer produces an unnecessary payment-reconciliation notice.
  Historical direct activity remains accessible in Wallet mode.
- Couples invitations preserve the actual selected care language; legacy unbooked
  invitations need a renewed invitation/consent, never a guessed language.
- The new clinician submission language check accidentally called a local SQL
  result named `rows`. It now executes the correct dict query; full browser
  submission passes. Missing self-assessment has specific corrective guidance.
- Remaining active reviewer/tour labels use Credentials/CV, retaining old storage
  names and translation keys for compatibility.

One request rerun correctly found no feasible supply because the test patient
already had an overlapping newly booked appointment. Tracing both clinician and
patient conflicts confirmed that hard constraint. Repeating with the separate
unoccupied adult test account passed; no eligibility rule was weakened.
An older long-lived test worker had retained pre-fix reminder code. It was
restarted before final fixture/recovery acceptance; earlier events were retained,
not deleted to manufacture a pass.

## Visual Comparison and Approved Extensions

Paired screenshots are in [screenshots/offline-telebirr](screenshots/offline-telebirr).
The reference remains outside the repository at
`/home/frappe/teletena-design-reference`; captures use the exact rendered hashes.

| Reference / Current State | Inspected Comparison |
|---|---|
|B06/B07 professional steps → new application|Retained compact guided column, blue headings, bordered fields and progressive steps. Credentials rows, contextual private upload instructions and issuer priority are added operational states. Existing expanded seven-step flow supersedes the older two-screen prototype; no credential verification is inferred.|
|H02 → clinician Account practice|Retains cards, professional heading/field hierarchy and practice links. Previously accepted section navigation remains; receiving number/language assessment extend its shared surfaces. No duplicate photo editor. Long evidence/language history scrolls rather than being clipped.|
|I03 → application Private Documents|Retains reviewer step navigation, bounded panels and separate decision stage. Individual language rationale/evidence controls sit before professional evidence. Mobile steps wrap; native fields/details remain operable. ID access is explicitly assigned, not granted to all reviewers.|
|C06/C08/D06 → calendar/booking/offer payment|Calendar and disclosure composition retained. The new Offline instructions replace Wallet custody wording with a claim/verification surface; explicit amount/payee/deadlines/history and authorized next-step link. This new payment state has no literal prototype counterpart; no pixel-equivalence claim.|
|H01/H02 financial activity → Expenses/Revenue Ledgers|Shared bordered cards/labels and readable status totals, with historical Wallet link. No fictitious amount/rating was copied from the reference. Pending, verified and refund states remain distinct.|
|Financial configuration → new permission-scoped screen|Existing minimal shell/guided-panel/fields, clear mode explanation and transition-plan warning. No existing reference screen for this new administrative decision. Desktop content is bounded;390px stacks cleanly.|

Codex inspected rendered composition, hierarchy, control states and readable
wrapping separately from functional tests. Available controls remain reachable by
scrolling at mobile/200%; no no-scroll claim at those sizes. Full-page captures
can show sticky navigation at the capture scroll position; viewport captures
record its actual fixed placement. The accepted two-column consultation stage was
not redesigned. Owner visual acceptance is still pending.

## Remaining Human and External Gates

- Explicit administrator role assignment/mode selection, operational deadline and
  reconciliation/refund procedure approval. No automatic Selfmade switch.
- Actual clinician receiving-account checks and consenting live transfer/refund
  tests; screenshot submission and recorded human verification do not prove a
  provider-settled payment. No commission/custody/payment rail activated.
- Clinical-owner review of proposed competency vocabulary, language self-rating
  scale, seven curated priority entries and individual existing care-language
  claims. New offerings need approved languages. No automatic grandfather approval.
- Human Amharic/Afaan Oromo translation/layout review; policies remain review
  content until formally approved. Directory data coverage gaps remain disclosed.
- Consenting live SMS/email receipt and physical-device calls remain separate.
  Existing hosted LiveKit individual/couples tests from the prior accepted release
  are inherited; this sprint's targeted media adapters use fake tokens/devices
  and do not re-establish hosted token revocation or physical hardware behavior.
  The room/End/revocation core was not changed.
- Owner acceptance of new states and final visual comparisons. No automated check
  substitutes for that decision.

Use the [operator walkthrough](offline-telebirr-operator-walkthrough.md),
[translation exchange](localization-review-guide.md), and
[Selfmade update/backup/rollback procedure](selfmade-offline-telebirr-update.md).
No public roadmap website or remote configuration was changed.
