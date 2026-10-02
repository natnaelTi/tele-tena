# Availability save hotfix

## Finding

The failure was reproduced on the production-built React bundle served by the
isolated Frappe 16 site at `/teletena/`. The browser submitted
`tele_tena.api.scheduling.save_schedule` with weekly interval keys
`start_local` and `end_local` (for example, `09:00` and `17:00`). The backend
validator only read `start` and `end`, so it treated both values as missing and
returned HTTP 417 with the generic `invalid_input` code. This was a client/server
payload-contract mismatch; the screenshot alone did not establish the cause.

The API now accepts the editor's local-time names while preserving the earlier
`start`/`end` shape for existing callers. Schedule reads normalize database TIME
values to HTML-compatible `HH:MM`. Specific validation codes cover malformed
times, overlap, end-before-start, invalid timezone and empty published schedules.
The editor retains entered values, annotates the affected fields, blocks duplicate
saves and distinguishes session expiry, permission denial and service failure.
The change does not weaken authorization, approved-scope checks, CSRF or booking
conflict validation.

## Verification

Against the disposable Frappe 16.2.1 / ERPNext 16.1.0 site, on the built Frappe
route (not Vite):

- Before the fix, the browser request returned HTTP 417 `invalid_input` with
  weekly `start_local`/`end_local` fields.
- After the fix, the clinician saved a published schedule; the browser observed
  HTTP 200 and those exact field names/values in the request, then reloaded and
  read the saved `09:00`–`17:00` times.
- The synthetic patient saw an eligible slot and completed a booking through the
  patient booking journey.
- Eight `tests/presentation.py` checks passed, including time round-trip,
  invalid-overlap and reversed-time atomicity, and cross-clinician authorization.
- `npm run build` passed. `npm run lint` completed with pre-existing warnings;
  no lint error was reported.

The broad `tests/integration.py` invocation was attempted on this site's
invited-review configuration. It is not a passing result: its legacy harness
assumes a different HTTP base/site configuration and its phone-auth cases expect
phone access enabled, while this review site intentionally disables it. Those
failures do not demonstrate an availability defect. A configuration-matched
full-suite run remains outstanding.

The hosted Selfmade site is still pinned to the operator-reported commit
`8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6`. No remote installation or data was
changed. The hotfix PR is independently based on merged `main` and is safe to
review separately from the ongoing design branch; deployment remains a separate
operator action.

## Follow-up calendar verification

The design branch keeps the same API fix and uses a timezone-derived weekly
calendar with recurring/date-only editing and a mobile agenda alternative. A
second browser check exposed hit testing that blocked date overrides over a
weekly availability block; date-only controls now sit above recurring blocks
while already reserved appointment blocks remain protected. The check confirms
clicking Monday 10:00 prepares a date-scoped 10:00–11:00 replacement, makes no
implicit save, and leaves the change visibly unsaved.

On 2026-10-02, the built production route passed clinician save, payload
inspection, reload persistence and patient booking using a fresh synthetic
patient. A separate calendar browser test passed accessible time-field focus,
copy-to-day and date-only exception editing. `tests/presentation.py` passed 12
cases; selected `tests/integration.py` cases 01–17 passed 18/18. The selected
suite did not include the legacy phone-auth cases because this invited-review
site deliberately disables phone access. The synthetic patient was created
with a new balanced wallet; the old seeded patient was excluded after a stale
manual test worker wrote wallet/log events without journals. No existing data
was repaired or discarded. See the current-branch limits in
`presentation-readiness-verification.md`.
