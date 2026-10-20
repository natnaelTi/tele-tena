"""Explicit disposable Frappe16 guest-first install. No seed or retained-site writes.
Uses an operator-owned local test DB socket,never a production/root TCP endpoint.
"""
import os,secrets,sys,subprocess
from pathlib import Path
BENCH=Path(os.environ['TELE_TENA_TEST_BENCH']).resolve()
SITE='teletena-guest-first-fresh.localhost';DB='tt_guest_first_fresh'
SOCKET=Path('/home/frappe/teletena-compat/runtime/mariadb-target.sock')
assert BENCH==Path('/home/frappe/teletena-compat/bench') and SOCKET.is_socket()
assert not (BENCH/'sites'/SITE).exists()
os.chdir(BENCH/'sites');sys.path.insert(0,str(BENCH/'apps/tele_tena'))
import frappe,pymysql
admin=pymysql.connect(unix_socket=str(SOCKET),user='root',autocommit=True)
assert not admin.cursor().execute('SHOW DATABASES LIKE %s',(DB,))
from frappe.commands.site import new_site
from unittest.mock import patch
# Empty-password unix-socket root exists only in this task-owned disposable DB.
# Prevent an interactive prompt; production configuration is never read here.
with patch('getpass.getpass',return_value=''):
 new_site.callback(db_name=DB,site=SITE,db_root_username='root',db_root_password='',admin_password=secrets.token_hex(32),db_password=secrets.token_hex(32),db_type='mariadb',db_socket=str(SOCKET),mariadb_user_host_login_scope='localhost',install_app=['erpnext','tele_tena'])
frappe.destroy()
for i in range(2):
 subprocess.run([sys.executable,'-m','frappe.utils.bench_helper','frappe','--site',SITE,'migrate'],cwd=BENCH/'sites',check=True,stdout=subprocess.DEVNULL)
frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect()
assert set(('frappe','erpnext','tele_tena'))<=set(frappe.get_installed_apps())
for table in ('tt_policy_acceptance','tt_history_grant','tt_history_grant_event','tt_notice_preference','tt_booking_notice'):
 assert frappe.db.sql('SELECT COUNT(*) FROM '+table)[0][0]==0
from tele_tena.api import directory,contact_auth
from tele_tena.review import enabled
frappe.set_user('Guest');assert directory.offerings()['items']==[]
options=contact_auth.sign_in_options();assert not options['phone_otp'] and not options['patient_registration'] and not options['clinician_registration']
assert not enabled();frappe.destroy()
print('PASS Frappe16 fresh install, two native repeat migrations, empty new consent/grant/outbox tables, guest directory empty, access switches disabled; no seed.')
