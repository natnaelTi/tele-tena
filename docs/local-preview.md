# Local MVP review preview

The review site is `teletena-mvp-presentation.localhost` in
`/home/frappe/frappe/frappe-bench`, **not** the compatibility Bench. Its URL is
http://127.0.0.1:8017/teletena/. The web application uses packaged assets; Vite
is unnecessary. The original development Bench does not launch this web port.

After a Windows reboot, open the existing WSL distribution, start its existing
MariaDB and shared cache Redis arrangement (the original Bench may already do
this), then run as the normal frappe user:

```sh
cd /home/frappe/frappe/frappe-bench/apps/tele_tena
../../env/bin/python scripts/local_review.py start
../../env/bin/python scripts/local_review.py status
# To stop ONLY this preview:
../../env/bin/python scripts/local_review.py stop
```

No sudo startup change, migration, seed, password change or unrelated service
restart is performed. Dedicated web port 8017 and queue Redis13917 are loopback
only. The isolated native worker and scheduler see just the review site; the
shared scheduler keeps it disabled. The command validates PID ownership before
signalling processes and refuses an occupied port owned by another process.
Stop waits for graceful worker shutdown; if a job does not finish, investigate
rather than force killing it or removing its queued work.

`status` prints source and packaged-source identities separately. Evidence-only
commits can differ; runtime changes require a clean-checkout package build and
preview stop/start. Never let old workers continue through financial migrations:
back up the named site, run `scripts/local_review.py stop --keep-queue`
with Bench Python so queue Redis remains available but no old workers/web can
write, migrate **only** that site, build
from the pinned clean source, then start and run authenticated smoke checks.

An offline fallback after reboot may indicate a stopped server. Check status and
HTTP first. After service recovery use its **Try again** link. Application
updates use the existing explicit **Refresh to update** notice; active calls and
other protected workflows are not reloaded automatically. No private API data
is cached. Windows-to-WSL browser connectivity must be checked on the host; a
Linux HTTP check alone is not evidence for it.

Credentials stay in the mode-600 private site file
`/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private/tele_tena_presentation_accounts.json`.
The normal preview uses invited review: Use email instead → Use password
instead. Enabled-registration tests use a separate site and controlled transport.
