# Selfmade incremental refinements: existing800a591 → reviewed candidate

No remote operation or merge was performed. This procedure is **only** for the
already repaired `/home/smcs/frappe-bench`, `teletena.selfmadecs.com`, currently
at800a591ac6af9c6c3b4afd61ed4353be4ff0826e. Do **not** repeat the shared repair,
change Amazon, remove/install Bench, run a seed/setup/refresh, reset credentials,
or change registration/provider switches. Do not run `bench update`, shared
requirements installation, framework upgrades or `bench setup nginx`.

## Exact release and delta

Installation/build pin: **deeb583fbbfaaf276acc51aef05982dbf28d27e8**.
Branch `fix/selfmade-incremental-refinements`; descends from the requested
5efe78527309f8dab9e2a5bb391114cba153a862 and installed800a591. It includes the
PR44/PR43 ancestry and PR45 deployment safeguards. PRs remain unmerged/draft.

An additional verification found that Frappe16's `pdf_contains_js` does not resolve
the standard PDF root names tree.5efe785 accepted a PDF with named JavaScript.
The candidate adds one application-level rejection for `/Names/JavaScript`, with
a regression test; no framework change. Install this fixed descendant,not5efe785.
This is not antivirus/malware scanning or a claim of exhaustive PDF threat detection.

| Area | Exact change from installed800a591 |
|---|---|
| Python/app dependencies | No pyproject/requirements changes. Existing MaxMind/Pillow/PDF reader dependencies remain. Normal guarded editable TeleTena metadata rebuild only; no other distribution/version/source may change. |
| Frontend | Locked `libphonenumber-js`1.13.15 added; existing locked dependencies preserved. `npm ci` via repository build script. |
| Schema | Only v1.39 `tt_history_document`:id,patient,filename,mime,LONGBLOB content,content_size,content_sha256,created; owner/content/name unique key and owner/time index. Additive,initially empty. Fresh bootstrap invokes it. No update/delete/backfill of existing records. |
| Configuration | No automatic changes. Optional `tele_tena_country_mmdb`, `tele_tena_country_trusted_proxies`; owner quota `tele_tena_history_storage_mb` defaults100MB. Existing site/provider/access/LiveKit/financial settings unchanged. |
| Functional UI | Country selector; shared drop/picker controls for photo/resume/evidence; multiple owner-only history files in onboarding/profile,textarea retained. |
| Preserved runtime | OTP authorization/provider,booking,financial/consent/disclosure,LiveKit,scheduler hooks,ERPNext/Frappe versions unchanged. Deployment tools/docs are not automatically invoked. |

**Country is not SMS coverage.** UI and server restrict SMS Ethiopia to Ethiopian
mobile numbers (`+2517…`/`+2519…`). Other selections direct users to email; no new
SMS destinations or live delivery are implied. No MMDB configuration is required
for manual country selection. Without it,loopback/private/unknown IP defaults to
editable Ethiopia. Do not install optional packages or trust forwarded headers
as part of this update. Separate setup,if wanted,requires verified proxy CIDRs.

History files are owner-only blobs,not public Frappe File URLs. Other patients,
clinicians,reviewers,clinics and guests cannot download them. Text-history sharing
never grants file access. Server validates extension,decoded5MB size,content/parser,
PDF restrictions,image format and owner storage quota. Downloads are attachment,
private/no-store,nosniff,sandbox. No fixed file-count cap; quota applies.

## 1. Inspect without changing the repaired environment

Run as normal `smcs`. Execute blocks separately and stop on **any** failure or
unexpected output. Coordinate a shared-Bench maintenance window:stopping the four
Python services below interrupts **all** Bench sites. Their names were previously
observed;compare current status before using them. Never substitute `restart all`.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
SITE=teletena.selfmadecs.com
OLD_SHA=800a591ac6af9c6c3b4afd61ed4353be4ff0826e
RELEASE_SHA=deeb583fbbfaaf276acc51aef05982dbf28d27e8
BENCH_CLI=/home/smcs/.pyenv/versions/3.14.2/bin/bench
TOOL_SHA=53dd0df81342eedd8f7785a732f97827316159cb
UPDATE_BACKUP=$(mktemp -d /home/smcs/teletena-before-refinements.XXXXXXXX)
chmod 700 "$UPDATE_BACKUP"
test "$(git -C apps/tele_tena rev-parse HEAD)" = "$OLD_SHA"
test -z "$(git -C apps/tele_tena status --porcelain)"
test -z "$(git -C apps/erpnext status --porcelain)"
env/bin/python -m pip check
env/bin/python - "$OLD_SHA" <<'PYOLD'
import json,sys
from pathlib import Path
assert json.loads(Path('apps/tele_tena/tele_tena/public/review/release.json').read_text())['source_commit']==sys.argv[1]
print('PASS: existing source/build800a591 match')
PYOLD
"$BENCH_CLI" --version
"$BENCH_CLI" --site "$SITE" list-apps
"$BENCH_CLI" --site "$SITE" doctor
sudo supervisorctl status
sudo nginx -t
test "$(env/bin/python -c 'import platform;print(platform.python_version())')" = 3.14.2
test "$(node --version)" = v24.13.0
test "$(git -C apps/frappe rev-parse HEAD)" = 8f6e24728b86b7c6427908ed6536289a41ea9cf4
test "$(git -C apps/erpnext rev-parse HEAD)" = bb2bada1fde0ae7a3c3cad32bed781ebd470e27d
printf '%s\n' "$OLD_SHA" > "$UPDATE_BACKUP/tele_tena.sha"
git -C apps/ecommerce_integrations rev-parse HEAD > "$UPDATE_BACKUP/amazon.sha"
git -C apps/ecommerce_integrations diff --binary HEAD > "$UPDATE_BACKUP/amazon-working.patch"
cp sites/apps.txt "$UPDATE_BACKUP/apps.txt"
cp sites/common_site_config.json "$UPDATE_BACKUP/common_site_config.json"
cp "sites/$SITE/site_config.json" "$UPDATE_BACKUP/site_config.json"
cp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
env/bin/python -m pip list --format=json > "$UPDATE_BACKUP/packages.json"
sudo nginx -T > "$UPDATE_BACKUP/nginx.loaded.before.txt" 2> "$UPDATE_BACKUP/nginx.before.log"
git -C apps/tele_tena fetch origin fix/selfmade-incremental-refinements
git -C apps/tele_tena cat-file -e "$RELEASE_SHA^{commit}"
git -C apps/tele_tena merge-base --is-ancestor "$OLD_SHA" "$RELEASE_SHA"
git -C apps/tele_tena merge-base --is-ancestor 5efe78527309f8dab9e2a5bb391114cba153a862 "$RELEASE_SHA"
TOOLS="$UPDATE_BACKUP/tools"
mkdir -m 700 "$TOOLS"
for TOOL in dependency_checkpoint.py release_preflight.py check_frappe_lock.py backup_review_release.py verify_release_backup.py restore_review_release.py; do
  git -C apps/tele_tena show "$TOOL_SHA:scripts/$TOOL" > "$TOOLS/$TOOL"
done
env/bin/python "$TOOLS/check_frappe_lock.py" apps/frappe
env/bin/python "$TOOLS/release_preflight.py" --bench /home/smcs/frappe-bench --site "$SITE" > "$UPDATE_BACKUP/preflight.before.json"
env/bin/python "$TOOLS/dependency_checkpoint.py" snapshot "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
```

Require healthy existing queues/scheduler,review-site binding,no developer mode,
CSRF bypass or SQL-body logging;versions as verified above. Any other TeleTena
site sharing this code must also have an approved compatible migration plan.
The known caniuse-lite-only Frappe lock delta is preserved;other edits stop the
check. Do not discard changes. Amazon source/working patch and every installed
package/direct/editable identity are recorded for preservation,not repaired.

Privately inspect the saved nginx dump for the **existing TeleTena server's**
trailing-slash removal exception:it must exempt `/teletena` and its descendants.
Preserve it exactly. Do not regenerate shared Nginx configuration,replace its
server block,or reload Nginx for this application-only update. Before outage:

```bash
curl --fail --silent --show-error --max-redirs 0 --output /dev/null \
  --write-out 'Existing /teletena/ HTTP %{http_code}\n' https://teletena.selfmadecs.com/teletena/
```

Expected200 directly. A redirect,loop or unexpected host is a stop to inspect the
already-configured exception;do not follow an old guide that removes it.

## 2. Stop writers and create a complete verified backup

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
# Preserve private manifests/provider credentials outside private/files as well.
tar --create --file "$UPDATE_BACKUP/private-state.tar" --exclude='./files' --exclude='./backups' \
  -C "sites/$SITE/private" .
test -s "$UPDATE_BACKUP/private-state.tar"
tar --list --file "$UPDATE_BACKUP/private-state.tar" > "$UPDATE_BACKUP/private-state.files"
sha256sum "$UPDATE_BACKUP/private-state.tar" > "$UPDATE_BACKUP/private-state.sha256"
sha256sum --check "$UPDATE_BACKUP/private-state.sha256"
cp -a apps/tele_tena/tele_tena/public/review "$UPDATE_BACKUP/review-assets"
printf 'Protected backup location: %s\n' "$UPDATE_BACKUP"
```

Expected:four named Python services STOPPED;fresh database,public/private archives,
site config and private checksum manifest verified. Missing/corrupt archives fail,
including the previous empty-selection failure case. Backups/config/private
manifests stay under the mode700 directory,not nginx. Do not apply755/644 to them.
The helper's temporary DB option file prevents passwords appearing in child argv.
If existing encrypted-backup policy is enabled,it stops for a reviewed encrypted
procedure;never disable encryption. Copy the verified bundle to protected backup
storage before proceeding. Redis,DB,nginx and Node Socket.IO remain running.

## 3. Pinned app-only update,locked build and public permissions

```bash
git -C apps/tele_tena checkout --detach "$RELEASE_SHA"
test -z "$(git -C apps/tele_tena status --porcelain)"
env/bin/python -m pip install --dry-run --constraint "$UPDATE_BACKUP/dependencies/constraints.txt" \
  --report "$UPDATE_BACKUP/dependency-plan.json" -e apps/tele_tena > "$UPDATE_BACKUP/dependency-plan.log" 2>&1
env/bin/python "$TOOLS/dependency_checkpoint.py" plan "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena --report "$UPDATE_BACKUP/dependency-plan.json"
env/bin/python -m pip install --constraint "$UPDATE_BACKUP/dependencies/constraints.txt" \
  -e apps/tele_tena > "$UPDATE_BACKUP/dependency-install.log" 2>&1
env/bin/python "$TOOLS/dependency_checkpoint.py" verify "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
env/bin/python -m pip check
env/bin/python apps/tele_tena/scripts/build_review.py > "$UPDATE_BACKUP/frontend-build.log" 2>&1
"$BENCH_CLI" build --app tele_tena
# umask077 is correct for backups but public build output must be nginx-readable.
PUBLIC=/home/smcs/frappe-bench/apps/tele_tena/tele_tena/public
test -d "$PUBLIC/review"
test -z "$(find "$PUBLIC" -type l -print -quit)"
find "$PUBLIC" -type d -exec chmod 755 {} +
find "$PUBLIC" -type f -exec chmod 644 {} +
namei -l "$PUBLIC/review/release.json"
env/bin/python apps/tele_tena/scripts/check_review_assets.py --site-private "sites/$SITE/private"
env/bin/python - "$RELEASE_SHA" <<'PY'
import json,sys
from pathlib import Path
release=json.loads(Path('apps/tele_tena/tele_tena/public/review/release.json').read_text())
assert release['source_commit']==sys.argv[1]
print('PASS: packaged source',release['source_commit'])
PY
cmp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
test "$(git -C apps/ecommerce_integrations rev-parse HEAD)" = "$(cat "$UPDATE_BACKUP/amazon.sha")"
git -C apps/ecommerce_integrations diff --binary HEAD > "$UPDATE_BACKUP/amazon-working.after.patch"
cmp "$UPDATE_BACKUP/amazon-working.patch" "$UPDATE_BACKUP/amazon-working.after.patch"
```

The dependency plan must contain only the intentional editable TeleTena rebuild.
No shared repair,Amazon checkout or unrelated package installation is authorized.
Stop on resolver/preservation failure;do not use `--no-deps` or relax constraints.
Public permissions apply **only** to the app's public subtree. Check parent
traversal with `namei`;if nginx cannot traverse an ancestor,stop for a narrowly
reviewed ownership/group fix. Never recursively chmod the Bench,sites,home,private
files or backups. Existing private modes are retained. A5MB base64 JSON upload needs approximately7MB
of request-body allowance. Inspect the current TeleTena server/location limit
privately;HTTP413 is a proxy limit,not permission to bypass app validation or
regenerate shared nginx. Any required site-only adjustment is a separate reviewed
operation,not performed by these commands.

## 4. Target-only migration and scoped service recovery

```bash
"$BENCH_CLI" --site "$SITE" migrate > "$UPDATE_BACKUP/migrate.log" 2>&1
"$BENCH_CLI" --site "$SITE" clear-cache
"$BENCH_CLI" --site "$SITE" clear-website-cache
cmp sites/common_site_config.json "$UPDATE_BACKUP/common_site_config.json"
cmp sites/apps.txt "$UPDATE_BACKUP/apps.txt"
env/bin/python "$TOOLS/dependency_checkpoint.py" verify "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
sudo nginx -t
sudo nginx -T > "$UPDATE_BACKUP/nginx.loaded.after.txt" 2> "$UPDATE_BACKUP/nginx.after.log"
cmp "$UPDATE_BACKUP/nginx.loaded.before.txt" "$UPDATE_BACKUP/nginx.loaded.after.txt"
sudo supervisorctl start frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl status
"$BENCH_CLI" --site "$SITE" set-maintenance-mode off
"$BENCH_CLI" --site "$SITE" doctor
env/bin/python "$TOOLS/release_preflight.py" --bench /home/smcs/frappe-bench --site "$SITE" > "$UPDATE_BACKUP/preflight.after.json"
```

Require v1.39 migration success;no financial migration/reseed/reconciliation repair
is performed. If any migration fails,keep writers stopped and logs intact. No
`--site all`,no nginx reload/regeneration,no scheduler/access/provider settings
change. Start only services actually stopped in this window;they resume all shared
sites. A different current service list is a stop to derive the correct names,
not permission to invent them. Existing scheduled jobs retain their queues/policy.

## 5. HTTPS,authentication,private files and PWA checks

No credentials in curl arguments. Run the following read-only unauthenticated
check;it checks TLS normally and fails on loops,missing assets or wrong source:

```bash
env/bin/python - "$RELEASE_SHA" <<'PY'
import hashlib,json,sys
from urllib.request import urlopen
from urllib.error import HTTPError
base='https://teletena.selfmadecs.com'
def get(path):
    response=urlopen(base+path,timeout=30)
    assert response.status==200
    return response,response.read()
response,index=get('/teletena/')
assert response.url==base+'/teletena/'
assert 'no-store' in response.headers.get('Cache-Control','')
response,_=get('/teletena/patient/account')
assert 'no-store' in response.headers.get('Cache-Control','')
_,body=get('/assets/tele_tena/review/release.json');release=json.loads(body)
assert release['source_commit']==sys.argv[1]
for path,digest in release['files'].items():
    _,content=get('/assets/tele_tena/review/'+path)
    assert hashlib.sha256(content).hexdigest()==digest,'Static asset differs: '+path
response,worker=get('/teletena/sw.js')
assert response.headers.get('Service-Worker-Allowed')=='/teletena/'
assert 'no-store' in response.headers.get('Cache-Control','')
_,body=get('/api/method/tele_tena.api.contact_auth.session')
assert json.loads(body)['message']['authenticated'] is False
try:
    get('/api/method/tele_tena.api.history_documents.list_documents')
    raise AssertionError('Guest history list unexpectedly accessible')
except HTTPError as error:
    assert error.code in (401,403)
print('PASS HTTPS namespace/deep link,all asset hashes,SW scope,guest state and private history denial')
PY
```

Then use the **existing** private demo manifest and accounts. Do not seed or reset
passwords. Sign in as a patient using the existing password/email path;open
Account→Personal profile→Optional saved history. Existing text/privacy settings
must remain. Upload two small fictional PDF/PNG/JPEG files,refresh,download and
remove only your new test files. Verify another patient,clinician and reviewer
cannot download the copied authenticated API link;guests must be denied too.
Check filename/content mismatch and a file above5MB fail usefully. No live patient
content and no external delivery. Verify existing reviewer/clinician login and an
existing appointment/detail without making a new charge just for deployment.

On signed-out phone access,confirm country selector and Ethiopian-only SMS help.
Other countries use email;do not send trial SMS as an automatic smoke check.
Optional IP suggestion can remain unconfigured/manual. Preserve SMS/SMTP/LiveKit
secrets and registration switches exactly. No live-provider claim from local tests.

For an already-open browser,finish any active call/edit first. Use the supported
update prompt and reload when safe. Confirm `release.json` source and new country/
upload controls. Service worker caches public static assets only;authenticated
API/history/file responses must not appear in Cache Storage. Never clear an
active consultation or force a SW update to reload it. A stale offline fallback
is diagnosed by HTTPS/server/build checks first,not by indiscriminate cache reset.
Inspect after-preflight for subscribed workers/unpaused intended scheduler and
new scheduled-job execution metadata. Do not manually invoke earnings release,
expire active records,enable another site's scheduler or purge shared queues.

## 6. Rollback

Keep the repaired packages,healthy external Bench and Amazon patch. Before
migration,code plus matched public assets can be restored if no new-format writes
occurred. After migration or legitimate new writes,old code alone is **not** a
rollback. Prefer fix-forward if new registrations/uploads/financial events occurred;
a full restore would lose them. Obtain an explicit recovery choice before that.

For an immediate failed update with no new legitimate activity:stop the same
four services,maintenance on,and capture the current failed state first:

```bash
"$BENCH_CLI" --site "$SITE" set-maintenance-mode on
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl stop frappe-bench-web:frappe-bench-frappe-web
RECOVERY=$(mktemp -d "$UPDATE_BACKUP/pre-rollback.XXXXXXXX")
env/bin/python "$TOOLS/backup_review_release.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" --destination "$RECOVERY/site-backups"
env/bin/python "$TOOLS/verify_release_backup.py" "$RECOVERY/site-backups"
env/bin/python "$TOOLS/verify_release_backup.py" "$UPDATE_BACKUP/site-backups"
sha256sum --check "$UPDATE_BACKUP/private-state.sha256"
# New history uploads require selective recovery,never silent data loss.
env/bin/python - "$SITE" <<'PYHISTORY'
import os,sys
os.chdir('sites')
import frappe
frappe.init(site=sys.argv[1]);frappe.connect()
try:
    exists=frappe.db.sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=%s",('tt_history_document',))[0][0]
    if exists and frappe.db.sql('SELECT COUNT(*) FROM tt_history_document')[0][0]:
        raise SystemExit('STOP: new private history uploads exist; choose fix-forward/selective recovery')
finally:frappe.destroy()
PYHISTORY
# Preserve current files/metadata before replacing matched snapshot contents.
env/bin/python - "$SITE" "$RECOVERY" <<'PY'
from pathlib import Path
import shutil,sys
assert sys.argv[1]=='teletena.selfmadecs.com'
root=Path('sites')/sys.argv[1];saved=Path(sys.argv[2])
for kind in ('public','private'):
    current=root/kind/'files'
    if current.exists():shutil.move(str(current),str(saved/(kind+'-files')))
    current.mkdir(parents=True,exist_ok=True,mode=0o700 if kind=='private' else 0o755)
(saved/'private-state').mkdir(mode=0o700)
for current in (root/'private').iterdir():
    if current.name not in ('files','backups'):shutil.move(str(current),str(saved/'private-state'/current.name))
PY
git -C apps/tele_tena checkout --detach "$OLD_SHA"
env/bin/python "$TOOLS/restore_review_release.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" --confirm-restore-site "$SITE" --backup "$UPDATE_BACKUP/site-backups"
tar --extract --file "$UPDATE_BACKUP/private-state.tar" -C "sites/$SITE/private"
cp "$UPDATE_BACKUP/site_config.json" "sites/$SITE/site_config.json"
chmod 600 "sites/$SITE/site_config.json"
# Preserve the failed new asset bundle;restore matched old assets,not a mixture.
mv apps/tele_tena/tele_tena/public/review "$RECOVERY/new-review-assets"
cp -a "$UPDATE_BACKUP/review-assets" apps/tele_tena/tele_tena/public/review
find apps/tele_tena/tele_tena/public -type d -exec chmod 755 {} +
find apps/tele_tena/tele_tena/public -type f -exec chmod 644 {} +
env/bin/python apps/tele_tena/scripts/check_review_assets.py --site-private "sites/$SITE/private"
env/bin/python "$TOOLS/dependency_checkpoint.py" verify "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
test "$(git -C apps/ecommerce_integrations rev-parse HEAD)" = "$(cat "$UPDATE_BACKUP/amazon.sha")"
cmp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
"$BENCH_CLI" --site "$SITE" clear-cache
"$BENCH_CLI" --site "$SITE" clear-website-cache
```

Native same-site SQL restore restores backed-up tables;it does not silently drop
additional v1.39 tables. With no post-update activity,the empty additive history
table may remain inert under800a591. If it contains new records,stop for selective
recovery;never delete it to make an old schema appear restored. Current-state
backup retains all new blobs and audit evidence. Do not replay migrations using
new code on the restored old data. Inspect target queued jobs for code/data
compatibility;never purge shared Redis queues. Resume only the previously stopped
services and original maintenance/scheduler state. For the previously running
services used above,the exact recovery commands are:

```bash
sudo supervisorctl start frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl status
"$BENCH_CLI" --site "$SITE" doctor
```

Rerun the HTTPS verification block with `"$OLD_SHA"` instead of `"$RELEASE_SHA"`,
omitting the new history endpoint check because that method is absent at800a591.
The restored pre-window site config retains its previous maintenance/scheduler
state;do not globally enable services that were previously intentionally stopped. Keep nginx exception and restrictive private permissions unchanged.

See [incremental-refinements-verification.md](incremental-refinements-verification.md)
for actual local results and external gates. Remote HTTPS/device/provider checks
are operator acceptance,not claimed local achievements.
