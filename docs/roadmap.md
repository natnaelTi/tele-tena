# Product roadmap and capability boundaries

This roadmap reconciles the agreed product contract with the current delivery tracker. The tracker and operational screen map are evidence sources; a planned row is not evidence that it works. PRs #12–#15 remain open stacked work (PR #15 → #14 → #13 → #12); PR #11 is an open availability hotfix. Do not infer a merged/deployed state from this roadmap.

## Demonstration sequence

1. Establish safe accounts, adult patient onboarding, manually approved clinician applications and individually approved service scopes.
2. Provide direct discovery and booking, immutable disclosure and policy snapshots, transactional simulated patient reservations, explicit consultation documentation, and the demonstration earnings subledger.
3. Provide private patient requests and clinician offers. Immediate requests require fresh clinician presence and an explicitly enabled service policy; scheduled requests seek future appointments. The current dependent implementation passed a packaged scheduled request→offer→acceptance journey and its Frappe 16 regressions on 2026-10-05, but remains under broader acceptance review and does not promise a three-minute match.
4. Complete route-by-route responsive design and browser acceptance, including recurring availability, account/payment summaries, call states and role tours.
5. Close remaining demonstration gaps: clinician records/documentation polish, consent-aware couples participation, ratings based on real completed feedback, cancellation/rescheduling/no-show workflows, and authorized extension rules.
6. Establish pilot operations and safety policies with the clinician/operator before exposing a real pilot. Real payment custody, ERPNext accounting, settlement, credential verification, emergency response, SMS delivery confirmation and native translation approval remain external readiness work.

## Open-request decisions from prior contract

- Requests are private; there is no public health-request feed.
- “As soon as possible” and “Schedule for later” are distinct. The immediate three-minute target is measured from publication to confirmed appointment creation, not to a future booking. Time to both participants joining is a separate metric.
- Matching is deterministic: active manual approval, service-scope approval, language, format, valid service schedule and non-conflicting slot. It is not a diagnosis, paid ranking or lowest-price auction.
- Clinicians receive only the request disclosure snapshot needed to respond. Patient-authored free text can identify the author. Non-selected clinicians cannot inspect offers or broader records.
- Offers do not reserve funds or hold slots. Acceptance revalidates authorization, expiry and availability and uses the existing appointment/reservation transaction. Insufficient funds leave an offer/request retryable only while still valid.
- A bounded eligible group receives notices. Current in-app reconnect uses authenticated polling; notifications contain no request text or identity. The three-minute target depends on real coverage and response behavior and requires pilot evidence.
- Presence expires server-side. Current demonstration defaults (90-second presence; 15-minute request and offer lifetimes; configured per-site publication/offer limits) are adjustable demonstration values, not agreed commercial SLAs.

## Approved future capability groups

The full approved target now includes the groups below. The group names indicate
product scope, not shipped capability:

- Human-led clinician identity/qualification vetting, individual scope decisions,
  credential lifecycle and multidimensional non-composite trust indicators.
- Linked service categories, professional scopes, approaches, patient support
  topics, participant formats, typed versioned service attributes and tailored
  offerings. Clinical catalog entries remain drafts until medical-lead review.
- Persisted clinic profiles, staff/membership roles, affiliation checks, resource
  scheduling and encounter-specific record grants.
- Adult multi-participant care with independent identities, invitations, consent,
  disclosure, LiveKit authorization and recipient-specific notes.
- Laboratory/diagnostics orders, partner roles, specimen custody, review,
  correction, release and consent-based sharing.
- Subscription entitlements, second-opinion case-sharing, and medical-travel
  coordination with conditional estimates and jurisdiction checks.
- Auditable clinic/lab/financial/routing/support administration with separation
  between vetting, clinical records and finance permissions.

## Explicitly outside the current implementation

Clinic membership/workspaces and referral attribution, natural-language clinical matching or relevance feedback, ratings, couples consent, mutual rescheduling, no-show workflows, email summary delivery, real money movement, real credential verification and emergency escalation are not represented as working features. See `mvp-delivery-tracker.md` for current status and evidence.

## Current vetting and routing checkpoint (2026-10)

The dependent `feat/vetting-catalog-routing` work adds native catalog records,
an explicitly inactive sourced catalog proposal, a human-reviewed per-scope
application/decision path, readiness reason codes, scope revalidation at offer
and acceptance, continuous immediate-start selection, and bounded progressive
private notification waves. Existing legacy review services remain separately
marked and are never silently promoted into the public catalog. This does not
complete a clinical taxonomy or credential-verification workflow. The proposed
rubric is not an agreed rubric and needs medical-lead approval; independent
credential verification, affiliations, evidence-by-scope, appeals, expiry and
reverification UI, full jurisdiction/accessibility checks, reliability/experience
ranking, patient feedback, and native catalog review remain pending. See
`vetting-routing-verification.md` for local failure evidence and verification
boundaries.
