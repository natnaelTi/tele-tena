# Selfmade review deployment — TeleTena

This packages the presentation release from **PR #7, `84bd97296e2030e679f621f7d8776921b65f0ec6`**.
PR #7 remains open; this deployment branch depends on it. Neither PR is authorized
for an automatic merge. No remote installation has been performed. Do not add the
separate earnings or redesign follow-up to this release.

## Isolation and compatibility gate

Use a **new dedicated review site and hostname**, containing only synthetic data.
Prefer a separate bench/container image if the existing Selfmade environment does
not match the tested stack, or cannot pin app dependencies without affecting other
sites. Python packages and frontend assets are bench/image-wide even when data and
configuration are site-specific. Do not upgrade a customer bench to accommodate this
review. Do not install TeleTena into a customer site.

Observed local baseline (not an assertion about Selfmade): Frappe **15.121.2**,
ERPNext **15.121.6**, Python **3.12.3**, Node **22.23.3**, MariaDB **10.11.14**,
Redis server **7.0.15**, Gunicorn **23.0.0**. TeleTena declares Python >=3.10,
but this release has only been verified on Python 3.12.3 and this Frappe 15 stack.
Node >=22.12 is required by the locked Vite 8 build; use the observed Node version.
ERPNext must be present on the image/bench **and installed on the review site**.
LiveKit Python API **1.2.1** and protocol **1.1.27** are pinned in package metadata;
install app dependencies through the image/bench build, not system Python.
React and all frontend dependencies come from `frontend/package-lock.json` with
`npm ci`, not a fresh unconstrained npm install. Exact observed package versions
and source IDs are in `deployment/tested-stack.json`; each build creates a separate
`public/review/release.json` with its source SHA, lock digest and artifact hashes.

Requirements: MariaDB/InnoDB, Redis cache and queue, Frappe web processes,
short/default/long workers as required by Frappe/ERPNext, a running scheduler, and
an HTTPS reverse proxy. The pending-confirmation expiry hook runs every scheduler
cycle (Frappe `all` event); a stopped scheduler delays expiry and must be treated
as an operational fault. Session cookies and CSRF remain Frappe-managed. LiveKit
Cloud must be reachable over HTTPS/WSS and its media network paths. Cloud cached-token
revocation is required; self-hosted LiveKit does not provide equivalent revocation.

## Read-only target preflight

Run `python3 scripts/remote_preflight.py --bench /absolute/bench/path` as an
unprivileged operator, or omit `--bench` for host inventory. It does not change
services, read secret configuration values, or install anything. Review its output
before sharing. For Docker first identify the compose/orchestrator project, custom
image source and persistent volumes. Do not assume a bench layout on the host.

The operator must additionally verify/report (no secret values):

- Dedicated proposed site name and DNS hostname; current Frappe/ERPNext versions
  and code SHAs; app list on the intended site; whether customer sites share this image.
- Bench/service manager versus Docker/compose; image build repository and deployment
  pipeline. Do not send `docker inspect` environment or compose files with secrets.
- TLS terminator/reverse proxy, certificate renewal, public 443, proxy host/site
  selection and trusted forwarded protocol; current asset routing and shared volumes.
- Web, socket.io, workers, scheduler and Redis/database health and topology;
  network access to LiveKit Cloud. Never publish ports 8000, 9000, 5173 or Redis/DB.
- Site database/private/public-file backups, encryption-key backup, image/code
  snapshot retention and a tested restore procedure. Confirm available disk capacity.

Only after this preflight can final host-specific installation commands be chosen.
For Docker, build a **new versioned custom image** including Frappe, ERPNext and
TeleTena at pinned SHAs, Python dependencies, and generated assets. Use the existing
supported site-creation/migration jobs and persistent asset/private-file volumes.
Deploy the same image to web, workers and scheduler. Do not `pip install`, `git pull`
or build assets ephemerally inside a running production container.

## Build artifact (normal user, no secrets)

In a compatible **isolated review bench or image build context**, obtain the reviewed
release SHA from the deployment PR and check it out on a fresh worktree/clone. Preserve
all source branches. Do not assume `main` includes PR #7.

```sh
# Run from the bench directory; Node must be the supported version.
python3 apps/tele_tena/scripts/build_review.py
bench build --app tele_tena
```

The first command requires a clean checkout so its recorded SHA identifies the actual
source. It uses `npm ci`, TypeScript and Vite, then copies artifacts into
`tele_tena/public/review`. Build output is deliberately not committed. `bench build`
links app public assets into `sites/assets/tele_tena`; the reverse proxy must serve
that assets tree. In an image pipeline copy both built app public files and the
resulting asset tree into the final image/volume as required by that deployment.
The build refuses frontend `.env*` files and strips inherited `VITE_*` variables.
No site credentials are read. Old hashed files are retained for open clients.
Keep license files for the packaged fonts. Do not expose source maps or secret files.

The public app URL is **`https://HOST/teletena/`**. Example deep link:
`https://HOST/teletena/patient/appointments`. React uses the `/teletena` basename;
APIs use same-origin `/api/method/...`. The Frappe page renderer owns only
`/teletena` and `/teletena/*`, and only on the explicitly enabled review site.
It returns a no-store shell for deep-link refresh. It never intercepts `/api`,
`/assets`, `/private`, `/app`, `/login` or the site's existing homepage.
Share `/teletena/`, not `/`. No Vite process is needed.

## Dedicated-site installation and private configuration

Before changes, back up the intended site's database, public/private files and
site encryption/configuration material to access-controlled storage. For an
existing review site, a compatible Bench deployment normally uses
`bench --site REVIEW_SITE backup --with-files`; confirm the backup actually exists
and test restore to a separate site. This command is a template, not authorization
to back up or alter a customer site.

On a confirmed compatible Bench layout, the intended order is:

1. Create the dedicated site with the deployment's supported `new-site` procedure.
   Enter DB-administration and Administrator passwords interactively; never pass
   passwords on the command line. Never change root authentication or existing sites.
2. Install ERPNext, then TeleTena: `bench --site REVIEW_SITE install-app erpnext`,
   then `bench --site REVIEW_SITE install-app tele_tena`. The apps and Python
   dependencies must already be installed in the bench/image at pinned SHAs.
3. Build assets as above; run `bench --site REVIEW_SITE migrate` (do not skip
   failing patches), then `bench --site REVIEW_SITE clear-cache`.
4. Run `bench --site REVIEW_SITE execute tele_tena.review.configure`. Type the
   exact dedicated site name and its HTTPS origin. This binds review mode to that
   site name and disables Frappe public signup. It refuses developer mode or a CSRF bypass; it does **not** enable either.
   TeleTena OTP request/verification is uniformly disabled on this invited review
   site, so neither an old challenge nor the legacy phone route creates accounts.
   The local development site retains its existing phone/email/password behavior.
5. Run `bench --site REVIEW_SITE execute tele_tena.review.seed` **explicitly**.
   It creates unique synthetic patient/clinician/reviewer accounts, separate service
   scope approval, published recurring availability, confirmed, cancelled and pending appointments, private synthetic PDF evidence,
   and reserved demonstration funds. A second successful run changes nothing. There is
   no public seed API or install/migration seed. No existing account is overwritten.
   Generated passwords are written only to the site-private mode-600
   `tele_tena_review_accounts.json`. Read it locally as the operator and transfer
   individual credentials securely; do not paste them into tickets/chat/reports.
   A failed partial seed retains credentials and fails closed for manual diagnosis;
   do not remove its marker or rerun against arbitrary existing data.
6. Optional LiveKit: `bench --site REVIEW_SITE execute tele_tena.development.configure_livekit`.
   Despite the historical module name, the helper accepts only `erp.localhost` or an
   explicitly bound review site, via local Administrator CLI. Key and secret use
   invisible prompts; files are private/mode600. Use a separate **development Cloud
   project**, not production. The browser receives only the public URL and a
   short-lived authorized participant token. No token logging.
7. Optional delivery helpers are `tele_tena.development.configure_email` and
   `tele_tena.development.configure_sms`, with the same site/CLI guard and invisible
   secret prompts. Live delivery remains unverified; OTP stays disabled for this
   review. Password review access does not depend on either provider.
8. Enable the site's scheduler using the deployment-supported command (Bench:
   `bench --site REVIEW_SITE enable-scheduler`), ensure workers are live, and restart
   only the identified review services to load new Python hooks. Configure DNS/TLS
   and the supported Frappe proxy template for this site. Do not generate or reload
   a shared server configuration before reviewing its impact on customer sites.

`deployment/review.env.example` contains placeholders only; it is documentation,
not a frontend environment file. Keep review flags in this site's config, never in
`common_site_config.json`. Copying configuration to a differently named site does
not enable funding or seed access. The single demo ribbon remains visible. Real
payments, withdrawals and clinical use are not activated.

## HTTPS and proxy requirements

Use the existing platform's supported Frappe proxy/image routing; map hostname to
the dedicated site, preserve Host and trusted HTTPS forwarding, and serve public
`/assets/` only from the asset tree. Do not use a global SPA `try_files` fallback.
Proxy `/teletena/*` including its service worker to Frappe. Do not map the site
private directory as static content. Private file/download routes stay under
Frappe authorization. Disable intermediary caching of authenticated/API responses;
do not cache HTML or the SW route. Confirm secure session cookies on the actual
HTTPS deployment. Do not suppress CSRF checks or set `ignore_csrf`.

The worker has scope `/teletena/`; it caches only this release's public assets.
API/private routes, session responses, notes and financial data remain network-only.
Offline navigation shows a generic “Nothing was saved” page. Updates wait for old
clients to close and do not reload calls. Remote HTTPS installation/device and media
network tests remain separate from the local loopback tests.

## Smoke checks and troubleshooting

After installation, run `python3 scripts/check_review_url.py https://HOST` for
read-only HTTPS/public-route checks. This does not authenticate or replace the
manual permissions, scheduler and device checks below.

- Load `/teletena/`, sign in via **Use email instead → Use password instead**.
  Open an appointment direct link and refresh. Sign out and confirm private APIs
  reject the same browser. Check logo/fonts/manifest and no requests to port 5173.
- Patient discovers the approved clinician, selects a generated time, previews
  sharing and books. Verify available/reserved funds, then clinician authorization.
  Confirm reviewer cannot read clinical notes or another account's private content.
- Review PDF download only as owner/reviewer. Confirm `/private/` never becomes
  a public directory. Check scheduler execution on this site and no effect elsewhere.
- Two separate devices over HTTPS: camera/microphone permission, real two-way
  audio/video, mute/camera/audio-only, Leave/rejoin, clinician End and rejection of
  cached original/refreshed tokens. Preserve the hosted automated regression; local
  fake-media evidence does not prove remote network/device behavior.
- On mobile test installation, manifest scope, offline state and update behavior.
  No promise of uninterrupted background calls. Do not use real patient information.

503 at app URL: build artifact missing. 404: check exact site-bound configuration,
installed app/hooks cache and hostname routing. Missing JS/fonts: inspect assets
symlink/volume and locked build output. Login/CSRF failure: check same-origin URL,
HTTPS forwarding/cookies; never disable security. Join unavailable: verify participants,
appointment state/time/window and privately configured Cloud credentials. Review
service logs without copying request bodies, passwords or participant tokens.

## Updates and rollback

Pin the next reviewed code SHA and build a new versioned image/artifact. Back up
**matching database + private/public files + configuration/encryption keys + current
code/image and dependency versions** before migration. Stop new review activity,
apply migration, load the new code/assets on all review processes, run smoke checks,
then reopen access. Never seed again to make old records look complete.

A schema-changing rollback requires restoring that compatible database and file
backup together with the previous code/image and dependencies. Checking out old
code alone is not rollback. Test restoration on a separate site first. Keep the
source branches, artifact hashes and previous compatible backup until the review
is accepted. No production deployment is part of this package.
