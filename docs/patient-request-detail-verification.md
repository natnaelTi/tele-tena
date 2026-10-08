# Patient open-request detail verification

## Current implementation

The patient request list links to a dedicated owner-scoped route at
`/teletena/patient/requests/:requestId`; the patient dashboard uses the same
opaque request identifier for an active request. `my_request_detail` selects by
both request ID and authenticated patient. Unknown IDs and another patient's
IDs return the same `request_unavailable` outcome; non-patient roles fail the
patient-profile permission check. The query includes only the saved request,
its exact disclosure snapshot, and that request's offers. The URL contains no
request narrative, profile email, or phone number. The frontend does not store
request text in local storage or the service worker cache.

The detail screen shows lifecycle/progress, timezone-aware request times,
patient-supplied disclosure, offer status and price, and the matched appointment
link. Offer acceptance invokes the existing atomic offer/appointment/reservation
workflow. Error rendering distinguishes unavailable IDs, expired sessions,
permissions, and retryable load failures. Amharic and Afaan Oromo strings are
provisional pending native review.

## Verification evidence

- Frappe 15 `tests/presentation.py`: **34/34 passed** on
  `tele-tena-pr12-fresh.localhost`; the added regression confirms the owner can
  read the exact persisted snapshot, another patient cannot, a clinician cannot,
  and an unknown ID is indistinguishable from a foreign ID.
- `scripts/browser-patient-request-details.cjs`: passed against the packaged
  `/teletena/` Frappe application. It signs in with the private local synthetic
  patient fixture (credentials are not emitted), opens a persisted request by
  opaque ID, reloads, returns to the request list, and checks an unknown ID
  shows the generic unavailable state without the prior request text.
- Rendered-browser overflow checks passed at 320, 390, 768 and 1440 CSS px;
  localized request headings rendered in Amharic and Afaan Oromo. The exact
  screenshots are `docs/screenshots/request-details/patient-detail-390.png` and
  `docs/screenshots/request-details/patient-detail-1440.png`.
- `npm run lint` and `npm run build` passed. Lint has existing warnings in
  surrounding components; the build reports the existing large-chunk advisory.
- The package manifest source is `72f64236fa2ce537191f677053267adffaac96d4`;
  the backend API was introduced in `1a9eeeaa9a83808e4725150aa9e6bdae64354832`.
  The running preview at `http://127.0.0.1:8017/teletena/` returned HTTP 200
  after a graceful reload of the identified loopback Gunicorn master.

This slice does not add a separate clinician-side offer detail page or prove a
complete open-request waiting/dispatch pilot. Worker-backed wave widening,
three-minute real-pilot performance, live SMS, physical-device calling and
native translation approval remain outside this check.
