# Selfmade Incremental Translation Release — Operator Procedure

**Localization deployment is blocked by human review.** Technical candidate:
`569537640665d9dcbb07738523fd49e4c5c5354a`, branch
`feat/offline-telebirr-mvp`, draft [PR50](https://github.com/natnaelTi/tele-tena/pull/50)
dependent on [PR49](https://github.com/natnaelTi/tele-tena/pull/49).
It contains every completed current MVP refinement, but imports **zero** workbook
translations because neither locale has human approvals/reviewer names. Dictionary
hash `ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356` is the
unchanged empty reviewed dictionary, not a completed Amharic/Oromo release.

The pre-outage approval gate below deliberately fails for this pin. Do not bypass
it. After human review/import/local verification, prepare a new immutable pin and
update this guide. The remaining checkpoints describe the exact guarded update
procedure; they are not authorization to ship unapproved drafts.

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
RELEASE_SHA=569537640665d9dcbb07738523fd49e4c5c5354a
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
git -C apps/tele_tena fetch origin feat/offline-telebirr-mvp
git -C apps/tele_tena cat-file -e "$RELEASE_SHA^{commit}"
git -C apps/tele_tena merge-base --is-ancestor "$OLD_SHA" "$RELEASE_SHA"
git -C apps/tele_tena merge-base --is-ancestor \
  45e1600a35a9450bb26b50397749c01491b2d4a7 "$OLD_SHA"
env/bin/python - "$RELEASE_SHA" <<'PY'
import json,subprocess,sys
sha=sys.argv[1]
def read(path):return json.loads(subprocess.check_output(['git','-C','apps/tele_tena','show',sha+':'+path],text=True))
reviewed=read('localization/reviewed.json');catalog=read('localization/catalog.json')
required={e['english'] for e in catalog.values()}
for locale in ('amharic','afaan_oromo'):
    supplied={e['english'] for e in reviewed.values() if e.get(locale)}
    print(locale,'reviewed unique phrases',len(required&supplied),'missing',len(required-supplied))
    assert not required-supplied,'STOP: human-reviewed localization is incomplete; do not start maintenance'
PY
```

The second ancestry guard defines the verified translation-only baseline. If the
installed release predates45e1600 or is on unrelated ancestry, stop: collect the
installed SHA and `git diff "$OLD_SHA" "$RELEASE_SHA" -- tele_tena/patches.txt
pyproject.toml frontend/package-lock.json` for a baseline-specific functional/schema
upgrade plan. The candidate includes older features, but unknown older migrations
must not be silently treated as this verified translation-only delta.

## 3. Initialize Once, or Resume the Retained Bundle

**Choose one block. Never rerun initialization when resuming.** Do not make a new
empty backup directory to get past a missing/failed checkpoint.

Initialize once, only after the approval/baseline gates pass:

```bash
UPDATE_BACKUP=$(mktemp -d /home/smcs/teletena-before-translations.XXXXXXXX)
chmod 700 "$UPDATE_BACKUP"
printf '%s\n' "$OLD_SHA" > "$UPDATE_BACKUP/tele_tena.sha"
printf '%s\n' "$SITE" > "$UPDATE_BACKUP/site.txt"
printf '%s\n' "$RELEASE_SHA" > "$UPDATE_BACKUP/candidate.sha"
TOOLS="$UPDATE_BACKUP/tools"
mkdir -m 700 "$TOOLS"
for TOOL in dependency_checkpoint.py release_preflight.py check_frappe_lock.py backup_review_release.py verify_release_backup.py restore_review_release.py export_loaded_supervisor.py release_preservation.py check_financial_owners.py; do
  git -C apps/tele_tena show "$RELEASE_SHA:scripts/$TOOL" > "$TOOLS/$TOOL"
done
printf 'RETAIN THIS EXACT BACKUP PATH: %s\n' "$UPDATE_BACKUP"
```

Resume in a new shell **instead** (replace the example with the actual retained path):

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
SITE=teletena.selfmadecs.com
BENCH_CLI=/home/smcs/.pyenv/versions/3.14.2/bin/bench
RELEASE_SHA=569537640665d9dcbb07738523fd49e4c5c5354a
UPDATE_BACKUP=/home/smcs/teletena-before-translations.RETAINED_PATH
TOOLS="$UPDATE_BACKUP/tools"
test -d "$UPDATE_BACKUP" && test ! -L "$UPDATE_BACKUP"
test "$(stat -c %u "$UPDATE_BACKUP")" = "$(id -u)"
test "$(stat -c %a "$UPDATE_BACKUP")" = 700
test "$(cat "$UPDATE_BACKUP/site.txt")" = "$SITE"
test "$(cat "$UPDATE_BACKUP/candidate.sha")" = "$RELEASE_SHA"
OLD_SHA=$(cat "$UPDATE_BACKUP/tele_tena.sha")
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
env/bin/python apps/tele_tena/scripts/check_translation_release.py --require-complete
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
"$BENCH_CLI" --site "$SITE" migrate > "$UPDATE_BACKUP/migrate.repeat.log" 2>&1
env/bin/python "$TOOLS/release_preservation.py" verify --bench /home/smcs/frappe-bench \
  --site "$SITE" --snapshot "$UPDATE_BACKUP/preserved-state.json"
env/bin/python "$TOOLS/check_financial_owners.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" > "$UPDATE_BACKUP/financial.after.json"
"$BENCH_CLI" --site "$SITE" clear-cache
"$BENCH_CLI" --site "$SITE" clear-website-cache
```

Current translation-only delta has no schema patch, requirement change or new
payment mode. All protected native TeleTena/command records, users/auth, files,
configuration and financial history remain strict. Do not skip patches or delete
holds. If an older separately planned upgrade executes the owner-approvedv1.48
reviewer default, the helper has an explicit `--expect-reviewer-default-v148` mode:
it verifies only missing Financial Configuration grants to existing reviewers,
matching audited events and associated modification/index metadata; all credentials,
settings, other roles/records/files remain strict. It is not a general ignore flag.
Use it only in that separately reviewed older-baseline plan, never to hide an
unexplained mismatch in this translation-only procedure.

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

## 11. Existing-Account Three-Locale Smoke Test

Use retained private demo credentials; do not seed or print passwords. For each
locale check proper Ethiopic/Oromo text, wrapping, dialogs/keyboard focus at390,
768,1440 and actual200% zoom, with the approved translation hash from checkpoint10.

1. Guest directory → profile → Sign in to Book → exact offering calendar return.
2. Patient Account saved locale → reload; privacy/file selection unchanged. Requests,
   actual offers, payment status/timeline and authorized receipts; no competitor data.
3. Clinician Account/onboarding, care-language search/grouping/approval, Requests
   payment notification/pane, manual pause, appointment handoff and Revenue Ledger.
4. Reviewer application/credential/scope/language decisions remain separate; policy
   translations retain actual draft/publication state and do not approve legal text.
5. Reuse authorized individual/couples consultation/notes/recipient/payment evidence;
   run a fresh bounded call only if changed behavior warrants it. No payment or live
   SMS/email smoke send without a separately consenting operator/recipient.

Navbar locale selection is session/in-memory behavior; Account's saved preference
is durable. Interface locales are not the catalog of clinician care languages.
SMS remains Ethiopian-only, and provider acceptance is not delivery. Preserve all
balances, historical holds, payee snapshots and notification preferences.

## 12. Rollback Before Migration

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
