# Reviewer service-definition editor verification

Date: 2026-10-08

## Scope

The reviewer route `/teletena/admin/services` edits existing native `Tele Tena
Service` definitions and `Tele Tena Service Attribute Definition` metadata. New
and edited records remain inactive Drafts. This route cannot approve clinical
terminology, clinician vetting scopes, or activate a bookable service. Dynamic
attribute metadata is not a live patient intake form.

## Checks

- `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost env/bin/python tests/presentation.py Presentation.test_service_catalog_edits_are_typed_draft_only_and_reviewer_scoped`: **1/1 passed**. Covers approver draft save/edit, forced inactive/vetting-required state, invalid duration, private clinical field matching rejection, typed metadata save, review lock, and patient denial.
- `TELE_TENA_TEST_SITE=tele-tena-pr12-fresh.localhost env/bin/python tests/presentation.py`: **37/37 passed**. Uses isolated synthetic fixtures; does not migrate `erp.localhost`.
- `npm --prefix frontend run lint`: **passed with existing warnings**; no lint errors.
- `npm --prefix frontend run build`: **passed**.
- `scripts/build_review.py`: **passed**, generated and copied app-owned static assets with source SHA `e2d1617996919850b335cc93030a4f96b9e16005` at the time of this verification. This SHA is superseded by the final source commit noted below if later test/documentation changes are committed; rebuild before release.
- `scripts/browser-service-catalog.cjs` against the built Frappe route: **passed**. Reviewer signed in through the existing email/password path, created a synthetic inactive Draft, reloaded and reselected it, captured at 390/768/1440 CSS px with no horizontal overflow, and requested terminology review. The UI then locked edits; no clinical approval or activation was attempted.

The first browser attempt selected an older similarly named fixture. The list now displays the stable service code as a secondary identifier, and the rerun passed. This was a test-selection defect, not a service-save defect.

## Screenshots

- [`reviewer-draft-390.png`](screenshots/service-catalog/reviewer-draft-390.png)
- [`reviewer-draft-768.png`](screenshots/service-catalog/reviewer-draft-768.png)
- [`reviewer-draft-1440.png`](screenshots/service-catalog/reviewer-draft-1440.png)

The captured 390px layout uses the mobile workspace navigation and a single-column definition editor. The screenshots include synthetic service fixtures only.

## Remaining limitations

Clinical terminology and source approval, service activation, treatment-approach and concern editor workflows, runtime dynamic intake validation, medical-lead rubric approval, clinical credential/jurisdiction verification, and human native-language review remain pending. The current screen has English copy with provisional Amharic and Afaan Oromo strings; this is not native review. This slice does not claim acceptance of the broader 142-screen inventory.
