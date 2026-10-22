# Clinician Application Comparisons

Reference source remains outside Git. Captures use English, matching390/768/1440
viewports and100% zoom unless the filename says200-percent. Prototype review chrome
is visible in reference captures. The22October direction intentionally replaces the
older full-name and combined qualification/license steps; comparisons preserve the
established component language, not obsolete fields. All application evidence and
identities shown are development fixtures; no uploaded document content is shown.

| State | Approved reference | Current application | Difference |
|---|---|---|---|
| Professional profile | [B06 desktop](reference/b06-1440.png) | [Profile desktop](after/professional-profile-1440.png) | Structured names, search/selection and private ID extend original wizard. |
| Qualifications | [B07 mobile](reference/b07-390.png) | [Qualifications mobile](after/qualifications-390.png) | Awarded title separate from specialty; repeatable certificates/CV. |
| License | [B07 desktop](reference/b07-1440.png) | [License desktop](after/license-1440.png) | Separate grouped dates/authority, no guessed regulator. |
| Affiliation/declaration | [B08 mobile](reference/b08-390.png) | [Affiliations mobile](after/affiliations-390.png) | Search, pending facility, accuracy and adult declarations separate. |
| Final review | [B10 desktop](reference/b10-1440.png) | [Final review desktop](after/application-review-1440.png) | Explicit versioned choices; no automatic scope grant. |
| Human application review | [I03 tablet](reference/i03-768.png) | [Reviewer tablet](after/reviewer-structured-768.png) | Submitted structured evidence/self-ratings; identification redacted. |
| Contextual registration | [Before desktop](before/clinician-register-1440.png) | [After desktop](after/clinician-registration-1440.png) | Context heading, one mode action, compact flag/code and required semantics. |
| Actual browser zoom | Not an obsolete prototype equivalence claim | [License200%](after/professional-section-2-200-percent.png), [Signup200%](after/clinician-signup-200-percent.png) | Actual Chromium zoom with accessible document scrolling; controls are not clipped to force one viewport. |

The extra live directory/ID/evidence fields make the new flow longer than B06/B07;
short grouped steps, collapsible search and certification rows control density.
Existing tour invitation is dismissible and remains available in the help island.
200% uses CDP viewport capture because Playwright full-page capture crops at actual
browser zoom; these are not CSS-scaled or artificially narrowed screenshots.

See [the field checklist and verification](../../clinician-onboarding-context-sprint.md).
Functional verification and Codex visual inspection are distinct from owner acceptance.
`sha256.json` records image integrity; image existence is not acceptance.

Owner-requested simplification: [Mobile range card](after/competency-range-card-390.png) · [Desktop range card](after/competency-range-card-1440.png). Replaces per-domain upload and rating dropdown; historical evidence retained.

Clinician Account follow-up (H02, new B06/B07 fields):
[Before desktop](account-before/professional-1440.png) ·
[After desktop](account-after/professional-0-1440.png) ·
[Personal desktop](account-after/personal-1440.png) ·
[Mobile qualifications](account-after/professional-1-390.png) ·
[Actual200% license](account-after/counselor-section-2-200-percent.png).
Account screenshots contain deliberately unsaved UI test entries; no approval,
credential or actual professional-record change is implied.
