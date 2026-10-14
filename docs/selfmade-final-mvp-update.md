# Selfmade — pinned final MVP review update

This prepares an operator update; **no remote deployment was performed**.
The current remote SHA/runtime/service state must be observed in step1, not
assumed from earlier reports. The previously reported host is managed Bench
`/home/smcs/frappe-bench`, site `teletena.selfmadecs.com`, Frappe16.2.1,
ERPNext16.1.0, Python3.14.2, Node24.13.0, MariaDB10.6.22, Redis6.0.16,
nginx1.18, Supervisor. The domain reportedly has no Cloudflare proxy.
Current version differences are a stop for investigation, not permission to
upgrade/downgrade shared frameworks, Node/Python or `bench update`.

Release pin: **RELEASE_PIN_PENDING_FINAL_CHECKS** on `feat/mvp-release-handover`.
PR44 remains draft, depending on PR43 (`feat/adult-relationship-links`); this
branch contains its ancestry. Installing a pinned unmerged commit does not merge
any PR. Owner acceptance is still separate from automated verification.
Use this guide from the reviewed PR/doc checkout before detaching the app.

## 1. Inspect, preserve and stop conditions

Run as `smcs` with the existing Bench executable, not root. Do not paste output
containing credentials/configuration into chat. Execute blocks separately and
stop on any failed command or unexpected result.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
RELEASE_SHA='RELEASE_PIN_PENDING_FINAL_CHECKS'
SITE='teletena.selfmadecs.com'
CURRENT_SHA=$(git -C apps/tele_tena rev-parse HEAD)
printf 'Installed TeleTena commit: %s\n' "$CURRENT_SHA"
test -z "$(git -C apps/tele_tena status --porcelain)"
test -z "$(git -C apps/frappe status --porcelain)"
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

Fetch the release without switching yet, then extract the read-only inspector
outside the app so the old checkout can remain intact:

```bash
git -C apps/tele_tena fetch origin feat/mvp-release-handover
git -C apps/tele_tena cat-file -e "$RELEASE_SHA^{commit}"
PREFLIGHT=$(mktemp /home/smcs/teletena-preflight.XXXXXXXX.py)
git -C apps/tele_tena show "$RELEASE_SHA:scripts/release_preflight.py" > "$PREFLIGHT"
env/bin/python "$PREFLIGHT" --bench /home/smcs/frappe-bench --site "$SITE"
```

Expected: TeleTena/Frappe/ERPNext installed, review bound to exactly this site,
no developer mode/CSRF bypass/SQL body logging, no dirty checkouts, healthy
queues. Version assertions for the **previously verified target**:

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
env/bin/python -m pip list --format=json > "$UPDATE_BACKUP/packages.json"
cp -a apps/tele_tena/tele_tena/public/review "$UPDATE_BACKUP/review-assets"
bench --site "$SITE" set-maintenance-mode on
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl stop frappe-bench-workers:frappe-bench-frappe-long-worker-0 frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl stop frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl status
bench --site "$SITE" backup --with-files
cp -a sites/teletena.selfmadecs.com/private/backups "$UPDATE_BACKUP/site-backups"
find "$UPDATE_BACKUP/site-backups" -maxdepth 1 -type f -printf '%f\n'
find "$UPDATE_BACKUP/site-backups" -maxdepth 1 -type f -exec sha256sum {} \; > "$UPDATE_BACKUP/backup.sha256"
printf 'Private backup bundle: %s\n' "$UPDATE_BACKUP"
```

Expected: named services STOPPED, newest database/public/private archives present
and nonempty. Verify checksums, readable archives and a matching site config/key;
copy the bundle to approved protected backup storage and confirm a restore path
before proceeding. Never publish backup/config/private files through nginx.
The saved config is from **before** maintenance mode. Socket.IO can remain running;
its code/dependencies are unchanged, but notifications pause with the web/worker.
This cutover prevents old web/workers from writing legacy financial events after
new financial schema activation. Do not migrate while any old writer remains.

## 3. Pinned source, additive dependencies and production assets

```bash
git -C apps/tele_tena checkout --detach "$RELEASE_SHA"
test "$(git -C apps/tele_tena rev-parse HEAD)" = "$RELEASE_SHA"
test -z "$(git -C apps/tele_tena status --porcelain)"
env/bin/python apps/tele_tena/scripts/dependency_checkpoint.py snapshot "$UPDATE_BACKUP/dependencies"
env/bin/python -m pip install --dry-run --constraint "$UPDATE_BACKUP/dependencies/constraints.txt" \
  --report "$UPDATE_BACKUP/dependency-plan.json" -e apps/tele_tena > "$UPDATE_BACKUP/dependency-plan.log" 2>&1
env/bin/python apps/tele_tena/scripts/dependency_checkpoint.py plan "$UPDATE_BACKUP/dependencies" --report "$UPDATE_BACKUP/dependency-plan.json"
env/bin/python -m pip install --constraint "$UPDATE_BACKUP/dependencies/constraints.txt" -e apps/tele_tena > "$UPDATE_BACKUP/dependency-install.log" 2>&1
env/bin/python apps/tele_tena/scripts/dependency_checkpoint.py verify "$UPDATE_BACKUP/dependencies"
env/bin/python -m pip check
env/bin/python apps/tele_tena/scripts/build_review.py
bench build --app tele_tena
env/bin/python apps/tele_tena/scripts/check_review_assets.py --site-private sites/teletena.selfmadecs.com/private
```

The guard must pass without replacing existing package versions. Stop on a
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
bench --site "$SITE" restore /ABSOLUTE/PATH/TO/MATCHING-database.sql.gz \
  --with-public-files /ABSOLUTE/PATH/TO/MATCHING-files.tar \
  --with-private-files /ABSOLUTE/PATH/TO/MATCHING-private-files.tar
cp "$UPDATE_BACKUP/site_config.json" sites/teletena.selfmadecs.com/site_config.json
chmod 600 sites/teletena.selfmadecs.com/site_config.json
```

Archive suffixes may differ; use observed filenames, not the placeholders. Keep
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
