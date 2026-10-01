# Local WSL setup

The only canonical development working copy is:
`/home/frappe/frappe/frappe-bench/apps/tele_tena`.
The original `/home/frappe/projects/tele-tena` is retained as an unchanged source
snapshot; do not develop there. `main` contains the reviewed foundation and
milestone 1 merges. PR #3 remains open and unmerged on
`feat/milestone-2-consultations`; phone access is developed separately from
`main` on `feat/phone-otp`.

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
Vite sends `X-Frappe-Site-Name: erp.localhost`; override with `FRAPPE_DEV_SITE`
for a different isolated site. The React journey signs in through Frappe password
authentication and obtains its session CSRF token for POST commands.
See [milestone review](milestone-1-verification.md) for isolated synthetic accounts.

LiveKit credentials belong on the backend only; SMS credentials likewise. No secrets
are needed for the current scaffold. Use provider secret storage or untracked local
configuration, never chat messages or committed files.

For the LiveKit consultation demo, configure credentials interactively in a Bench
terminal as the normal Linux user (the API secret prompt is hidden):

```sh
cd /home/frappe/frappe/frappe-bench
bench --site erp.localhost execute tele_tena.development.configure_livekit
```

Enter the LiveKit **public WebSocket connection URL** (`wss://...` for a hosted
project), API key and API secret when prompted. The command writes only to
`sites/erp.localhost/private/tele_tena_livekit.json` with directory mode 700 and
file mode 600; it prints only a safe configured/path/mode result. It refuses
non-loopback `ws://` URLs, does not change site config, and is restricted to
`erp.localhost`. Do not copy values into React, Vite variables, shell arguments,
logs or Git. The browser receives only the public URL and a short-lived,
appointment-scoped participant token. To replace credentials, rerun the command.
To disable credentials locally, remove that one private file as the normal user.

For local development only, `ws://localhost` or `ws://127.0.0.1` is accepted.
Remote phone browsers need HTTPS for camera/microphone permission. If needed,
put only the Vite application behind a temporary authenticated HTTPS tunnel and
keep the Bench/Frappe admin interface bound to loopback; never tunnel port 8000.
Review the tunnel provider's privacy settings before use and use synthetic
accounts only.

For a local SMS Ethiopia credential, run
`bench --site erp.localhost execute tele_tena.development.configure_sms` in an
interactive terminal. It prompts invisibly, writes a mode-600 backend-only file,
prints no secret and sends no message. Live testing still requires a consenting
recipient whitelisted with the provider; automated tests mock the adapter.

Fresh-install bootstrap is `tele_tena.schema.install` in after_install. Upgrades
use numbered Frappe post-model-sync patches recorded in Patch Log; native service
and scope models use standard model sync. There is no recurring after_migrate DDL. Run normal `bench --site erp.localhost migrate` after checkout,
then `bench --site erp.localhost clear-cache`. The development CLI fixture command
`bench --site erp.localhost execute tele_tena.development.setup` creates isolated
accounts and rotates their passwords into a mode-600 file in /tmp; it does not
reset profiles, appointments or simulation transaction-log entries. No web authentication bypass exists.
