# Incremental refinements verification —14October2026

## Candidate and boundaries

- Installed baseline:800a591ac6af9c6c3b4afd61ed4353be4ff0826e.
- Requested refinements:5efe78527309f8dab9e2a5bb391114cba153a862.
- **Verified install/build candidate:deeb583fbbfaaf276acc51aef05982dbf28d27e8.**
  Contains both ancestors,PR44/PR43 and PR45 safeguards;no merge performed.
- Branch:fix/selfmade-incremental-refinements,dependent on PR45. Documentation-only
  follow-up commits do not change the installation pin or runtime artifacts.
- Why a descendant instead of exactly5efe785:the additional encrypted/scripted PDF
  test reproduced an accepted named-JavaScript PDF on5efe785. Frappe16's helper
  does not resolve the indirect root names tree. The candidate adds a single
  app-level `/Names/JavaScript` rejection. Framework remains unchanged. The test
  fails on5efe785 and passes on the candidate. No malware-scan claim.

Source/build metadata is exact:the compatibility app's `public/review/release.json`
recordsdeeb583 and all packaged asset hashes. Locked build used Node24.13.0.
Source/build inspection,diff and clean checkout were checked before building.

## Exact dependency,schema and configuration differences

Python requirements/pyproject are unchanged. Shared editable TeleTena rebuild was
approved by update-mode dry-run/preservation guard;all other installed versions and
editable/direct-source identities remain unchanged. Repaired staged Python3.14.2
runtime passes pip check. The already-applied Selfmade repair is **not repeated**.
No Amazon source,package pair or CLI installation is changed by the update.

Frontend adds only locked libphonenumber-js1.13.15. New v1.39 creates only
`tt_history_document`,with owner,filename,mime,content blob,size,hash,UTC timestamp,
owner/content/name unique constraint and owner/time index. It adds no historical
rows and does not rewrite existing tables. Fresh schema bootstrap invokes the same
patch;previous v1.39 fresh-install evidence in history-country-verification.md
remains applicable because DDL/bootstrap did not change. A new fresh installation
was not repeated for this incremental existing-install task.

No automatic configuration/access/registration/provider/financial change.
Optional offline country MMDB/trusted proxy settings and the default100MB owner
history quota are documented in history-uploads-and-country.md. Missing country
lookup remains manual/editable Ethiopia. Arbitrary forwarded IPs are not trusted.
Country selection does not enable SMS outside Ethiopian mobile numbers.

## Actual local checks

Environment:isolated compatibility Bench `/home/frappe/teletena-compat/bench`,
Frappe16.2.1 commit8f6e24728b86b7c6427908ed6536289a41ea9cf4,
ERPNext16.1.0 commitbb2bada1fde0ae7a3c3cad32bed781ebd470e27d,
Python3.14.2,Node24.13.0,MariaDB10.6.22,Redis6.0.16. Used already-repaired private
trial runtime;no global/original Bench package change or new repair execution.

| Check | Result/evidence |
|---|---|
| Ancestry/runtime diff | Both800a591 and5efe785 are ancestors of candidate. OTP/provider,review switches,accounting,booking,LiveKit and scheduler hook code unchanged. |
| Existing-install upgrade | Complete matched800 database/public/private/config plus existing private credential manifests cloned into `teletena-incremental-candidate.localhost`. Source800 snapshot,then **direct checkout/migration todeeb583**,PASS. No seed/setup/refresh called. |
| Preservation |75 original operational/native tables,1,309 rows unchanged using private hash-only snapshots;includes profiles,scope/clinical records,consent/disclosure snapshots,files/blobs,ledger/reservations and authentication/roles.6 original public/private files including credential manifests unchanged;all config values unchanged. |
| Credentials and owners |13 original stored passwords accepted.6 patient owners and5 clinician owners reconciled;balanced journals. Historical obligations unchanged. |
| Repeat migration |PASS on exact candidate;all the same original data/config/passwords and owner balances preserved. New history table initially empty;no fabricated files. |
| Existing history suite |4/4 PASS:owner retry/no-store/download,text/privacy preservation,other patient/clinician/reviewer/guest denial,invalid file/quota atomicity,verified-consenting onboarding and disabled-registration gate,trusted proxy boundary. |
| New constraints |2/2 PASS on candidate:ET canonicalization and US/UK/Kenya rejection without provider invocation;encrypted/named-script PDF rejection;valid JPEG/PNG and mismatched image-extension rejection. |
| Real browser upload journey |PASS on packaged candidate:existing password sign-in,country manual choice/help,keyboard picker,two files,third real drop,reload persistence,unchanged history textarea,owner download,own fixture removal.390/768/1440 captures privately in `/tmp/tt-history-browser`. No mocked success responses. |
| Real HTTP authorization/validation |PASS using separate existing patient/clinician/reviewer sessions,normal cookies/CSRF:server rejects extension/content mismatch,malformed PDF and decoded size above5MB. Owner download succeeds;other patient/clinician/reviewer/guest denied;no generic File resource bypass. Private/no-store,attachment,nosniff,sandbox headers confirmed. Only test-owned file removed. |
| Production packaging |Locked npm build and app-scoped native Frappe asset build PASS. Exact candidate source in release.json;asset hash/scope/no sourcemap/config/credential scan PASS against13 existing private passwords. |
| Lint |PASS,existing React hook/purity warnings remain. Existing bundle-size warning remains;no claim these warnings were fixed in an unrelated update. |
| Hosting permissions |Local public-only755/644 normalization tested;private modes unchanged. Remote nginx traversal and previously configured slash exception remain operator smoke gates. No nginx config regenerated. |
| Rollback |Matched800 SQL/public/private/config bundle verified,then native same-site rollback under800 source passed;all75 tables/1,309 rows,6 files,13 passwords and6/5 owners preserved again. No root password needed/no password in child argv. Empty additive history table retained,not deleted. |

Earlier test-harness failures were diagnosed,not suppressed:initial API login raced
pending guest bootstrap;waiting for bootstrap resolved it. Cache-Control assertion
now checks both required tokens regardless of their standard token order. The
**real** PDF acceptance defect required the focused app fix above. Private logs
retain diagnostics;no file bodies,credentials or clinical narratives are published.

Private evidence directory:
`/home/frappe/teletena-shared-repair/incremental-evidence` (mode700).
Key logs:direct-candidate-migrate.log,direct-candidate-preserved.log,
direct-candidate-repeat-preserved.log,history-tests.log,constraints-tests-fixed.log,
browser-candidate.log,http-privacy-candidate.log,build-candidate.log,
frappe-assets.log,asset-privacy.log,rollback.log,rollback-preserved.log.
No database dumps,site configuration,passwords or hash snapshots are committed.

## Scope of reused evidence and external limits

No financial/appointment/LiveKit/OTP authorization or scheduled-job code changed.
Their valid earlier acceptance evidence is retained;the expensive hosted-call
suite was not repeated for unchanged media behavior. New history files remain
owner-only even if text history was previously shared with an encounter. Uploads
are not implicitly disclosed to clinicians,reviewers,couples or clinics.

No live SMS/email/Amazon/provider call or transfer was made. No physical-device or
native-language approval claim. The optional live IP database/proxy configuration
and remote HTTPS/nginx/private-file tests are operator checks,not locally inferred.
No Selfmade service,data,credential,configuration,package or source was changed.
No demonstration data reinstalled and no public registration enabled.

Use [selfmade-incremental-refinements-update.md](selfmade-incremental-refinements-update.md)
for the ordered backup/build/migration/service/HTTPS/rollback commands. The repaired
shared environment and Amazon patch remain authoritative;older first-install and
shared-repair procedures are not prerequisites to repeat.

## Cleanup

Both task-owned disposable databases/users/sites and only their6 remaining queued
jobs were removed after checks. Private pre-upgrade/rollback evidence was retained.
The task's isolated HTTP listener,MariaDB and Redis processes were stopped;the
compatibility app checkout returned to its original62706f9. Frappe/ERPNext worktrees
remain clean. Original development checkout remains5efe785 and its existing8017
preview still returns200;this task did not silently switch that preview to the
new release. Selfmade remains unchanged until the operator executes the guide.
All guide shell blocks passed `bash -n`;all committed evidence is sanitized counts
and source/build identities rather than private snapshots or records.
