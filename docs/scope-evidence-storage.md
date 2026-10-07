# Per-service-scope applicant evidence

This additive v1.16 workflow lets an applicant attach supporting PDFs to an
individual service-scope application. It complements the clinician-level CV;
it does not verify a credential, activate a catalog definition, or approve a
service scope.

## Storage and permissions

- `Tele Tena Scope Evidence` is the native Frappe metadata DocType. Each row is
  an immutable evidence revision linked to one scope application, applicant,
  evidence category, upload time, size and SHA-256 digest.
- Binary PDF bytes are stored in the private `tt_scope_evidence_content` table.
  The content is not a `File` record and has no public or generic Frappe file
  URL. The only download endpoint checks the authenticated applicant owner or
  `Tele Tena Approver` role before returning content. App API responses use the
  existing private/no-store middleware.
- Applicants can upload only to their own `Draft` or `Clarification` scope
  application. A replacement creates a higher revision; prior bytes and
  metadata remain available in the audit history. Submitted, resubmitted,
  approved, rejected, suspended and expired applications cannot be changed by
  applicants.
- Reviewer assessment records snapshot the evidence IDs, types, revisions and
  digests visible when the human decision is recorded. This records the
  evidence set presented; it does not attest that an external authority was
  checked.
- PDF extension, size (5 MiB), base64 integrity, PDF signature and EOF marker
  are checked server-side. Malware scanning is not configured or claimed.

The metadata DocType is subject to owner/reviewer permission hooks and its
controller rejects generic writes. Binary content remains outside Desk,
reports, exports and unauthenticated routes. No existing CV or application
record is rewritten by migration.

## Verification

On the isolated Frappe 15 site, the presentation suite checks that applicants
can create revisions before submission, invalid and post-submission uploads do
not persist, unrelated clinicians and patients cannot download evidence,
reviewers can retrieve it, and the assessment stores the revision snapshot.
Fresh-site installation from an empty database and rendered applicant/reviewer
browser acceptance remain pending for this patch. Human credential checks,
medical-lead approval of the proposed rubric and external malware scanning are
separate gates.
