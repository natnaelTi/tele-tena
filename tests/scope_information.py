"""Decision-specific validation; missing evidence must not block a safe outcome."""
from scope_intake import *
from tele_tena import communications,notifications

class ScopeInformation(ScopeIntake):
 def setUp(self):
  super().setUp();self.enqueue=patch('tele_tena.communications._enqueue');self.enqueue.start();self.addCleanup(self.enqueue.stop)
 def without_license(self):
  app=self.finish()[0]
  frappe.db.sql('DELETE FROM tt_scope_evidence_content WHERE evidence IN (SELECT name FROM `tabTele Tena Scope Evidence` WHERE scope_application=%s)',(app.name,))
  frappe.db.sql('DELETE FROM `tabTele Tena Scope Evidence` WHERE scope_application=%s',(app.name,));return app
 def incomplete(self):
  return dict(identity_reviewed=True,credential_verified=True,qualification_relevant=True,experience_adequate=True,adult_scope_appropriate=True,interview_completed=True,credential_source='Unfinished check, not verified',scored_criteria={'scope_education':{'score':'','rationale':'','evidence':[]}})
 def test_each_nonapproval_outcome_accepts_missing_license_and_unfinished_checks(self):
  app=self.without_license();frappe.set_user(users['reviewer'])
  for outcome in ('Clarification','Rejected','Suspended','Expired'):
   with self.subTest(outcome=outcome):
    frappe.db.savepoint('each_outcome')
    result=vetting.review_scope_application(app.name,outcome,findings='Please provide your license before this service can be approved.',**self.incomplete());self.assertEqual(result['status'],outcome)
    assessment=frappe.get_doc('Tele Tena Vetting Assessment',result['assessment']);self.assertFalse(assessment.credential_verified);self.assertFalse(assessment.credential_verification_snapshot);self.assertFalse(assessment.scored_criteria_snapshot)
    self.assertEqual(frappe.db.get_value('Tele Tena Vetting Scope Application',app.name,'status'),outcome)
    self.assertFalse(j.service_scope_is_current(self.user,app.service));self.assertEqual(len(j.rows("SELECT id FROM tt_booking_notice WHERE context_ref=%s AND event=%s",(app.name,'Scope'+outcome))),3)
    frappe.db.rollback(save_point='each_outcome')
 def test_approval_still_blocks_missing_license_and_verification_details(self):
  app=self.without_license();frappe.set_user(users['reviewer'])
  with self.assertRaises(frappe.ValidationError):vetting.review_scope_application(app.name,'Approved',findings='Cannot actually approve without evidence.',**self.incomplete())
  self.assertEqual(frappe.local.response['tele_tena_error'],'credential_provenance_required');self.assertEqual(frappe.db.get_value('Tele Tena Vetting Scope Application',app.name,'status'),'Submitted');self.assertFalse(j.service_scope_is_current(self.user,app.service))
 def test_reason_permissions_and_notification_retry_boundaries(self):
  app=self.without_license();frappe.set_user(users['reviewer'])
  with self.assertRaises(frappe.ValidationError):vetting.review_scope_application(app.name,'Clarification',findings='')
  for who in (self.user,users['patient'],'Guest'):
   frappe.set_user(who)
   with self.assertRaises(frappe.PermissionError):vetting.review_scope_application(app.name,'Clarification',findings='Not an authorized reviewer.')
  frappe.set_user(users['reviewer']);reason='Upload the missing license, then resubmit this service application.'
  vetting.review_scope_application(app.name,'Clarification',findings=reason,**self.incomplete());vetting.review_scope_application(app.name,'Clarification',findings=reason)
  self.assertEqual(len(j.rows("SELECT id FROM tt_booking_notice WHERE context_ref=%s AND event='ScopeClarification'",(app.name,))),3)
  frappe.set_user(self.user);mine=next(r for r in vetting.my_scope_applications() if r.name==app.name);self.assertEqual(mine.clarification_request,reason)
  notice=next(r for r in notifications.feed() if r['kind']=='ScopeClarification');self.assertNotIn(reason,json.dumps(notice));self.assertEqual(notice['href'],'/clinician/vetting')
 def test_owner_upload_and_resubmit_does_not_approve_scope(self):
  app=self.without_license();frappe.set_user(users['reviewer']);vetting.review_scope_application(app.name,'Clarification',findings='Upload your license and resubmit.')
  frappe.set_user(self.user);evidence=vetting.upload_scope_evidence(app.name,'License or registration','fictional-correction.pdf',base64.b64encode(professional.download(self.license).data).decode());self.assertTrue(evidence['id'])
  item=next(r for r in vetting.my_scope_applications() if r.name==app.name);values={k:item.get(k) for k in vetting.APPLICANT_FIELDS if k not in ('service','clinician') and item.get(k) is not None}
  result=vetting.save_scope_application(app.service,values,submit=True);self.assertEqual(result['status'],'Resubmitted');self.assertFalse(j.service_scope_is_current(self.user,app.service))

if __name__=='__main__':
 try:unittest.main(defaultTest='ScopeInformation')
 finally:frappe.db.rollback();frappe.destroy()
