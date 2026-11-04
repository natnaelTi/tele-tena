# Application Workflow Revision — Verified Local Candidate

Runtime/install pin `c30d4cdff475a91f864af5bab9aafa329040e33a`, branch
`feat/application-tracker-assisted-entry`, dependent on draft PR50. Later evidence
and documentation commits do not change runtime. Preview:
http://127.0.0.1:8017/teletena/ ; site
`teletena-mvp-presentation.localhost` (Frappe15.121.2/ERPNext15.121.6).
Compatibility/browser acceptance uses Frappe16.2.1/ERPNext16.1.0/Python3.14.2
on the separate isolated communications clone. No remote deployment or merge.

## Defects and Resulting Journeys

The former clarification flow returned clinicians to a large submission form and
stored generic evidence without necessarily linking it as a license. Scope intake
also copied PDF licenses only, although professional profiles accepted license
images. The new typed response links validated PDF/JPEG/PNG license bytes and hashes
into the scope's license field and the current professional draft selection. Earlier
submissions, evidence rows and decisions are retained; reclassification appends a
new typed link and never rewrites the original document's purpose.

**Clinician:** Service Applications → one application → Information Requested →
focused popup containing only requested items → Submit Additional Information →
Resubmitted for Review. Error/close/reopen retains in-memory responses; successful
submission and reload show persisted status. Existing already-supplied files can
be selected instead of reuploaded. Legacy untyped requests show their original
reason and an explicit optional document-category choice, without inventing what
the earlier reviewer selected. General approval never grants service approval.

**Reviewer:** primary Service Applications → searchable/status queue → grouped
application details/current documents → Review and Decide → focused existing
assessment steps. Request Information selects exact document/field categories and
records the reason. Missing license/unfinished approval checks do not block a
nonapproval decision. Approval still requires the existing full rubric, license,
source verification and service-definition guards. The current license appears
in both its document section and License Document to Verify selector.

**Email assistance:** verified clinician chooses services and requests help from
onboarding or the tracker → supplies information/authorization by email → reviewer
opens Applications → Email-Assisted Applications → six short sections → saved draft
→ private authorization PDF, source reference, received date and seven separate
recorded statements → Submit With Recorded Email Authorization → separate general,
scope and language reviews. The owner explicitly selected reviewer submission with
recorded email authorization. No impersonation, forged UI policy acceptance,
automatic credential verification or role/scope approval is introduced. Verified
sign-in contacts help the reviewer associate the correspondence with the right
account. This records manual correspondence, not automatic inbound-email ingestion.

## Requirement / Route / State Acceptance

The existing `mvp-screen-acceptance.json` remains the authoritative MVP matrix.
This table details the bounded revision; new compositions extend the approved
B10/B11 application-review/progress and I02/I03 reviewer-list/detail references.
Typed response and email-assistance states were absent from that prototype and
are explicit owner-requested extensions of its panels, forms and dialogs.

| Role / Route / State | Functional Result | Visual Result / Remaining Review |
| --- | --- | --- |
| Clinician `/clinician/vetting` | Search, status filters, per-service links, new-entry route; Information Requested distinct from Resubmitted | Inspected390/768/1440 and200%; owner acceptance pending |
| Clinician `/clinician/vetting/:id` | Current typed documents, feedback/history, private preview, preserved legacy snapshots | Grouped background/license and separate timeline; owner review |
| Detail response dialog | Only requested fields/files, existing-document reuse, malformed/missing-file recovery, retained input, reload after success, idempotent backend retry | Mobile/desktop and actual200%, Escape/focus; normal dialog scrolling preserves submit access |
| Reviewer `/admin/vetting` | Primary navbar entry, status/search queue | Shared list/status treatment; actual200%; owner review |
| Reviewer `/admin/vetting/:id` and `/review` | Dedicated current facts/detail; focused decision steps; typed Request Information, linked license selection | Responsive grouped evidence, collapsed historical snapshot; owner review |
| Onboarding / assistance popup | New email OTP clinician requests assistance without completing the full form; saved work retained | Responsive existing dialog; owner review |
| Reviewer `/admin/assisted/:case` | Case authorization; profile/language/CV/license save/reload; recorded email declarations; two separate pending scopes; no inferred language/general/scope approval | Six section selectors;390/768/1440 inspected; owner review |
| Reviewer Help & Tours | Guide follows queue/detail/review/typed response; email-assisted walkthrough | Existing universal help island preserved |

## Checks Actually Run

- **16 Frappe16 backend tests pass**, rollback-only: retained general/scope intake,
  manual grant, approval/nonapproval guards, atomic failure rollback, typed license
  mapping, image bytes/hash preservation, original historical evidence, legacy
  response categorization, retries, wrong-purpose/unknown-field denial, private
  document denial, assisted authorization/identity restrictions, declaration source,
  separate pending scopes and real assistance-queue SQL join. Browser testing caught
  and fixed a mixed-collation queue join without changing framework table collations.
- **Production-built two-role browser flow passes:** reviewer requests license plus
  explanation; clinician receives targeted dialog, recovers invalid upload, closes/
  reopens, resubmits; reviewer sees the actual current license and previews it; reload
  persists status and verification selection. No mocked API success responses.
- **New registration/email-assisted flow passes:** private random test OTP; assistance
  request; independent reviewer session; profile/language/CV/license entry; draft
  save/reload; private authorization and separate acknowledgements; submission;
  clinician tracker has two pending scopes and zero inferred approved scopes.
- **390/768/1440 and actual Chromium200%:** native1440physical/720CSSpx/DPR2,
  reduced motion, keyboard dialog/Escape and normal scrolling. Screenshot inspection
  covered composition, type, status contrast, wrapping and form grouping, not only
  overflow assertions. Full-page captures may place sticky navigation at its current
  viewport boundary; native viewport zoom captures are also retained.
- **Native worker:** resubmission queues all three durable channels. System is
  Available; email is ProviderAccepted exactly once by the private test adapter.
  This email-only fixture's SMS is correctly Unavailable with zero attempts, not
  fabricated delivery. Additional phone-link test encounters the isolated site's
  exhausted SMS budget; production caps are not altered. Retained earlier
  `scope-information-fix-2026-11-04.md` covers SMS adapter dispatch with a verified
  synthetic phone. Unit tests assert the three rows and idempotent response.
- **Native additive migration/repeat:** Frappe16 clone preserves102 original tables/
  18,488 rows and private/configuration state. Main preview complete verified backup,
  migration and repeat preserve102 original tables/19,301 rows/26 private/config
  files; strict repeat compares106 tables after the four additions. No reseeding,
  password/settings/provider/payment-mode reset or historical financial edit.
- **Read-only main reconciliation:**11 patient owners,2 clinician owners,22 accounts;
  zero patient projection, clinician obligation, account/journal or balance errors.
- Locked production build, lint (existing nonblocking warnings), asset hashes and
  exact private-credential scan pass. Localization exchange5 and extraction2 pass.
  The full exchange has8,739 source rows and a200-row bounded source delta. Existing
  reviewed dictionaries are unchanged; no workbook draft was approved/imported.

Private logs, synthetic browser sessions and screenshots:
`/home/frappe/teletena-application-workflow/` (outside Git). Curated synthetic images
and before/current comparison notes: [screenshots](screenshots/application-workflow/README.md).
No real IDs, email authorization, passwords or OTPs appear in committed evidence.

## Schema, Operations and Remaining External Checks

v1.52 adds `tt_scope_information_request`, `tt_scope_information_response`,
`tt_assistance_case`, `tt_assisted_submission`; no existing value backfill.
Unique request/case keys, response digests and transactional locks protect retries.
IDs remain accessible only to owners and specifically assigned identity reviewers;
ordinary scope reviewers receive no new identification-document entitlement.
Authorization evidence uses existing private/no-store downloads. No package or
framework/Amazon/provider configuration change. Hosted calls, financial business
logic and unchanged broader MVP journeys reuse existing matrix evidence; no new
physical-device call or full fresh Frappe installation is claimed for this revision.

Owner UI acceptance, native-language approvals and live consenting-recipient email/
SMS receipt remain external. The diagnosed local SMTP reachability timeout is not
repaired by this application work. Draft policy content is not made legally approved
by recording its displayed version. Existing clinical/governance retention questions
remain unchanged; historical evidence is not deleted by current reclassification.

## Owner Walkthrough

1. Clinician: More → Service Applications. Open an Information Requested item.
   Read the reason; provide only requested fields or select an existing document.
   Submit, reload and confirm Resubmitted for Review.
2. Reviewer: Service Applications in primary navigation. Open that service, inspect
   its license/document section, then Review and Decide. Approve still requires full
   evidence; Request Information needs a reason and requested-item selection.
3. New clinician: onboarding → Request Email Assistance; choose preferred services,
   authorize help and use Contact for the configured destination/reference.
4. Reviewer: Applications → Email-Assisted Applications. Enter only the clinician's
   emailed claims, save sections, record the private authorization/source/date and
   separate policy/declaration statements. Submit; then use the ordinary distinct
   general, service-scope and language decision workflows.
5. Use Help & Tours → Reviewer Guide for the detailed decision and assistance steps.
   Check notification channel status rather than assuming provider acceptance means
   inbox/SMS receipt.

Selfmade installation/backup/rollback commands are in
[selfmade-translation-update.md](selfmade-translation-update.md). No remote action
has been taken. Main preview restart: from the primary app directory run
`../../env/bin/python scripts/local_review.py start` and `status` after WSL database/
shared cache services are available; do not start the compatibility bench instead.
