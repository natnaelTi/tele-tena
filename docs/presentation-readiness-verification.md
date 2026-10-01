# Presentation release verification — in progress

Branch: `feat/presentation-ready-release` from merged main `7222836`. Synthetic
fixtures only. An item is complete only with server behavior and browser evidence.

## Requirement status

| Requirement | Status | Evidence |
|---|---|---|
| 1. Clinician recurring schedule and patient valid-slot booking | pending | Recurrence/DST/exceptions/conflict/concurrency tests and browser calendar pending. |
| 2. Appointment/call/documentation state separation; confirmation, cancellation and exact release | pending | Lifecycle transition and idempotency API tests pending. |
| 3. Private clinician notes, published patient summaries, revisions and follow-up | pending | Direct patient API privacy and amendment tests pending. |
| 4. Focused LiveKit room and actual-track audio activity | pending | Preserve hosted Cloud revocation test; audio-only behavior and screenshots pending. |
| 5. Status-aware consultation detail and exact booking snapshot | pending | Patient/clinician status coverage and timing limits pending. |
| 6. Product copy and one persistent demo ribbon | pending | Three-language copy and all-route inspection pending. |
| 7. Encounter-scoped clinician care directory | pending | Alias privacy, filters, paging and cross-clinician denial tests pending. |
| 8. Account sections and backed balance summaries | pending | Persisted preferences and balance-summary journey pending. |
| 9. Admin display and application evidence review | pending | Name/scopes/evidence route tests pending. |
| 10. Private PDF resume upload and download | pending | Type/size/direct-route/role checks pending. |
| 11. Public-only PWA cache and responsive review | pending | Service-worker URL tests, offline/update and browser journey pending. |
| 12. Role-specific guided tours | pending | Persist/dismiss/replay/role filtering/accessibility tests pending. |

## Checks and artifacts

- Baseline PR #6 verification: inherited from merged main; see `consolidation-verification.md`.
- New release checks: pending.
- Screenshots: pending in `/tmp/tele-tena-presentation-review/`.
- Fresh install: pending on a separate disposable site; existing development records must remain unchanged.

## Limitations

Pending. Do not infer physical-device, native-language, regulated financial, or
production-clinical readiness from automated tests.

## Presenter walkthrough

Pending implementation. The final walkthrough will cover the patient booking and
privacy preview, clinician schedule and consultation notes, patient-visible
summary, and reviewer-only application evidence without using personal data.
