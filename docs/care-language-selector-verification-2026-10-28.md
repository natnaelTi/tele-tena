# Care-Language Names, Search and Flags — 28 October 2026

Source/build: `45e1600a35a9450bb26b50397749c01491b2d4a7`.
Branch `feat/offline-telebirr-mvp`, draft PR50 dependent on PR49.
Preview: http://127.0.0.1:8017/teletena/;
site `teletena-mvp-presentation.localhost`. Later test/document commits do not change runtime.

## Delivered Changes

The old display helper asked the browser for every language name and accepted the
returned code as a display label. The shipped630-language catalog now provides
complete English names regardless of the browser's language-data coverage.
Reviewed/localized full names remain available; unsupported translations fall
back to the catalog name, never a bare language code. Reviewer views, saved claims,
public cards/previews, booking selectors and onboarding summary share the helper.
The onboarding summary previously called every non-English/non-Amharic code Oromo;
that incorrect fallback is removed.

Onboarding and Account share an immediately visible search with native checkboxes,
selected chips, loading/empty/error/retry states, keyboard focus from search,
retained selections and bounded20-row server paging. Search matches configured
English names, aliases and exact language codes. Ordering is applied before paging:
English and the catalog's Ethiopian-language group first, then other languages;
each group is alphabetical by canonical English name with stable code tie-breaks.
Self-assessment and separate reviewer approval requirements are unchanged.

Flag emoji depend on platform fonts and can appear as regional-indicator letters.
Language rows/selected chips/self-assessment headings and phone-country controls now
use local SVG flags, not an OS-specific emoji font. The phone picker uses the existing
accessible dialog with country/calling-code search and native buttons. Country IDs,
manual override, connection-based suggestion, E.164 normalization and Ethiopian-only
SMS restrictions are retained. No external image request or new runtime dependency.

## Sources, Coverage and Reproduction

- Names: existing `care-languages-v1.json`, Unicode CLDR via Babel2.16.0:630 records.
- Group: [CLDR territory-language data](https://cldr.unicode.org/index/requesting-additionsupdates-to-cldr-languagepopulation-data)
  for Ethiopia, intersected with the current catalog: **Afar, Amharic, English,
  Geez, Oromo, Sidamo, Somali, Tigrinya, Wolaytta**. This is9 records including
  English, not an exhaustive list of Ethiopian languages or a clinical endorsement.
- Region hints: [CLDR likely subtags](https://unicode.org/cldr/charts/45/supplemental/likely_subtags.html),
  with ET for local catalog languages other than English. They are a visual
  association, not nationality, an exclusive language country or practice permission.
  International/historical/constructed languages without an applicable country use
  a neutral globe. English uses CLDR's US regional association.
- Flags:259 locally served4:3 SVGs (257 two-letter originals plus2 territory mappings) from [flag-icons7.5.0](https://github.com/lipis/flag-icons/tree/v7.5.0),
  MIT; local `frontend/public/flags/LICENSE.txt` and `SOURCE.md` retain attribution,
  pinned archive URL and SHA256. The archive's npm SHA512 integrity was verified.
  SVGs were checked for script/foreignObject/image elements before vendoring.
- `scripts/generate_language_display.py` deterministically generates server/client
  display metadata from the shipped names and recorded Babel2.16 source. It reads
  no sites/private data and is not run during deployment. No shared package repair
  or dependency installation is necessary.

## Verification Actually Run

- `tests/language_catalog.py`: **3/3**, real Frappe16.2.1 backend as Guest, read-only.
  Verified priority roster/order before pagination,630 unique records over pages,
  matching-only English/alias queries, empty results, public allowlist and all
  applicable region assets. No clinical/private fields in the public projection.
- `scripts/browser-care-languages.cjs`: real isolated Frappe16 registration through
  randomized private email test transport; no live SMS/email. Checked full Acehnese
  name, keyboard selection, ET/US/ID SVGs, country manual override/focus return,
  both alphabetic groups, query changes, selection retention during failed search,
  Retry, explicit self-assessment, Save for Later and reload from persistent data.
  Screenshots at390/768/1440 visually inspected. New synthetic test applicant only;
  existing demonstration accounts/approvals/provider settings/balances unchanged.
- `scripts/browser-language-zoom.cjs`: final runtime at actual Chromium200% zoom,
  720CSS pixels/DPR2/visualViewport.scale1 at1440physical width. Country dialog,
  Account's shared care-language selector/group heading/search and scrollable
  controls verified without changing existing clinician claims. Screenshots inspected.
  The signup run used03d75dc; actual200% useda18c04f, which only made the two
  headings explicit translation keys. Final45e1600 has identical client/API code to
  a18c04f, with two additional territory SVGs: AC from upstreamsh-ac and TA from
  upstreamsh-ta. `tests/language_assets.cjs` verifies all245 supported phone countries
  and630 names; actual built AC/TA/ET loading and selection checked separately.
  No broader flow assertions were weakened to accommodate these mappings.
- Production build and lint passed (existing warnings retained); packaged asset/hash
  and privacy checks passed. CSV updated including both group headings:
  **8,690** entries;4/4 translation-exchange tests passed. Missing/provisional
  translations remain identified, not clinically/native-language approved.

No schema migration, data conversion, approval backfill or payment/provider change
was needed. Prior financial/consultation evidence remains applicable; those expensive
unchanged suites were not rerun. No remote deployment or merge. Owner visual
acceptance, native-language review and physical-device review remain manual.

See `docs/screenshots/care-language-selector/`. Screenshots use only synthetic data.
