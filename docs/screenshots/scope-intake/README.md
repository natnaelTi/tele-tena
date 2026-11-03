# Scope Intake / Reviewer Handoff — 3 November 2026

Production build `d400cb5d9e68d35a2b602f11497f76ce3441a58e`, real persisted
Frappe16 isolated fixture on8021, separate clinician/reviewer sessions. All people,
licenses and documents are synthetic; no real IDs or patient records are included.

- [General application1440px](requested-scope-links-1440.png): independent requested-scope status and exact review link. One service is Clarification while the other remains Submitted; general approval remains separate.
- [General application390px](requested-scope-links-390.png): readable grouped review and mobile navigation.
- [Scope evidence768px](linked-scope-evidence-768.png): exact professional submission, CV/credential review and the selected license PDF available to its scope assessment. IDs remain restricted to individually assigned credential reviewers.
- [Manual initiation390px](manual-scope-start-390.png): approved clinician, service and required audit reason; continuation explains assessment versus legacy grants.
- [Manual assessment1440px](manual-scope-assessment-1440.png): reviewer initiation opens the existing grouped human vetting workflow; no fabricated approval.
- [Independent decision](scope-clarification-1440.png): persisted clarification and existing correction/review mechanism. The first decision browser run also verifies the visible success notice; later read-only captures retain the saved state.
- [Actual200% zoom](zoom-scopes-200-percent.png): physical1440/CSS720/DPR2 with visualViewport scale1; no clipped controls or inaccessible content, normal page scrolling retained.

Codex inspected composition, label wrapping, status/link grouping, evidence location,
required markers and responsive scrolling. Existing TeleTena grouped onboarding,
professional-review and scope-assessment reference compositions are reused. No new
visual direction or unrelated workspace change. Fixed mobile navigation may appear
within full-page captures at the viewport boundary; page content remains scrollable.
Owner/native-language acceptance is not inferred from screenshots. Earlier successful
onboarding/evidence layouts are retained in `../attachment-photos/`; the original
failure was missing persisted scope applications rather than a new screen design.

Complete private captures390/768/1440, onboarding/reload and browser logs remain at
`/home/frappe/teletena-scope-intake-release/`. No live delivery/payment/device result
is claimed by these browser checks.
