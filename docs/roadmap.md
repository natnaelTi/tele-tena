# Product roadmap and capability boundaries

This roadmap reconciles the agreed product contract with the current delivery tracker. The tracker and verification report are evidence sources; a planned row is not evidence that it works.

## Demonstration sequence

1. Establish safe accounts, adult patient onboarding, manually approved clinician applications and individually approved service scopes.
2. Provide direct discovery and booking, immutable disclosure and policy snapshots, transactional simulated patient reservations, explicit consultation documentation, and the demonstration earnings subledger.
3. Provide private patient requests and clinician offers. Immediate requests require fresh clinician presence and an explicitly enabled service policy; scheduled requests seek future appointments. This slice and dependent vetting/routing work remain under acceptance review; it does not promise a three-minute match.
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
