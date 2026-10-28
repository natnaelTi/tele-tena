# Translation Workbook Release Readiness — 28 October 2026

**Human language review blocks a localized deployment.** All independent local
implementation, reconciliation, preservation and packaging work is complete.
No workbook draft has been imported or copied into production assets. This is a
review package and a verified technical candidate, not native-language acceptance.

## Identity and Scope

- Runtime/build pin: `569537640665d9dcbb07738523fd49e4c5c5354a`.
- Branch: `feat/offline-telebirr-mvp`; draft [PR50](https://github.com/natnaelTi/tele-tena/pull/50), dependent on draft PR49.
- Final source HEAD may add only this report, guides, test harnesses and screenshots
  after that runtime pin. No rebuild is necessary for those documentation changes.
- Reviewed dictionary SHA256: `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356`;
  zero approved entries in each locale; backend/frontend/source dictionaries match.
- Preview: http://127.0.0.1:8017/teletena/ ; site `teletena-mvp-presentation.localhost`;
  Bench `/home/frappe/frappe/frappe-bench`, Frappe15.121.2 / ERPNext15.121.6 / Python3.12.3; app0.1.0 / current v1.48 schema.
- Compatibility Bench `/home/frappe/teletena-compat/bench`: observed Frappe16.2.1,
  ERPNext16.1.0, Python3.14.2, Node24.13.0; real-backend browser site
  `teletena-payments-v147-fresh.localhost` on8021. These are separate environments.
- Preserves PR43–49 ancestry, existing public/private redesign, onboarding/account,
  reviewed care-language eligibility, Offline Direct Payment and retained wallet
  mode, automatic notification/payment navigation, selectors and all prior MVP work.
- Compared with workbook baseline0529937: no dependency, schema, payment-mode,
  provider/access-setting or business-state transition change. The272 throw-call
  replacements preserve exception classes/arguments; template interpolation follows
  reviewed translation. AST equivalence and focused backend tests cover this change.

## Workbook Result and Approval Package

Original `/home/frappe/tele-tena-dictionary/TeleTena_Translation_Review_Completed.xlsx`
is unchanged. SHA256 `fdf8991a953408ea28f7734e63385c8f1b3b88ec3248a6c9ab8feda7c5ba3495`.
All8,690 source rows match stated05299379183efa0e8f1b599c46c60bd9531d6296:
no missing/duplicate/unknown baseline keys or changed source/hash. Both locales
have8,472 Draft and218 Needs Clarification, zero Approved, no reviewer attribution.
Current catalog8,384 keys /5,419 unique English phrases:351 baseline machine-only
keys excluded;45 newly extracted validation templates need independent review.
No translations were inferred for the new keys.

Private package: `/home/frappe/teletena-translation-release/review-package/`;
transferable ZIP: `/home/frappe/teletena-translation-release/TeleTena-Translation-Approval-Package.zip`.
`SHA256SUMS` verifies its contents; adjacent ZIP.sha256 verifies the archive.
These remain outside Git/public assets with700 directories/600 files.

Working XLSX preserves keys/English/hashes/reviewer states/notes and adds Q:T
validation columns.328 machine-literal corrections in its translation cells are
explicitly logged before/after, with zero linguistic corrections or invented
approvals. Original workbook remains byte-identical. Four legitimate visible
unit/type-specimen/version-prefix entries were retained despite clarification flags.
`source-delta.csv`, `issues.csv`, `delta-review.csv`, `correction-log.csv`, validation,
per-locale preview and attribution audit are included. Header-only approved CSVs
are intentional. Summary counts are committed in
[workbook-review-summary.json](../localization/workbook-review-summary.json).

| Review prompt | Amharic | Afaan Oromo |
| --- | ---: | ---: |
| Locale/script heuristic |93|1|
| Supplied wording specifically flagged in workbook |100|0|
| Clinical/financial terminology |34|34|
| Policy meaning/status review |21|21|
| Product name review |3|0|
| Same-English fallback-conflict rows |19|24|

Counts overlap and include original excluded rows for traceability. They are
review prompts, not linguistic verdicts. Structural placeholder identity/count,
URLs, markup, numeric tokens and paragraph/truncation checks found no failures;
semantic accuracy still requires native reviewers, especially the flagged Amharic
Oromo-like wording, offers versus discounts and credentials terminology.

Smallest remaining action: qualified reviewers independently review each locale,
correct wording/conflicts in the working copy, and enter genuine Approved states
and reviewer attribution only for reviewed values. Review45 new templates from
the delta in context. Run the documented converter/preview/import after approval;
then rebuild and repeat rendered review with a **new immutable pin**. No draft
preview/bypass was introduced. Approval of Amharic cannot import unapproved Oromo.
Policy translation never approves/publishes a policy or changes consent versions.

## Current Verification

Logs retained privately in `/home/frappe/teletena-translation-release/`; no private
records or credentials are committed. All automated delivery used synthetic/mocked
transports; no live SMS/email or real payment was triggered.

| Check | Result / evidence |
| --- | --- |
| Workbook converter |7 tests pass: source/original preservation, independent approvals, malformed input, safety checks |
| Existing CSV exchange |4 tests pass, approved-only import/history/rollback retained |
| Source extraction |2 tests pass; real visible copy retained, machine values excluded by source usage |
| Reviewed runtime |2 tests pass; missing/unapproved values retain fallback |
| Permission/template errors |4 Frappe16 tests pass; class/error code/denial preserved; locale grants no roles |
| Policy projection |3 Frappe16 tests pass; only exact shipped defaults translate, custom content/version/status unchanged |
| Throw rewrite |1 AST equivalence test passes against1dca1ff, expected call targets/imports only |
| Preservation helper |4 tests pass, narrow auditedv1.48 grant exception; unrelated changes rejected |
| Required backup archives |1 test passes with absent/empty/corrupt archive rejection and valid bundle verification |
| Dependency guard |8 tests pass, intended app update only, no shared editable/package replacement |
| Existing professional onboarding |9 Frappe16 tests pass,99 original tables preserved |
| Existing public content |4 Frappe16 tests pass,11 protected tables preserved |
| Offline payment regression |21 Frappe16 tests pass after error/locale integration; no live transport |
| Production build/lint |Locked build passes; lint passes with existing nonblocking warnings |
| Assets/privacy |All manifest hashes and dictionary hash/counts pass; no source maps/config/provider credential leakage |
| Browser candidate |Guest directory/profile → sign-in → exact selected offering calendar; patient/clinician/reviewer Account/admin at en/am/om and390/768/1440; zero browser errors |
| Locale persistence |Navbar transient choice preserved as existing behavior; Account saved preference survives reload, fixture preference restored |
| PWA candidate |Actual service worker on8017: packaged source/hash identity, static-only cache, guest private-history denial, offline fallback and online recovery pass; no live messages |
| Actual200% zoom |Chromium physical1440 / CSS720 / DPR2 / visualViewport1; all three locale policy screens remain scrollable through final document; locale header asserted |

Browser harnesses: `scripts/browser-translation-release.cjs` and
`scripts/browser-translation-zoom.cjs`; run only against isolated synthetic sites
with private existing account manifests. They are evidence of current
provisional/fallback UI, **not** workbook language or owner visual acceptance.
Screenshots under [screenshots/translation-release](screenshots/translation-release/).
Complete36 role/locale/width captures plus policy zoom are retained privately.

Visual inspection: Ethiopic glyphs render without missing boxes; Oromo apostrophes
and long headings wrap; mobile Account cards and desktop reviewer grid retain the
accepted hierarchy. At200% the responsive menu exposes locale controls and long
policy text remains reachable. Known untranslated application-owned labels include
Applications, Expenses Ledger, Revenue Ledger and policy bodies. These are recorded
approval gaps, not accepted fully localized screens. User-authored service names,
people/proper names and invariant units are not automatically translated.

## Migration, Preservation and Reconciliation

Complete native database/public/private/config backup created and verified,
including600 archive files in a700 bundle. The first compatibility-site migrations
applied the already owner-approvedv1.48 reviewer default: exactly3 missing Financial
Configuration grants and3 audit records. Strict preservation detected this first;
a full backup was restored into a disposable isolated database, original protected
hashes verified, and the narrow semantic comparison proved all other stable user,
Auth, private/config, clinical/operational and financial rows unchanged. Scratch
restoration DB removed. No existing account or financial record was reset.

Subsequent native repeat migrations passed strict101-table /18,918-row /9
private/config-file verification. Original snapshot had18,912 rows before the6
expected grant/audit additions. This is transparent inherited patch execution, not
an unreported localization migration. This task adds no schema patch.

Actual presentation site:11 patient owners,2 clinician owners,22 accounts; all
projection/obligation/journal mismatch counts and unbalanced journals zero.
Browser isolated site:2 patient owners,4 accounts; all mismatch counts zero.
Retained guest-first compatibility fixture: one **pre-existing** clinician obligation
mismatch; all financial hashes unchanged from backup, patient/account journals
balanced. It is preserved, not repaired or hidden. The hosted procedure stops on
any real target discrepancy and requires a separate audited reconciliation decision.

Freshv1.48 schema installation, prior populated upgrade/payment-navigation,
notification scheduler, private uploads, individual/couples/hosted LiveKit,
OTP expiry/rate-limit/delivery and PWA safety evidence is **inherited unchanged**
from `payment-navigation-verification-2026-10-28.md`,
`offline-telebirr-verification-2026-10-28.md` and the existing matrix. These expensive
unchanged workflows were not rerun merely for wording extraction. Current tests
cover the changed locale/error/policy/build behavior; this report does not claim
new hosted-call, physical-device, live delivery or native-language acceptance.

## Owner Walkthrough and Hosted Handoff

1. Open8017, choose each interface language and inspect public directory/profile.
   Existing fallback copy remains visible until the language review gate closes.
2. Sign in with retained private patient account, choose an offering, inspect
   booking language versus interface language, Account history/privacy and payment
   instructions. Do not make a real transfer or send provider messages.
3. Clinician: inspect Professional Profile/Credentials/care-language selector and
   payment notifications/Revenue Ledger. Reviewer: inspect application/scope/language
   review, without changing decisions for this localization review.
4. Compare the recorded width/zoom screenshots; review package wording in source
   context. Owner layout acceptance and native-language review remain separate.

Use [selfmade-translation-update.md](selfmade-translation-update.md). It contains
exact baseline/loaded-launcher inspection, init-versus-resume, required verified
backups, dependency identity guard, locked build/public permissions, target-only
repeat migration/preservation, scoped recovery, HTTPS/PWA/hash checks and separate
pre-/post-migration rollback. The pre-outage localization gate intentionally fails
for this technical pin. Unknown/older remote ancestry requires a baseline-specific
plan; no installed Selfmade SHA is invented. Existing Amazon repair, Frappe lock
change, Nginx exception, providers, payment mode, credentials/demo records remain
untouched. No merge, remote deployment or roadmap website update occurred.

External/manual gates: independent Amharic/Oromo approvals (including new source
and conflicts), owner rendered acceptance after import, final policy approval,
consenting live SMS/email delivery and physical-device calls. SMS remains
Ethiopian-only. Interface locales remain separate from approved consultation
languages. None of these is claimed passed by automated fake/synthetic evidence.

The private package also includes `new-source-review.csv` for the45 new keys.
Review this separately through the existing CSV workflow, one locale at a time
with the other blank and genuine attribution in translator_notes. Only change
provisional to reviewed after human review; preview/import separately. Do not
append new keys to the old-baseline workbook or fabricate source hashes.
