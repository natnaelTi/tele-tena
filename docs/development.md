# Local WSL setup

The only canonical development working copy is:
`/home/frappe/frappe/frappe-bench/apps/tele_tena`.
The original `/home/frappe/projects/tele-tena` is retained as an unchanged source
snapshot; do not develop there. Work on `feat/project-foundation` in the bench copy.

The isolated development site is `erp.localhost`. Observed installation versions:
Bench 5.31.0, Frappe 15.121.2, ERPNext 15.121.6, tele_tena 0.1.0.

Report non-secret environment details from the bench directory:

```sh
pwd
bench version
bench --site YOUR_SITE_NAME list-apps
python3 --version
node --version
```

Do not send site_config.json or passwords. Do not upgrade the working bench yet.
The foundation was installed using Bench's supported local-repository route:

```sh
bench get-app --branch feat/project-foundation tele_tena /home/frappe/projects/tele-tena
bench --site erp.localhost install-app tele_tena
```

Bench created a physical Git working copy, installed the editable Python package,
registered the app and built its assets. The clone's remote was restored to
`https://github.com/natnaelTi/tele-tena.git`; the source history and foundation
branch were retained. ERPNext was verified installed before installation.
Do not rerun get-app over the existing canonical directory.

From apps/tele_tena/frontend run npm ci then npm run dev. Its /api proxy targets
http://127.0.0.1:8000 by default. Set FRAPPE_DEV_URL locally if your bench uses another
address. For multiple sites ensure the development hostname selects the correct site.
The foundation screen tests an authenticated endpoint; it does not implement login yet.
An unauthenticated response is expected until the session integration is implemented.

LiveKit credentials belong on the backend only; SMS credentials likewise. No secrets
are needed for the current scaffold. Use provider secret storage or untracked local
configuration, never chat messages or committed files.
