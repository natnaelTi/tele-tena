# Explicit consultation-note sharing

MVP/reference E11: clinician notes are private by default, with an explicit option
to publish the chosen revision to the appointment's patient. The separately
entered patient summary has its own publication flag. No affiliation, partner,
reviewer or payer relationship adds recipients or grants private-note access.
Two-adult appointment recipients remain a separate, unimplemented release gate.

`tt_note_revision.note_share_selected` records draft intent;
`note_published` records the final publication decision. Both default to 0.
Saving or previewing a selected draft exposes nothing to the patient. Only the
treating clinician may save/preview/finalize after the call is Ended. Finalization
publishes only explicitly selected content, records an immutable revision and
uses the existing exactly-once completion/earnings workflow.

The patient detail query selects only rows with `note_published=1`, exposing
`shared_consultation_notes` with text/revision/time. Unshared text, clinician
private-note objects, draft selections and account identifiers are omitted.
The separate summary query still requires `summary_published=1`. Private tables
have no generic DocType/read/report/file interface. Server ownership checks run
before either query; operational reviewer roles grant no clinical access.

Amending creates a new draft; it does not rewrite a published revision. The
amendment begins private unless explicitly selected again. Previously published
notes/summaries remain visible in history; the UI does not suggest they can be
unseen. A finalized query and re-finalization cannot change old flags. Publication
changes use a new draft and explicit finalization, without a second earning.

Additive v1.31/v1.32 patches are included in normal migration and fresh-install
bootstrap. Existing notes retain publication and selection 0; no historical
sharing, financial settlement or outcomes are inferred. Back up code/database/
private files together before migration. Rolling back code alone is insufficient.
The isolated-site migration and exact original-row/repeat checks passed; current
fresh-site installation and Frappe 16 verification remain pending. Current evidence:
[mvp-journey-verification-2026-10-09.md](mvp-journey-verification-2026-10-09.md).
