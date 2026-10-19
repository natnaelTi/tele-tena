# Consolidated Request Workspaces — 19 October Follow-up

Packaged runtime: `ba60959e7eb2f921c130a2ea4c426d2db8c6552b` on `feat/guest-first-mvp`, draft PR #47, dependent on PR #46. Later evidence/documentation commits contain no runtime difference.

Preview: http://127.0.0.1:8017/teletena/ · site `teletena-mvp-presentation.localhost` · `/home/frappe/frappe/frappe-bench` (Frappe15/Python3.12). Production assets, no Vite. All41 manifest hashes match. Owned web257763, worker257690, scheduler257695 and Redis13917 remain running. Python code is byte-identical to the preceding backend checkpoint; no restart/migration/schema/dependency change was needed. The original Bench and Selfmade were not changed.

## Implemented Journey

| Role / route | Local micro-flows |
|---|---|
| Patient `/patient/requests` | Compact Active/History list; guided description/preferences/privacy; publish → real server progress → profile pane → comparable private offers → disclosure/price/balance review → optional funding dialog → accepted appointment card, all in the workspace |
| Clinician `/clinician/requests` | Compact eligible inbox; selected authorized request beside an inline approved-offering/time/optional quote editor; send → private offer waiting/outcome → accepted handoff; Active/History paging and withdrawal stay in the workspace |
| Preserved patient/clinician request/offer deep links | Canonical workspace selection uses opaque request/offer query references. Reload retains the selected record/review. No request text or credentials enter URLs or browser persistence |

Patient identity/text/file choices and the authoritative sharing preview remain explicit. An offer itself reserves neither time nor funds. Add funds does not guarantee continued offer validity. Acceptance still revalidates service approval, language/format, presence where applicable, exact time, price, disclosure and balance in the original atomic/idempotent command. Competing clinicians never receive one another's quotes. Accepted notifications and the clinician availability card are unchanged.

The patient stays on the matched request after acceptance; opening its appointment is an explicit next step. The appointment card uses the existing shared status presenter and authorized appointment API, so a later cancellation or ended/incomplete call does not remain “confirmed” simply because the request once matched. No visual status settles earnings.

Draft form state survives local view changes. Initial auto-selection is pinned so incoming/polled records do not silently replace the request being edited. Hidden drafts retain the existing tour-unsaved guard; successful sends/publishes clear only the corresponding completed draft. Drafts are deliberately in memory: reload does not claim that unpublished clinical text was saved. Schedule-for-later prepares a new draft; the original keeps its real state until explicitly cancelled.

## Defects Found and Fixed

- Old patient publication navigated to separate progress/detail pages and offer links navigated again. Repeated full request cards obscured the active task. These are now one selected workspace and local dialogs.
- Clinician cards repeated a full disclosure and setup/time notices for every row, with a separate modal and offers page. Cards are now compact selectors; only the selected request displays its authorized context and editor. Private history is integrated and remains paginated/owner-scoped.
- A zero custom quote produced the generic save failure because a local Error passed through the shared safe API-error mapper. Quote validation is now field-specific, preserves inputs, opens/focuses the optional price section, and never bypasses server price validation. A no-additional-supply result now has an informational explanation rather than throwing a generic failure.
- The acceptance dialog's stacked wallet/file/disclosure blocks were too long. It now groups schedule/total, sharing controls, optional file selection, real balance and exact disclosure into compact responsive columns. A failed sharing-preview fetch has an explicit retry. Small screens/zoom retain accessible scrolling.
- Historical matched requests could imply their appointment remained confirmed after cancellation. Current appointment status is fetched/presented separately from the durable match event.

## Checks Actually Run

Private logs: `/home/frappe/teletena-guest-first/requests-*.log`.

| Check | Result |
|---|---|
| Production build / TypeScript / package hashes | Pass at exact source above; all41 hashes match. No lockfile/dependency changes. Existing bundle-size warning remains |
| Frontend lint | Pass,63 warnings/0 errors. Existing React/compiler warning debt is recorded, not described as warning-free |
| Real two-role Frappe16 browser | Pass on `teletena-guest-first-test.localhost`, compatibility Bench Frappe16.2.1/ERPNext16.1.0/Python3.14.2: persisted scheduled publication → eligible inbox → inline custom quote → patient profile pane → insufficient funds → cancel/reopen funding with sharing retained → real demonstration top-up → accepted appointment/reservation, both roles staying on their Requests route |
| Retry / denial | Repeated accepted payload returned the same appointment/idempotent result. Foreign patient request and foreign clinician quote reads denied. No mocked successful responses |
| Retained preview browser | Patient/clinician1440/768/390; draft/Back/view-switch retention; hidden draft guard; integrated history; old offers path redirects to the selected workspace; Amharic/Afaan Oromo390 layout/font checks. No publication/quote/funding/settings changes on this retained site |
| Actual200% / negative recovery | Separate patient and clinician persistent browser contexts, outer1440/inner720/DPR2/visualViewport.scale1, reduced motion. Old deep links, readable/scrollable price/disclosure/funding controls, funding Cancel retains review, real clinician withdrawal closes stale acceptance, no remaining Review-and-accept action, explicit patient request cancellation. No financial reservation on this withdrawn path |
| Immediate no-supply browser | Real immediate publication with an explicit required language unavailable in this scope; server eligible_supply0. Honest waiting/fallback, scheduled draft reuses service/preferences; original request cancelled explicitly. Available/reserved balances unchanged. No fabricated offers or silently widened constraints |
| Current appointment state | Both roles show confirmed after the durable match, then Cancelled after authorized cancellation. Reload verified; matched request/accepted offer history remains distinct |
| Focused backend regressions | Four pass: owner-scoped persisted request snapshot; private competing offers/insufficient funds/atomic match; immediate continuous-start grid boundary; concurrent two-patient slot claims. Unchanged expiry/disclosure/cancellation rules exercised through those APIs; no full hosted-call/financial suite rerun |
| Financial preservation | Each accepted test appointment has one booking journal and one release after authorized cancellation called twice. Balanced postings retained; no reset/repair. Owner reconciliation passes main11 patients/8 clinicians and isolated16 patients/6 clinicians |
| Private configuration/files | Original24 private credential/provider/manifests byte-identical; site config values identical. No access switches, schedule rules, approvals, credentials, seeded balances or shared services overwritten |

The complete two-role browser flow ran at `53f28ef355252e0a6d63da13edb6ac279d5cc5ce`; subsequent runtime changes only added truthful post-match appointment status and the hidden-draft guard. Those additions were checked against the final build. Its acceptance/form/API logic and visual styles are byte-identical to that passing flow; unchanged evidence is reused rather than republishing requests needlessly.

Harness diagnosis was kept separate from product defects: one zoom attempt incorrectly reused a cookie context and was corrected to separate persistent contexts. Existing accepted-offer/tour popups were dismissed using their real controls, never hidden/force-clicked. A withdrawal assertion initially expected exact text without the accompanying Close button; direct browser inspection confirmed the correct Withdrawn card, closed review and recovery notice. The resumed assertion checks the actual notice and absence of an acceptance action. The same persisted requests were retained; none were deleted/reseeded or backdated to manufacture a pass.

All writes were isolated synthetic flows. Two demonstration funding additions went through the existing UI/ledger; test appointments were cancelled through the authorized API and audit entries retained. Withdrawn/no-supply requests were cancelled explicitly. The test site scheduler/workers were not activated; no SMS/email provider delivery occurred. Main preview-owned processing remains running, unchanged. The temporary8029 browser server is stopped after verification.

## Rendered Comparisons

Screenshots: `docs/screenshots/request-workspace/`.

| Reference | Application / visual inspection |
|---|---|
| D01, D03 | Guided composition/preferences/privacy; compact active/history index replaces the old full-list form. Existing type, controls, borders, spacing and disclosure components retained |
| D05, D09 | `patient-waiting-1440`, `patient-offers-*`, `patient-acceptance-*`, matched/current-status images: real state rail, compact comparable cards, profile and funding/acceptance dialogs |
| F02, F03 | `clinician-response-*`: compact recipient selector, authorized narrative/disclosure context, approved offering/time/quote editor. Detail expansion is deliberate; no clinical authorization inferred from copy |
| F04, F13–F15 | `clinician-waiting-1440`, `clinician-accepted-1440`, current-status and200% images: private outcomes and appointment handoff integrated without a second offers page |
| Mobile, locales, zoom, empty states | `preview/`,390/768 role images, `patient-no-supply-390`, and actual200% captures. Whitespace/wrapping, button reachability, dialogs and scrolling inspected, not just overflow assertions |

Reference files were rendered locally at the same1440×1000 viewport/100% zoom. Images were opened and compared visually. The owner's explicit one-page instruction supersedes the old multi-screen composition: a compact persistent selector and local panels/dialogs are intentional deviations, not a claim of pixel identity. Actual names/prices/supply and outcomes remain backend facts; reference fictional ratings/amounts are not copied. The reference's older three-minute copy remains superseded by the approved unvalidated3–5-minute target. Source-specific screenshots for unchanged states remain valid as explained above.

Owner visual acceptance is still pending. Native-language approval, live SMS/email delivery, physical-device calls and real-market response-time performance are external/manual gates, not claimed. Existing individual/couples calls, End/revocation, notes/recipient isolation, account/crop, availability and earnings behavior were not changed. Prior valid hosted-call/migration/fresh-install evidence is reused; no new fresh-install run is claimed for this frontend-only change.

## Reviewer Walkthrough

1. Patient → Requests → New request. Describe support, select timing/service/language/format and review disclosure before publishing.
2. Stay on the page: the selected request shows real progress. Open a clinician's profile pane and review a private offer. Add funds inside the dialog if needed; acceptance rechecks eligibility/time and reserves once.
3. Clinician → Requests. Select one eligible request, inspect authorized details, choose an approved offering/time and optionally set a custom quote. Send; the same page shows its waiting/accepted outcome.
4. Use Your offers/History and reload to confirm persistence. Open the appointment only after acceptance; its actual join window and status remain authoritative. Request availability remains managed by the accepted dashboard card.
5. Test no-response alternatives or cancellation deliberately. Unpublished drafts survive local navigation, but refresh discards unsaved text; no health text is persisted in browser storage.

Keep draft PR #47 unmerged. No remote update, shared dependency repair, new modules or reseed is authorized or performed by this change.
