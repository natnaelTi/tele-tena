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
  asset integration passed for source `888e40138a07336c9aa93ef2b6b8130bf20089ba`;
  the private credential scan found zero matches. A subsequent applicant form
  resume affordance is included in source commit `9ef9838` and requires a fresh
  packaged build before its review.
- Browser inspection on the built `/teletena/` route at
  `http://127.0.0.1:8017/teletena/`: authenticated clinician application page
  at 1440px and reviewer queue at 390px rendered without browser exceptions or
  horizontal overflow. Captures are `docs/screenshots/vetting-appeals/`.

## Not verified in browser

The captured clinician has no terminal scope decision and the reviewer queue
has no pending appeals. Therefore these captures verify normal and empty states,
not appeal submission, reviewer resolution, reopened evidence upload, or
resubmission through the rendered UI. Those state transitions are covered by
real persisted backend command tests only. A populated authenticated browser
journey remains required before this screen is locally accepted.

No clean empty-site installation was performed for v1.18 in this slice. Existing
applications, evidence, appointments, balances, and credentials were preserved;
the two isolated sites were backed up before schema migration. No remote install,
live SMS, real-money settlement, or clinician credential verification is
claimed.
