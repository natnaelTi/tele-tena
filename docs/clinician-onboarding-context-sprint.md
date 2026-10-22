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
| Prefix / First / Last Name | Applicant confirms structured values. No legacy-name splitting. Display derived on explicit submission; historical appointment/disclosure snapshots unchanged. | Implemented; browser verification pending |
| Profession / optional Specialties | Separate typed directories, server search/paging, aliases, keyboard-native selection/removal, Other and retained selections. No scope authorization. | Implemented; backend checks pass |
| Bio | 50 Unicode-whitespace-delimited tokens; hyphenated terms remain one token. Same JS/Python rule; live count, no truncation. Existing biography retained until edited. | Implemented; backend limits pass |
| Identification | National ID / Driver’s License / Passport, validated private PDF/JPEG/PNG. No number. Owner and explicitly assigned credential reviewer only. | Implemented; owner/ordinary-reviewer/cross-role denial passes |
| Qualification | Related specialty area and actual awarded title separate. Issuer and country independent of practice jurisdiction. | Implemented; browser verification pending |
| CV / certifications | CV PDF; repeatable certification title, description, issuer, dates, files. Unselect/remove does not delete historical evidence. | Implemented; browser verification pending |
| License | Number, jurisdiction, selected/manual authority, consecutive Valid From / Valid Until, explicit non-expiring option, private files. | Implemented; server date validation passes |
| Competency domains | Configured domains, explicit applicant rating, definitions, optional explanation/evidence. Unchecked is absent; no default proficiency. | Implemented; backend tests pass |
| Affiliations / declaration | Independent and multiple native/imported facilities; inline pending facility and reviewer deduplication. No staff/record grants. Versioned affirmative accuracy declaration and retained adult eligibility. | Implemented; browser/reviewer acceptance pending |
| Service scope applications | Applicant-led multiple selection, existing individual pending/approved/declined/clarification and evidence decisions remain authoritative. General approval never approves scopes. | Preserved; focused regression pending |
| Reviewer | Structured private claims, certification rows, source/date fields, evidence, immutable submission digest/version; IDs redacted without specific assignment. | Implemented; backend denial passes |
| Contextual authentication | Patient/clinician sign-in and verification-first signup; one contextual creation link, no signup password alternative; allowlisted return intents retained. | Implemented; browser verification pending |
| Country display | Flag + code collapsed; full country identity in native options/accessibility; Ethiopian-only SMS unchanged. | Implemented; browser verification pending |
| Required fields / Title Case | Shared required markers tied to actual required semantics; static heading-copy edits and translation aliases replace broad CSS capitalization. User/proper/localized values untouched. | Implemented; route audit pending |

## Private Models and Review Boundaries

Additive v1.44: `tt_reference`, `tt_professional_draft`, immutable
`tt_professional_submission`, `tt_professional_evidence`, and per-clinician
`tt_identity_reviewer`. These app-owned tables have no generic DocType/file/report
API. Evidence download checks authorization every time and returns no-store,
attachment/nosniff/sandbox headers. No public projection includes these fields.
Uploads reuse the medical-history parser restrictions, 5 MB/file and image checks.
Technical limits: 200 certification rows/application, 100 domains or selected
references/group, 1,000 retained files and 250 MB evidence/owner. These are abuse/
performance limits, not a clinical-history policy. Removal deselects evidence;
submitted versions and content hashes remain. Identity-document retention/deletion
policy requires explicit governance review; no automatic destruction is invented.

Self-rating scale v1 is a proposed applicant instrument (1 introductory exposure,
2 supervised practice, 3 independent within scope, 4 substantial advanced practice,
5 supervises/trains within scope). It is separate from the existing Medical Lead
rubric and mandatory evidence gates. No scores affect approval/ranking automatically.

## Actual Reference Coverage

See `tele_tena/reference_data/manifest.json`. ROR CC0 v2.15 (20 October2026)
provides 8,308 education-organization and 7,028 healthcare-organization entries,
194 countries; Ethiopian subset10 education and3 healthcare organizations. Only
complete valid JSON records from the downloaded prefix were normalized; the full
archive transfer was interrupted. No global-completeness claim. ROR education
membership is not a degree-awarding/accreditation assertion. Profession/specialty/
domain labels are source-informed configured navigation vocabulary pending human
review. Eight sourced regulator/responsible-ministry entries are initial coverage,
not a comprehensive international regulatory directory.

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

## Verification In Progress

Real Frappe16.2.1/Python3.14/MariaDB10.6 isolated retained test site:
5/5 focused tests pass, including repeat migration/full-row preservation of89
preexisting tables, draft/conflict/submit retry, bio/date/rating, private evidence
and cross-role denial, history retention, search/paging and pending facility dedupe.
Retained Frappe15 preview migration:5/5,85 preexisting tables preserved. Test writes
roll back; provider/configuration/credential/balance values are not reset.
Production build passes. Browser/reviewer/registration/visual/locale checks continue;
no declaration of owner acceptance or live delivery from these backend results.
