"""Real MariaDB authorization/state/migration tests, rollback-isolated synthetic evidence."""
import os,sys,json,hashlib,unittest,uuid,base64,io
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];BENCH=Path(os.environ['TELE_TENA_TEST_BENCH']);SITE=os.environ['TELE_TENA_TEST_SITE']
assert SITE in ('teletena-guest-first-test.localhost','teletena-mvp-presentation.localhost')
os.chdir(BENCH/'sites');sys.path.insert(0,str(REPO))
import frappe
frappe.init(site=SITE);frappe.connect();frappe.local.lang='en';frappe.set_user('Administrator')
from tele_tena.api import professional as p,professional_directory as directory
assert Path(p.__file__).resolve()==REPO/'tele_tena/api/professional.py'
from tele_tena.patches.v1_44_professional_onboarding import execute

columns={}
def fingerprint(table):
 if table not in columns:columns[table]=[r[0] for r in frappe.db.sql('SHOW COLUMNS FROM `'+table+'`')]
 values=frappe.db.sql('SELECT '+','.join('`'+c+'`' for c in columns[table])+' FROM `'+table+'`')
 return hashlib.sha256(json.dumps(sorted([json.dumps(v,default=lambda x:hashlib.sha256(bytes(x)).hexdigest() if isinstance(x,(bytes,bytearray,memoryview)) else str(x),sort_keys=True) for v in values]),sort_keys=True).encode()).hexdigest()
protected=[t[0] for t in frappe.db.sql('SHOW TABLES') if t[0]!='tt_reference' and ( t[0].startswith(('tt_','tabTele Tena ')) or t[0] in ('tabUser','tabHas Role','__Auth'))]
before={t:fingerprint(t) for t in protected};execute();frappe.db.commit();assert before=={t:fingerprint(t) for t in protected},'Migration changed preexisting data'
new={t[0]:fingerprint(t[0]) for t in frappe.db.sql("SHOW TABLES LIKE 'tt_professional%'")};new['tt_reference']=fingerprint('tt_reference');execute();frappe.db.commit();assert new=={t:fingerprint(t) for t in new};print('PASS additive/repeat migration preserves '+str(len(protected))+' original tables by full-row hashes')
users=json.loads((BENCH/'sites'/SITE/'private/tt-demo-mvp-v2-records.json').read_text())['users']
class Professional(unittest.TestCase):
 def setUp(self):frappe.set_user(users['counselor']);frappe.db.savepoint('professional_test')
 def tearDown(self):frappe.db.rollback(save_point='professional_test');frappe.set_user('Administrator')
 def payload(self):return {'first_name':'Selam','last_name':'Bekele','profession':'profession:counselor','specialties':['specialty:relationship-counseling'],'bio':'Collaborative adult counseling.','qualification_title':'Master of Arts in Counseling','issuer':'Other','issuer_other':'Fictional Development College','issuer_country':'ET','adult':True,'declaration':True,'competencies':[{'domain':'domain:therapeutic-communication','rating':2,'explanation':'Fictional supervised training'}]}
 def test_draft_submit_retry_conflict_and_no_approval(self):
  old=frappe.db.sql('SELECT status FROM tt_application WHERE user=%s',(users['counselor'],));scopes=fingerprint('tabTele Tena Clinician Service') if frappe.db.table_exists('Tele Tena Clinician Service') else None
  state=p.application();p.save(self.payload(),state['revision']);state=p.application();self.assertEqual(state['payload']['first_name'],'Selam')
  with self.assertRaises(frappe.ValidationError):p.save(self.payload(),0)
  state=p.application();p.save(self.payload(),state['revision'],True);state=p.application();p.save(self.payload(),state['revision'],True);self.assertEqual(len(p.application()['submissions']),1)
  self.assertEqual(old,frappe.db.sql('SELECT status FROM tt_application WHERE user=%s',(users['counselor'],)))
  if scopes:self.assertEqual(scopes,fingerprint('tabTele Tena Clinician Service'))
 def test_bio_date_and_self_assessment(self):
  self.assertEqual(p.word_count(' one\n two-word\t ሦስት '),3)
  for patch in [{'bio':'word '*51},{'valid_from':'2026-02-02','valid_until':'2026-01-01'},{'competencies':[{'domain':'domain:therapeutic-communication','rating':0}]},{'declaration':False}]:
   with self.assertRaises(frappe.ValidationError):p.validate({**self.payload(),**patch},users['counselor'],True)
  self.assertFalse(p.validate({**self.payload(),'competencies':[]},users['counselor'],True)['competencies'])
 def test_private_evidence_and_historical_retention(self):
  from PIL import Image
  f=io.BytesIO();Image.new('RGB',(8,8),'white').save(f,format='PNG');encoded=base64.b64encode(f.getvalue()).decode();id=p.upload('Identification','fictional-id.png',encoded)['id'];self.assertEqual(id,p.upload('Identification','fictional-id.png',encoded)['id'])
  self.assertEqual(p.download(id).status_code,200)
  for who in ('patient','therapist','reviewer'):
   frappe.set_user(users[who])
   with self.assertRaises(frappe.PermissionError):p.download(id)
  frappe.set_user(users['reviewer']);self.assertNotIn(id,json.dumps(p.application(users['counselor']),default=str))
  frappe.set_user(users['counselor']);state=p.application();value={**self.payload(),'identification_type':'National ID','identity_files':[id]};p.save(value,state['revision'],True);state=p.application();p.save({**value,'identity_files':[]},state['revision'],True);self.assertTrue(frappe.db.sql('SELECT id FROM tt_professional_evidence WHERE id=%s',(id,)));self.assertIn(id,json.dumps(p.application()['submissions'],default=str))
  for filename in ('bad.html','bad.pdf'):
   with self.assertRaises(frappe.ValidationError):p.upload('License',filename,base64.b64encode(b'<script>alert(1)</script>').decode())
 def test_search_paging_and_facility_dedupe(self):
  a=directory.search('issuer',limit=20);b=directory.search('issuer',offset=20,limit=20);self.assertLessEqual(len(a['items']),20);self.assertFalse(set(x.id for x in a['items'])&set(x.id for x in b['items']))
  c=directory.add_facility('Fictional Clinic '+uuid.uuid4().hex[:8],'ET','Addis Ababa','Clinic');label=c['label'];self.assertEqual(c['id'],directory.add_facility(label,'ET','Addis Ababa','Clinic')['id'])
  self.assertTrue(any(x.id==c['id'] for x in directory.search('facility',search=label)['items']))
  frappe.set_user(users['therapist']);self.assertFalse(directory.search('facility',search=label)['items'])
 def test_identity_assignment_and_facility_review(self):
  from PIL import Image
  f=io.BytesIO();Image.new('RGB',(8,8),'white').save(f,format='PNG');id=p.upload('Identification','fictional-id.png',base64.b64encode(f.getvalue()).decode())['id']
  clinic=directory.add_facility('Fictional Reviewed Facility '+uuid.uuid4().hex[:8],'ET','Addis Ababa','Clinic')
  frappe.set_user('Administrator');p.assign_identity_reviewer(users['counselor'],users['reviewer'],'Explicit synthetic credential review assignment')
  frappe.set_user(users['reviewer']);self.assertEqual(p.download(id).status_code,200)
  self.assertTrue(directory.review_facility(clinic['id'],'Reviewed','Directory name reviewed, not affiliation or accreditation')['saved'])
  frappe.set_user('Administrator');p.revoke_identity_reviewer(users['counselor'],users['reviewer'],'Review complete')
  frappe.set_user(users['reviewer'])
  with self.assertRaises(frappe.PermissionError):p.download(id)
 def test_new_cv_legacy_projection(self):
  from pypdf import PdfWriter
  f=io.BytesIO();writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.write(f)
  id=p.upload('CV','fictional-cv.pdf',base64.b64encode(f.getvalue()).decode())['id'];state=p.application();p.save({**self.payload(),'cv_files':[id]},state['revision'],True)
  self.assertTrue(p.cv_available(users['counselor']));self.assertEqual(p.submitted_legacy_claims(users['counselor'])['qualification'],'Master of Arts in Counseling')
  from tele_tena.api import journey
  frappe.set_user(users['reviewer']);record=next(x for x in journey.applications() if x.user==users['counselor']);self.assertTrue(record.resume_uploaded);self.assertTrue(record.evidence_complete)
 def test_license_reuse_is_private_and_retry_safe(self):
  from tele_tena.api import vetting
  candidates=frappe.db.sql("SELECT name FROM `tabTele Tena Service` s WHERE vetting_required=1 AND catalog_status IN ('Draft','Active') AND NOT EXISTS (SELECT name FROM `tabTele Tena Vetting Scope Application` a WHERE a.clinician=%s AND a.service=s.name) LIMIT 1",(users['counselor'],))
  self.assertTrue(candidates,'Fixture needs an unapplied structured scope')
  scope=vetting.save_scope_application(candidates[0][0],{'professional_category':'Counselor','qualification':'Fictional development qualification','issuing_institution':'Fictional college','population_adults':True},False)
  from pypdf import PdfWriter
  f=io.BytesIO();writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.write(f)
  id=p.upload('License','fictional-license.pdf',base64.b64encode(f.getvalue()).decode())['id']
  first=p.attach_scope_license(scope['name'],id);second=p.attach_scope_license(scope['name'],id);self.assertEqual(first['id'],second['id']);self.assertTrue(second['already_attached'])
  self.assertEqual(frappe.db.sql("SELECT COUNT(*) FROM `tabTele Tena Scope Evidence` WHERE scope_application=%s AND evidence_type='License or registration'",(scope['name'],))[0][0],1)
  cv=p.upload('CV','fictional-cv.pdf',base64.b64encode(f.getvalue()).decode())['id'];state=p.application();p.save({**self.payload(),'cv_files':[cv],'license_files':[id]},state['revision'],True);version=p.application()['submissions'][0]['id']
  submitted=vetting.save_scope_application(candidates[0][0],{'professional_category':'Counselor','qualification':'Fictional development qualification','issuing_institution':'Fictional college','population_adults':True},True)
  self.assertEqual(frappe.db.get_value('Tele Tena Vetting Scope Application',submitted['name'],'professional_submission'),version)

  from PIL import Image
  image=io.BytesIO();Image.new('RGB',(8,8),'white').save(image,format='PNG');identity=p.upload('Identification','fictional-id.png',base64.b64encode(image.getvalue()).decode())['id']
  with self.assertRaises(frappe.ValidationError):p.attach_scope_license(scope['name'],identity)
  frappe.set_user(users['therapist'])
  with self.assertRaises(frappe.PermissionError):p.attach_scope_license(scope['name'],id)
 def test_generic_api_denial(self):
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):p.application(users['counselor'])
  with self.assertRaises(frappe.PermissionError):p.save(self.payload(),0)
  with self.assertRaises(frappe.PermissionError):directory.pending_facilities()
  self.assertFalse(frappe.db.exists('DocType','tt_professional_evidence'))
if __name__=='__main__':
 try:unittest.main()
 finally:frappe.db.rollback();frappe.destroy()
