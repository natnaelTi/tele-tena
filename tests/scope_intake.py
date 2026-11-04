"""Real Frappe16 DB, rollback-only synthetic onboarding and manual scope review."""
from direct_payments import *
from unittest.mock import patch
from tele_tena.api import professional,contact_auth,scope_intake,vetting,policies,care_languages
from tele_tena.patches.v1_50_onboarding_scope_intake import execute

class ScopeIntake(unittest.TestCase):
 def setUp(self):
  frappe.set_user('Administrator');frappe.local.lang='en';frappe.db.savepoint('scope_intake')
  self.user='scope-'+uuid.uuid4().hex+'@offline-test.invalid'
  from tele_tena.account_context import authorized_user_change
  with authorized_user_change():
   frappe.get_doc({'doctype':'User','email':self.user,'first_name':'Fictional Scope Applicant','user_type':'Website User','send_welcome_email':0}).insert()
  frappe.db.sql('INSERT INTO tt_onboarding VALUES (%s,%s,0,%s,NULL,UTC_TIMESTAMP(6))',(self.user,'clinician','{}'))
  frappe.db.sql('INSERT INTO tt_contact_identity VALUES (%s,%s,%s,UTC_TIMESTAMP(6))',('email',self.user,self.user))
  self.services=frappe.db.sql("SELECT name FROM `tabTele Tena Service` WHERE vetting_required=1 AND catalog_status IN ('Draft','Active') ORDER BY name LIMIT 3",pluck=True);self.assertEqual(len(self.services),3)
  frappe.set_user(self.user)
  from pypdf import PdfWriter
  stream=io.BytesIO();writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.write(stream);pdf=base64.b64encode(stream.getvalue()).decode()
  self.transport=patch('tele_tena.review.registration_enabled',return_value=True);self.transport.start();self.addCleanup(self.transport.stop)
  self.cv=professional.upload('CV','fictional-cv.pdf',pdf)['id'];self.license=professional.upload('License','fictional-license.pdf',pdf)['id']
  self.payload={'first_name':'Fictional','last_name':'Applicant','profession':'profession:counselor','qualification_title':'Fictional Counseling Qualification','issuer':'Other','issuer_other':'Fictional Training College','issuer_country':'ET','adult':True,'declaration':True,'cv_files':[self.cv],'license_files':[self.license],'experience_years':'4'}
  professional.save(self.payload,0)
  care_languages.save_claims([{'code':'en','proficiency':3,'explanation':'Synthetic self-assessment only'}])
  policy=policies.current()
  self.answers={'adult':True,'consent':True,'terms_accepted':True,'privacy_acknowledged':True,'terms_version':policy['terms_version'],'privacy_version':policy['privacy_version'],'care_languages':['en'],'requested_services':self.services[:2]}
 def tearDown(self):
  frappe.set_user('Administrator');frappe.db.rollback(save_point='scope_intake');frappe.clear_cache(user=self.user)
 def finish(self):
  self.assertTrue(contact_auth.save_onboarding('clinician',3,self.answers,1)['completed'])
  return [r for r in vetting.my_scope_applications() if r.service in self.services]
 def test_complete_creates_independent_submissions_and_private_license_snapshots(self):
  items=self.finish();self.assertEqual(len(items),2);self.assertTrue(all(r.status=='Submitted' for r in items))
  self.assertNotIn('Tele Tena Clinician',frappe.get_roles(self.user))
  self.assertFalse(j.rows('SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s',(self.user,)))
  for item in items:
   submission=frappe.db.get_value('Tele Tena Vetting Scope Application',item.name,'professional_submission');self.assertTrue(submission)
   evidence=vetting._scope_evidence_rows(item.name);self.assertEqual(len(evidence),1);self.assertEqual(evidence[0].evidence_type,'License or registration')
   vetting.download_scope_evidence(evidence[0].id);self.assertEqual(frappe.local.response.filecontent,professional.download(self.license).data)
  frappe.set_user(users['reviewer']);review=next(r for r in j.applications() if r.user==self.user);self.assertEqual(len(review.scope_applications),2)
  vetting.review_scope_application(items[0].name,'Clarification',findings='Supply scope-specific supervised practice evidence.')
  vetting.review_scope_application(items[1].name,'Rejected',findings='Evidence does not support this requested scope.')
  frappe.set_user(self.user);states={r.service:r.status for r in vetting.my_scope_applications()};self.assertEqual(set(states.values()),{'Clarification','Rejected'})
  for who in ('Guest',users['patient'],users['therapist']):
   frappe.set_user(who)
   with self.assertRaises(frappe.PermissionError):vetting.download_scope_evidence(evidence[0].id)
 def test_missing_legacy_intakes_recovered_repeat_safe_without_rewriting_decisions(self):
  self.finish();frappe.db.sql('DELETE FROM tt_scope_evidence_content WHERE evidence IN (SELECT name FROM `tabTele Tena Scope Evidence` WHERE clinician=%s)',(self.user,));frappe.db.sql('DELETE FROM `tabTele Tena Scope Evidence` WHERE clinician=%s',(self.user,));frappe.db.sql('DELETE FROM `tabTele Tena Vetting Scope Application` WHERE clinician=%s',(self.user,))
  frappe.set_user('Administrator')
  sys.path.insert(0,str(ROOT/'scripts'));from release_preservation import capture,verify_scope_intake
  site=BENCH/'sites'/SITE;original=capture(frappe,site);execute();verify_scope_intake(original,capture(frappe,site),frappe)
  before=j.rows('SELECT * FROM `tabTele Tena Vetting Scope Application` WHERE clinician=%s',(self.user,));self.assertEqual(len(before),2)
  vetting.review_scope_application(before[0].name,'Clarification',findings='Additional synthetic scope evidence required.')
  snapshot=j.rows('SELECT * FROM `tabTele Tena Vetting Scope Application` WHERE clinician=%s',(self.user,));execute();execute();self.assertEqual(snapshot,j.rows('SELECT * FROM `tabTele Tena Vetting Scope Application` WHERE clinician=%s',(self.user,)))
 def test_reviewer_initiates_manual_assessment_but_cannot_bypass_vetting(self):
  self.finish();frappe.set_user(users['reviewer']);j.review(self.user,'Approved')
  with self.assertRaises(frappe.ValidationError):j.review_service_scope(self.user,self.services[2],'Approved')
  self.assertEqual(frappe.local.response['tele_tena_error'],'scope_vetting_required')
  result=scope_intake.prepare_review(self.user,self.services[2],'Explicit synthetic manual review request')
  self.assertEqual(result,scope_intake.prepare_review(self.user,self.services[2],'Retry the same manual review'))
  self.assertTrue(result['application']);self.assertFalse(j.rows('SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s',(self.user,)))
  with self.assertRaises(frappe.ValidationError):vetting.review_scope_application(result['application'],'Approved',findings='Cannot skip mandatory evidence and scores.')
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):scope_intake.prepare_review(self.user,self.services[2],'Unauthorized attempt')
 def test_manual_review_can_record_real_approval_and_legacy_grant(self):
  self.finish();frappe.set_user(users['reviewer']);j.review(self.user,'Approved')
  result=scope_intake.prepare_review(self.user,self.services[2],'Reviewer initiated synthetic service assessment')
  # Catalog state is an isolated rollback fixture, not a real medical-lead claim.
  frappe.db.sql("UPDATE `tabTele Tena Service` SET active=1,catalog_status='Active',clinical_review_status='Approved' WHERE name=%s",(self.services[2],))
  frappe.set_user('Administrator');vetting.approve_rubric_version('proposed-1.0','Synthetic rollback-only rubric review, no production clinical approval')
  evidence=vetting._scope_evidence_rows(result['application'])[0].id
  scores={k:{'score':2,'rationale':'Synthetic assessment evidence supports this domain.','evidence':[]} for k in ('scope_education','supervised_experience','approach_training','adult_population','ethics_safeguarding','assessment_interview')}
  frappe.set_user(users['reviewer'])
  decision=vetting.review_scope_application(result['application'],'Approved',identity_reviewed=True,credential_verified=True,qualification_relevant=True,experience_adequate=True,adult_scope_appropriate=True,interview_completed=True,findings='Synthetic complete individual assessment only.',scored_criteria=scores,credential_source='Fictional test registry',credential_checked_on=frappe.utils.today(),credential_evidence=evidence,credential_source_reference='FICTIONAL-TEST-ONLY')
  self.assertEqual(decision['status'],'Approved');self.assertTrue(j.service_scope_is_current(self.user,self.services[2]))
  self.assertEqual(len(j.rows('SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s',(self.user,))),1)
  legacy=j.one("SELECT name FROM `tabTele Tena Service` WHERE active=1 AND vetting_required=0 LIMIT 1").name
  self.assertEqual(scope_intake.prepare_review(self.user,legacy,'Synthetic explicit legacy manual grant')['status'],'Approved')
 def test_failed_final_submission_rolls_back_all_selected_scope_work(self):
  real=scope_intake._copy_license;calls=[]
  def fail_second(*args):
   calls.append(1)
   if len(calls)==2:raise frappe.ValidationError('Synthetic storage failure')
   return real(*args)
  frappe.db.savepoint('atomic_scope')
  with patch.object(scope_intake,'_copy_license',side_effect=fail_second):
   with self.assertRaises(frappe.ValidationError):contact_auth.save_onboarding('clinician',3,self.answers,1)
  frappe.db.rollback(save_point='atomic_scope')
  self.assertFalse(j.rows('SELECT user FROM tt_application WHERE user=%s',(self.user,)));self.assertFalse(j.rows('SELECT name FROM `tabTele Tena Vetting Scope Application` WHERE clinician=%s',(self.user,)))
  self.assertEqual(len(self.finish()),2)

if __name__=='__main__':
 try:unittest.main(defaultTest='ScopeIntake')
 finally:frappe.db.rollback();frappe.destroy()
