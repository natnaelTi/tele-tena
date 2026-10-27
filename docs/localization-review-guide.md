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
