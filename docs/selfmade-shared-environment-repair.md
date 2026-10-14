# Selfmade shared-environment repair — reviewed staged proposal

**One existing Bench: `/home/smcs/frappe-bench`. No separate production Bench,
framework upgrade, framework edits, production installation or service change was
performed.** Amazon source changes are in a separate repository/bundle. TeleTena
installation remains pinned to800a591ac6af9c6c3b4afd61ed4353be4ff0826e. That pin
intentionally excludes subsequent country-selector/history-upload changes.

## 1. Evidence and exact repair

Input:private all-app audit,44 apps,247 installed distributions,121 app-source
requirement edges, plus40 focused distribution/source edges. Supplied clean Amazon
source:7acdf6c8596c3a4f741675d2bb51dab6e6b95b14,ecommerce_integrations1.17.0.
External Bench5.29.0 `/home/smcs/.pyenv/versions/3.14.2/bin/bench` reportedly passes
its own pip check and lists the review site's apps. Retain it unchanged.

| Distribution | Before | Exact target | Relevant audited intersection |
|---|---|---|---|
| requests |2.33.1 |2.32.5 |Frappe~=2.32.5; Plaid,Twilio,Stripe,Google APIs,PostHog,OAuth wrappers,etc permit it |
| cryptography |48.0.0 |46.0.7 |Frappe~=46.0.3; pyOpenSSL>=45.0.7,<47; py-vapid>=46; http-message-signatures>=36.0.2 |
| oauthlib |3.3.1 |3.2.2 |Frappe~=3.2.2; requests-oauthlib>=3.0.0 |
| websockets |16.0 |15.0.1 |Frappe~=15.0.1; Print Designer has no narrowing pin |
| boto3 |1.28.85 |1.43.113 |Separate Amazon patch changes only runtime requirement~=1.28.10→~=1.43.113 |
| botocore |1.31.85 |1.43.113 |Boto3>=1.43.113,<1.44; accepts urllib3>=1.25.4,!=2.2.0,<3 |
| s3transfer |0.7.0 |0.19.2 |Required by new Boto3>=0.19,<0.20; accepts selected Botocore |
| frappe-bench,application env only |5.29.0 |Remove duplicate distribution |Keep external CLI; Click8.3.1 remains for Frappe |

Amazon metadata is deliberately rebuilt at the **same existing editable path and
app version1.17.0**. No other installed distribution is added,replaced or removed.
After repair247→246 distributions. Protect **all** other versions and identities,
including urllib32.6.3,Click8.3.1,http-message-signatures1.0.1,http-sfv0.9.9,
PyPika0.48.9 commit2c50e6142b2d61d2d243e466fdd5dc03b3d918f2 and Gunicorn23.0.0
commitbb554053bb87218120d76ab6676af7015680e8b6. No obsolete urllib3 downgrade.

The audit has no installed distribution metadata for frappe_pawapay. Its supplied
source declarations are nevertheless enforced:http-message-signatures>=1.0,<2.0
and http-sfv>=0.9,<1.0. Do not install/rename that app as a side effect. The only
other unresolved audit rows are Frappe's two direct-source requirements; the guard
checks both exact versions,VCS commits and source-identity hashes independently.
Any new missing app,requirement or changed source fails the guard.

## 2. What was tested; boundaries

See [shared-repair-verification.md](shared-repair-verification.md). All201 target
index-package versions were resolved and installed on isolated Python3.14.2,
including supplied DuckDB1.3.2:ldd/import/in-memory queries pass. Four real editable
apps:Frappe16.2.1,ERPNext16.1.0,TeleTena,Amazon. The other39 unchanged private
editable applications are **not** falsely presented as locally imported/tested;
their audited requirements are enforced,and their exact identities must survive
an additional full copied-environment gate on Selfmade before production repair.
That copy uses existing native packages; no unrelated source rebuild is needed.

A representative staging environment reproduced the eight reported conflicts;
normal offline installation repaired them,then clean pip check,exact preservation,
9 guard tests and10 Amazon tests passed. No `--no-deps`,unrelated upgrades or
constraint weakening. The Amazon tests cover actual SDK client/STS XML HTTP
serialization/signing/503 retry,Stubber AssumeRole/denial,LWA behavior,Orders
pagination/encoding,Catalog/Finances,independent SigV4 comparison and original
repository retry limits. Synthetic credentials and loopback/fake transports only.

The app's existing direct LWA/SP-API calls still lack explicit transport timeouts
and return HTTP-error JSON rather than automatically retrying it as SPAPIError.
This dependency-only patch preserves that behavior. Modern Botocore defaults to
regional STS; verify the applicable `sts.<region>.amazonaws.com` network route.
Existing explicit AWS endpoint/retry configuration is not changed automatically.
Live LWA,STS and a read-only Orders request remain an operator gate.

## 3. Read-only observations before either procedure

Do not remove the duplicate based on generated configuration alone. Bench uses
`os.execv`,so a running `frappe.utils.bench_helper` process erases the original
CLI argv. Collect **Supervisor RPC in-use command evidence** plus PID/module/cwd,
external CLI health and runtime Bench-library consumers. The exporter does not
emit environment variables or raw command arguments. If Supervisor configuration
has been reread without applying pending changes,resolve that discrepancy before
claiming the RPC configuration describes the running group. No `reread`,update,
configuration regeneration or restart is performed by these observation tools.

Transfer the prepared artifact directory from the development machine using your
existing SSH route; do not publish it under nginx. Local artifact directory:
`/home/frappe/teletena-shared-repair/artifacts`. Set the actual SSH host yourself:

```bash
# Local WSL; replace SSH_HOST with the established SSH hostname/IP.
SELFMADE_SSH='smcs@SSH_HOST'
ssh "$SELFMADE_SSH" 'umask 077; mkdir -p /home/smcs/teletena-repair-artifacts; chmod 700 /home/smcs/teletena-repair-artifacts'
scp -r /home/frappe/teletena-shared-repair/artifacts/. "$SELFMADE_SSH:/home/smcs/teletena-repair-artifacts/"
```

On Selfmade as smcs. Execute blocks separately;all use fail-fast behavior.
Commands intentionally retain the current application checkout during inspection:

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
BENCH_CLI=/home/smcs/.pyenv/versions/3.14.2/bin/bench
TOOL_SHA=53dd0df81342eedd8f7785a732f97827316159cb
AMAZON_BASE=7acdf6c8596c3a4f741675d2bb51dab6e6b95b14
AMAZON_PATCH=6dccb8e63cc078ea1790d8b826d8fa3b4ed194e9
ARTIFACTS=/home/smcs/teletena-repair-artifacts
AUDIT=$(mktemp -d /home/smcs/teletena-repair-observations.XXXXXXXX)
TOOLS="$AUDIT/tools"
mkdir -m 700 "$TOOLS"
git -C apps/tele_tena fetch origin fix/selfmade-shared-dependency-repair
for TOOL in dependency_checkpoint.py shared_dependency_audit.py shared_repair_guard.py export_loaded_supervisor.py observe_shared_launchers.py check_frappe_lock.py backup_review_release.py verify_release_backup.py restore_review_release.py; do
  git -C apps/tele_tena show "$TOOL_SHA:scripts/$TOOL" > "$TOOLS/$TOOL"
done
(cd "$ARTIFACTS" && sha256sum --check SHA256SUMS)
test "$(uname -m)" = x86_64
test "$(env/bin/python -c 'import platform;print(platform.python_version())')" = 3.14.2
test "$(node --version)" = v24.13.0
env/bin/python -c 'import ssl;print(ssl.OPENSSL_VERSION)'
getconf GNU_LIBC_VERSION
"$BENCH_CLI" --version
# Inspect the literal external CLI shebang; use that interpreter for its own pip check.
head -1 "$BENCH_CLI"
/home/smcs/.pyenv/versions/3.14.2/bin/python -m pip check
"$BENCH_CLI" --site teletena.selfmadecs.com list-apps
git -C apps/tele_tena rev-parse HEAD
git -C apps/frappe rev-parse HEAD
git -C apps/erpnext rev-parse HEAD
test "$(git -C apps/ecommerce_integrations rev-parse HEAD)" = "$AMAZON_BASE"
test -z "$(git -C apps/ecommerce_integrations status --porcelain)"
env/bin/python "$TOOLS/check_frappe_lock.py" apps/frappe
env/bin/python "$TOOLS/shared_dependency_audit.py" --bench /home/smcs/frappe-bench > "$AUDIT/all-app-requirements.json"
sudo supervisorctl status > "$AUDIT/supervisor-status.txt"
# Obtain the actual sudo supervisorctl interpreter; do not assume its Python environment.
SUPERVISORCTL=$(sudo sh -c 'command -v supervisorctl')
SUPERVISOR_SHEBANG=$(sudo head -n 1 "$SUPERVISORCTL")
SUPERVISOR_PY=${SUPERVISOR_SHEBANG#\#!}
test "${SUPERVISOR_PY#/}" != "$SUPERVISOR_PY"
test -x "$SUPERVISOR_PY"
sudo "$SUPERVISOR_PY" "$TOOLS/export_loaded_supervisor.py" > "$AUDIT/supervisor-loaded.json"
# Only use this flag after confirming no unapplied Supervisor configuration changes.
env/bin/python "$TOOLS/observe_shared_launchers.py" --bench /home/smcs/frappe-bench \
  --external-cli "$BENCH_CLI" --status-file "$AUDIT/supervisor-status.txt" \
  --loaded-config "$AUDIT/supervisor-loaded.json" --no-pending-config-changes \
  --output "$AUDIT/launchers.json"
```

Expected:external5.29.0 healthy;Frappe8f6e247/ERPNextbb2bada versions unchanged;
current all-app audit agrees with installed metadata. Library imports of Bench or
unparsed runtime source stop removal. Review possible shell-CLI references;the
procedure retains `env/bin/bench` as a symlink to the healthy external executable,
so interactive/hardcoded CLI paths keep working **without** duplicate metadata or
libraries. Python code importing Bench from the application environment is a stop,
not solved by that symlink. No global PATH/interpreter/service configuration edit.
Do not continue if the RPC in-use launchers differ from the external CLI.

## 4. Full copied-environment gate; production remains untouched

This is a copy of the environment inside the same server,**not another Bench/site**.
All43 original editable identities are initially retained. Only the staged Amazon
editable identity deliberately points to its separate patch worktree. The guard
records that exception and verifies original Bench source commits do not change.
No scheduler/worker/web process is launched against the copy.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
git -C apps/ecommerce_integrations bundle verify "$ARTIFACTS/ecommerce-selfmade-sdk.bundle"
git -C apps/ecommerce_integrations fetch "$ARTIFACTS/ecommerce-selfmade-sdk.bundle" \
  refs/heads/fix/selfmade-maintained-boto:refs/remotes/selfmade-repair/maintained-boto
test "$(git -C apps/ecommerce_integrations rev-parse refs/remotes/selfmade-repair/maintained-boto)" = "$AMAZON_PATCH"
git -C apps/ecommerce_integrations merge-base --is-ancestor "$AMAZON_BASE" "$AMAZON_PATCH"
git -C apps/ecommerce_integrations diff --stat "$AMAZON_BASE" "$AMAZON_PATCH"
STAGE=$(mktemp -d /home/smcs/teletena-repair-stage.XXXXXXXX)
cp -a --reflink=auto env "$STAGE/env"
git -C apps/ecommerce_integrations worktree add --detach "$STAGE/amazon" "$AMAZON_PATCH"
"$STAGE/env/bin/python" "$TOOLS/shared_repair_guard.py" snapshot "$STAGE/checkpoint" \
  --bench /home/smcs/frappe-bench --stage --amazon-path "$STAGE/amazon" \
  --audit "$AUDIT/all-app-requirements.json" --launchers "$AUDIT/launchers.json"
"$STAGE/env/bin/python" -m pip install --dry-run --no-index --find-links "$ARTIFACTS/wheels" \
  --constraint "$STAGE/checkpoint/constraints.txt" --report "$STAGE/plan.json" \
  -r "$STAGE/checkpoint/repair-pins.txt" -e "$STAGE/amazon" > "$STAGE/plan.log" 2>&1
"$STAGE/env/bin/python" "$TOOLS/shared_repair_guard.py" plan "$STAGE/checkpoint" \
  --bench /home/smcs/frappe-bench --stage --amazon-path "$STAGE/amazon" --report "$STAGE/plan.json"
"$STAGE/env/bin/python" -m pip uninstall -y frappe-bench > "$STAGE/remove-duplicate.log" 2>&1
test ! -e "$STAGE/env/bin/bench" && test ! -L "$STAGE/env/bin/bench"
ln -s "$BENCH_CLI" "$STAGE/env/bin/bench"
"$STAGE/env/bin/bench" --version
"$STAGE/env/bin/python" -m pip install --no-index --find-links "$ARTIFACTS/wheels" \
  --constraint "$STAGE/checkpoint/constraints.txt" -r "$STAGE/checkpoint/repair-pins.txt" \
  -e "$STAGE/amazon" > "$STAGE/install.log" 2>&1
"$STAGE/env/bin/python" "$TOOLS/shared_repair_guard.py" verify "$STAGE/checkpoint" \
  --bench /home/smcs/frappe-bench --stage --amazon-path "$STAGE/amazon" --amazon-commit "$AMAZON_PATCH"
"$STAGE/env/bin/python" "$STAGE/amazon/compatibility/test_selfmade_sdk.py" > "$STAGE/amazon-tests.log" 2>&1
"$STAGE/env/bin/python" -c 'import duckdb;assert duckdb.__version__=="1.3.2";assert duckdb.sql("SELECT 42").fetchone()==(42,);print("Native DuckDB unchanged and working")'
```

Require clean pip check,all original packages present except duplicate CLI,only7
version replacements,all unrelated editable/direct-source identities unchanged.
If any source-extra requirement or missing artifact prevents resolution,**stop**;
do not widen constraints,add `--no-deps`,upgrade frameworks or rebuild unrelated
native dependencies. Preserve the copy/logs for diagnosis. The guard fails visibly
on missing DuckDB;the supplied working native wheel closed that local test gap.

### Bounded live Amazon test (operator only)

The Amazon-owning site may be different from TeleTena. Identify its installed apps
and an existing active Amazon SP API Settings record privately. No credentials
belong in arguments/chat. With an authorized account and working stored credentials:

```bash
AMAZON_SITE='ACTUAL_AMAZON_OWNING_SITE'
AMAZON_SETTINGS='EXISTING_SETTINGS_DOCUMENT_NAME'
"$STAGE/env/bin/python" "$STAGE/amazon/compatibility/live_readonly_smoke.py" \
  --bench /home/smcs/frappe-bench --site "$AMAZON_SITE" --settings "$AMAZON_SETTINGS" --perform-live
```

One LWA refresh,one STS AssumeRole (at most2 attempts;5s connect/15s read),one Orders
page (at most10 records in memory;no pagination/import/save). Requests5s/15s
limits;TLS verification remains enabled. Prints stages/pass-fail only,no responses,
credentials or order/customer data. No background sync,report creation or document
mutation. Require success before production repair when Amazon is active. Missing
credentials/permissions/network access is a specific remaining live gate,not proof
of an SDK failure or permission to reset credentials/IAM scopes.

## 5. Reviewed shared maintenance window and production repair

**The following block changes production packages when the operator executes it;
it was not executed by Codex.** Coordinate impact across all sites in this Bench.
Compare exact service names to current status. Keep Redis,MariaDB,nginx and Node
Socket.IO running;Python web/workers/scheduler must stop to avoid mixed packages.
Do not use `restart all`,`bench update`,global pip or Supervisor regeneration.
Ensure current protected backup coverage for other customer sites;the repair
itself runs no migrations or database writes. TeleTena's ensuing schema update
requires the explicit matched target-site backup below.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
REPAIR_BACKUP=$(mktemp -d /home/smcs/teletena-before-shared-repair.XXXXXXXX)
cp -a --reflink=auto env "$REPAIR_BACKUP/env"
cp -a config "$REPAIR_BACKUP/bench-config"
cp sites/common_site_config.json "$REPAIR_BACKUP/common_site_config.json"
cp sites/apps.txt "$REPAIR_BACKUP/apps.txt"
cp apps/frappe/yarn.lock "$REPAIR_BACKUP/frappe-yarn.lock"
git -C apps/frappe diff HEAD --binary -- yarn.lock > "$REPAIR_BACKUP/frappe-yarn-lock.patch"
sha256sum apps/frappe/yarn.lock > "$REPAIR_BACKUP/lock.sha256"
cp -a "$AUDIT" "$REPAIR_BACKUP/observations"
env/bin/python "$TOOLS/shared_repair_guard.py" snapshot "$REPAIR_BACKUP/checkpoint" \
  --bench /home/smcs/frappe-bench --audit "$AUDIT/all-app-requirements.json" --launchers "$AUDIT/launchers.json"
"$BENCH_CLI" --site teletena.selfmadecs.com set-maintenance-mode on
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl stop frappe-bench-web:frappe-bench-frappe-web
env/bin/python "$TOOLS/backup_review_release.py" --bench /home/smcs/frappe-bench \
  --site teletena.selfmadecs.com --destination "$REPAIR_BACKUP/site-backups"
env/bin/python "$TOOLS/verify_release_backup.py" "$REPAIR_BACKUP/site-backups"
test -s "$REPAIR_BACKUP/site-backups/database.sql.gz"
test -s "$REPAIR_BACKUP/site-backups/public-files.tar"
test -s "$REPAIR_BACKUP/site-backups/private-files.tar"
test -s "$REPAIR_BACKUP/site-backups/site-config.json"
git -C apps/ecommerce_integrations checkout --detach "$AMAZON_PATCH"
env/bin/python -m pip install --dry-run --no-index --find-links "$ARTIFACTS/wheels" \
  --constraint "$REPAIR_BACKUP/checkpoint/constraints.txt" --report "$REPAIR_BACKUP/plan.json" \
  -r "$REPAIR_BACKUP/checkpoint/repair-pins.txt" -e apps/ecommerce_integrations > "$REPAIR_BACKUP/plan.log" 2>&1
env/bin/python "$TOOLS/shared_repair_guard.py" plan "$REPAIR_BACKUP/checkpoint" \
  --bench /home/smcs/frappe-bench --report "$REPAIR_BACKUP/plan.json"
env/bin/python -m pip uninstall -y frappe-bench > "$REPAIR_BACKUP/remove-duplicate.log" 2>&1
test ! -e env/bin/bench && test ! -L env/bin/bench
ln -s "$BENCH_CLI" env/bin/bench
hash -r
env/bin/python -m pip install --no-index --find-links "$ARTIFACTS/wheels" \
  --constraint "$REPAIR_BACKUP/checkpoint/constraints.txt" -r "$REPAIR_BACKUP/checkpoint/repair-pins.txt" \
  -e apps/ecommerce_integrations > "$REPAIR_BACKUP/install.log" 2>&1
env/bin/python "$TOOLS/shared_repair_guard.py" verify "$REPAIR_BACKUP/checkpoint" \
  --bench /home/smcs/frappe-bench --amazon-commit "$AMAZON_PATCH"
sha256sum --check "$REPAIR_BACKUP/lock.sha256"
env/bin/bench --version
"$BENCH_CLI" --site teletena.selfmadecs.com list-apps
```

Expected:no baseline conflict remains;CLI link/external5.29.0 works;original43
application editable identities and2 direct-source hashes/commits preserved;only
Amazon source advances to reviewed patch. Do not restart Python writers with a
failed install/verify. Confirm TeleTena code still matches its pre-update schema
before restarting;resolve the recorded interrupted105cd15 checkout first if it
is still present. This repair does not reconcile an unknown code/schema mismatch.

Finish the repair's shared-service smoke check before entering the separate update
procedure. The following starts only the exact services stopped above;all affected
Bench sites resume. Redis,MariaDB,nginx and Node Socket.IO were never restarted.

```bash
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl start frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl status
"$BENCH_CLI" --site teletena.selfmadecs.com doctor
"$BENCH_CLI" --site teletena.selfmadecs.com set-maintenance-mode off
```

Require working web/queues and the previously verified external launchers. Then
follow the pinned TeleTena guide from step1,taking a **new healthy update-mode
snapshot** and complete backup. Its preflight expects live workers;do not falsely
mark stopped workers healthy. It intentionally stops the four services again
before activating TeleTena's schema. Thus this exact procedure has two coordinated
shared-service pauses. Old code can run only with old schema between phases;
no old writer may continue after the TeleTena migration begins. Never reuse the
pre-repair conflicted snapshot for the application update.

## 6. Repair rollback versus TeleTena schema rollback

Before any TeleTena migration,the repair changes packages/Amazon source only.
Keep web/workers/scheduler stopped. Preserve failed logs/env and restore the
whole original app environment to its **original prefix**;never restore a copied
venv under a different live prefix or blindly pip-downgrade seven packages:

```bash
set -euo pipefail
cd /home/smcs/frappe-bench
test ! -e "$REPAIR_BACKUP/failed-env"
mv env "$REPAIR_BACKUP/failed-env"
cp -a "$REPAIR_BACKUP/env" /home/smcs/frappe-bench/env
test -z "$(git -C apps/ecommerce_integrations status --porcelain)"
git -C apps/ecommerce_integrations checkout --detach "$AMAZON_BASE"
sha256sum --check "$REPAIR_BACKUP/lock.sha256"
```

The baseline's eight known conflicts return;this is a faithful recovery,not a
claim that the baseline became healthy. External CLI/frameworks/lockfiles/configs
remain unchanged. Confirm restored package/source identities from the original
snapshot before restarting exact stopped services. Source worktrees and backups
are retained;do not automatically delete staging or audit records.

**After TeleTena migration,code/package rollback alone is insufficient.** Use the
matched TeleTena code+database+public/private/config backup from its update window,
as described in [selfmade-final-mvp-update.md](selfmade-final-mvp-update.md).
Normally retain the successfully repaired shared environment/Amazon source when
rolling back only TeleTena. Never restore one site's SQL over another site or
undo other customer data to repair a package conflict.

## 7. Continue the pinned TeleTena update

Use [selfmade-final-mvp-update.md](selfmade-final-mvp-update.md) after the repair,
with `BENCH_CLI` explicitly pointing to the retained external5.29.0 executable.
Release remains800a591ac6af9c6c3b4afd61ed4353be4ff0826e. Require current installed
SHA/schema observations;the known earlier interrupted checkout105cd15 occurred
before migration. Do not assume it is still the current state. Recover a mismatched
checkout only after establishing whether any later migration actually happened.
Only `teletena.selfmadecs.com` is migrated or seeded. Authentication/access flags,
SMS/SMTP/LiveKit credentials,real-payment safeguards and existing balances remain.
