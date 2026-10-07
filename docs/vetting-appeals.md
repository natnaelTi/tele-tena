# Per-scope reconsideration workflow

This is the proposed demonstration process for reconsidering a human vetting
decision. The medical lead should approve the policy before real clinical use.
It does not replace the proposed vetting rubric or establish a legal appeal
right.

An applicant may submit one reconsideration statement against the latest
`Rejected`, `Suspended`, or `Expired` assessment for their own service-scope
application. The statement and reviewer response are private to that applicant
and authorized vetting approvers. Generic DocType APIs enforce the same owner
boundary. The unique assessment reference and the shared vetting transaction
gate make concurrent/retried submissions idempotent. A retry with the same
statement returns the original appeal; a changed statement cannot overwrite it.

An authorized approver records a rationale and one outcome:

```text
Submitted → Upheld
Submitted → Reopened → Clarification → Resubmitted → new full scope assessment
```

`Upheld` preserves the existing decision. `Reopened` is not approval: the
applicant must provide any requested information, resubmit, and receive a new
human decision through the ordinary mandatory checks. Scope authorization stays
revoked until that later decision explicitly approves it. Every prior
`Tele Tena Vetting Assessment` remains immutable; each appeal is a separate
append-preserved native DocType record linked to its basis assessment. A single
decision cannot be appealed twice. A later assessment may be reconsidered
separately. No appeal gives access to patient records, financial review, or
unrelated applicants' evidence.

## Limits

- Appeal deadlines, external independent reviewer requirements, and legal
  reconsideration rights have not been decided; no time window is invented here.
- Assignment of a second reviewer and formal conflict-of-interest checks are
  not implemented.
- The applicant can submit a short statement but cannot attach a new evidence
  revision until the reviewer reopens the application to `Clarification`.
- This workflow is an operational audit trail, not an external credential
  appeal or regulatory process.
