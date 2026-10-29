"""Explicit reviewer financial defaults: native User saves, isolated database rollback."""
import os,sys,uuid,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BENCH=Path('/home/frappe/teletena-compat/bench');os.chdir(BENCH/'sites');sys.path.insert(0,str(ROOT))
import frappe
frappe.init(site='teletena-guest-first-test.localhost');frappe.connect();frappe.set_user('Administrator');frappe.clear_cache()
class ReviewerDefaults(unittest.TestCase):
 def setUp(self):frappe.set_user('Administrator');frappe.db.savepoint('reviewer_defaults')
 def tearDown(self):frappe.db.rollback(save_point='reviewer_defaults');frappe.clear_cache();frappe.set_user('Administrator')
 def user(self):return frappe.get_doc({'doctype':'User','email':'roles-'+uuid.uuid4().hex+'@offline-test.invalid','first_name':'Fictional Role Test','send_welcome_email':0,'user_type':'Website User'}).insert()
 def test_new_reviewer_default_and_explicit_removal(self):
  u=self.user();u.add_roles('Tele Tena Approver');self.assertIn('Tele Tena Financial Configuration',[r.role for r in u.roles])
  u.remove_roles('Tele Tena Financial Configuration');u.first_name='Updated Fictional Reviewer';u.save();self.assertNotIn('Tele Tena Financial Configuration',[r.role for r in u.roles])
 def test_clinician_does_not_receive_financial_control(self):
  u=self.user();u.add_roles('Tele Tena Clinician');self.assertNotIn('Tele Tena Financial Configuration',[r.role for r in u.roles])
 def test_existing_reviewer_backfill_is_repeat_safe(self):
  from tele_tena.patches.v1_48_reviewer_financial_defaults import execute
  u=self.user();u.add_roles('Tele Tena Approver');u.remove_roles('Tele Tena Financial Configuration')
  config=frappe.db.sql('SELECT * FROM tt_payment_config');journal=frappe.db.sql('SELECT COUNT(*) FROM tt_journal')
  execute();first=frappe.db.sql("SELECT COUNT(*) FROM tt_audit WHERE action='ReviewerFinancialDefaultGranted'");execute();self.assertEqual(first,frappe.db.sql("SELECT COUNT(*) FROM tt_audit WHERE action='ReviewerFinancialDefaultGranted'"))
  self.assertIn('Tele Tena Financial Configuration',frappe.get_roles(u.name));self.assertEqual(config,frappe.db.sql('SELECT * FROM tt_payment_config'));self.assertEqual(journal,frappe.db.sql('SELECT COUNT(*) FROM tt_journal'))
if __name__=='__main__':
 try:unittest.main()
 finally:frappe.db.rollback();frappe.destroy()
