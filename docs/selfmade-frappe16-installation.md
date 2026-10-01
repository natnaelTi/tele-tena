# Selfmade: pinned Frappe 16 review installation

This is an operator runbook, **not a record of remote execution**. PR #8 at
`ba674b79bfa493a05689b1cee96d7a0d663766ec` includes PR #7's product. Both remain
unmerged. The compatibility branch includes that exact release, with no earnings
or redesign changes. See [compatibility evidence](frappe16-compatibility-verification.md).
The final installation SHA is recorded there; use that SHA, not `main` or a moving
branch. The generic [review guide](selfmade-review-deployment.md) remains applicable.

## Confirmed target and stop conditions

Bench `/home/smcs/frappe-bench`, site `teletena.selfmadecs.com`; Frappe 16.2.1
`8f6e24728b86b7c6427908ed6536289a41ea9cf4`, ERPNext 16.1.0
`bb2bada1fde0ae7a3c3cad32bed781ebd470e27d`, Python 3.14.2, Node 24.13.0.
MariaDB 10.6.22 Ubuntu22.04 build, Redis 6.0.16, nginx 1.18.0, Supervisor.
The hostname is not behind Cloudflare. TLS certificate/vhost contents and actual
worker queue subscriptions have not been supplied or remotely tested.

The site already exists with Frappe and ERPNext. Do **not** create it again or
install ERPNext again. Do not run `bench update`, change framework checkouts,
change system Python/Node, migrate all sites, or regenerate shared nginx/Supervisor
configuration. Do not run `get-app` with automatic dependency setup. Abort on a
version mismatch, dirty framework checkout, existing TeleTena app, dependency
replacement, failed backup or failed checks. Use the separate-bench alternative.

Python dependencies, apps registry, assets and web/worker processes are **shared**.
Agree a shared-bench maintenance window with its owner before installation or
restarts. Site-only configuration does not isolate process/dependency changes.

## 1. Read-only baseline and backup

Run as `smcs`, not root, from a normal shell with the deployment's existing Bench
command available. Stop on failure; execute sections individually and inspect
results. `INSTALL_SHA` below must be set to the full reviewed installation commit
from the verification report; this explicit gate prevents installing a branch tip.

```bash
set -euo pipefail
umask 077
cd /home/smcs/frappe-bench
INSTALL_SHA='REPLACE_WITH_FULL_REVIEWED_INSTALLATION_SHA'
[[ "$INSTALL_SHA" =~ ^[0-9a-f]{40}$ ]]
test "$(env/bin/python -c 'import platform; print(platform.python_version())')" = 3.14.2
test "$(node --version)" = v24.13.0
test "$(git -C apps/frappe rev-parse HEAD)" = 8f6e24728b86b7c6427908ed6536289a41ea9cf4
test "$(git -C apps/erpnext rev-parse HEAD)" = bb2bada1fde0ae7a3c3cad32bed781ebd470e27d
test -z "$(git -C apps/frappe status --porcelain)"
test -z "$(git -C apps/erpnext status --porcelain)"
test ! -e apps/tele_tena
bench --site teletena.selfmadecs.com list-apps
env/bin/python -m pip check
sudo supervisorctl status
bench --site teletena.selfmadecs.com doctor
REVIEW_BACKUP=$(mktemp -d /home/smcs/teletena-before-install.XXXXXXXX)
chmod 700 "$REVIEW_BACKUP"
cp sites/apps.txt "$REVIEW_BACKUP/apps.txt"
cp sites/teletena.selfmadecs.com/site_config.json "$REVIEW_BACKUP/site_config.json"
env/bin/python -m pip list --format=json > "$REVIEW_BACKUP/packages.json"
git -C apps/frappe rev-parse HEAD > "$REVIEW_BACKUP/frappe.sha"
git -C apps/erpnext rev-parse HEAD > "$REVIEW_BACKUP/erpnext.sha"
# Back up this site only; encryption key/config above is essential to restoration.
bench --site teletena.selfmadecs.com backup --with-files
cp -a sites/teletena.selfmadecs.com/private/backups "$REVIEW_BACKUP/site-backups"
cp -a sites/assets/assets*.json "$REVIEW_BACKUP/"
```

Verify new database/public/private archives exist, are readable, and have a
restorable matching config. Copy the bundle to approved access-controlled backup
storage. Confirm a tested restore procedure before proceeding. Shared-bench
rollback additionally requires the operator's compatible environment/assets
snapshot; the copies above alone are not an atomic shared-bench backup. Do not
publish backup paths through nginx. Do not paste config or passwords into chat.

## 2. Pinned source and additive-only dependency gate

```bash
git clone --no-checkout https://github.com/natnaelTi/tele-tena.git apps/tele_tena
git -C apps/tele_tena fetch origin "$INSTALL_SHA"
git -C apps/tele_tena checkout --detach "$INSTALL_SHA"
test "$(git -C apps/tele_tena rev-parse HEAD)" = "$INSTALL_SHA"
env/bin/python apps/tele_tena/scripts/dependency_checkpoint.py snapshot "$REVIEW_BACKUP/dependencies"
env/bin/python -m pip install --dry-run \
  --constraint "$REVIEW_BACKUP/dependencies/constraints.txt" \
  --report "$REVIEW_BACKUP/dependency-plan.json" -e apps/tele_tena \
  > "$REVIEW_BACKUP/dependency-plan.log" 2>&1
env/bin/python apps/tele_tena/scripts/dependency_checkpoint.py plan \
  "$REVIEW_BACKUP/dependencies" --report "$REVIEW_BACKUP/dependency-plan.json"
# Proceed only if the guard passes; constraints preserve every existing version.
env/bin/python -m pip install \
  --constraint "$REVIEW_BACKUP/dependencies/constraints.txt" -e apps/tele_tena \
  > "$REVIEW_BACKUP/dependency-install.log" 2>&1
env/bin/python apps/tele_tena/scripts/dependency_checkpoint.py verify "$REVIEW_BACKUP/dependencies"
env/bin/python -m pip check
```

Inspect additions in the private plan. A constraints failure is a **stop**, not
permission to relax constraints. The isolated test used a separate Bench CLI env:
Bench 5.31.0's requests requirement conflicts with this Frappe commit's pinned
requests requirement when installed in the same env. Leave remote Bench CLI alone.
Do not install Bench itself into the app env to reproduce the CLI version.

## 3. Locked frontend, app registration and site-only migration

```bash
env/bin/python apps/tele_tena/scripts/build_review.py
env/bin/python apps/tele_tena/scripts/check_review_assets.py
# Register the already installed app, preserving every other entry.
env/bin/python - <<'PY'
from pathlib import Path
path = Path('sites/apps.txt')
entries = path.read_text().splitlines()
assert 'frappe' in entries and 'erpnext' in entries
assert 'tele_tena' not in entries
with path.open('a') as stream:
    stream.write(('' if path.read_bytes().endswith(b'\n') else '\n') + 'tele_tena\n')
PY
bench build --app tele_tena --production
bench --site teletena.selfmadecs.com install-app tele_tena
bench --site teletena.selfmadecs.com migrate
bench --site teletena.selfmadecs.com clear-cache
```

`build_review.py` uses `npm ci` and the committed lock, excludes frontend secrets,
records the source SHA and retains old hashed assets for open clients. `bench build`
changes shared asset links/metadata even with `--app tele_tena`; inspect output and
never expand this to all apps on the remote bench. No Vite server is needed.

## 4. Site-bound review access and private provider setup

```bash
bench --site teletena.selfmadecs.com execute tele_tena.review.configure
# At its prompts enter exactly:
# teletena.selfmadecs.com
# https://teletena.selfmadecs.com
bench --site teletena.selfmadecs.com execute tele_tena.review.seed
bench --site teletena.selfmadecs.com execute tele_tena.development.configure_livekit
```

Use a development LiveKit **Cloud** project. The helper prompts invisibly for keys,
stores them privately and never changes other sites. Do not copy credentials into
shell arguments or frontend variables. The seed runs only explicitly, is idempotent,
and writes unique passwords to a mode-600 site-private account file. Access it only
locally and send each doctor's assigned account through a secure private channel.
Do not use Administrator or share one account for both call participants.

Review login is **Use email instead → Use password instead**. Public landing is
available; public enrollment/OTP is disabled on the bound review site. SMS/SMTP
live delivery is unverified and unnecessary for password review. Do not turn on
developer mode, a fixed OTP, CSRF bypass, real payments, withdrawals or clinical use.

## 5. Queue gate, scheduler and scoped Supervisor restarts

The two running worker names do not establish which queues they consume. Before
opening review booking, confirm the existing workers include **default**, short
and long as needed. Use `bench --site teletena.selfmadecs.com console` and this
read-only snippet; do not dump job kwargs, which can contain private information:

```python
from frappe.utils.background_jobs import get_queue
from frappe.utils.doctor import get_workers
for worker in get_workers():
    print(worker.name, worker.queue_names(), worker.last_heartbeat)
for name in ('short', 'default', 'long'):
    queue = get_queue(name)
    print(name, queue.count, queue.started_job_registry.count, queue.failed_job_registry.count)
exit()
```

Take another snapshot after a scheduler cycle and examine job age/worker heartbeats
locally. The observed 22 queued jobs alone do not show they are stuck. Do not purge
or retry existing jobs as part of this install. If default has no active consumer
or a growing unexplained backlog, stop and have the managed-services operator
resolve it; do not silently edit shared worker config. The isolated test executed
TeleTena's site-bound expiry job through RQ 2.6.1 against Redis 6.0.16.

In the agreed maintenance window, these are the **observed exact Supervisor names**:

```bash
bench --site teletena.selfmadecs.com enable-scheduler
sudo supervisorctl restart frappe-bench-web:frappe-bench-frappe-web
sudo supervisorctl restart frappe-bench-workers:frappe-bench-frappe-long-worker-0
sudo supervisorctl restart frappe-bench-workers:frappe-bench-frappe-short-worker-0
sudo supervisorctl restart frappe-bench-workers:frappe-bench-frappe-schedule
sudo supervisorctl status
bench --site teletena.selfmadecs.com doctor
```

These four restarts reload code for **all sites on this bench** and briefly interrupt
web traffic/job processing. Drain/coordinate long-running work first. They do not
restart MariaDB, Redis, socket.io or nginx. Do not use `supervisorctl restart all`
or imply a site-only process restart. Confirm the review site's expiry Scheduled
Job Type is present and its subsequent scheduler runs succeed before showing
manual-confirmation booking. Do not submit synthetic jobs on customer sites.

## 6. Existing HTTPS vhost and smoke checks

No nginx regeneration/reload is prescribed: the existing site's vhost/certificate
has not been inspected. The operator must confirm `teletena.selfmadecs.com` resolves
to this service, a valid matching certificate is served, Host/HTTPS forwarding is
correct, `/assets` serves the shared public asset tree, and `/teletena/*` reaches
Frappe. No global SPA fallback or private-directory alias; no intermediary cache
of authenticated/API/private responses. Only public 443 is needed for the website.
Never expose Bench 8000/9000/5173, database or Redis ports.

```bash
cd /home/smcs/frappe-bench
env/bin/python apps/tele_tena/scripts/check_review_url.py https://teletena.selfmadecs.com
env/bin/python apps/tele_tena/scripts/check_review_assets.py \
  --site-private sites/teletena.selfmadecs.com/private
```

Share **https://teletena.selfmadecs.com/teletena/** only after these pass plus:

- Password sign-in/out, authenticated direct-link refresh, secure session cookies,
  guest rejection and genuine CSRF protection over HTTPS.
- Patient generated-slot booking/reservation, clinician notes with private text
  absent from patient API, and resume download restricted to owner/reviewer.
- Two devices: media permission/exchange, Leave/rejoin, End. Remote network/device
  behavior is separate from the local fake-media Cloud tests. Preserve the Cloud
  original/refreshed-token rejection regression; do not run local destructive
  synthetic harnesses against the remote shared bench.
- Mobile PWA install/offline checks; only public assets cached. Offline writes
  must not appear saved. No uninterrupted mobile background-call claim.

## Update, rollback and separate-bench alternative

For each update, pin a reviewed SHA, back up compatible database/files/config and
shared environment/assets, repeat dependency-plan review, rebuild and migrate only
this site. Never reseed or rewrite existing records for presentation.

After a schema-changing migration, rollback restores **matching code + dependencies
+ database + public/private files + site config/encryption key**. Restore first to
an isolated recovery site and verify it. Do not restore a customer database or
reset shared dependencies from one site's backup. A failed dependency gate before
installation requires no migration rollback; preserve the report for diagnosis.

If the shared bench cannot accept additive dependencies or coordinated restarts,
provision a separate managed Bench/container with the exact tested Frappe/ERPNext
commits and Python/Node versions, separate database/site, Redis ports, workers and
scheduler. Use a separate service account and versioned image/venv, not shared
package upgrades. Install and smoke-test there first; have the operator explicitly
approve DNS/vhost changes later. Do not move this hostname or modify its existing
site automatically. No remote installation or physical-device test is claimed.
