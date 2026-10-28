# TeleTena Translation Review Exchange

This dictionary contains application-owned source copy, not patient records,
biographies, uploaded documents, receipts, user credentials or database exports.
English, Amharic and Afaan Oromo remain separate from care-language eligibility.
Existing translations are provisional; no native-language approval is inferred.

## Export and Review

Run from the repository with its existing frontend dependencies installed:

```sh
python3 scripts/localization/catalog.py export localization/teletena-translations.csv
```

The UTF-8 CSV has `key,context,english,amharic,afaan_oromo` followed by
`source_location,placeholders,source_hash,review_status,translator_notes`.
Keep keys/English/hash/placeholders unchanged. Translate in context, retain
interpolation spelling/count, punctuation, deliberate newlines and CSV quoting.
Use `reviewed` only for values a human translator has reviewed. Empty values
remain missing. `provisional` values are never applied by import. Review one
locale at a time if needed; leave the other blank rather than approving a guess.

Spreadsheet-formula prefixes are escaped by an initial apostrophe; the importer
reverses this exact encoding. Keep that protection in the CSV. Do not change cells
into formulas. Use a UTF-8 CSV editor/import with text columns to preserve Unicode,
leading punctuation, quoting and embedded newlines. Review narrow mobile labels
in the product after import; the export does not establish layout acceptance.

## Preview, Apply and Roll Back

```sh
python3 scripts/localization/catalog.py preview /path/to/reviewed.csv --report /path/to/translation-preview.json
python3 scripts/localization/catalog.py import /path/to/reviewed.csv --report /path/to/translation-import.json
```

Preview reports changed values, unknown/duplicate keys, placeholder mismatches,
stale English/hash rows, missing rows/translations and stale prior reviewed keys.
An invalid import writes no dictionary. A partial file applies only supplied,
nonempty reviewed values; absent keys/locales keep their current reviewed value.
Contextually conflicting values for callers using the same English fallback are
rejected; give that caller an explicit semantic context before applying a distinct
translation. Do not choose an arbitrary conflicting translation.

Valid import updates source-only reviewed dictionaries in `localization`, React
and the backend, and retains immutable content-hash versions under
`localization/versions/`. Commit the reviewed change, rebuild public assets and
restart affected Python processes using the existing scoped release procedure.
Frontend `w`/`t` and backend validation use reviewed values before existing English
or provisional fallbacks. Backend dynamically composed copy needs its original
placeholder template, not a private interpolated string, when adding new callers.

```sh
python3 scripts/localization/catalog.py rollback CONTENT_HASH
python3 scripts/localization/catalog.py rollback CONTENT_HASH --apply
```

The first command previews; the second restores that reviewed dictionary version
without touching clinical records. Rebuild/restart to serve it. Preserve source
hashes and inspect `localization/coverage.json` / `source-changes.json` after every
export. A dictionary with missing or unreviewed entries is not production-language
acceptance. No external translation service is called.

## October 28 Workbook Reconciliation

Use the supplied XLSX locally; do not replace it or upload it to a translation
service. The converter reads both `Start Here` and `Translations`, verifies the
Git baseline and preserves source cells, independent locale states and reviewer
attribution. Its separate working copy records only logged technical-literal
corrections plus review annotations. It does not approve linguistic changes.

```sh
python3 scripts/localization/workbook.py \
  /home/frappe/tele-tena-dictionary/TeleTena_Translation_Review_Completed.xlsx \
  --output /home/frappe/teletena-translation-release/review-package \
  --baseline 05299379183efa0e8f1b599c46c60bd9531d6296
python3 scripts/localization/catalog.py preview \
  /home/frappe/teletena-translation-release/review-package/approved-amharic.csv \
  --report /home/frappe/teletena-translation-release/review-package/preview-amharic.json
python3 scripts/localization/catalog.py preview \
  /home/frappe/teletena-translation-release/review-package/approved-afaan_oromo.csv \
  --report /home/frappe/teletena-translation-release/review-package/preview-afaan-oromo.json
python3 scripts/check_translation_release.py
```

Use a new private output directory for each human review revision; retain the
original and prior packages. Only exact `Approved` plus actual nonempty reviewer
attribution makes that locale eligible; structural/source/conflict validation must
also pass. The other locale is blank in its export. Current exports contain zero
rows: no human approvals were supplied. Do not mark drafts Approved to satisfy an
import gate. There is no isolated draft-preview mechanism, and none was added.

`source-delta.csv` separates new templates from source-confirmed machine literals;
`issues.csv` flags scripts/terminology/policies and same-English fallback conflicts.
`delta-review.csv` combines source changes with conflicting draft values for human
review. Four visible unit/type-specimen entries remain, rather than blindly
removing ambiguous abbreviations. Exclusion rules and source reasons are recorded
in `localization/extraction-exclusions.json`. Review source context before changing
these rules. No biography, medical record or receipt is part of this exchange.

The approved-only runtime now preserves permission/error classes while translating
original templates before interpolation. An explicit `X-TeleTena-Locale` selects
only en/am/om; it grants no role or care-language eligibility. Default policy text
can translate only when it exactly matches the app-owned template; custom content,
publication flags, versions and consent are unchanged. Draft policy translation
is not policy approval. Release metadata includes reviewed dictionary hash/counts.

After genuine approvals, repeat validation, preview/import independently using the
existing commands above, commit the immutable version history, rebuild and rerun
locale/browser checks. `--require-complete` on check_translation_release.py remains
a failing release gate until review coverage is complete. Current provisional UI
and English fallbacks are explicitly not workbook-language acceptance.

The private package also includes `new-source-review.csv` for the45 new keys.
Review this separately through the existing CSV workflow, one locale at a time
with the other blank and genuine attribution in translator_notes. Only change
provisional to reviewed after human review; preview/import separately. Do not
append new keys to the old-baseline workbook or fabricate source hashes.
