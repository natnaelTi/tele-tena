# Selfmade Offline Telebirr Incremental Update

Operator procedure only; **nothing has been remotely deployed or merged**.
Install/build pin: **cd89a9ff82484233caa4a8353341cde6c3b4a182**.
Fetch branch `feat/offline-telebirr-mvp`, draft [PR50](https://github.com/natnaelTi/tele-tena/pull/50), dependent on unmerged [PR49](https://github.com/natnaelTi/tele-tena/pull/49). This pin preserves PR43–49 ancestry and the subsequent onboarding, Account, payment and language changes. Later guide/evidence commits need no runtime update. Read [sprint evidence](offline-telebirr-verification-2026-10-28.md) first.

Run as normal `smcs`, one checkpoint at a time in the same shell. Stop on **any**
failed command, unexpected source/version/service/identity, preservation mismatch,
missing archive or unresolved queue failure. Keep private logs for diagnosis;
never paste passwords, provider settings, backup contents or pip-report URLs.

This is for the **already repaired shared Bench**. No dependency repair, Amazon
patch change, framework upgrade, Bench installation/removal, public signup switch,
seed, scenario refresh or password reset. Do not run `bench update`, `pip install
-r apps/frappe/requirements.txt`, `bench setup nginx`, `bench setup supervisor`,
`--site all migrate`, or `--no-deps`. No new real-money rails are activated.

## 1. Establish the actual baseline — read-only application inspection

Plan a staff cutover window before proceeding. This release intentionally requires
individual care-language decisions even in Wallet mode. Earlier self-declarations
have no fabricated proficiency/approval: migrated claims are Pending, so affected
offerings are excluded from new discovery/booking until the clinician supplies a
self-assessment and a reviewer decides. Existing appointments remain unchanged.
Coordinate those clinicians/reviewers and test the updated eligibility before
inviting patients back. Do not represent a temporarily empty directory as migration
data loss or bypass the approval gate. If that staffed window is unavailable, stop
before checkout/migration and arrange it; it is not a reason to preapprove claims.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
SITE=teletena.selfmadecs.com
BENCH_CLI=/home/smcs/.pyenv/versions/3.14.2/bin/bench
RELEASE_SHA=cd89a9ff82484233caa4a8353341cde6c3b4a182
OLD_SHA=$(git -C apps/tele_tena rev-parse HEAD)
printf 'Installed TeleTena: %s\n' "$OLD_SHA"
git -C apps/tele_tena status --short
test -z "$(git -C apps/tele_tena status --porcelain)"
git -C apps/frappe status --short
git -C apps/erpnext status --short
git -C apps/ecommerce_integrations status --short
test -z "$(git -C apps/erpnext status --porcelain)"
"$BENCH_CLI" --version
"$BENCH_CLI" --site "$SITE" list-apps
"$BENCH_CLI" --site "$SITE" doctor
env/bin/python --version
node --version
env/bin/python -m pip check
sudo supervisorctl status
sudo nginx -t
test "$(env/bin/python -c 'import platform;print(platform.python_version())')" = 3.14.2
test "$(node --version)" = v24.13.0
test "$(git -C apps/frappe rev-parse HEAD)" = 8f6e24728b86b7c6427908ed6536289a41ea9cf4
test "$(git -C apps/erpnext rev-parse HEAD)" = bb2bada1fde0ae7a3c3cad32bed781ebd470e27d
UPDATE_BACKUP=$(mktemp -d /home/smcs/teletena-before-offline-payments.XXXXXXXX)
chmod 700 "$UPDATE_BACKUP"
printf '%s\n' "$OLD_SHA" > "$UPDATE_BACKUP/tele_tena.sha"
git -C apps/tele_tena branch --show-current > "$UPDATE_BACKUP/tele_tena.branch"
curl --fail --silent --show-error --max-redirs 0 \
  https://teletena.selfmadecs.com/assets/tele_tena/review/release.json \
  > "$UPDATE_BACKUP/served-release.before.json"
curl --fail --silent --show-error --max-redirs 0 --output /dev/null \
  --write-out 'Existing /teletena/ HTTP %{http_code}\n' \
  https://teletena.selfmadecs.com/teletena/
"$BENCH_CLI" --site all list-apps > "$UPDATE_BACKUP/all-sites-apps.txt"
git -C apps/tele_tena fetch origin feat/offline-telebirr-mvp
git -C apps/tele_tena cat-file -e "$RELEASE_SHA^{commit}"
git -C apps/tele_tena merge-base --is-ancestor "$OLD_SHA" "$RELEASE_SHA"
git -C apps/tele_tena merge-base --is-ancestor 800a591ac6af9c6c3b4afd61ed4353be4ff0826e "$OLD_SHA"
TOOLS="$UPDATE_BACKUP/tools"
mkdir -m 700 "$TOOLS"
for TOOL in dependency_checkpoint.py release_preflight.py check_frappe_lock.py backup_review_release.py verify_release_backup.py restore_review_release.py export_loaded_supervisor.py release_preservation.py; do
  git -C apps/tele_tena show "$RELEASE_SHA:scripts/$TOOL" > "$TOOLS/$TOOL"
done
env/bin/python "$TOOLS/check_frappe_lock.py" apps/frappe
env/bin/python "$TOOLS/release_preflight.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" > "$UPDATE_BACKUP/preflight.before.json"
sudo /usr/bin/python3 "$TOOLS/export_loaded_supervisor.py" \
  > "$UPDATE_BACKUP/supervisor.loaded.json"
```

Expected: clean TeleTena/ERPNext, healthy repaired `pip check`, versions above,
subscribed workers, scheduler enabled/unpaused, review binding correct, no developer
mode/CSRF bypass/SQL-body logging, directHTTPS200. `check_frappe_lock` accepts only
clean or the already reviewed caniuse-lite-only change. Preserve it. Amazon local
patches may be intentional; record them below, never discard them.

Inspect the private all-sites list: if another site has TeleTena installed, **stop**
for that site's approved compatibility/migration plan: Python code and assets are
Bench-wide. An unknown/non-ancestor or pre800a591 installed release is also a stop
for a baseline-specific plan, not permission to reset/force checkout.

Confirm the **loaded** RPC service commands and running processes, not merely a
regenerated config. If the system Supervisor Python/RPC helper is unavailable,
stop and identify its actual interpreter; do not install into the application env.
For currently running worker/scheduler PIDs shown in `sudo supervisorctl status`:

```bash
env/bin/python - <<'PY'
from pathlib import Path
import re,subprocess
for line in subprocess.check_output(['sudo','supervisorctl','status'],text=True).splitlines():
    if not line.startswith('frappe-bench-workers:'): continue
    match=re.search(r'\bpid\s+(\d+)',line)
    assert match,'Expected running worker/scheduler; inspect before update'
    p=Path('/proc')/match.group(1)
    args=(p/'cmdline').read_bytes().split(b'\0')
    print(line.split()[0], 'exe=',(p/'exe').resolve(), 'cwd=',(p/'cwd').resolve(),
          'argv0=',args[0].decode(), 'bench_helper=',b'frappe.utils.bench_helper' in args)
PY
```

Previously observed names below must match the current evidence; otherwise stop
and derive the commands from the observed service manager. Workers ultimately
using the app env's `python -m frappe.utils.bench_helper` is expected. Keep the
healthy external Bench CLI and existing launchers; no CLI removal/reconfiguration.

Record protected shared state before the outage:

```bash
cp sites/apps.txt "$UPDATE_BACKUP/apps.txt"
cp sites/common_site_config.json "$UPDATE_BACKUP/common_site_config.json"
cp "sites/$SITE/site_config.json" "$UPDATE_BACKUP/site_config.before-maintenance.json"
cp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
git -C apps/ecommerce_integrations rev-parse HEAD > "$UPDATE_BACKUP/amazon.sha"
git -C apps/ecommerce_integrations diff --binary HEAD > "$UPDATE_BACKUP/amazon.patch"
sudo nginx -T > "$UPDATE_BACKUP/nginx.before.txt" 2> "$UPDATE_BACKUP/nginx.before.log"
env/bin/python "$TOOLS/dependency_checkpoint.py" snapshot "$UPDATE_BACKUP/dependencies" \
  --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
```

Privately confirm the existing **TeleTena Nginx block exempts `/teletena` from
trailing-slash removal**, including its descendants. Preserve the dump/exception;
this procedure requires no Nginx regeneration or reload. Review the baseline's
actual app/version/schema delta privately if different from previously prepared
deeb583: `git -C apps/tele_tena diff --stat "$OLD_SHA" "$RELEASE_SHA"` and
`git -C apps/tele_tena diff "$OLD_SHA" "$RELEASE_SHA" -- pyproject.toml frontend/package-lock.json tele_tena/patches.txt`.

## 2. Stop writers and create a verified complete backup

**Arrange a shared-Bench maintenance window first.** These four Python services
serve/work for all sites. This unavoidable interruption prevents stale Python
workers or web processes writing old events after migration. Redis, MariaDB,
Nginx and Socket.IO remain running. Never use `stop all`/`restart all`.

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
printf 'Protected backup location: %s\n' "$UPDATE_BACKUP"
```

Require four STOPPED statuses and all explicitly named backup artifacts. The
verifier checks gzip/TAR integrity, required config and SHA256; missing archives
fail, even when a shell glob would have matched nothing. It uses a temporary
mode600 DB option file, not a password argument. Encryption policy enabled?
Stop for a verified encrypted-backup procedure; do not disable it. Copy this
mode700 bundle to protected backup storage before proceeding. The extra private
archive preserves provider files/account manifests outside `private/files`.
No passwords or clinical contents are printed. Do not change private permissions.

This update intentionally grants financial configuration to current reviewers through the auditedv1.48 migration. It does not grant receipt/private clinical access, change payment mode or activate providers. New payment links resolve directly to the authorized receipt page. See [navigation verification](payment-navigation-verification-2026-10-28.md).

## 3. Pinned, guarded app update and packaged assets

```bash
git -C apps/tele_tena checkout --detach "$RELEASE_SHA"
test -z "$(git -C apps/tele_tena status --porcelain)"
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
env/bin/python apps/tele_tena/scripts/build_review.py > "$UPDATE_BACKUP/frontend-build.log" 2>&1
"$BENCH_CLI" build --app tele_tena
PUBLIC=/home/smcs/frappe-bench/apps/tele_tena/tele_tena/public
test -d "$PUBLIC/review"
test ! -L "$PUBLIC"
test -z "$(find "$PUBLIC/review" -type l -print -quit)"
chmod 755 "$PUBLIC"
find "$PUBLIC/review" -type d -exec chmod 755 {} +
find "$PUBLIC/review" -type f -exec chmod 644 {} +
namei -l "$PUBLIC/review/release.json"
env/bin/python apps/tele_tena/scripts/check_review_assets.py --site-private "sites/$SITE/private"
env/bin/python - "$RELEASE_SHA" <<'PY'
import json,sys
from pathlib import Path
r=json.loads(Path('apps/tele_tena/tele_tena/public/review/release.json').read_text())
assert r['source_commit']==sys.argv[1]
print('PASS packaged source',r['source_commit'])
PY
"$BENCH_CLI" --site "$SITE" migrate > "$UPDATE_BACKUP/migrate.log" 2>&1
"$BENCH_CLI" --site "$SITE" clear-cache
"$BENCH_CLI" --site "$SITE" clear-website-cache
env/bin/python "$TOOLS/release_preservation.py" verify --bench /home/smcs/frappe-bench \
  --site "$SITE" --snapshot "$UPDATE_BACKUP/preserved-state.json"
```

Expected plan: **only** the intentional local editable `tele-tena` package. It
rejects other replacements, new packages, version/source changes and swapped
editable identities. No `--no-deps`, relaxed constraints or repeated shared repair.
No Python requirement changes from PR49. Frontend Vite is pinned to8.3.3 to resolve the development-server advisories; no other locked frontend package version changed in that patch. Source changes do not require reinstalling Frappe dependencies. The repository build performs locked `npm ci`;
no Vite server. The native app build maintains the existing assets link. Verify
`readlink -f sites/assets/tele_tena` resolves to `$PUBLIC`; stop if it differs.

Public755/644 applies only to this output/root, **never** Bench/sites/backups,
configuration or private files. If an ancestor is not traversable by Nginx, stop
for a narrow ownership/group fix rather than recursively chmodding a home.
Migration adds any missing earlier patches and v1.45–v1.48. Existing payment mode is preserved (fresh installations default to Wallet); new language claims are Pending, never automatically approved. It must not rewrite original records,
credentials, sharing choices, wallets or historical holds. Preserve failure logs;
do not skip patches or seed data to make migration/preservation pass.

## 4. Shared-state checks and scoped recovery

```bash
cmp sites/apps.txt "$UPDATE_BACKUP/apps.txt"
cmp sites/common_site_config.json "$UPDATE_BACKUP/common_site_config.json"
cmp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
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

Start only these currently verified/stopped services; they resume all shared
sites. Do not restart Nginx, Redis, database, Socket.IO or unrelated services.
Require web/workers/scheduler RUNNING and intended queues subscribed. Check the
private after-preflight for successful current TeleTena job executions; wait for
the normal minute/five-minute schedules. A running process alone does not prove
execution. Do not manually release earnings, purge queues or change dispute policy.
If the original scheduler was disabled/unhealthy, diagnose that baseline with the
operator before this update; these commands do not silently enable it or change
provider/access switches.

## 5. HTTPS, privacy, PWA and existing-account smoke checks

```bash
env/bin/python - "$RELEASE_SHA" <<'PY'
import hashlib,json,sys
from urllib.request import urlopen
from urllib.error import HTTPError
base='https://teletena.selfmadecs.com'
def get(path):
    r=urlopen(base+path,timeout=30);assert r.status==200;return r,r.read()
r,_=get('/teletena/');assert r.url==base+'/teletena/'
assert 'no-store' in r.headers.get('Cache-Control','')
for path in ['/teletena/care','/teletena/patient/requests','/teletena/clinician/account']:
    r,_=get(path);assert 'no-store' in r.headers.get('Cache-Control','')
_,body=get('/assets/tele_tena/review/release.json');release=json.loads(body)
assert release['source_commit']==sys.argv[1]
for name,digest in release['files'].items():
    _,content=get('/assets/tele_tena/review/'+name)
    assert hashlib.sha256(content).hexdigest()==digest,'Asset hash differs: '+name
r,_=get('/teletena/sw.js');assert r.headers.get('Service-Worker-Allowed')=='/teletena/'
assert 'no-store' in r.headers.get('Cache-Control','')
_,body=get('/api/method/tele_tena.api.contact_auth.session');assert not json.loads(body)['message']['authenticated']
_,body=get('/api/method/tele_tena.api.directory.offerings');assert isinstance(json.loads(body)['message']['items'],list)
try:
    get('/api/method/tele_tena.api.history_documents.list_documents')
    raise AssertionError('Guest history access allowed')
except HTTPError as e:assert e.code in (401,403)
print('PASS HTTPS routes/assets/SW scope/guest discovery/private history denial;source',release['source_commit'])
PY
```

Use the **existing** private demo-account manifest on the site; never print its
passwords or run any seed/refresh. Walkthrough:

1. Guest: Find Care → service groups/reactive language/format/availability filters
   → View profile → Sign in to Book. Existing patient sign-in returns to that
   exact offering's calendar, not Home. Refresh preserves the selection.
2. Patient: confirm existing privacy/file preferences and balances. For a new booking, review the real total/disclosure and the snapshotted payment method. Confirmed
   versus pending must be truthful. Notifications bell and Appointment delivery
   history show actual known states; provider acceptance is not receipt.
3. Clinician: Today/Requests availability card; published schedule and connected
   presence required. Manual pause survives navigation/reload, capacity pauses
   resume when a full session fits. Requests → private offer → patient acceptance
   → persisted outcome/authorized appointment link. No competitor quotes visible.
4. Account: compact editors/photo crop; history files private until individually
   selected for a particular treating clinician. Use only new fictional files for
   any upload smoke test; verify cross-role download denial.
5. Individual/couples appointment: consented participants, authorized join window,
   Leave/rejoin distinct from clinician End; private notes/shared recipients and
   mode-correct financial result on finalization (Wallet pending earning; Offline no second receipt or wallet credit). Do not force historical calls or balances.

New-patient actual-name/text defaults are editable; **existing choices are not
changed**. Uploaded files still require individual selection. No full history is
broadcast to request recipients. Three minutes produces one clinician email
reminder, not automatic cancellation: the booking's accepted expiry policy governs
cancellation. Booking Confirmation Response remains separate from competence and
clinical ranking. SMS remains Ethiopian-only despite country selection.

Only test signup if its **existing** site switches permit it. Live delivery needs
configured providers and a consenting recipient; do not enable switches or send
bulk demo messages. OTP test transports are local verification tools, not remote
server entrypoints. No live SMS/email/physical-device result is implied here.

For an already open PWA, finish unsaved work and use its **update/refresh** prompt.
Verify the network-served release manifest first; a normal reload fetches the
no-store shell. If still stale, inspect service-worker update/registration and
network failures. Clearing browser data is not a substitute for correcting wrong
source, missing assets, permissions or the preserved Nginx slash exception.

## 6. Rollback — choose the correct boundary

Keep the backup path and original SHA outside the repository. Before migration
and before any new-format writes, code/assets rollback is sufficient **only if**
the dependency guard proved all other packages untouched:

```bash
# Keep the same four services stopped and the site in maintenance.
PUBLIC=/home/smcs/frappe-bench/apps/tele_tena/tele_tena/public
git -C apps/tele_tena checkout --detach "$(cat "$UPDATE_BACKUP/tele_tena.sha")"
env/bin/python -m pip install --constraint "$UPDATE_BACKUP/dependencies/constraints.txt" \
  -e apps/tele_tena > "$UPDATE_BACKUP/rollback-package.log" 2>&1
env/bin/python -m pip check
# Guard the exact ignored output path before replacing only public build assets.
test "$PUBLIC" = /home/smcs/frappe-bench/apps/tele_tena/tele_tena/public
test ! -L "$PUBLIC/review"
test -s "$UPDATE_BACKUP/review-assets/release.json"
rm -rf -- "$PUBLIC/review"
cp -a "$UPDATE_BACKUP/review-assets" "$PUBLIC/review"
```

After **any migration**, do not claim old code reverses schema. Prefer fix-forward
when legitimate new activity exists. A full restore loses post-backup activity;
obtain an explicit operator recovery decision first, and take another verified
backup of the failed/new state. Stop the same four writers again if they restarted,
turn target maintenance on, then restore the original code/assets as above and:

```bash
env/bin/python "$TOOLS/verify_release_backup.py" "$UPDATE_BACKUP/site-backups"
env/bin/python "$TOOLS/restore_review_release.py" --bench /home/smcs/frappe-bench \
  --site "$SITE" --backup "$UPDATE_BACKUP/site-backups" --confirm-restore-site "$SITE"
# Existing private provider/account state was not changed by this procedure.
# Restore the verified extra private archive only if it actually changed and
# after reviewing newer files; do not overwrite new credentials automatically.
env/bin/python "$TOOLS/release_preservation.py" verify --bench /home/smcs/frappe-bench \
  --site "$SITE" --snapshot "$UPDATE_BACKUP/preserved-state.json"
"$BENCH_CLI" --site "$SITE" clear-cache
"$BENCH_CLI" --site "$SITE" clear-website-cache
```

The restore helper requires matching DB/encryption credentials and maintenance;
it validates all backup digests and restores database/public/private-files together.
Do not overwrite shared `common_site_config.json`, Amazon code or shared packages.
No migration of the old code after restore. Restart the same verified four Python
services, turn maintenance off, repeat HTTPS checks against the **saved old build**
SHA and original-account smoke checks. If preservation differs, keep writers stopped
and inspect the protected backup/restore log; do not edit balances to reconcile it.


## 7. Explicit Offline Mode Cutover — Separate Operator Action

The update **does not** switch modes or change provider/access settings. New language approval is a deliberate prerequisite: each existing clinician opens Account → Professional Profile & Practice → Care Languages, supplies an explicit self-assessment, and the authorized reviewer records an individual language decision. Ensure approved offering languages remain appropriate. Pending declarations are preserved without invented ratings. Existing appointments and their original payment rules remain intact; withdrawn language approval flags future appointments for operational review.

1. Use Administrator or explicitly assign `Tele Tena Financial Configuration` to a trusted financial operator. Per the28October owner decision, v1.48 assigns this role to existing reviewers (Tele Tena Approver) and new administrator-assigned reviewers receive it by default. Clinicians do not receive it from their clinician role. Explicit later removals remain respected. Open `/teletena/financial-configuration`. Review current mode, revision, unresolved direct payments, legacy wallet holds and payout requests.
2. Each participating clinician saves their own Telebirr receiving number in Account's practice/payment section. It must be an eligible Ethiopian number. This is a declared receiving account, not provider verification. Public discovery never receives this number.
3. Agree the proposed hold/verification defaults (30 minutes/24 hours, capped at session start) and an operational late-proof/refund procedure before cutover. There is no three-minute payment cancellation rule.
4. Pause new intake during cutover, resolve active direct intents if any. If historical wallet holds/payouts or unresolved external reconciliation remain, supply a concrete audited transition plan. Historical Wallet appointments, holds, earnings and payouts keep their original method/rules. No money is converted or discarded.
5. Select Offline Direct Payment, enter the decision reason and any required transition plan, confirm. Stale clients receive a safe retry/refresh error; active clients refresh capabilities. Do not edit database mode rows or independent switches.
6. New booking/open-offer acceptance: authorized payer sees amount, ETB, snapshotted receiving number/reference and deadline; transfers externally; uploads a private JPEG/PNG receipt (5 MB/file) and transaction ID. Clinician verifies their actual Telebirr account. An image is only a claim. Automatic booking confirms after verification; manual acceptance remains a separate decision. Payment/appointment reminder clocks remain separate.
7. Read Expenses/Revenue Ledgers: Submitted is unverified, Verified means a clinician recorded receipt. No custody, withdrawable wallet earning, platform fee collection or automatic refund is implied. Completion must not credit the payment again. Offline-parent extensions require their own consent/quote/direct payment; Wallet-parent extensions retain Wallet rules.
8. Late/incorrect/disputed proof, a lost slot, or decline/cancellation after payment enters Reconciliation/Refund Required. Preserve every proof revision. Clinician reports an external refund; payer confirms receipt separately. No platform transfer is generated. Couples' second participant cannot access the payer's receipt/payee instructions.

Use the existing privately stored reviewer/demo accounts; **do not reseed, reset passwords, refresh scenarios or automatically send live notices**. For the new workflow, use a consenting operator and clearly synthetic receipt until an explicitly authorized real transfer test is arranged. Mock provider acceptance is not delivery. Production clinical/policy/translation approvals and physical-device checks remain external gates.

Rollback after mode selection must additionally preserve all new payment events/receipts and consult the operator about activity since backup; never restore an old snapshot over new direct-payment evidence without that decision. Turning Wallet back on does not erase Offline history; historical Direct Payment Activity remains accessible under its original authorization.
