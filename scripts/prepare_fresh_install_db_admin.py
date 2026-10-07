"""Create a short-lived local DB admin for the PR12 fresh-install fixture.

Run as the normal Frappe user from an interactive WSL terminal. Sudo prompts
for local socket administration; credentials are never printed or passed in
argv. The fresh-install harness removes the account and credential file.
"""
import json
import os
from pathlib import Path
import secrets
import subprocess

# This dedicated test database/site must never alias the retained review site.
USER = os.environ.get('TELE_TENA_DB_ADMIN_USER', 'tt_clinic_access_admin')
DATABASE = os.environ.get('TELE_TENA_FRESH_DB', 'teletenaclinicaccessfresh')
SITE = os.environ.get('TELE_TENA_FRESH_SITE', 'tele-tena-clinic-access-fresh.localhost')
CREDENTIALS = Path(os.environ.get('TELE_TENA_DB_CREDENTIALS', '/tmp/tele-tena-clinic-access-db-admin.json'))
if not SITE.endswith('.localhost') or SITE == os.environ.get('TELE_TENA_RETAINED_SITE', 'erp.localhost'):
    raise SystemExit('Disposable fresh-site name must be a distinct localhost site')
if not DATABASE.replace('_', '').isalnum():
    raise SystemExit('Disposable database name is invalid')

if os.geteuid() == 0:
    raise SystemExit('Run as the normal Linux user, not root')
if CREDENTIALS.exists() or CREDENTIALS.is_symlink():
    raise SystemExit('Credential file already exists; refusing to overwrite it')

password = secrets.token_urlsafe(40)
sql = f"""CREATE USER '{USER}'@'localhost' IDENTIFIED BY '{password}';
GRANT CREATE USER, RELOAD ON *.* TO '{USER}'@'localhost';
GRANT ALL PRIVILEGES ON `{DATABASE}`.* TO '{USER}'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
"""
result = subprocess.run(['sudo', 'mariadb', '--protocol=socket'], input=sql,
                        text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
if result.returncode:
    raise SystemExit('Temporary database administrator setup failed; no credentials were stored')

try:
    fd = os.open(CREDENTIALS, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump({'db_root_username': USER, 'db_root_password': password,
                   'db_name': DATABASE}, stream)
except Exception:
    subprocess.run(['sudo', 'mariadb', '--protocol=socket'],
                   input=f"DROP USER IF EXISTS '{USER}'@'localhost';\nFLUSH PRIVILEGES;\n",
                   text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    raise

print('Created temporary localhost database access for the disposable fresh-install site. Run scripts/check_fresh_install.py with the same site/database environment; it removes the account and mode-600 credential file.')
