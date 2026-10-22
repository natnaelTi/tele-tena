# Clinician Onboarding and Contextual Access — 22 October 2026

Bounded follow-up to public redesign PR48; branch `feat/clinician-onboarding-context`.
Baseline source `25fa5acbfe0acd513e2bf0c138de5f8aada65578`, packaged/owner-confirmed
`f679e6ce8a1a8169b9bba16626a2880e5e212a75`. No merge, remote deployment, existing
scenario reseed, provider/access change or shared dependency repair is authorized.

The existing MVP matrix remains authoritative. This document is the field-level
extension of its `clinician_onboarding_context_revision` entry, not a replacement.
The approved design language remains unchanged; these grouped operational states
extend professional application B06/B07 and scope/reviewer states in that matrix.

| Section / Field | Persistence and acceptance | Current result |
|---|---|---|
| Prefix / First / Last Name | Applicant confirms structured values. No legacy-name splitting. Display derived on explicit submission; historical appointment/disclosure snapshots unchanged. | Functionally verified; rendered comparison recorded below |
| Profession / optional Specialties | Separate typed directories, server search/paging, aliases, keyboard-native selection/removal, Other and retained selections. No scope authorization. | Implemented; backend checks pass |
| Bio | 50 Unicode-whitespace-delimited tokens; hyphenated terms remain one token. Same JS/Python rule; live count, no truncation. Existing biography retained until edited. | Implemented; backend limits pass |
| Identification | National ID / Driver’s License / Passport, validated private PDF/JPEG/PNG. No number. Owner and explicitly assigned credential reviewer only. | Implemented; owner/ordinary-reviewer/cross-role denial passes |
| Qualification | Related specialty area and actual awarded title separate. Issuer and country independent of practice jurisdiction. | Functionally verified; rendered comparison recorded below |
| CV / certifications | CV PDF; repeatable certification title, description, issuer, dates, files. Unselect/remove does not delete historical evidence. | Functionally verified; rendered comparison recorded below |
| License | Number, jurisdiction, selected/manual authority, consecutive Valid From / Valid Until, explicit non-expiring option, private files. | Implemented; server date validation passes |
| Competency domains | Configured domains, explicit applicant rating, definitions, optional explanation/evidence. Unchecked is absent; no default proficiency. | Implemented; backend tests pass |
| Affiliations / declaration | Independent and multiple native/imported facilities; inline pending facility and reviewer deduplication. No staff/record grants. Versioned affirmative accuracy declaration and retained adult eligibility. | Functionally verified; owner acceptance pending |
| Service scope applications | Applicant-led multiple selection, existing individual pending/approved/declined/clarification and evidence decisions remain authoritative. General approval never approves scopes. | Six focused scope regressions pass; separate human decisions preserved |
| Reviewer | Structured private claims, certification rows, source/date fields, evidence, immutable submission digest/version; IDs redacted without specific assignment. | Implemented; backend denial passes |
| Contextual authentication | Patient/clinician sign-in and verification-first signup; one contextual creation link, no signup password alternative; allowlisted return intents retained. | Functionally verified; rendered comparison recorded below |
| Country display | Flag + code collapsed; full country identity in native options/accessibility; Ethiopian-only SMS unchanged. | Functionally verified; rendered comparison recorded below |
| Required fields / Title Case | Shared required markers tied to actual required semantics; static heading-copy edits and translation aliases replace broad CSS capitalization. User/proper/localized values untouched. | Shared primitives implemented; 46-route rendered survey passes; owner acceptance pending |

## Private Models and Review Boundaries

Additive v1.44: `tt_reference`, `tt_professional_draft`, immutable
`tt_professional_submission`, `tt_professional_evidence`, and per-clinician
`tt_identity_reviewer`. These app-owned tables have no generic DocType/file/report
API. Evidence download checks authorization every time and returns no-store,
attachment/nosniff/sandbox headers. No public projection includes these fields.
Uploads reuse the medical-history parser restrictions, 5 MB/file and image checks.
Technical limits: 200 certification rows/application, 100 domains or selected
references/group, 2,000 total file references/submission, 1,000 retained files and
250 MB evidence/owner. These are abuse/
performance limits, not a clinical-history policy. Removal deselects evidence;
submitted versions and content hashes remain. Identity-document retention/deletion
policy requires explicit governance review; no automatic destruction is invented.

Self-rating scale v1 is a proposed applicant instrument (1 introductory exposure,
2 supervised practice, 3 independent within scope, 4 substantial advanced practice,
5 supervises/trains within scope). It is separate from the existing Medical Lead
rubric and mandatory evidence gates. No scores affect approval/ranking automatically.

## Actual Reference Coverage

See `tele_tena/reference_data/manifest.json`. Combined unique bundled coverage:
8,362 education/issuer organizations, 7,034 healthcare/facility organizations,
30 professions, 32 specialties, 14 proposed competency domains and 8 authorities.
The Ethiopian subset contains 64 issuer organizations, 9 facilities and one
responsible-ministry authority entry. Existing native clinics are additional,
with their existing verification states preserved.

ROR CC0 v2.15 (20 October 2026) supplies the organization records across 194
countries. The first archive download was interrupted; only 48,133 complete valid
JSON records from its prefix were processed. A supplementary Ethiopian API pass
retrieved 126 unique records despite a reported total of159; duplicates/omissions
across pages prevented a completeness assertion. Education/healthcare types are
filtered into distinct roles. ROR membership is not accreditation or proof that an
institution awards every qualification. Configured profession/specialty/domain
vocabulary is source-informed and awaits professional review. The eight regulator
entries are initial sourced coverage, not a comprehensive regulatory directory.

Sources and permissions:
- [ROR data/CC0](https://ror.readme.io/docs/data-dump) and
  [source release](https://zenodo.org/records/23500708).
- [Ethiopian MOH MFR developer access](https://mfrpublic.moh.gov.et/developers)
  requires approved API access and confirmed permitted reuse. Not scraped.
- [WDOMS terms](https://www.wdoms.org/terms/) prohibit unrestricted scraping/reuse;
  [subscription](https://www.wdoms.org/subscription/) requires permission. No import.
- Official regulator URLs accompany individual records; no institution-to-regulator
  mapping or authority assignment is inferred.

`python scripts/import_professional_references.py source.zip new-version.json.gz`
normalizes a CRC-checked full ROR archive; output must be a new versioned bundle.
The migration imports bundles idempotently with stable source IDs, never overwrites
reviewer edits/merges or existing references. Directory reviewer merges retain old
IDs and snapshots; updates to imported metadata require a reviewed new bundle/change
rather than silently rewriting existing decisions. Facilities entered by applicants
remain owner-selectable pending names until review; native clinic confirmation and
membership remain separate. Manual institution/authority entry remains usable.

Extensive Ethiopian facility coverage and comprehensive professional-regulator/
awarding-body data remain external data-access/curation dependencies. Search/import
architecture is implemented; these missing datasets are not marked complete.

## Candidate and Verification

Packaged runtime: `6a3fb4df2cc73bbb11480f1853ef80ed439e2366`. Later evidence/test-only
commits do not require another runtime build. Preview remains
http://127.0.0.1:8017/teletena/ on `teletena-mvp-presentation.localhost` in
`/home/frappe/frappe/frappe-bench` (Frappe15.121.2/ERPNext15.121.6/Python3.12.3).
The isolated compatibility bench `/home/frappe/teletena-compat/bench` uses
Frappe16.2.1/ERPNext16.1.0/Python3.14.2/MariaDB10.6 and explicitly imports this
branch's backend; it is not the preview's older app checkout.

| Check | Actual result / evidence |
|---|---|
| Backend state, permission and migration | `tests/professional_onboarding.py`:9/9 pass on Frappe16. Full-row hashes preserve89 original application/auth tables; repeat migration unchanged. Private ID owner/assigned reviewer/revocation, ordinary reviewer/patient/cross-owner denial, file validation, immutable versions, retry, bio/dates/ratings, facility review, scope license reuse and patient/clinician step separation. |
| Fresh combined schema | Final runtime6a3fb4d: Frappe16+ERPNext16+TeleTena installed on `teletena-onboarding-v144-final.localhost`; two native migrations pass, legacy-name/reference-snapshot columns present, private application tables empty, full bundled directory imported and registration/provider switches off. Earlier fresh-v144 fixture evidence is retained separately. |
| Existing scope workflows | Six focused Presentation tests pass: draft/clarification/resubmission, initial claims, atomic multi-scope intake, three distinct scope decisions→discovery/inbox, Medical Lead catalog gate, credential expiry/reverification. Fixture explicitly uses invited-review settings; no weakening of the production policy. |
| Registration browser | `browser-professional-onboarding.cjs`:real randomized test-transport OTP, wrong/expired/resend/retry; new clinician seven-step journey, private ID/CV/certificate, invalid-file retry, concurrent typing/upload retention, issuer/Other authority, invalid-date correction, explicit self-rating, inline pending clinic, scope interests, declaration and policy acceptance. Reload persists certification. Submission creates Applicant only.390/768/1440. |
| Reviewer browser | `browser-professional-review.cjs`:same newly registered applicant; structured claims/dates/certification/CV download, ID redaction, human general approval, clinician scope workspace; no scope auto-approval.390/768/1440. |
| Contextual auth | `browser-contextual-access.cjs`:existing clinician→application; clinician entering patient context receives explicit denial without role mutation; patient→dashboard; existing Medical Lead→rubrics; external next URL ignored. |
| Guest return regressions | `browser-public-experience.cjs`:real directory/filter/profile→password→exact selected offering and reload; volatile guest request→auth→request workspace with no publication/storage leakage; clinician application intent; reduced motion and provisional locales. |
| Keyboard and actual zoom | `browser-professional-accessibility.cjs`:Chromium extension sets actual200% (inner720, DPR2, visualViewport1); patient/clinician registration never offers password; five persisted application sections; native directory keyboard/Escape/focus; empty and failed real query/retry retain selection. A single query is aborted for failure testing, never mocked as a success. |
| Shared route regression | `browser-mvp-polish.cjs`:46 real-backend role/route views at390/768/1440; navigation/deep links and page width. This survey is functional/layout evidence, not universal visual acceptance. |
| Build/lint/assets | TypeScript/production build passes; lint has existing hook/purity warnings, no errors. `check_review_assets.py` verifies all packaged hashes/scope/no source maps/config files and scans20 private credential values without printing them. No package/lockfile dependency changes. |
| Retained private state | Original presentation config and24 original provider/key/account manifest files byte-identical; database/public/private-file backup was verified before migration. No balances, credentials, preferences, scope grants or existing scenarios reset. |

Private detailed logs are under `/home/frappe/teletena-onboarding-sprint` (mode700).
No codes, session cookies or credential manifests belong in repository evidence.
The OTP transport exists only on loopback8021 and the named disposable test site;
normal expiry/HMAC/single-use/rate controls remain. Deliberately expiring the one
synthetic challenge tests recovery without changing the system clock or production
rows. Test registration/review settings were restored byte-for-byte after checks; caches cleared, loopback transport stopped and captured codes/session cookies removed.

New patient registration and unchanged consultations/couples/financial concurrency
retain their earlier evidence in the main matrix; this sprint does not claim a
fresh hosted-call or financial end-to-end run. No live SMS/email receipt, physical
device calling, native-language approval or owner visual acceptance is asserted.

## Rendered Comparisons and Specific Exceptions

Evidence: `docs/screenshots/clinician-onboarding-context/`. Each B06/B07 comparison
uses the same viewport, zoom and English locale. The source reference remains
outside the repository; only rendered evidence is included. Existing application
before images use the owner-confirmed f679e6ce build; after images identify the
runtime above (earlier new-registration capture at a6ed9de differs only by required
label accessibility/CV hints and reviewer wording; final reviewer/zoom use6a3fb4d).

| Reference → route/state | Inspected composition and result |
|---|---|
| B06 → `/onboarding?intent=clinician`, profile | Retains narrow wizard, logo, progress, blue/teal fields and heading hierarchy. New structured names, searchable directories and private ID intentionally extend the older full-name prototype. Search panels are collapsible and retain selected chips. Desktop/mobile inspected. |
| B07 → qualification and license steps | Reference combines qualification/license/CV. This approved revision deliberately separates qualification/certifications from license, with repeatable evidence and paired dates. Same field/card language, readable mobile stacking. No silent credential equivalence or license assignment. |
| B08/B09/B10 → competency/affiliation/scopes/final declaration | Older prototype has shorter affiliation/final-review states; domain ratings and pending clinic intake are documented operational extensions. No dummy proficiency/verified affiliation is copied. |
| I02/I03 → `/admin/applications/:opaqueId`, private documents/decision | Structured claims and self-ratings remain distinct from reviewer verification. Existing guided review and individual scope decisions retained; identity evidence remains redacted absent explicit assignment. Long content scrolls, mobile values wrap/stack. |
| A02/A03 → `/sign-in?intent=patient|clinician&mode=register` | Current approved minimal OTP-first shell retained; contextual heading/action, country flag/code, one creation/sign-in switch. Public marketing shell and obsolete account-type chooser are not reintroduced. |
| Existing `/clinician/vetting` and Account editor | Same five groups reused inside current accepted workspace; historical claims are labeled, not deleted. Actual200% screenshots use browser/CDP capture, not CSS zoom or a clipped full-page zoom capture. Dismissible tour remains available. |

Visually inspected by Codex: profile1440; qualifications390; license1440;
competencies390; affiliations/mobile; reviewer768 and390; contextual signup;
actual200% form/controls. New fields are approved functional extensions, not a
claim of pixel equivalence to obsolete full-name/combined-qualification forms.
Owner acceptance remains pending. Amharic/Afaan Oromo core new labels are
provisional; some extended guidance falls back to English pending translation.

## Preservation and Operations

v1.44 is additive: new app-owned tables, one nullable scope-submission reference,
and safe widening of short native credential fields. Legacy full names are never
split. The exact prior name is retained when an owner first edits/submits a
structured name; historical appointment/disclosure snapshots are unchanged.
Submitted claims include immutable evidence hashes and reference-source metadata.
Legacy CVs and free-text qualifications/competencies/certifications remain readable.
A removed row/file selection does not delete evidence referenced by earlier review.
Only an explicit owner action reuses a License PDF in an individual scope
application; ID evidence cannot enter that path. New claims do not create scope
approval, verification, ranking or clinic privileges.

Backup (private): named22October database plus public/private archives under the
presentation site's private/backups; validated gzip/tar/nonempty archives and
protected checksums recorded before migration. Never apply a code-only rollback
as a database reversal. No Selfmade update is authorized in this sprint.

Preview controls, from the repository, with the native bench Python:
```sh
/home/frappe/frappe/frappe-bench/env/bin/python scripts/local_review.py status
/home/frappe/frappe/frappe-bench/env/bin/python scripts/local_review.py start
/home/frappe/frappe/frappe-bench/env/bin/python scripts/local_review.py stop --keep-queue
```
These address the identified isolated preview services; they do not start the
original development site's web process or modify shared hosted services.

## Owner Walkthrough and Remaining Dependencies

1. Open the preview. Patient/clinician entry keeps its contextual sign-in/signup
   heading. Existing invited-review access policy remains; enabled registration
   was tested only on the isolated test configuration.
2. Clinician: Account→Professional Profile or Professional Review. Confirm names
   yourself, search profession/specialties/issuer, add a certification and private
   evidence, enter a license or explicit non-expiry, select and rate domains,
   select/add a pending clinic, save draft, reload, submit an accurate update.
3. Service applications remain below/in their existing section. Apply to multiple
   scopes and explicitly select supporting license evidence. General approval
   does not authorize them. Each reviewer decision still needs its own evidence.
4. Reviewer: Applications→named application→Private Documents. Inspect structured
   claims and certification rows; ordinary review cannot open identity evidence.
   Medical Lead assignment requires a reason and is separately auditable.
5. Directory/facility review accepts a catalog name or merges a duplicate while
   preserving referenced IDs. Clinic verification/affiliation confirmation remain
   separate, and no patient access follows from affiliation.

External/human work: approved MFR access/reuse, broader regulator/awarding-body
coverage, clinical vocabulary/self-rating review, identity retention governance,
native-language review, live consenting delivery/device checks and owner acceptance.
These are not marked passed. No invented institutions, credentials, regulatory
verification or clinical approval fills a gap.
