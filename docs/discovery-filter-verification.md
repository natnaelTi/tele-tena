# Discovery filter verification

This focused discovery slice is served by the production-built Frappe app at
`http://127.0.0.1:8017/teletena/`, site `tele-tena-pr12-fresh.localhost`.
The browser test uses the site's existing synthetic patient and clinician
records; it does not seed, publish a request, or change their schedules.

## Behavior verified

- Discovery displays approved, published services from `tele_tena.api.journey.services`.
- Service search and the explicit service selector filter persisted discovery results.
- Care-language filtering uses the clinician's declared supported language codes.
- Session-format filtering uses the published schedule's consultation format.
- “Open times in the next 14 days” queries the authenticated scheduling calendar
  for each candidate offering and retains offerings with generated slots. A
  calendar API failure is shown as an error rather than as a claim that no
  clinicians are available.
- Search text, selected service, language and format are carried in router state
  into the request composer. The browser check confirms the draft fields and
  stops before publishing.
- The controls remain within the viewport at 320, 390, 768, and 1440 CSS px.
  The tablet layout uses two columns; mobile uses one column.

## Evidence

`scripts/browser-discovery-filters.cjs` runs against the packaged app, signs in
with the existing synthetic patient fixture, applies real filters, exercises
the server-generated availability query, inspects request-draft preservation,
and saves rendered screenshots at:

- [`screenshots/discovery-filters/filtered-390.png`](screenshots/discovery-filters/filtered-390.png)
- [`screenshots/discovery-filters/filtered-320.png`](screenshots/discovery-filters/filtered-320.png)
- [`screenshots/discovery-filters/filtered-768.png`](screenshots/discovery-filters/filtered-768.png)
- [`screenshots/discovery-filters/filtered-1440.png`](screenshots/discovery-filters/filtered-1440.png)

The screenshot names refer to CSS viewport widths. Screenshots are synthetic
review-site content. The production asset manifest's `source_commit` is the
authoritative frontend build source. The final screenshot/browser run used
packaged source `ef9a370fb7af211ae1d29b3e4efb64f6e93d23be`; the manifest was
read from the running Frappe static asset route and matched that source. The
app route returned HTTP 200. The browser journey passed on the same
`/teletena/` app and site after a targeted Gunicorn master reload.

The Frappe 15 presentation regression suite passed 39/39. The frontend
production build passed; lint exited successfully with existing repository
warnings. These focused checks do not establish acceptance for every screen in
the product inventory.

## Limits

This verifies the filter slice, not the entire discovery, booking, or matching
product journey. The availability selector only checks the next 14 days.
Natural-language service suggestions, relevance feedback, previous-clinician
filtering, and proximity ranking are not implemented. Locale keys exist for
English, Amharic, and Afaan Oromo, but this browser run used English; the two
Ethiopian-language translations remain provisional pending native review.
200% browser zoom, Frappe 16 and live SMS/device validation are not part of
this check.
