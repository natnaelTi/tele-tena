# TeleTena operational design integration

7 October 2026. Authorized target: implement the complete approved design inventory and extended modules in the existing React/TypeScript + Frappe/ERPNext architecture. The 142-screen design gallery remains a separate prototype. Do not replace the existing product with the static gallery or create a second authoritative wallet.

## Current slice

Based on 62604e6 (draft PR 14), preserving PR 12–14 ancestry. Two-sided practical homepage, server-state request motion, clinician-owned paged offers/history endpoint, masked patient label from the original disclosure snapshot, accepted-appointment handoff and withdrawal are added. Existing dispatch, offer submission, atomic booking and reservation logic remain authoritative. No schema change is required for this slice; offer records already persist their lifecycle and appointment reference.

Motion never fabricates an ETA, receipt, offer or booking. Changing prompts describe current facts. Reduced-motion users receive static text. No request narrative or competitor quote is copied into the new history response. The clinician must authenticate with the clinician role and matching profile. The appointment join is actor-scoped. Limits use bounded paging; read-time expiry does not require a scheduler write.

The homepage query is passed through in-memory navigation state, not a new URL query string. Existing patient profiles returning from sign-in can return to discovery. A newly created account still completes onboarding; preserving the original query through every onboarding step requires follow-up acceptance work. Discovery is still a service/name filter, not a complete natural-language classification engine.

## Remaining implementation sequence

1. Finish the mental-health core: settle PR dependencies; fresh install and migration preservation; verify clinician history authorization/pagination, live immediate dispatch, rescheduling, returning-clinician flow, ratings, full service taxonomy and vetting evidence. Port every A–I screen state to real commands and records.
2. Complete finance and operations: repair and reconcile legacy demo records by owner; verify call completion → pending earnings → dispute/release → payout reservation; implement provider-supported funds/refunds/payouts only after the permitted arrangement is confirmed. Live SMS/email, language review, physical devices, clinical escalation and support/dispute operations are release gates.
3. Implement clinic teams and shared adult care: distinct roles and explicit encounter grants; calendars/resources; separate adult eligibility/consent and private intake; multi-participant authorization and recipient-specific summaries. Clinic membership and payment never grant blanket records access.
4. Implement laboratory workflows: versioned test definitions and specimen constraints, orders/referrals, collection/chain of custody, review/release/corrections and scoped sharing; partner integrations need approved contracts and validation.
5. Implement optional subscriptions, second opinions and medical travel: durable entitlements/provider events, credits without a second wallet, independent case consent, licensure/jurisdiction validation, conditional estimates and coordinator roles. Basic access to one's records remains available without a subscription.

`operational-screen-map.json` preserves every approved screen ID and maps it to a module and required contract. Every item needs its specific API, data model, actor rules, errors/empty/loading states, localization, evidence and migration story before acceptance. Family mappings are implementation starting points, not claims of completion.

## Verified here

Frontend TypeScript/production build passes; lint exits successfully with existing warnings. Four isolated offer-status tests pass. Dependency checkpoint (3 tests), service-worker privacy checks, Python compilation and whitespace checks pass. The design prototype has separate DOM/browser evidence.

## Not verified here

This execution environment has no Frappe runtime, Bench service or MariaDB site. The new history assertions were added to the existing two-clinician integration regression but were not executed here. No Frappe integration, migrations, fake/live media, live SMS/email, financial reconciliation, browser authentication or actual React/backend journey was run for this slice. No merge or Selfmade deployment occurred. Do not mark this draft operational or install over the remote site without running these checks on the isolated compatibility Bench.
