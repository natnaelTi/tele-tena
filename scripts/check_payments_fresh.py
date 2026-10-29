"""Fresh v1.47, isolated compatibility socket only; no existing site changes."""
assert __name__=='__main__', 'This fixture may run only as an explicit local CLI, never by import'

import os,secrets,sys,subprocess,json
from pathlib import Path
from unittest.mock import patch
BENCH=Path('/home/frappe/teletena-compat/bench');ROOT=Path(__file__).resolve().parents[1]
SITE=os.environ.get('TELE_TENA_FRESH_SITE','teletena-payments-v147-fresh.localhost')
assert SITE in ('teletena-payments-v147-fresh.localhost','teletena-payments-v147-final.localhost','teletena-payments-v147-candidate.localhost','teletena-payments-v148-fresh.localhost','teletena-photos-v149-fresh.localhost')
DB='tt_photos_v149_fresh' if SITE=='teletena-photos-v149-fresh.localhost' else 'tt_payments_v148_fresh' if SITE=='teletena-payments-v148-fresh.localhost' else 'tt_payments_v147_candidate' if SITE.endswith('-candidate.localhost') else 'tt_payments_v147_final' if SITE.endswith('-final.localhost') else 'tt_payments_v147_fresh';SOCKET=BENCH.parent/'runtime/mariadb-target.sock'
assert SOCKET.is_socket() and not (BENCH/'sites'/SITE).exists()
os.chdir(BENCH/'sites');sys.path.insert(0,str(ROOT))
import frappe,pymysql
admin=pymysql.connect(unix_socket=str(SOCKET),user='root',autocommit=True);assert not admin.cursor().execute('SHOW DATABASES LIKE %s',(DB,));admin.close()
from frappe.commands.site import new_site
with patch('getpass.getpass',return_value=''):
 new_site.callback(db_name=DB,site=SITE,db_root_username='root',db_root_password='',admin_password=secrets.token_hex(32),db_password=secrets.token_hex(32),db_type='mariadb',db_socket=str(SOCKET),mariadb_user_host_login_scope='localhost',install_app=['erpnext','tele_tena'])
frappe.destroy();env={**os.environ,'PYTHONPATH':str(ROOT)}
for i in range(2):subprocess.run([sys.executable,'-c',"import sys,runpy;sys.path.insert(0,sys.argv.pop(1));import tele_tena;sys.argv=['bench','frappe','--site',sys.argv[1],'migrate'];runpy.run_module('frappe.utils.bench_helper',run_name='__main__')",str(ROOT),SITE],cwd=BENCH/'sites',env=env,check=True,stdout=subprocess.DEVNULL)
frappe.init(site=SITE,sites_path=str(BENCH/'sites'));frappe.connect()
for table in ('tt_professional_draft','tt_professional_submission','tt_professional_evidence','tt_identity_reviewer','tt_direct_payment','tt_direct_payment_event','tt_direct_receipt','tt_care_language_claim'):assert frappe.db.sql('SELECT COUNT(*) FROM '+table)[0][0]==0
counts=frappe.db.sql('SELECT kind,COUNT(*) FROM tt_reference GROUP BY kind');assert dict(counts)['issuer']>8000
assert frappe.db.has_column('Tele Tena Vetting Scope Application','professional_submission')
assert frappe.db.sql("SHOW COLUMNS FROM tt_professional_draft LIKE 'legacy_name'")
assert frappe.db.sql("SHOW COLUMNS FROM tt_professional_submission LIKE 'reference_snapshot'")
for field in ('qualification','issuing_institution','issuing_authority'):
 width=frappe.db.sql('SELECT CHARACTER_MAXIMUM_LENGTH FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s',('tabTele Tena Vetting Scope Application',field))[0][0]
 assert width>=240
from tele_tena.api.contact_auth import sign_in_options
from unittest.mock import patch as mock
frappe.set_user('Guest');options=sign_in_options();assert not options['patient_registration'] and not options['clinician_registration']
assert frappe.db.sql('SELECT mode FROM tt_payment_config WHERE id=1')[0][0]=='Wallet'
assert frappe.db.sql('SELECT COUNT(*) FROM tt_care_language')[0][0]==630
assert dict(counts)['domain']==78
assert frappe.db.sql("SHOW COLUMNS FROM tt_couple_plan LIKE 'care_language'")
frappe.set_user('Administrator');frappe.clear_cache();u=frappe.get_doc({'doctype':'User','email':'fresh-reviewer@offline-test.invalid','first_name':'Fictional Fresh Reviewer','send_welcome_email':0,'user_type':'Website User'}).insert();u.add_roles('Tele Tena Approver');assert 'Tele Tena Financial Configuration' in [r.role for r in u.roles];frappe.db.rollback()
assert frappe.db.sql("SHOW TABLES LIKE 'tt_patient_photo_preference'")
assert frappe.db.sql('SELECT COUNT(*) FROM tt_patient_photo_preference')[0][0]==0
frappe.destroy();print('PASS fresh Frappe16 installation and two native migrations; structured/evidence tables empty; full bundled directory imported; access/provider switches remain off. Counts:',dict(counts))
