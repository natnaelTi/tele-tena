# Selfmade — pinned final MVP review update

This prepares an operator update; **no remote deployment was performed**.
The current remote SHA/runtime/service state must be observed in step1, not
assumed from earlier reports. The previously reported host is managed Bench
`/home/smcs/frappe-bench`, site `teletena.selfmadecs.com`, Frappe16.2.1,
ERPNext16.1.0, Python3.14.2, Node24.13.0, MariaDB10.6.22, Redis6.0.16,
nginx1.18, Supervisor. The domain reportedly has no Cloudflare proxy.
Current version differences are a stop for investigation, not permission to
upgrade/downgrade shared frameworks, Node/Python or `bench update`.

Release pin: **800a591ac6af9c6c3b4afd61ed4353be4ff0826e** on `feat/mvp-release-handover`.
PR44 remains draft, depending on PR43 (`feat/adult-relationship-links`); this
branch contains its ancestry. Installing a pinned unmerged commit does not merge
any PR. Owner acceptance is still separate from automated verification.
Use this guide from the reviewed PR/doc checkout before detaching the app.

## 0. Recover the recorded interrupted attempt first

The supplied transcript ended after code checkout, before actual pip installation
or migration. Web/workers/scheduler were STOPPED and maintenance was on. If no
further install/migration occurred and TeleTena is clean, return it to
`8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6`, start the exact three worker/scheduler
and web names below, then `bench --site teletena.selfmadecs.com set-maintenance-mode off`.
This is pre-migration recovery, **not** a database rollback. Do not restore an
incomplete backup or discard the modified Frappe lockfile. If anything changed
after the transcript, inspect it before choosing recovery. Keep
`/home/smcs/teletena-before-mvp.8aDCDM6v` and failed dependency logs.

## 1. Inspect, preserve and stop conditions

Run as `smcs` with the existing Bench executable, not root. Do not paste output
containing credentials/configuration into chat. Execute blocks separately and
stop on any failed command or unexpected result.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
RELEASE_SHA='800a591ac6af9c6c3b4afd61ed4353be4ff0826e'
SITE='teletena.selfmadecs.com'
CURRENT_SHA=$(git -C apps/tele_tena rev-parse HEAD)
test "$CURRENT_SHA" = 8f7ab9cd8d5e779d17b632dc9afdae3e700ab3c6
printf 'Installed TeleTena commit: %s\n' "$CURRENT_SHA"
test -z "$(git -C apps/tele_tena status --porcelain)"
test -z "$(git -C apps/erpnext status --porcelain)"
bench --site "$SITE" list-apps
env/bin/python --version
node --version
env/bin/python -m pip check
sudo supervisorctl status
sudo nginx -t
bench --site "$SITE" doctor
```

If a checkout is dirty, **stop**. Commit or copy changes to protected backup
storage with the owner; do not stash/reset/force-checkout automatically. Record
which sites have TeleTena installed using a read-only inspection of installed
apps; incompatible schemas on another TeleTena site are a shared-code stop.
Existing non-TeleTena sites still share dependencies/assets/services.

Before any outage or checkout, `env/bin/python -m pip check` must pass. The supplied
14October baseline has eight conflicts: **stop here until the separate, staged
[shared-environment repair proposal](selfmade-shared-environment-repair.md) is resolved**.
A TeleTena update must not repair these by relaxing its guard.

Fetch the release without switching yet, then extract the tools outside the app so
the old checkout can remain intact:

```bash
git -C apps/tele_tena fetch origin feat/mvp-release-handover
git -C apps/tele_tena cat-file -e "$RELEASE_SHA^{commit}"
TOOLS=$(mktemp -d /home/smcs/teletena-release-tools.XXXXXXXX)
chmod 700 "$TOOLS"
for TOOL in release_preflight.py dependency_checkpoint.py shared_dependency_audit.py check_frappe_lock.py backup_review_release.py verify_release_backup.py; do
  git -C apps/tele_tena show "$RELEASE_SHA:scripts/$TOOL" > "$TOOLS/$TOOL"
done
PREFLIGHT="$TOOLS/release_preflight.py"
env/bin/python "$TOOLS/check_frappe_lock.py" apps/frappe
env/bin/python "$TOOLS/shared_dependency_audit.py" --bench /home/smcs/frappe-bench > "$TOOLS/all-app-dependencies.json"
env/bin/python -m pip check
env/bin/python "$PREFLIGHT" --bench /home/smcs/frappe-bench --site "$SITE"
```

Expected: TeleTena/Frappe/ERPNext installed, review bound to exactly this site,
no developer mode/CSRF bypass/SQL body logging, clean TeleTena/ERPNext checkouts, healthy queues. The exact supplied caniuse-lite-only
Frappe lock delta is allowed by the read-only check and remains untouched. Any other
Frappe change stops the update; never reset or discard the lockfile. Version assertions for the **previously verified target**:

```bash
test "$(env/bin/python -c 'import platform;print(platform.python_version())')" = 3.14.2
test "$(node --version)" = v24.13.0
test "$(env/bin/python -c 'import importlib.metadata as m;print(m.version("frappe"))')" = 16.2.1
test "$(env/bin/python -c 'import importlib.metadata as m;print(m.version("erpnext"))')" = 16.1.0
```

Inspect actual worker queue subscriptions. Two RUNNING workers do not prove the
default queue is subscribed. A job-count snapshot does not prove stuck jobs.
If default is not subscribed, stop and arrange the confirmed Supervisor worker
configuration; do not invent another unit, regenerate shared configuration or
purge queues. Preserve all LiveKit/SMS/SMTP/configuration and access switches.

## 2. Maintenance/cutover and verified backup

Coordinate a shared-bench maintenance window first: stopping the named web,
workers and scheduler pauses **all sites on this bench**, not just TeleTena.
These exact names were previously supplied by the operator. Compare them against
**today's** `supervisorctl status`; stop if any name/manager differs. Do not run
`restart all`, restart Redis/MariaDB/nginx or change sudoers.

```bash
UPDATE_BACKUP=$(mktemp -d /home/smcs/teletena-before-mvp.XXXXXXXX)
chmod 700 "$UPDATE_BACKUP"
printf '%s\n' "$CURRENT_SHA" > "$UPDATE_BACKUP/tele_tena.sha"
git -C apps/tele_tena branch --show-current > "$UPDATE_BACKUP/tele_tena.branch"
cp sites/apps.txt "$UPDATE_BACKUP/apps.txt"
cp sites/teletena.selfmadecs.com/site_config.json "$UPDATE_BACKUP/site_config.json"
cp sites/common_site_config.json "$UPDATE_BACKUP/common_site_config.json"
git -C apps/frappe diff HEAD --binary -- yarn.lock > "$UPDATE_BACKUP/frappe-yarn-lock.patch"
cp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
env/bin/python -m pip list --format=json > "$UPDATE_BACKUP/packages.json"
cp -a apps/tele_tena/tele_tena/public/review "$UPDATE_BACKUP/review-assets"
env/bin/python "$TOOLS/dependency_checkpoint.py" snapshot "$UPDATE_BACKUP/dependencies-update" --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
bench --site "$SITE" set-maintenance-mode on
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl stop frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl status
env/bin/python "$TOOLS/backup_review_release.py" --bench /home/smcs/frappe-bench --site "$SITE" \
  --destination "$UPDATE_BACKUP/site-backups"
env/bin/python "$TOOLS/verify_release_backup.py" "$UPDATE_BACKUP/site-backups"
test -s "$UPDATE_BACKUP/site-backups/database.sql.gz"
test -s "$UPDATE_BACKUP/site-backups/public-files.tar"
test -s "$UPDATE_BACKUP/site-backups/private-files.tar"
test -s "$UPDATE_BACKUP/site-backups/site-config.json"
test -s "$UPDATE_BACKUP/site-backups/verified-manifest.json"
printf 'Private verified backup bundle: %s\n' "$UPDATE_BACKUP"
```

Expected: named services STOPPED, explicit database/public/private archives present and nonempty. Native Frappe
BackupGenerator is invoked with file backup enabled, force enabled and partial
backup filters disabled in this CLI process. The temporary client option file
keeps database passwords out of argv; no framework files are modified.
The verifier consumes gzip and tar payloads and records private hashes; missing
or corrupt archives fail, even when a files directory has no user uploads.
An active encrypted-backup policy stops this helper for a verified encrypted
procedure; never turn encryption off to proceed. Check a matching site config/key;
copy the bundle to approved protected backup storage and confirm a restore path
before proceeding. Never publish backup/config/private files through nginx.
The saved config is from **before** maintenance mode. Socket.IO can remain running;
its code/dependencies are unchanged, but notifications pause with the web/worker.
The update snapshot is made using the new external helper **before** maintenance
or code switching, so invalid mode/identity fails without an outage.
This cutover prevents old web/workers from writing legacy financial events after
new financial schema activation. Do not migrate while any old writer remains.

## 3. Pinned source, additive dependencies and production assets

```bash
git -C apps/tele_tena checkout --detach "$RELEASE_SHA"
test "$(git -C apps/tele_tena rev-parse HEAD)" = "$RELEASE_SHA"
test -z "$(git -C apps/tele_tena status --porcelain)"
env/bin/python -m pip install --dry-run --constraint "$UPDATE_BACKUP/dependencies-update/constraints.txt" \
  --report "$UPDATE_BACKUP/dependency-plan.json" -e apps/tele_tena > "$UPDATE_BACKUP/dependency-plan.log" 2>&1
env/bin/python apps/tele_tena/scripts/dependency_checkpoint.py plan "$UPDATE_BACKUP/dependencies-update" --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena --report "$UPDATE_BACKUP/dependency-plan.json"
env/bin/python -m pip install --constraint "$UPDATE_BACKUP/dependencies-update/constraints.txt" -e apps/tele_tena > "$UPDATE_BACKUP/dependency-install.log" 2>&1
env/bin/python apps/tele_tena/scripts/dependency_checkpoint.py verify "$UPDATE_BACKUP/dependencies-update" --mode update --app-path /home/smcs/frappe-bench/apps/tele_tena
env/bin/python -m pip check
env/bin/python apps/tele_tena/scripts/build_review.py
bench build --app tele_tena
env/bin/python "$TOOLS/check_frappe_lock.py" apps/frappe
cmp apps/frappe/yarn.lock "$UPDATE_BACKUP/frappe-yarn.lock"
env/bin/python apps/tele_tena/scripts/check_review_assets.py --site-private sites/teletena.selfmadecs.com/private
```

Explicit update mode permits only TeleTena replacement, including its same-version
editable rebuild. No other distribution may be replaced or added in update mode. Every other
installed version **and editable identity** is protected; the TeleTena constraint alone is omitted. Default install mode refuses
an existing app. Use a new snapshot directory; preserve the earlier incomplete
`dependencies` folder and failed pip logs for diagnosis. The guard must pass
without replacing other package versions/identities. Stop on a
constraints conflict; do not relax pins or install Bench CLI into the app env.
Build uses `npm ci` and locked dependencies; packaged React lives in the app's
public/review assets. No Vite server/public development ports. No frontend .env
files or VITE secrets. Framework builds are app-scoped, though asset indexes and
app dependencies are shared. Ensure the generated `release.json` matches the pin.

## 4. Target-only migration and cache maintenance

```bash
bench --site "$SITE" migrate
bench --site "$SITE" clear-cache
bench --site "$SITE" clear-website-cache
```

Stop on migration/reconciliation failure. Existing wallet snapshots and unknown
legacy events must remain auditable; do not delete rows or silently accept a
financial discrepancy. Historical completed/reserved records are not silently
settled. Repeat migration is safe but does not mean old code can read new schema.
No `--site all migrate`, `bench update`, framework/core checkout change, seed,
credential reset or access-switch change is implicit in this step.

## 5. Start confirmed services and explicit review dataset

```bash
sudo supervisorctl start frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl start frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl status
bench --site "$SITE" set-maintenance-mode off
bench --site "$SITE" doctor
env/bin/python "$PREFLIGHT" --bench /home/smcs/frappe-bench --site "$SITE"
bench --site "$SITE" execute tele_tena.demo_dataset.setup
bench --site "$SITE" execute tele_tena.demo_dataset.setup --kwargs '{"dry_run":False}'
bench --site "$SITE" execute tele_tena.demo_dataset.setup --kwargs '{"dry_run":False}'
```

Read the first dry-run. Stop if review binding/configuration, positive-net fee
policy or namespace conflict checks fail; never toggle real-money/access settings
to force seeding. First creation initializes a fresh missing signing key only
when no encrypted credentials/couples plans exist; existing keys are preserved.
Expected first created:true, second already_present:true, owner reconciliation
balanced:true, five patient owners and four clinician owners. Ten new fictional
accounts and seven namespace-owned services are additive. The old review seed
is not rerun, and existing passwords/balances/schedules/decisions stay intact.
Protected credentials:
`/home/smcs/frappe-bench/sites/teletena.selfmadecs.com/private/tt-demo-mvp-v2-accounts.json`.
Full role mapping/scenario IDs: adjacent `tt-demo-mvp-v2-records.json`.

Read [dataset details and walkthrough](demo-dataset.md). If preparing a later
review after offers expire, use explicit `refresh` with a new generation label;
it creates request/offer records only, never fresh money or new approvals.

## 6. HTTPS/authentication/PWA and automatic jobs

```bash
env/bin/python apps/tele_tena/scripts/check_review_url.py https://teletena.selfmadecs.com
curl --fail --silent --show-error https://teletena.selfmadecs.com/assets/tele_tena/review/release.json \
  | env/bin/python -c 'import json,sys;print(json.load(sys.stdin)["source_commit"])'
bench --site "$SITE" doctor
```

Expected HTTPS built landing/sign-in/deep links, no-store app/API/SW headers,
correct manifest scope `/teletena/`, guest denial and exact artifact SHA. Use the
private seeded accounts through email → password; don't put passwords in curl
arguments. Check patient booking/privacy/reservation; clinician offers/accepted
notification and notes; reviewer private evidence; couples independent consent;
private patient/reviewer photos and explicit clinician publication. Sign out and
confirm the workspace is inaccessible. Source/asset success alone is insufficient.

If the site scheduler is disabled, decide explicitly to enable **this review
site's** required jobs; this is not a seed side effect or an enrollment change:

```bash
bench --site "$SITE" enable-scheduler
bench --site "$SITE" doctor
```

Confirm subscribed default queue first. Observe later `Scheduled Job Log` Complete
entries for request/couples expiry and earnings release using the read-only
inspector (release cron every5 minutes; expiry every minute). An existing Pending
earning is released only after its snapshotted window and without a dispute.
Do not claim automatic processing just because workers are RUNNING, manually
invoke a release and call it scheduler evidence, change the clock, clear shared
Redis queues or reset withholding. Investigate Error/stale metadata with safe
server logs. Other bench services/sites are not enabled by this site command.

An open browser receives the existing **Refresh to update** notice. Finish/leave
calls and save drafts before opting in; no automatic active-call reload. Check
an installed PWA and direct links after refresh. Offline never means a booking,
note or payment was saved. Cache only public assets. Do not publish Bench ports.
Hosted HTTPS/network/phone-device calls, SMS receipt and native-language review
are separate operator tests, not proof inherited from local fake devices.
LiveKit/SMS/SMTP helpers are unchanged and their private configuration is retained;
do not rerun configuration merely to update code or seed users.

## 7. Rollback

Stop the same confirmed web/worker/scheduler processes and keep maintenance on.
Before schema/data change, reverting the app/build may be sufficient only after
checking dependency/data compatibility. **After migration or seed writes**, a
reliable rollback normally restores the matching database + public/private files
+ site configuration + compatible app/dependency/assets snapshot. Old code alone
does not reverse schema, journal entries, scope decisions or users.

Choose the exact matching database/public/private archive paths from step2,
confirm privately, then run (passwords stay in terminal prompts):

```bash
git -C apps/tele_tena checkout --detach "$(cat "$UPDATE_BACKUP/tele_tena.sha")"
bench --site "$SITE" restore "$UPDATE_BACKUP/site-backups/database.sql.gz" \
  --with-public-files "$UPDATE_BACKUP/site-backups/public-files.tar" \
  --with-private-files "$UPDATE_BACKUP/site-backups/private-files.tar"
cp "$UPDATE_BACKUP/site_config.json" sites/teletena.selfmadecs.com/site_config.json
chmod 600 sites/teletena.selfmadecs.com/site_config.json
```

These exact archive paths are produced and verified by the helper. Do not use
the incomplete earlier bundle: its file archives were absent. Keep
shared common config unchanged unless an identified compatible dependency restore
requires coordinated bench-wide recovery. Restore/check pinned packages from the
private environment snapshot; don't blindly downgrade shared dependencies. Rebuild
that old source's assets or restore its complete matched asset bundle (don't leave
a mixture). Do not migrate restored data forward with the new code.

Inspect review-site queued jobs for code/data compatibility before restarting
workers; restored database/files don't restore Redis atomically. Do not purge the
shared queue. Restart only confirmed processes, restore the prior intended
maintenance/scheduler state from backup, and repeat HTTPS/auth/private-file smoke
checks. Keep both backups until the rollback/update is accepted.

## Verified update evidence

[Existing-install upgrade verification](existing-install-upgrade-verification.md)
covers actual installed baseline8f7ab9c, guarded pip installation, all original
operational rows/private credentials/config fields, repeat migration, LegacyHold,
and demonstration seeding twice. This differs from the older fresh-only evidence.
Shared-environment repair is separate; its44-app compatibility is not asserted
from the local three-app test environment.
