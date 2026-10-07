# Vetting reconsideration verification

This report covers the additive per-scope reconsideration slice on
`feat/vetting-reconsideration`. It does not claim the full vetting or product
program is complete.

## Implementation

`Tele Tena Vetting Appeal` is a native, read-scoped DocType with one unique
appeal per immutable `Tele Tena Vetting Assessment`. Applicants can submit a
statement for their own latest rejected, suspended, or expired scope decision.
An authorized approver records a reason and either upholds it or reopens the
scope to clarification. Reopening does not restore authorization; applicant
resubmission and a new ordinary assessment are required.

## Checks actually run

- Frappe 15.121.2 / ERPNext 15.121.6 retained isolated site
  `tele-tena-pr12-fresh.localhost`: migration to v1.18, repeat migration, and
  `tests/presentation.py`: **29/29 passed**. The focused regression includes
  same-payload replay, changed-payload rejection, direct-write denial, private
  reviewer queue, upheld decision, reopened resubmission, and scope remaining
  unavailable before new approval.
- Frappe 16.2.1 / ERPNext 16.1.0 compatibility site
  `tele-tena-pr2-test.localhost`: full site backup with private/public files,
  migration to v1.18, repeat migration, and the same presentation suite:
  **29/29 passed**. The tested app code was isolated from the compatibility
  bench checkout using a detached worktree; the bench source branch was not
  switched.
- `npm run lint`: exited successfully; the repository still reports existing
  React hook/purity/Fast Refresh warnings. One duplicate locale key encountered
  during this slice was removed. Amharic and Afaan Oromo copy is provisional.
- `npm run build`: passed. The LiveKit client chunk-size advisory remains.
- `scripts/build_review.py` and `scripts/check_review_assets.py`: production
  asset integration passed for source `e227fde07dee02e7845c5103c05fb3e2051f8ad2`;
  the private credential scan found zero matches.
- Browser inspection on the built `/teletena/` route at
  `http://127.0.0.1:8017/teletena/`: authenticated clinician application page
  at 1440px and reviewer queue at 390px rendered without browser exceptions or
  horizontal overflow. Captures are `docs/screenshots/vetting-appeals/`.
- The runtime manifest and service-worker cache key identify source
  `e227fde07dee02e7845c5103c05fb3e2051f8ad2`; port 8017 was gracefully
  reloaded. Browser inspection confirmed the packaged asset URL and `/teletena/`
  service-worker scope/cache. A fresh Playwright context verified the new
  versioned public cache installs. Update notification in a pre-existing
  physical browser profile has not been independently tested.

## Populated browser journey update (2026-10-08)

A one-off synthetic clinician fixture was created through an explicitly invoked
local helper and removed after the run. In the packaged `/teletena/` app at
`http://127.0.0.1:8017/teletena/`, the authenticated browser journey completed:
applicant submitted an appeal → reviewer reopened the scope for clarification →
applicant resumed the saved application → uploaded new synthetic PDF evidence →
resubmitted. Reloads preserved the appeal/application state. Captures:

- `docs/screenshots/vetting-appeals/populated-applicant-390.png`
- `docs/screenshots/vetting-appeals/populated-reviewer-1440.png`
- `docs/screenshots/vetting-appeals/populated-resubmitted-390.png`

The browser script stopped before exercising the optional ordinary final scope
approval because its `getByLabel("Decision")` locator resolved ambiguously. A
DOM check found one visible decision select in the target card; this is a test
locator issue and was not treated as proof of a product failure. Final human
approval remains covered by persisted backend tests, not this populated browser
run. The temporary account, service, evidence and private fixture credential were
removed by the scoped cleanup helper.

## Remaining verification gaps

A clean empty-site v1.18 install is still not evidenced for this slice. Repeat
migrations and the 29-case presentation suite passed on backed-up existing Frappe
15 and Frappe 16 sites, but that is not a fresh-install result. A physical browser
profile update prompt, native Amharic/Afaan Oromo review, independent legal/medical
approval of the proposed appeal policy, external credential verification, live
SMS, real-money settlement, and physical-device consultation testing are also
not claimed. Existing applications, evidence, appointments, balances, and
credentials were preserved; no remote install or Selfmade change occurred.
