# Shared dependency repair verification —14October2026

No Selfmade package,service,configuration,source checkout or customer data was
changed. Target remains the existing `/home/smcs/frappe-bench`. No separate
production Bench is proposed. Reviewable repair branch:
`fix/selfmade-shared-dependency-repair`,based on PR44's5efe785 checkpoint.
Original MVP branch and running8017 preview remain untouched.

## Source and artifacts

- Input Amazon source:7acdf6c8596c3a4f741675d2bb51dab6e6b95b14,clean per operator.
- Separate Amazon patch:6dccb8e63cc078ea1790d8b826d8fa3b4ed194e9,branch
  `fix/selfmade-maintained-boto`,in local repository
  `/home/frappe/teletena-shared-repair/ecommerce_integrations`.
  Runtime diff:one Boto3 requirement. Tests/docs/live-only helper are separate
  files in that Amazon repository,not copied into TeleTena commits.
- Version-controlled Git bundle,new wheels,exact pins,release manifest and
  SHA256SUMS:`/home/frappe/teletena-shared-repair/artifacts`,owned private folder.
  All hashes verified. Contains the seven selected versions,compatible preserved
  transitive wheels and Flit3.12.0 for offline isolated build. No private app
  source,credentials,site configs,dumps or financial/clinical data in this bundle.
- TeleTena target remains800a591ac6af9c6c3b4afd61ed4353be4ff0826e,not the newer
  local UI build. Correct update mode and complete backup helpers at that pin
  are retained. See selfmade-final-mvp-update.md and the repair procedure.
- Private baseline/plan/install/preservation logs,snapshots,copied trial environments
  and representative upgrade evidence remain under
  `/home/frappe/teletena-shared-repair`. Do not publish these directories.

## Passing checks

| Check | Actual result |
|---|---|
| All-app intersection | Supplied44-app/247-distribution audit:161 focused/source edges checked; all seven selected replacements fit. PaWaPay's missing distribution metadata is explicitly supplemented by its two source requirements; Frappe's two direct-source requirements independently protected. |
| Complete third-party candidate resolution | Normal pip resolution of201 exact target index-package versions passed with all protected constraints. All201 are installed in the isolated runtime; no unrelated target index version was substituted. |
| Native DuckDB | Supplied1.3.2 cp314 Linux x86_64 wheel SHA25608e1ef23c1772f047c4026d150ce3e1768c51318a943b56566300232c3374d24. Linked libraries present,actual native import and SELECT42/count queries pass. Index identity remains ordinary/index,not a substituted direct-source package. Production DuckDB remains unchanged;its wheel is not in the production repair wheel set. |
| Representative conflicted baseline | Reconstructed all eight reported pip-check errors on Python3.14.2 using normal pip operations in an owned trial environment. Obsolete urllib3 existed only while constructing that historical sandbox;the repair keeps2.6.3 and never proposes that downgrade on Selfmade. |
| Real repair path | Actual offline pip dry-run matched the guard,normal install with dependencies repaired seven selected versions,only duplicate Bench distribution removed. Healthy external5.29.0 retained,app-env CLI symlink tested. No `--no-deps`,relaxed constraints or framework upgrades. |
| Post-repair | Clean pip check;every original local protected distribution/version/editable identity retained;both direct-source hashes unchanged. All201 target index versions match supplied audit plus explicit replacements. |
| Guard regressions |9/9 PASS against the supplied audit:exact plan/preservation,unrelated replacement,same-version source swap,SDK pair mismatch,protected identity/version drift,duplicate CLI/unplanned addition,conflicting new app constraint,missing app rejection. Ed25519 and RSA-PSS-SHA512 round trips through retained http-message-signatures1.0.1/http-sfv0.9.9 with Cryptography46.0.7. |
| Amazon compatibility |10/10 PASS on repaired graph. Actual STS client and Stubber AssumeRole/AccessDenied;LWA success/rejection/timeout;Orders URL encoding/pagination/marketplace;Catalog/Finances;SigV4 independently compared to Botocore;actual loopback HTTP XML serialization/signing and503 retry;original bounded repository retry/exhaustion;regional STS endpoints;inherited HTTP-error response behavior. No actual Amazon access. |
| Supervisor exporter | Actual isolated Supervisor4.3.0 RPC test,three harmless dummy processes:in-use commands/PIDs retrieved,raw command/environment omitted. Temporary Supervisor/processes shut down. Remote supplied worker processes are actual Frappe helper modules;initial CLI cannot be inferred after Bench's execv. Remote RPC/pending-config check remains a required observation. |
| External CLI | Local separate existing5.29.0 CLI and its pip check pass;compatibility entrypoint resolves to that CLI. Remote external5.29.0 health/list-apps was supplied by operator,not falsely claimed as a Codex remote execution. |
| Guarded TeleTena update | On repaired runtime,actual update-mode snapshot→normal pip dry-run→approved TeleTena-only install→post-preservation PASS. No other package may be repaired as part of TeleTena installation. |
| Existing-site migration | Complete matched synthetic8f7ab9c database/public/private/config backup restored into separate `teletena-shared-repair-upgrade.localhost`,then migrated at800a591 under repaired runtime. Original26 tables/41 operational rows,6 private/config/credential files and original passwords preserved. Original owner wallet reconciles;completed-but-reserved appointment remains LegacyHold,not silently settled. |
| Seed/repeat migration | Release's actual `tele_tena.demo_dataset.setup` preflight and explicit dry_runFalse passed;second run already_presentTrue/refreshedFalse.10 fictional accounts,5 patient/4 clinician owners reconciled,balanced postings,no outbound delivery. Repeat native migration and original-data preservation PASS;6 total patient wallets reconcile including original owner. |

The first all-app trial correctly rejected missing unchanged DuckDB;the supplied
cached native wheel closed it without changing the production plan. The first seed
invocation used a nonexistent method/incorrect literal;no seed ran. The documented
`setup --kwargs '{"dry_run":False}'` was then exercised successfully twice. Failure
locations and diagnostic logs were kept privately rather than weakening guards.

| Same-site rollback | Verified native database/public/private backup restored through the CLI-only same-site helper; no database password in child arguments, no root credential, no schema migration or grant change. Original owner/password/private-file preservation and wallet reconciliation passed again after restore. |

## Explicit limits and next operator gates

Local runtime contains four **real** editable applications:Frappe16.2.1,
ERPNext16.1.0,TeleTena and ecommerce_integrations. The other39 unchanged remote
editable app sources are not available locally and are not represented by fake
wheels or claimed as executed. Their declared requirements and all third-party
pins were checked. The same-server copied-environment stage in the command guide
must additionally verify all43 actual editable identities before production repair.
This stages existing native binaries and source paths rather than installing a
separate Bench or replacing customer apps.

Required fresh server observations:current TeleTena SHA/schema and dirty state;
current full audit;external CLI interpreter/health;Supervisor RPC in-use commands,
matching PIDs and no pending unapplied configuration;runtime Bench-library consumers;
actual service names/queue subscriptions;versions/architecture/GLIBC;backup location;
Amazon-owning site,active settings record,region and network endpoint overrides.

No actual Amazon credentials were available here. Bounded live check is shipped
in the **Amazon bundle**,explicit `--perform-live` only:one LWA refresh,bounded STS
AssumeRole,one read-only Orders page,no import/sync/save. It prints no provider
responses or customer data. Regional STS connectivity and existing IAM/LWA/Orders
permissions must be demonstrated by operator;synthetic tests do not establish them.

Unchanged hosted LiveKit/device/SMS/native-language evidence is not relabeled as
new verification. No physical-device,live SMS,real-payment or remote deployment
claim. The pre-existing Amazon transport limitations are documented;no unrelated
API rewrite or authorization broadening was hidden in this patch.

## Cleanup and retained preview

Only the task-owned upgrade database/user/site and its58 queued search-index jobs
were removed after verified backup and rollback checks. Matched database/public/
private/config backup and credential manifests remain in the protected
`verified-upgrade-backup` directory. Task-started isolated MariaDB/Redis processes
were stopped by verified PID/command identity;the compatibility source checkout
was returned to62706f9. Original development Bench,data,credentials and services
remain unchanged. Main production-built preview responds HTTP200 at
http://127.0.0.1:8017/teletena/,site teletena-mvp-presentation.localhost,
source/build5efe78527309f8dab9e2a5bb391114cba153a862. It is intentionally newer
than the requested remote800a591 pin;this deployment-only branch adds no UI changes.

Both operator guides passed shell syntax checks;artifact SHA256SUMS and final9
guard regressions passed. Remote execution remains an operator-controlled step.
