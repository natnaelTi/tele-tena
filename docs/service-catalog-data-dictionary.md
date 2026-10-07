# Service catalog and data dictionary (draft for clinical review)

Status: structurally implemented in this branch; all newly curated definitions remain non-bookable drafts until the medical lead approves terminology, eligibility, professional-category requirements, jurisdiction rules, and workflow capability. This catalog is a starting set, not an exhaustive clinical taxonomy. Patient support topics are not diagnoses.

## Linked domain models

- **Service category** is broad navigation (for example psychotherapy, counseling, or psychiatric consultation).
- **Service definition** is an adult service and approval scope with a stable key, version, population, participant structure, allowed delivery formats, credential requirements, location/jurisdiction policy, booking rules, required consent/intake schema, workflow capabilities, effective dates, and lifecycle status. The native `Tele Tena Service` DocType remains the source of truth used by scopes, offerings, discovery and appointments.
- **Treatment approach** is a separately controlled term with evidence requirements (for example cognitive behavioral or interpersonal approach). A selected approach never grants a service scope.
- **Concern/support topic** is a patient-facing search phrase such as stress, grief or relationship difficulty. It is not a diagnosis and does not authorize clinical interpretation.
- **Participant format** is individual, couple, family or group. Only individual services are bookable in this pilot; the other formats remain catalog-only pending consent workflows.
- **Clinician offering** is a clinician-owned title/description/price/duration and booking format within one approved service. It cannot expand authorization; multiple offerings can share a scope.

Storage note (2026-10): v1.0's legacy unique key limited a clinician to one
offering per service. The additive v1.23 migration removes only that key and
preserves offering identifiers and dependent records. See
[`multiple-offerings.md`](multiple-offerings.md) for retry and compatibility
semantics and verification evidence.
- **Service attribute definition** has versioned fixed-type metadata (text, integer, date, boolean, controlled choice), allowed values, required flag, validation bounds, public/private/sensitive visibility, applicability and filter/matching flags. It cannot contain executable expressions. The schema records are present, but service-specific dynamic intake values and matching validation are not yet implemented; no arbitrary JSON currently drives matching.

The core service fields are typed Frappe fields. Localized labels/descriptions and synonyms are represented as separate fields/controlled terms where present; catalog search synonym support is incomplete. Dynamic attribute values are not yet collected or validated by runtime APIs. A future inactive diagnostics schema demonstrates `specimen_type`, `preparation_requirements`, and `expected_turnaround`; it is not an operational or advertised laboratory service.

## Draft adult service set

| Key | Patient-facing draft label | Category | Intended scope / status |
|---|---|---|---|
| `initial-psychotherapy` | Initial psychotherapy consultation | Psychotherapy | Adult individual; draft, not bookable |
| `ongoing-psychotherapy` | Ongoing individual psychotherapy | Psychotherapy | Adult individual; draft, not bookable |
| `individual-counselling` | Individual counseling | Counseling | Adult individual; draft, not bookable |
| `stress-adjustment-support` | Stress and life-change support | Counseling | Adult individual; draft, not bookable |
| `grief-support` | Grief and bereavement support | Counseling | Adult individual; draft, not bookable |
| `relationship-counselling` | Relationship counseling | Relationship care | Adult individual for this pilot; draft, not bookable |
| `premarital-counselling` | Premarital counseling | Relationship care | Adult individual; draft, not bookable |
| `separation-support` | Support during separation or divorce | Relationship care | Adult individual; draft, not bookable |
| `psychiatric-assessment` | Psychiatric assessment | Psychiatry | Adult individual; requires locally reviewed medical scope; draft, not bookable |
| `psychiatric-follow-up` | Psychiatric follow-up | Psychiatry | Adult individual; requires locally reviewed medical scope; draft, not bookable |

Couple/family/group entries may be added as inactive catalog definitions. The workflow must reject offerings and bookings for those structures until individual participant consent and room/record policies exist.

## Controlled approach and concern seeds

Approaches: cognitive behavioral, interpersonal, psychodynamic, humanistic/person-centered, behavioral, integrative, problem-management/psychosocial support, stress-management, and supportive counseling. These are searchable claims only; clinicians select an approach per scope application and reviewers record evidence/restrictions.

Support topics: anxiety-related difficulties, low mood, stress, grief and loss, life transitions, relationship difficulties, communication concerns, and premarital preparation. These are patient language, not diagnostic labels.

## Evidence and review

Terminology is versioned `tele-tena-adult-catalog-1`, status `draft-clinical-review`. New catalog data is seeded idempotently and does not change historical appointment snapshots. Legacy synthetic service rows are marked `legacy-test` for normal discovery while remaining addressable by existing appointments. A new configuration entry can use current workflows; a materially new operational workflow still requires implementation and safety review.

Reference basis (not a local credential rule): WHO mhGAP provides evidence-based intervention guidance and adult anxiety/stress/depression modules; APA describes psychotherapy approaches and recognizes individual, couple, family and group formats. Ethiopian professional credential/jurisdiction requirements must be selected and verified by the responsible medical/legal reviewer; these references do not certify TeleTena clinicians.

- [WHO mhGAP guideline, third edition (2023)](https://www.who.int/publications/i/item/9789240084278)
- [WHO mhGAP recommendations announcement (2023)](https://www.who.int/news/item/20-11-2023-who-issues-new-and-updated-recommendations-on-the-treatment-and-care-of-mental--neurological-and-substance-use-conditions)
- [APA: Different approaches to psychotherapy](https://www.apa.org/topics/psychotherapy/approaches)
- [APA: Psychotherapy overview and delivery formats](https://www.apa.org/topics/therapy/)
- [Ethiopia Ministry of Health: EHPLE](https://www.moh.gov.et/ehple)
- [Ethiopia Ministry of Health: professional licensing requirements](https://www.moh.gov.et/Voluntary_Service_Requirement)

Catalog source/reviewer/version fields are stored with each definition. Native-language patient copy and all clinical scope mappings require human review before a pilot.
