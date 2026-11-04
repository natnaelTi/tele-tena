# Application Workflow — Before / Current Evidence

Current production runtime: `c30d4cdff475a91f864af5bab9aafa329040e33a`.
Only isolated fictional accounts, synthetic evidence and private test transport.
No real identity, authorization, OTP, password or receipt is shown.

| Earlier Implementation | Current Composition / Inspection |
| --- | --- |
| [Full reply form768](../scope-information/requested-application-resume-768.png) | [Tracker1440](clinician-tracker-1440.png), [390](clinician-tracker-390.png): per-service status/action rather than all forms on one page |
| [Existing reviewer decision1440](../scope-information/request-missing-license-1440.png) | [Queue768](reviewer-tracker-768.png); [grouped details1440](reviewer-current-license-1440.png), [390](reviewer-current-license-390.png): current license in its correct field; separate updates/history and Review and Decide |
| No typed requested-item popup | [Targeted dialog1440](focused-response-1440.png), [390](focused-response-390.png): only license plus explanation requested in this case; uploaded filename retained; existing-document selection |
| No recorded email-assisted submission | [Profile768](assisted-professional-profile-768.png), [authorization390](email-authorization-390.png), [owner tracker1440](assisted-owner-tracker-1440.png): source/date/private authorization plus separate acknowledgements; two pending scopes, no inferred approval |

Actual Chromium200% uses1440 physical pixels/720 CSS pixels/DPR2/visualViewport1:
[Response viewport](focused-response-200-percent.png),
[submit reachable by keyboard and normal dialog scrolling](focused-response-submit-200-percent.png),
[reviewer queue viewport](reviewer-tracker-200-percent.png).
These CDP viewport captures avoid Playwright's full-page bitmap clipping at native
browser zoom. Long-page captures retain sticky header/mobile-navigation positions
at the current viewport boundary; they do not imply the header is an inline section.

Codex inspected grouping, labels, status contrast, readable line wrapping, spacing,
file placement, dialog sizing and viewport scrolling. Existing shared TeleTena
panel/button/navigation patterns are retained. Reference inventory B10/B11/I02/I03
supplies the application/progress/reviewer composition language; the newly requested
typed-response/assistance states are documented extensions, not claimed identical
prototype screens. Owner visual acceptance and human language approval remain open.

All matching full screenshot sets/logs remain privately at
`/home/frappe/teletena-application-workflow/`. Functional/preservation results and
operator walkthrough: [verification](../../application-workflow-revision-2026-11-04.md).
