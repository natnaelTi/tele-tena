"""Real MariaDB content/version/permission tests; isolated site, no provider I/O."""
import hashlib,json,os,sys,unittest,uuid
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];BENCH=Path(os.environ['TELE_TENA_TEST_BENCH']);SITE=os.environ['TELE_TENA_TEST_SITE']
assert SITE=='teletena-guest-first-test.localhost','Only the isolated retained fixture is allowed'
os.chdir(BENCH/'sites');sys.path.insert(0,str(REPO))
import frappe
frappe.init(site=SITE);frappe.connect();frappe.local.lang='en'
from tele_tena.api import public_content as content,policies
from tele_tena.patches.v1_43_public_content import execute
state=json.loads(Path(frappe.get_site_path('private','tt-demo-mvp-v2-records.json')).read_text());users=state['users']
def fingerprint(table):
 values=frappe.db.sql('SELECT * FROM '+table,as_dict=True)
 return hashlib.sha256(json.dumps(sorted([dict(v) for v in values],key=lambda v:json.dumps(v,default=str,sort_keys=True)),sort_keys=True,default=str).encode()).hexdigest()
protected=['tt_profile','tt_appointment','tt_policy_acceptance','tt_history_document','tt_history_grant','tt_financial_account','tt_journal','tt_journal_line','tt_earning','tt_dispute','tt_payout']
protected=[table for table in protected if frappe.db.sql('SHOW TABLES LIKE %s',(table,))]
before={t:fingerprint(t) for t in protected}
execute();frappe.db.commit();initial={t:fingerprint(t) for t in ['tt_public_content_head','tt_public_content_revision']};execute();frappe.db.commit()
assert initial=={t:fingerprint(t) for t in initial},'Repeat migration changed content'
assert before=={t:fingerprint(t) for t in before},'Migration changed preexisting records'
print('PASS additive creation/repeat migration; '+str(len(before))+' preexisting profile/appointment/consent/history/financial tables preserved by full-row hashes.')
class PublicContent(unittest.TestCase):
 def setUp(self):frappe.db.savepoint('public_content_test');frappe.set_user(users['reviewer'])
 def tearDown(self):frappe.db.rollback(save_point='public_content_test');frappe.set_user('Administrator')
 def test_public_allowlist_and_internal_denial(self):
  frappe.set_user('Guest');public=content.public();self.assertTrue(public['contact']['mock']);self.assertEqual({v['key'] for v in public['documents']},{k for k,v in content.DOCUMENTS.items() if v[1]=='public'})
  self.assertNotIn('actor',json.dumps(public));self.assertFalse(any(v['audience']=='internal' for v in public['documents']))
  with self.assertRaises(frappe.PermissionError):content.manage()
  for role in ['patient','counselor']:
   frappe.set_user(users[role])
   with self.assertRaises(frappe.PermissionError):content.manage()
   with self.assertRaises(frappe.PermissionError):content.save_draft('contact',content.CONTACT,1)
   with self.assertRaises(frappe.PermissionError):content.publish_review('terms','anything',1)
 def test_contact_draft_visibility_validation_and_audit(self):
  item=next(v for v in content.manage() if v['key']=='contact');original=content.public()['contact'];payload={**item['payload'],'organization':'Fictional Edited Office'}
  saved=content.save_draft('contact',payload,item['revision']);self.assertEqual(content.public()['contact'],original)
  with self.assertRaises(frappe.ValidationError):content.publish_review('contact',saved['version'],item['revision'])
  content.publish_review('contact',saved['version'],saved['revision']);self.assertEqual(content.public()['contact']['organization'],payload['organization'])
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_public_content_event WHERE version=%s',(saved['version'],))[0][0],2)
  with self.assertRaises(frappe.ValidationError):content.save_draft('contact',{**payload,'email':'a\r\nb@example.org'},saved['revision']+1)
  with self.assertRaises(frappe.ValidationError):content.save_draft('contact',{**payload,'mock':False},saved['revision']+1)
 def test_immutable_versions_optimistic_conflict_and_visibility(self):
  item=next(v for v in content.manage() if v['key']=='retention');old=frappe.db.sql('SELECT payload FROM tt_public_content_revision WHERE id=%s',(item['draft_id'],))[0][0]
  with self.assertRaises(frappe.ValidationError):content.save_draft('retention',{**item['payload'],'audience':'public'},item['revision'])
  payload={**item['payload'],'body':'Edited Internal Heading\nPrivate operational draft.'};saved=content.save_draft('retention',payload,item['revision'])
  with self.assertRaises(frappe.ValidationError):content.save_draft('retention',payload,item['revision'])
  content.publish_review('retention',saved['version'],saved['revision']);frappe.set_user('Guest');self.assertNotIn('Private operational draft.',json.dumps(content.public()))
  self.assertEqual(frappe.db.sql('SELECT payload FROM tt_public_content_revision WHERE id=%s',(item['draft_id'],))[0][0],old)
 def test_policy_acceptance_snapshots_and_stale_version(self):
  before=fingerprint('tt_policy_acceptance');old=policies.current();item=next(v for v in content.manage() if v['key']=='terms');saved=content.save_draft('terms',{**item['payload'],'body':item['payload']['body']+'\n\nReview Change\nFictional test change.'},item['revision']);content.publish_review('terms',saved['version'],saved['revision']);new=policies.current();self.assertNotEqual(old['terms_version'],new['terms_version']);self.assertEqual(before,fingerprint('tt_policy_acceptance'))
  frappe.set_user(users['patient']);answers={'terms_accepted':True,'privacy_acknowledged':True,'consent':True,'terms_version':old['terms_version'],'privacy_version':old['privacy_version']}
  with self.assertRaises(frappe.ValidationError):policies.record(users['patient'],answers)
  answers['terms_version']=new['terms_version'];policies.record(users['patient'],answers);policies.record(users['patient'],answers)
  self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tt_policy_acceptance WHERE user=%s AND terms_version=%s',(users['patient'],new['terms_version']))[0][0],1)
if __name__=='__main__':
 try:unittest.main()
 finally:frappe.db.rollback();frappe.destroy()
