"""Fresh v1.44 on the isolated, operator-owned compatibility DB socket only."""
import os,secrets,sys,subprocess,json
from pathlib import Path
from unittest.mock import patch
BENCH=Path('/home/frappe/teletena-compat/bench');ROOT=Path(__file__).resolve().parents[1]
SITE='teletena-onboarding-v144-fresh.localhost';DB='tt_onboarding_v144_fresh';SOCKET=BENCH.parent/'runtime/mariadb-target.sock'
assert SOCKET.is_socket() and not (BENCH/'sites'/SITE).exists()
os.chdir(BENCH/'sites');sys.path.insert(0,str(ROOT))
import frappe,pymysql
admin=pymysql.connect(unix_socket=str(SOCKET),user='root',autocommit=True);assert not admin.cursor().execute('SHOW DATABASES LIKE %s',(DB,));admin.close()
from frappe.commands.site import new_site
with patch('getpass.getpass',return_value=''):
 new_site.callback(db_name=DB,site=SITE,db_root_username='root',db_root_password='',admin_password=secrets.token_hex(32),db_password=secrets.token_hex(32),db_type='mariadb',db_socket=str(SOCKET),mariadb_user_host_login_scope='localhost',install_app=['erpnext','tele_tena'])
frappe.destroy();env={**os.environ,'PYTHONPATH':str(ROOT)}
for i in range(2):subprocess.run([sys.executable,'-m','frappe.utils.bench_helper','frappe','--site',SITE,'migrate'],cwd=BENCH/'sites',env=env,check=True,stdout=subprocess.DEVNULL)
frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect()
for table in ('tt_professional_draft','tt_professional_submission','tt_professional_evidence','tt_identity_reviewer'):assert frappe.db.sql('SELECT COUNT(*) FROM '+table)[0][0]==0
counts=frappe.db.sql('SELECT kind,COUNT(*) FROM tt_reference GROUP BY kind');assert dict(counts)['issuer']>8000
assert frappe.db.has_column('Tele Tena Vetting Scope Application','professional_submission')
for field in ('qualification','issuing_institution','issuing_authority'):
 width=frappe.db.sql('SELECT CHARACTER_MAXIMUM_LENGTH FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s',('tabTele Tena Vetting Scope Application',field))[0][0]
 assert width>=240
from tele_tena.api.contact_auth import sign_in_options
from unittest.mock import patch as mock
frappe.set_user('Guest');options=sign_in_options();assert not options['patient_registration'] and not options['clinician_registration']
frappe.destroy();print('PASS fresh Frappe16 installation and two native migrations; structured/evidence tables empty; full bundled directory imported; access/provider switches remain off. Counts:',dict(counts))
