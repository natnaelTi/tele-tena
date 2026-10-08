# Human-led scope vetting rubric v1 (proposed)

Status: no previously agreed rubric was found in the product/architecture/backlog documents. `proposed-1.0` is now stored in an immutable version registry with a SHA-256 definition digest; the migration does not imply approval. It remains a **proposal for medical-lead approval**, not an approved credentialing standard or regulator accreditation. The system records reviewer evidence and decisions; it never autonomously verifies a professional or awards scope.

Each scope application pins a rubric version. Every assessment stores that version, a digest-checked definition snapshot, dimension scores, private rationale, and references to evidence revisions scoped to that application. Proposals are append-only; reviewers with the Approver or Medical Lead role may propose, but only a user assigned the separate `Tele Tena Medical Lead` role may approve a version. Approval supersedes the prior active version without rewriting existing applications or assessment history. A proposed version is not active for new applications until a medical lead explicitly approves it. Integrity mismatch fails closed.

The management route is `/teletena/admin/rubrics`. Role assignment is an administrator-controlled operational step; public signup never grants the Medical Lead role. Translation review, rubric governance assignment, and medical-lead approval are still pending. The proposed content below is not a clinical or legal policy decision.

## Mandatory gates (non-compensatory)

For each requested service scope, the reviewer must explicitly record Pass, Fail, or Needs information for:

1. Identity and submitted professional name are consistent with the evidence presented.
2. Professional category and qualification meet the service definition's approved requirement.
3. Issuing institution/authority and jurisdiction are recorded; required license/registration is current and human-verified against the appropriate source.
4. Required supervised practice, training and approach evidence are present for this scope.
5. Adult-only service suitability and population restrictions are understood.
6. No unresolved restriction, expiry, suspension or conflict prevents this scope.

Any Fail or unresolved mandatory item blocks approval regardless of scored items. Missing jurisdiction rules or unavailable verification sources result in `Needs information`/non-bookable, not presumed approval.

## Structured assessment dimensions

For reviewer organization only, each dimension may be rated 0–3 with evidence references and notes: scope-relevant education; supervised clinical experience; training in selected approach; adult population experience; ethical/privacy and safeguarding understanding; consultation/assessment interview. A weighted sum may help compare missing evidence, but it cannot override mandatory gates and cannot automatically decide approval. Reviewer notes and ratings remain private.

Reviewer outcomes per scope: `Approved`, `Request information`, `Rejected`, `Suspended`, or `Expired`. Each action records actor, time, rubric version, reason codes, free-text private notes, restrictions, evidence references, and prior decision. Clarification permits applicant resubmission and creates a new immutable review event. Reconsideration uses a separate appeal record tied to one immutable assessment. `Upheld` preserves the decision; `Reopened` returns the application to clarification and requires a new complete human assessment. An appeal never grants practice. The proposed process and its remaining policy decisions are in `vetting-appeals.md`.

## Credential wording

Use “TeleTena reviewed” only for a completed human review. Use “license verified” only when the reviewer records the authoritative issuer/source, date, identifier reference and expiry and has actually checked it. A resume, profile completion, phone verification, clinic affiliation, or score is not proof of a credential. A clinician's practice affiliation has a separate verification status and never establishes competence or records access.

## Reverification and lifecycle

Credentials may have `Pending`, `Verified`, `Unverifiable`, `Expired`, or `Suspended` status, with issuer, jurisdiction, valid-through date, source check metadata and reviewer. Scheduled expiry moves the related scope out of new-booking eligibility and flags already-booked appointments for operational review; it never deletes appointments or changes their historical disclosure/policy snapshots.
