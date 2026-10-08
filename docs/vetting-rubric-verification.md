# Versioned vetting rubric verification

## Implementation

Branch: `feat/vetting-rubric-assessment-engine`, stacked on the open draft
PR #39 head (`feat/relationship-acquisition-attribution`, 524c7f8). Rubric
implementation commits are `4cb0c99c288646077f83318d32e9dd98cdd1fc53` and
`49b8be1aaab3e3dc8c989821152893ae1643baf6`. The latter exposes the full
definition to reviewers before approval. The credential provenance slice is
being added in the current review commit. The final packaged source SHA is the
value in `tele_tena/public/review/release.json`, generated after this report
commit.

The rubric begins as `proposed-1.0`; no historical approval was assumed. Patch
v1.27 adds a read-only structured-assessment snapshot field. Patch v1.28 creates
an idempotent version registry and the separate Medical Lead role, then seeds
the proposal without overwriting it on subsequent migrations. Proposals cannot
be edited in place. Each new scope application pins the active rubric, while
each assessment snapshots the definition digest, dimensions, reviewer
rationale, and application-scoped evidence revision/hash. Tampered or missing
definitions fail closed. Scores organize evidence; mandatory gates and human
scope decisions remain independent.

Approvers can propose and inspect versions. Only an explicitly assigned
`Tele Tena Medical Lead` can approve a proposed version with a rationale;
approval supersedes the previous active version and an exact retry is
idempotent. Public signup never assigns this role. The React manager is embedded
in the vetting queue and also has a focused `/teletena/admin/rubrics` route.

New credential-verification decisions also require an issuer/source, a
non-future check date, a reference to the registry record, and license or
registration evidence attached to that same scope application. The assessment
stores a digest-checked provenance snapshot containing reviewer, time, evidence
revision and content hash. Applicant and patient responses omit it. Historical
assessments are preserved without fabricated provenance; a blank value means
the old decision did not capture these details.

## Verification performed

- Backed up `tele-tena-pr12-fresh.localhost` database and public/private files
  before schema changes.
- Frappe 15.121.2 site migration v1.29 passed; repeat migration passed.
- `tests/presentation.py`: **45/45 passed**, including provenance migration
  repeatability and preservation of historical assessments, required source
  and evidence fields, same-scope license evidence, privacy, and digest-tamper
  rejection, refusal of provenance without the verified flag, and rejection of
  future check dates, as well as registry migration
  idempotency, immutable proposal, patient denial, Approver denial of approval,
  Medical Lead approval and retry, active-version selection, and definition
  digest tamper detection.
- `npm run build`: passed with the existing large LiveKit chunk warning.
- `npm run lint`: exit 0 with existing repository warnings.
- `tests/integration.py`: **24/24 passed** after the provenance changes.
- `scripts/build_review.py`: packaged commit recorded in
  `tele_tena/public/review/release.json`; artifact verification passed with 40
  generated files, expected scope, and no private credentials.
- Production-built browser check at `http://127.0.0.1:8017/teletena/`: the
  synthetic reviewer opened `/teletena/admin/vetting`, inspected the complete
  proposed definition and digest, and was denied the Medical Lead-only route.
  Captures at 390/768/1440px are in `docs/screenshots/vetting-rubric/`.
- The built applicant/reviewer journey submitted a synthetic scope application,
  let the reviewer open its private evidence, and verified all four credential
  provenance controls at 1440 and 390 px. Screenshots are
  `docs/screenshots/vetting-rubric/credential-source-reviewer-{1440,390}.png`.
  The browser check did not submit a credential decision or alter a scope.
- The new provenance inputs have localization keys in English, Amharic and
  Afaan Oromo. Native-speaker review remains pending.

The preview uses Bench `/home/frappe/frappe/frappe-bench`, site
`tele-tena-pr12-fresh.localhost`, and Gunicorn master 287561 bound to loopback
port 8017 with the matching app checkout. It serves built Frappe assets, not
Vite. The site's scheduler is enabled, but this rubric feature schedules no
jobs; no worker execution is claimed for this change.

## Not verified / still required

- A clean fresh-site installation containing v1.27-v1.29 has not run. The
  requested disposable site `teletena-pr34-fresh.localhost` was not present at
  the time of this check; the existing review site was preserved.
- No real Medical Lead has approved the proposed rubric. This is not an agreed
  or medically validated standard, an accreditation, or credential verification.
- Browser checks used English. Amharic/Afaan Oromo native review and complete
  zoom, keyboard and screen-reader acceptance remain pending.
- Frappe 16 fresh-install verification, live providers, physical-device calling,
  and the broad A–I product scope remain pending or external as recorded in the
  delivery tracker.
