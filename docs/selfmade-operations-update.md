> Provider follow-up: [Plan V1 actual results](operations/live-verification-results-v1.md).
> Do not bind the proof configuration or enable replay/archive while following this
> update. The native demo release is separate from provider activation. Owner
> receipts are confirmed; settled replay completeness/deletion and application-wide
> capture integration remain pending. Preserve all existing provider settings.

# Selfmade Operations Sprint 1 — Incremental Update

This procedure distinguishes **Demo** from **Final Localized Release**. The owner
explicitly authorizes the demo with existing permitted translations and truthful
English fallbacks. It imports no workbook drafts and does not claim clinical,
legal-policy, native-language or real-payment readiness. Final localization still
requires genuine independent approvals, validated import and a new verified pin.

Installation pin: `79fcebde6a940d3c12e9b5df7be2eb03ab788ac7`, branch `feat/operations-journey-insights`,
draft PR dependent on PR51/50. The native v1.53 migration adds private operations
command tables only. Existing clinical, financial, evidence and preference values
remain unchanged. No Python requirements change; frontend adds locked PostHog JS
1.446.0 in quarantine, with replay/capture disabled. Bugsink uses the existing
Frappe Sentry SDK through an isolated, sanitized client. No provider is enabled.

See [Sprint1 evidence](operations/verification.md), [configuration](operations/configuration.md),
[collection contract](operations/collection-retention.md) and [operator walkthrough](operations/operator-and-sprint2.md).
Synthetic event/error ingestion, original-line mapping, provisional single-window
export/playback and owner alert receipt passed. Settled completeness/deletion,
application-wide capture integration, representative production capacity and
external monitor setup remain gates. This package is a
native operations review candidate, not a claim that those gates or launch acceptance passed.
The alert recipient stays privately configured and unlinked to demo accounts.

Nothing has been remotely deployed or merged. Do not run the separate historical
Offline mode-cutover section: this update preserves the current payment mode.
No dependency repair, Amazon patch change, reseed/refresh, password reset, provider
or public-registration change, framework upgrade, Nginx/Supervisor regeneration,
`bench update`, all-site migration, blanket restart or private chmod is permitted.

## 1. Read-Only Baseline

Use the normal `smcs` user. Stop on every failure/unexpected observation. All
private reports/backups stay outside Git. These versions/commits/service names are
previous observations; verify current state rather than replacing mismatches.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
SITE=teletena.selfmadecs.com
BENCH_CLI=/home/smcs/.pyenv/versions/3.14.2/bin/bench
RELEASE_SHA=79fcebde6a940d3c12e9b5df7be2eb03ab788ac7
RELEASE_PURPOSE=demo # only demo or localized; localized additionally requires complete approved coverage
OLD_SHA=$(git -C apps/tele_tena rev-parse HEAD)
printf 'Installed TeleTena: %s\n' "$OLD_SHA"
git -C apps/tele_tena status --short
test -z "$(git -C apps/tele_tena status --porcelain)"
git -C apps/frappe status --short
git -C apps/erpnext status --short
git -C apps/ecommerce_integrations status --short
"$BENCH_CLI" --version
"$BENCH_CLI" --site "$SITE" list-apps
"$BENCH_CLI" --site "$SITE" doctor
env/bin/python --version
node --version
env/bin/python -m pip check
env/bin/python - <<'PYVERSIONS'
import importlib.metadata as m,platform,subprocess
assert platform.python_version()=='3.14.2','STOP: unverified Python baseline'
for name,version in [('frappe','16.2.1'),('erpnext','16.1.0')]:
    assert m.version(name)==version,'STOP: unverified '+name+' baseline'
assert subprocess.check_output(['node','--version'],text=True).strip()=='v24.13.0','STOP: unverified Node baseline'
PYVERSIONS
sudo supervisorctl status
sudo nginx -t
curl --fail --silent --show-error --max-redirs 0 \
  https://teletena.selfmadecs.com/assets/tele_tena/review/release.json
```

Expected baseline: Frappe16.2.1, ERPNext16.1.0, Python3.14.2, Node24.13.0, healthy
external Bench CLI/repaired pip check, installed TeleTena, subscribed workers and
unpaused scheduler. An unknown installed SHA is not permission to force checkout.
Do not print site configuration, credentials, OTPs, provider bodies or private files.

## 2. Fetch Objects and Check Approval Before Any Outage

Fetching Git objects changes no running application. This stages reviewed tools
before backup; runtime checkout/install happens only in checkpoint6.

```bash
git -C apps/tele_tena fetch origin feat/operations-journey-insights
git -C apps/tele_tena cat-file -e "$RELEASE_SHA^{commit}"
git -C apps/tele_tena diff --stat "$OLD_SHA" "$RELEASE_SHA"
git -C apps/tele_tena diff "$OLD_SHA" "$RELEASE_SHA" -- pyproject.toml frontend/package.json frontend/package-lock.json tele_tena/patches.txt
git -C apps/tele_tena merge-base --is-ancestor "$OLD_SHA" "$RELEASE_SHA"
git -C apps/tele_tena merge-base --is-ancestor \
  de27a6fbd6e2ed8c23d74471d98b8c357178890a "$OLD_SHA"
env/bin/python - "$RELEASE_SHA" "$RELEASE_PURPOSE" <<'PY'
import json,subprocess,sys
sha,purpose=sys.argv[1:];assert purpose in ('demo','localized')
def read(path):return json.loads(subprocess.check_output(['git','-C','apps/tele_tena','show',sha+':'+path],text=True))
reviewed=read('localization/reviewed.json');catalog=read('localization/catalog.json')
required={e['english'] for e in catalog.values()}
for locale in ('amharic','afaan_oromo'):
    supplied={e['english'] for e in reviewed.values() if e.get(locale)}
    print(locale,'reviewed unique phrases',len(required&supplied),'missing',len(required-supplied))
    if purpose=='localized':assert not required-supplied,'STOP: human-reviewed localization is incomplete; do not start maintenance'
print('Purpose:',purpose,'; no draft dictionary import or provider/payment activation')
PY
```

The second ancestry guard defines the verified v1.49-or-later update baseline. If the
installed release predates de27a6f or is on unrelated ancestry, stop: collect the
installed SHA and `git diff "$OLD_SHA" "$RELEASE_SHA" -- tele_tena/patches.txt
pyproject.toml frontend/package-lock.json` for a baseline-specific functional/schema
upgrade plan. The candidate includes older features, but unknown older migrations
must not be silently treated as this verified v1.53 incremental delta.

## 3. Initialize Once, or Resume the Retained Bundle

**Choose one block. Never rerun initialization when resuming.** Do not make a new
empty backup directory to get past a missing/failed checkpoint.

Initialize once, only after the purpose-specific localization and baseline gates pass:

```bash
UPDATE_BACKUP=$(mktemp -d /home/smcs/teletena-before-operations.XXXXXXXX)
chmod 700 "$UPDATE_BACKUP"
printf '%s\n' "$OLD_SHA" > "$UPDATE_BACKUP/tele_tena.sha"
printf '%s\n' "$SITE" > "$UPDATE_BACKUP/site.txt"
printf '%s\n' "$RELEASE_SHA" > "$UPDATE_BACKUP/candidate.sha"
printf '%s\n' "$RELEASE_PURPOSE" > "$UPDATE_BACKUP/purpose.txt"
TOOLS="$UPDATE_BACKUP/tools"
mkdir -m 700 "$TOOLS"
for TOOL in dependency_checkpoint.py release_preflight.py check_frappe_lock.py backup_review_release.py verify_release_backup.py restore_review_release.py export_loaded_supervisor.py release_preservation.py check_financial_owners.py; do
  git -C apps/tele_tena show "$RELEASE_SHA:scripts/$TOOL" > "$TOOLS/$TOOL"
done
printf 'RETAIN THIS EXACT BACKUP PATH: %s\n' "$UPDATE_BACKUP"
```

Resume in a new shell **instead** (replace the example with the actual retained path).
If writers are already stopped, start here rather than rerunning the live HTTP/PID
checks in checkpoints1/4. Retain their original reports; do not overwrite the
pre-update baseline with the partly installed candidate. After validation, resume
only the first unfinished checkpoint. Do not rerun completed backup initialization:

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
SITE=teletena.selfmadecs.com
BENCH_CLI=/home/smcs/.pyenv/versions/3.14.2/bin/bench
RELEASE_SHA=79fcebde6a940d3c12e9b5df7be2eb03ab788ac7
RELEASE_PURPOSE=demo # only demo or localized; localized additionally requires complete approved coverage
UPDATE_BACKUP=/home/smcs/teletena-before-operations.RETAINED_PATH
TOOLS="$UPDATE_BACKUP/tools"
test -d "$UPDATE_BACKUP" && test ! -L "$UPDATE_BACKUP"
test "$(stat -c %u "$UPDATE_BACKUP")" = "$(id -u)"
test "$(stat -c %a "$UPDATE_BACKUP")" = 700
test "$(cat "$UPDATE_BACKUP/site.txt")" = "$SITE"
test "$(cat "$UPDATE_BACKUP/candidate.sha")" = "$RELEASE_SHA"
test "$(cat "$UPDATE_BACKUP/purpose.txt")" = "$RELEASE_PURPOSE"
OLD_SHA=$(cat "$UPDATE_BACKUP/tele_tena.sha")
CURRENT_SHA=$(git -C apps/tele_tena rev-parse HEAD)
test "$CURRENT_SHA" = "$OLD_SHA" || test "$CURRENT_SHA" = "$RELEASE_SHA"
test -z "$(git -C apps/tele_tena status --porcelain)"
test -s "$TOOLS/verify_release_backup.py"
# Required before resuming checkout/install/migration:
env/bin/python "$TOOLS/verify_release_backup.py" "$UPDATE_BACKUP/site-backups"
test -s "$UPDATE_BACKUP/preserved-state.json"
test -s "$UPDATE_BACKUP/dependencies/packages.json"
sha256sum --check "$UPDATE_BACKUP/private-state.sha256"
```

If interrupted before backup completion, inspect and finish only that unfinished
checkpoint in the same retained bundle. An existing incomplete native backup must
be investigated; the helper refuses to overwrite it. Do not proceed with absent
archives/snapshots or silently create a replacement parent bundle.

## 4. Inspect Loaded Launchers and Save Protected State

```bash
env/bin/python "$TOOLS/check_frappe_lock.py" apps/frappe
env/bin/python "$TOOLS/release_preflight.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" > "$UPDATE_BACKUP/preflight.before.json"
sudo /usr/bin/python3 "$TOOLS/export_loaded_supervisor.py" > "$UPDATE_BACKUP/supervisor.loaded.json"
"$BENCH_CLI" --site all list-apps > "$UPDATE_BACKUP/all-sites-apps.txt"
cp sites/apps.txt "$UPDATE_BACKUP/apps.txt"
cp sites/common_site_config.json "$UPDATE_BACKUP/common_site_config.json"
cp "sites/$SITE/site_config.json" "$UPDATE_BACKUP/site-config.before-maintenance.json"
cp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
git -C apps/frappe rev-parse HEAD > "$UPDATE_BACKUP/frappe.sha"
git -C apps/erpnext rev-parse HEAD > "$UPDATE_BACKUP/erpnext.sha"
git -C apps/ecommerce_integrations rev-parse HEAD > "$UPDATE_BACKUP/amazon.sha"
git -C apps/ecommerce_integrations diff --binary HEAD > "$UPDATE_BACKUP/amazon.patch"
sudo nginx -T > "$UPDATE_BACKUP/nginx.before.txt" 2> "$UPDATE_BACKUP/nginx.before.log"
curl --fail --silent --show-error https://teletena.selfmadecs.com/assets/tele_tena/review/release.json \
  > "$UPDATE_BACKUP/served-release.before.json"
env/bin/python "$TOOLS/dependency_checkpoint.py" snapshot "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
```

If an older operations helper is already installed, inspect its owned processes
before the maintenance window. Existing operational writers must also be stopped
in checkpoint5 before preservation snapshots. A separately managed custom worker
must be identified and stopped through its verified launcher, never duplicated.

```bash
if test -f apps/tele_tena/scripts/operations_service.py; then
  env/bin/python apps/tele_tena/scripts/operations_service.py status \
    --bench /home/smcs/frappe-bench --site "$SITE"
fi
# Protect an explicitly bound external provider configuration, without printing it.
env/bin/python - "$SITE" "$UPDATE_BACKUP" <<'PYPRIVATE'
import json,os,shutil,sys
from pathlib import Path
site,backup=sys.argv[1:];config=json.loads((Path('sites')/site/'site_config.json').read_text())
if config.get('tele_tena_operations_config_file'):
    source=Path(config['tele_tena_operations_config_file'])
    assert source.is_absolute() and source.is_file() and not source.is_symlink()
    assert source.stat().st_uid==os.getuid() and not source.stat().st_mode&0o077
    target=Path(backup)/'operations-provider-config.private.json'
    assert not target.exists(),'Do not overwrite retained provider backup'
    shutil.copyfile(source,target);target.chmod(0o600)
PYPRIVATE
```

Review these private reports before proceeding. Preserve the reviewed caniuse-lite
lock delta and Amazon patch. Verify the existing TeleTena Nginx trailing-slash
exception from the dump; do not regenerate/reload Nginx. If another site installs
TeleTena, stop for its own compatibility/migration plan: code/assets are shared.

Previously verified service names must match current loaded RPC configuration and
running process launchers. Inspect actual PIDs rather than generated config:

```bash
env/bin/python - <<'PY'
from pathlib import Path
import re,subprocess
for line in subprocess.check_output(['sudo','supervisorctl','status'],text=True).splitlines():
    if not line.startswith('frappe-bench-workers:'):continue
    match=re.search(r'\bpid\s+(\d+)',line);assert match,'Expected running process'
    path=Path('/proc')/match.group(1);args=(path/'cmdline').read_bytes().split(b'\0')
    print(line.split()[0],(path/'exe').resolve(),(path/'cwd').resolve(),args[0].decode(),'bench_helper=',b'frappe.utils.bench_helper' in args)
PY
```

The healthy external CLI remains `/home/smcs/.pyenv/versions/3.14.2/bin/bench`;
running worker/scheduler argv0 may be the application-env Python executing
`frappe.utils.bench_helper`. Preserve this arrangement. Stop on mismatching loaded
names/launchers; do not invent replacement service names.

## 5. Shared Maintenance Window, Writers and Complete Backup

These four Python services affect the shared Bench's sites. Arrange that outage.
Redis, database, Nginx and Socket.IO stay running. No broad stop/restart.

```bash
"$BENCH_CLI" --site "$SITE" set-maintenance-mode on
if test -f apps/tele_tena/scripts/operations_service.py; then
  env/bin/python apps/tele_tena/scripts/operations_service.py stop \
    --bench /home/smcs/frappe-bench --site "$SITE"
fi
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl stop frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl status
env/bin/python "$TOOLS/backup_review_release.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" --destination "$UPDATE_BACKUP/site-backups"
env/bin/python "$TOOLS/verify_release_backup.py" "$UPDATE_BACKUP/site-backups"
for REQUIRED in database.sql.gz public-files.tar private-files.tar site-config.json verified-manifest.json; do
  test -s "$UPDATE_BACKUP/site-backups/$REQUIRED"
done
tar --create --file "$UPDATE_BACKUP/private-state.tar" --exclude='./files' --exclude='./backups' \
  -C "sites/$SITE/private" .
tar --list --file "$UPDATE_BACKUP/private-state.tar" > "$UPDATE_BACKUP/private-state.files"
sha256sum "$UPDATE_BACKUP/private-state.tar" > "$UPDATE_BACKUP/private-state.sha256"
sha256sum --check "$UPDATE_BACKUP/private-state.sha256"
cp -a apps/tele_tena/tele_tena/public/review "$UPDATE_BACKUP/review-assets"
env/bin/python "$TOOLS/release_preservation.py" snapshot --bench /home/smcs/frappe-bench \
  --site "$SITE" --snapshot "$UPDATE_BACKUP/preserved-state.json"
env/bin/python "$TOOLS/check_financial_owners.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" > "$UPDATE_BACKUP/financial.before.json"
```

Require STOPPED for all four, valid gzip/SQL, both TAR archives, configuration and
manifest hashes. The helper writes fresh complete artifacts with600 files/700
bundle, uses a private temporary DB option file, and rejects missing archives.
Copy the verified bundle to protected backup storage. Encryption-enabled policy
requires a separately verified encrypted procedure; do not disable it. A baseline
financial discrepancy is a stop for audited reconciliation, never automatic repair.

## 6. Exact Checkout and App-Only Dependency Plan

```bash
test -z "$(git -C apps/tele_tena status --porcelain)"
git -C apps/tele_tena checkout --detach "$RELEASE_SHA"
env/bin/python -m pip install --dry-run \
  --constraint "$UPDATE_BACKUP/dependencies/constraints.txt" \
  --report "$UPDATE_BACKUP/dependency-plan.json" -e apps/tele_tena \
  > "$UPDATE_BACKUP/dependency-plan.log" 2>&1
env/bin/python "$TOOLS/dependency_checkpoint.py" plan "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena \
  --report "$UPDATE_BACKUP/dependency-plan.json"
env/bin/python -m pip install --constraint "$UPDATE_BACKUP/dependencies/constraints.txt" \
  -e apps/tele_tena > "$UPDATE_BACKUP/dependency-install.log" 2>&1
env/bin/python "$TOOLS/dependency_checkpoint.py" verify "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
env/bin/python -m pip check
```

Only the intended local editable TeleTena update is allowed. No unrelated new or
replacement distributions, editable identity changes, `--no-deps`, relaxed
constraints, framework requirements installation or shared dependency repair.

## 7. Locked Production Build and Public Permissions

```bash
if test "$RELEASE_PURPOSE" = localized; then
  env/bin/python apps/tele_tena/scripts/check_translation_release.py --require-complete
else
  env/bin/python apps/tele_tena/scripts/check_translation_release.py
fi
env/bin/python apps/tele_tena/scripts/build_review.py > "$UPDATE_BACKUP/frontend-build.log" 2>&1
"$BENCH_CLI" build --app tele_tena
PUBLIC=/home/smcs/frappe-bench/apps/tele_tena/tele_tena/public
test -d "$PUBLIC/review" && test ! -L "$PUBLIC"
test -z "$(find "$PUBLIC/review" -type l -print -quit)"
chmod 755 "$PUBLIC"
find "$PUBLIC/review" -type d -exec chmod 755 {} +
find "$PUBLIC/review" -type f -exec chmod 644 {} +
test "$(readlink -f sites/assets/tele_tena)" = "$PUBLIC"
env/bin/python apps/tele_tena/scripts/check_review_assets.py --site-private "sites/$SITE/private"
```

The repository build uses locked `npm ci`, not Vite dev.755/644 applies only to
this public output. Never recursively chmod sites/private, configuration, backups
or the home directory. An inaccessible ancestor requires a narrow ownership/group
fix, not a blanket chmod. Draft workbooks/approval artifacts must not be copied here.

## 8. Target-Only Migration, Repeat and Preservation

```bash
"$BENCH_CLI" --site "$SITE" migrate > "$UPDATE_BACKUP/migrate.first.log" 2>&1
env/bin/python "$TOOLS/release_preservation.py" verify --bench /home/smcs/frappe-bench \
  --site "$SITE" --snapshot "$UPDATE_BACKUP/preserved-state.json"
env/bin/python "$TOOLS/release_preservation.py" snapshot --bench /home/smcs/frappe-bench \
  --site "$SITE" --snapshot "$UPDATE_BACKUP/preserved-state.after-first.json"
"$BENCH_CLI" --site "$SITE" migrate > "$UPDATE_BACKUP/migrate.repeat.log" 2>&1
env/bin/python "$TOOLS/release_preservation.py" verify --bench /home/smcs/frappe-bench \
  --site "$SITE" --snapshot "$UPDATE_BACKUP/preserved-state.after-first.json"
env/bin/python "$TOOLS/check_financial_owners.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" > "$UPDATE_BACKUP/financial.after.json"
"$BENCH_CLI" --site "$SITE" clear-cache
"$BENCH_CLI" --site "$SITE" clear-website-cache
```

v1.53 adds operations tables only. Every original protected value remains strict:
users/auth, professional/scope/language decisions, evidence, files, credentials,
provider/payment settings, disclosure preferences and financial history. No legacy
recovery allowance is used for the verified de27a6f-or-newer baseline. Do not skip
patches or suppress mismatches. The second migration compares the after-first
snapshot strictly. Retain both snapshots; never overwrite them when resuming.
The new operations worker remains stopped until these checks pass so it cannot
change aggregate/heartbeat rows during repeat-migration comparison.

## 9. Shared-State Checks and Scoped Recovery

```bash
cmp sites/apps.txt "$UPDATE_BACKUP/apps.txt"
cmp sites/common_site_config.json "$UPDATE_BACKUP/common_site_config.json"
cmp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
test "$(git -C apps/frappe rev-parse HEAD)" = "$(cat "$UPDATE_BACKUP/frappe.sha")"
test "$(git -C apps/erpnext rev-parse HEAD)" = "$(cat "$UPDATE_BACKUP/erpnext.sha")"
test "$(git -C apps/ecommerce_integrations rev-parse HEAD)" = "$(cat "$UPDATE_BACKUP/amazon.sha")"
git -C apps/ecommerce_integrations diff --binary HEAD > "$UPDATE_BACKUP/amazon.after.patch"
cmp "$UPDATE_BACKUP/amazon.patch" "$UPDATE_BACKUP/amazon.after.patch"
env/bin/python "$TOOLS/dependency_checkpoint.py" verify "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
sudo nginx -t
sudo nginx -T > "$UPDATE_BACKUP/nginx.after.txt" 2> "$UPDATE_BACKUP/nginx.after.log"
cmp "$UPDATE_BACKUP/nginx.before.txt" "$UPDATE_BACKUP/nginx.after.txt"
sudo supervisorctl start frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl status
"$BENCH_CLI" --site "$SITE" set-maintenance-mode off
"$BENCH_CLI" --site "$SITE" doctor
env/bin/python "$TOOLS/release_preflight.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" > "$UPDATE_BACKUP/preflight.after.json"
```

Require correct queue subscriptions and actual subsequent job-execution metadata;
process RUNNING alone is insufficient. Reuse normal expiry/release schedules,
checking retries/dispute holds without forcing earnings release or sending test
provider messages. If the baseline scheduler was disabled, stop for its own diagnosis;
do not silently enable it. Preserve original notification preferences/caps/providers.

## 9b. Register and Start Only the New Operations Queue

After preservation verification and before relying on Operations Health, register
the native custom queue. This is the only deliberate shared configuration addition;
it preserves every existing key/worker definition. Do not regenerate Supervisor.
If the entry already exists with other settings, stop for review. Back it up once.

```bash
env/bin/python - "$UPDATE_BACKUP" <<'PYOPS'
import json,os,sys
from pathlib import Path
backup=Path(sys.argv[1]);file=Path('sites/common_site_config.json')
assert not file.is_symlink()
data=json.loads(file.read_text());workers=data.setdefault('workers',{})
expected={'timeout':120,'background_workers':1}
if 'teletena_ops' in workers:
    assert workers['teletena_ops']==expected,'STOP: different custom queue configuration'
else:
    target=backup/'common-config.before-operations-queue.json'
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as out:out.write(file.read_bytes())
    workers['teletena_ops']=expected
    temporary=file.with_name('common_site_config.operations-tmp.json')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as out:json.dump(data,out,indent=2)
    temporary.replace(file)
PYOPS
# Shared default/short workers cache the queue registry. These exact services
# must have passed the loaded-launcher inspection; the shared maintenance window applies.
sudo supervisorctl restart frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
env/bin/python apps/tele_tena/scripts/operations_service.py start \
  --bench /home/smcs/frappe-bench --site "$SITE"
env/bin/python apps/tele_tena/scripts/operations_service.py status \
  --bench /home/smcs/frappe-bench --site "$SITE"
```

The helper owns one dedicated RQ worker and independent health/watch process,
refuses an already-subscribed worker, protects PID/log files and never signals the
shared services itself. On reboot re-run the same `start`; to stop use `stop` with
the same arguments. Arrange an approved persistent launcher before production
reliance; no system-wide startup unit is installed by this task. Provider flags
remain off. Wait for a native scheduler tick and then confirm *both* scheduler and
worker-completed timestamps advance in reviewer System Health. A running PID alone
is insufficient. Queue processing must recover after an owned-worker stop/start.

Private configuration is a separate explicit operator step documented in
[configuration](operations/configuration.md). Do not paste secrets, automatically
subscribe a demo reviewer, enable integrations, send alerts or activate replay.

## 10. HTTPS, Build/Translation Identity and PWA

```bash
env/bin/python - "$RELEASE_SHA" <<'PY'
import hashlib,json,subprocess,sys
from urllib.request import urlopen
from urllib.error import HTTPError
base='https://teletena.selfmadecs.com'
def get(path):
    r=urlopen(base+path,timeout=30);assert r.status==200;return r,r.read()
r,_=get('/teletena/');assert r.url==base+'/teletena/'
for path in ['/teletena/care','/teletena/patient/requests','/teletena/clinician/account','/teletena/admin']:
    response,_=get(path);assert 'no-store' in response.headers.get('Cache-Control','')
_,body=get('/assets/tele_tena/review/release.json');release=json.loads(body)
assert release['source_commit']==sys.argv[1]
reviewed=json.loads(subprocess.check_output(['git','-C','apps/tele_tena','show',sys.argv[1]+':localization/reviewed.json'],text=True))
expected=hashlib.sha256((json.dumps(reviewed,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()).hexdigest()
assert release['translation_dictionary_sha256']==expected
for name,digest in release['files'].items():
    _,content=get('/assets/tele_tena/review/'+name);assert hashlib.sha256(content).hexdigest()==digest
r,_=get('/teletena/sw.js');assert r.headers.get('Service-Worker-Allowed')=='/teletena/'
assert 'no-store' in r.headers.get('Cache-Control','')
_,body=get('/api/method/tele_tena.api.contact_auth.session');assert not json.loads(body)['message']['authenticated']
_,body=get('/api/method/tele_tena.api.directory.offerings');assert isinstance(json.loads(body)['message']['items'],list)
try:
    get('/api/method/tele_tena.api.history_documents.list_documents');raise AssertionError('Guest private history allowed')
except HTTPError as error:assert error.code in (401,403)
print('PASS source/build/translation/asset hashes, HTTPS routes, public discovery and private denial')
PY
```

Finish unsaved work/calls before accepting the PWA update prompt. Inspect network
release metadata first, then perform a normal no-store-shell reload. Do not clear
private records/cookies or kill an active call as an update mechanism. If stale,
inspect worker registration/asset response/permissions and the preserved Nginx
exception. No authenticated API, medical data or OTP caching is authorized.

## 11. Existing-Account Three-Locale and Operations Smoke Test

Use retained private demo credentials; do not seed or print passwords. For each
locale check proper Ethiopic/Oromo text, wrapping, dialogs/keyboard focus at390,
768,1440 and actual200% zoom, with the packaged translation hash from checkpoint10. A demo deliberately retains
unreviewed English fallbacks; it must not be labeled final localization acceptance.

1. Guest directory → profile → Sign in to Book → exact offering calendar return.
2. Patient Account saved locale → reload; privacy/file selection unchanged. Requests,
   actual offers, payment status/timeline and authorized receipts; no competitor data.
3. Clinician Account/onboarding, care-language search/grouping/approval, Requests
   payment notification/pane, manual pause, appointment handoff and Revenue Ledger.
4. Reviewer application/credential/scope/language decisions remain separate; policy
   translations retain actual draft/publication state and do not approve legal text.
5. Patient primary navbar includes My Requests and Shared Care; More has neither.
   At narrow widths/200% use the scrollable primary rail. Verify Back/Forward.
6. Open a private receipt from patient and receiving clinician payment pages: dialog,
   original filename, zoom/fit, Escape/focus return, explicit Download only. Reviewer
   opens authorized professional evidence; ID still needs specific assignment.
7. Clinician final onboarding review groups ID/CV/license/each credential files;
   preview/close/reload must retain the step and inputs, never submit accidentally.
8. Patient Account → Privacy & Sharing → Share My Profile Photo With My Clinicians.
   Test withdrawal with a consenting demonstration patient, restore their chosen
   preference afterward; no owner-only file selection/name/history reset. Authorized
   image GET denies immediately after withdrawal, visible avatars revalidate every30s
   while active/on returning to the tab. Partners/unrelated clinicians remain denied.
9. Reuse authorized individual/couples consultation/notes/recipient/payment evidence;
   run a fresh bounded call only if changed behavior warrants it. No payment or live
   SMS/email smoke send without a separately consenting operator/recipient.

Navbar locale selection is session/in-memory behavior; Account's saved preference
is durable. Interface locales are not the catalog of clinician care languages.
SMS remains Ethiopian-only, and provider acceptance is not delivery. Preserve all
balances, historical holds, payee snapshots and notification preferences.

Additional operations smoke: patient Help → Report a Problem → reference; reviewer
More → Operations / User Support → internal note then visible reply/resolution;
patient must not see internal note. Check reviewer-only APIs from patient/guest,
private screenshot denial, report generation/export, stale/current health, disabled
provider labels and archive unavailable state. Native events carry no submitted
support text. No live alert or provider transport test is automatic.

## 12. Rollback Before Migration

Before restoring old code, stop the owned operations processes if started:

```bash
env/bin/python apps/tele_tena/scripts/operations_service.py stop \
  --bench /home/smcs/frappe-bench --site "$SITE"
```

Preserve the private deletion journal and current operations files before any
post-migration restore. Never restore an older tombstone journal over newer deletion
records. Extra private operations objects require review; do not blindly delete.
The custom-queue config addition may be reverted only by an exact pre/post diff
that proves no intervening shared changes; never overwrite live shared config from
an old backup by default. Existing framework/Amazon/Nginx changes remain preserved.


Keep the four writers stopped/site in maintenance. Only when no migration/new-format
writes occurred and the dependency guard confirmed preservation:

```bash
PUBLIC=/home/smcs/frappe-bench/apps/tele_tena/tele_tena/public
git -C apps/tele_tena checkout --detach "$(cat "$UPDATE_BACKUP/tele_tena.sha")"
env/bin/python -m pip install --constraint "$UPDATE_BACKUP/dependencies/constraints.txt" \
  -e apps/tele_tena > "$UPDATE_BACKUP/rollback-package.log" 2>&1
env/bin/python -m pip check
test "$PUBLIC" = /home/smcs/frappe-bench/apps/tele_tena/tele_tena/public
test ! -L "$PUBLIC/review"
test -s "$UPDATE_BACKUP/review-assets/release.json"
rm -rf -- "$PUBLIC/review"
cp -a "$UPDATE_BACKUP/review-assets" "$PUBLIC/review"
```

Resume only the verified four services, exit target maintenance and verify the old
saved manifest/account journeys. This changes no shared framework/Amazon state.

## 13. Recovery After Migration

Old code does not reverse migrations. Prefer fix-forward if new legitimate activity
exists. A restore overwrites post-backup activity and requires an explicit operator
recovery decision plus a fresh verified backup of the failed/current state first.
Stop the same four writers again if restarted; target maintenance stays on. Restore
old code/assets as above, then:

```bash
env/bin/python "$TOOLS/verify_release_backup.py" "$UPDATE_BACKUP/site-backups"
env/bin/python "$TOOLS/restore_review_release.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" --backup "$UPDATE_BACKUP/site-backups" --confirm-restore-site "$SITE"
env/bin/python "$TOOLS/release_preservation.py" verify --bench /home/smcs/frappe-bench \
  --site "$SITE" --snapshot "$UPDATE_BACKUP/preserved-state.json"
"$BENCH_CLI" --site "$SITE" clear-cache
"$BENCH_CLI" --site "$SITE" clear-website-cache
```

Do not migrate the old code after restore. Restore extra private-state files only
if proven changed, after checking the verified archive and protecting newer
credentials/files. Never overwrite shared configuration/Amazon/packages. Start the
same scoped services, exit maintenance and check the saved old build and original
accounts. A preservation/reconciliation mismatch remains a stop, not permission to
edit balances/delete records. Keep diagnostics and the retained backup bundle.


## Provider Configuration Follow-Up — No Production Activation

The owner has populated the **local** working file
`/home/frappe/teletena-operations-config/providers.json`; it passes local structural
checks, EU335848 consistency and600/700 permissions. Telegram chat remains unresolved.
Do not copy the template over this file, transfer credentials to Selfmade implicitly,
link the alert subscription to a demo reviewer or enable collection based on presence.
No Selfmade provider state is inferred from this local file. Preserve remote settings.

The native package pin above remains unchanged; new configuration/preflight tooling
is on PR52 and is not part of the earlier packaged application runtime. See
[actual capability/gap status](operations/configuration-readiness.md) and
[one bounded live authorization plan](operations/live-verification-plan-v1.md).
Only authorized isolated provider tests may advance connectivity/export/playback
evidence. UptimeRobot stays separate. Source maps, useful masked capture, complete
export/normalization and independent playback are not complete implementations yet.
Do not deploy this checkpoint as a final provider-connected launch release.
