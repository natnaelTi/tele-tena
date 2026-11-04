# Navigation, Attachment Preview and Encounter Identity Evidence

All visible identities, history and evidence are synthetic local fixtures. No real
identity document, payment receipt or patient record is included. The plain-color
photo is deliberate synthetic image data; the letter avatar is the normal fallback.

Current screenshots use the production-built `/teletena/` application, build
`553a6190b4c4a0431dc5126fc6d2d095e50f5faa`. Separate authenticated browser
contexts use the real persisted Frappe16 fixture on8021; no mocked success API.
Viewport width is in each filename where applicable. Full-page captures can be
taller than the viewport. These are Codex comparisons, pending owner acceptance.

| Before | After / comparison |
| --- | --- |
| [Appointment page](before-appointments-1440.png), retained owner preview build5695376 | [Encounter identity](patient-photo-shared.png): avatar LEFT of actual person name; generic title has no image |
| [Rejected heading placement](before-placement-patient-photo-shared.png), earlier sprint build | [Corrected placement](patient-photo-shared.png); [withdrawn fallback](patient-photo-withdrawn.png). Captures have different heights; compare the identity elements, not pixel totals |
| [Patient mobile navigation](before-patient-nav-390.png), retained build5695376 | [Primary Requests rail](after-patient-requests-390.png),390px; Requests/Shared Care removed from More |
| Existing download-only receipt action; see [earlier payment screenshot](../payment-navigation/clinician-receipt-1440.png) | [Patient dialog390px](after-patient-receipt-390.png), [clinician dialog1440px](after-clinician-receipt-1440.png): filename/purpose, fit/zoom, explicit Download, no automatic download |
| Existing final-review grouping retained | [Final review1440px](onboarding-application-review-1440.png): filenames under ID/CV/license/individual credentials, same authorized dialog |

Additional inspected states:

- [Privacy setting768px](after-photo-privacy-768.png): independent current sharing choice.
- [Preflight1440px](patient-preflight-name-avatar-1440.png): LEFT avatar/name in information panel; media left/details right preserved. Fake local devices only; no hosted Join claim.
- [Reviewer native PDF viewer](reviewer-private-evidence.png): full Chromium native PDF plugin, one blank synthetic PDF page. Headless-shell plugin absence is not counted as visual proof.
- [Actual200% Amharic viewport](zoom-receipt-am-200-percent.png): physical1440/CSS720, DPR2, normal visualViewport scale1; translated labels/fallbacks, accessible overflow and focus. Native-language approval remains outstanding.

Comparison notes: shared design tokens, Radix dialog, buttons, focus states and
Avatar remain consistent with the existing MVP reference compositions recorded in
`../../mvp-screen-acceptance.json`. New private-preview state has no separate static
reference screen. Operational labels/amounts reflect actual fixture state; no fake
rating/verification is copied from reference artwork. Original screenshots and
EN/AM/OM390/768/1440 +200% artifacts remain privately under
`/home/frappe/teletena-attachment-release/screens/`.
