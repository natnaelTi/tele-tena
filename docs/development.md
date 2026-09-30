# Local WSL setup

First report non-secret environment details from the bench directory:

```sh
pwd
bench version
bench --site YOUR_SITE_NAME list-apps
python3 --version
node --version
```

Do not send site_config.json or passwords. Do not upgrade the working bench yet.
The app scaffold has not been installed/tested on a live bench in the remote workspace.
After version review, install this feature branch into the isolated bench:

```sh
bench get-app --branch feat/project-foundation https://github.com/natnaelTi/tele-tena.git
bench --site YOUR_SITE_NAME install-app tele_tena
```

These commands require the branch to have been pushed. ERPNext must already be installed.
From apps/tele_tena/frontend run npm ci then npm run dev. Its /api proxy targets
http://127.0.0.1:8000 by default. Set FRAPPE_DEV_URL locally if your bench uses another
address. For multiple sites ensure the development hostname selects the correct site.
The foundation screen tests an authenticated endpoint; it does not implement login yet.
An unauthenticated response is expected until the session integration is implemented.

LiveKit credentials belong on the backend only; SMS credentials likewise. No secrets
are needed for the current scaffold. Use provider secret storage or untracked local
configuration, never chat messages or committed files.
