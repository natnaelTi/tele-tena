"""Persistent typed responses and email-authorized assistance; rollback-only fixtures."""
from scope_information import *
from tele_tena.api import application_flow as flow

class ApplicationFlow(ScopeInformation):
 def request(self,items=None):
  app=self.without_license();frappe.set_user(users['reviewer']);vetting.review_scope_application(app.name,'Clarification',findings='Please supply a current license PDF.',requested_items=items or ['license_document'])
  request=j.one("SELECT id FROM tt_scope_information_request WHERE application=%s AND state='Open'",(app.name,));return app,request
 def test_typed_license_response_populates_license_field_and_preserves_history(self):
  app,req=self.request();old=frappe.db.sql('SELECT id,payload,digest FROM tt_professional_submission WHERE user=%s',(self.user,));frappe.set_user(self.user)
  result=flow.respond(app.name,req.id,files={'license_document':[self.license]});again=flow.respond(app.name,req.id,files={'license_document':[self.license]});self.assertTrue(again['idempotent'])
  data=flow.detail(app.name);self.assertEqual(data['application'].status,'Resubmitted');license=[e for e in data['application'].scope_evidence if e.evidence_type=='License or registration'];self.assertEqual(len(license),1);self.assertEqual(data['professional']['payload']['license_files'],[self.license]);self.assertEqual(frappe.db.sql('SELECT id,payload,digest FROM tt_professional_submission WHERE user=%s',(self.user,)),old)
  self.assertEqual(j.one('SELECT status FROM `tabTele Tena Vetting Scope Application` WHERE name=%s',(app.name,)).status,'Resubmitted');self.assertEqual(len(j.rows("SELECT id FROM tt_booking_notice WHERE context_ref=%s AND event='ScopeResubmitted'",(app.name,))),3);self.assertFalse(j.service_scope_is_current(self.user,app.service))
  doc=flow.document(license[0].id);self.assertIn('no-store',doc.headers['Cache-Control']);self.assertEqual(doc.mimetype,'application/pdf')
  for who in ('Guest',users['patient'],users['therapist']):
   frappe.set_user(who)
   with self.assertRaises((frappe.PermissionError,frappe.ValidationError)):flow.document(license[0].id)
 def test_response_validates_requested_fields_owner_type_and_required_document(self):
  app,req=self.request();frappe.set_user(self.user)
  for fields,files in [({},{}),({'jurisdiction':'Not requested'},{}),({}, {'license_document':[self.cv]}),({}, {'qualification_document':[self.license]})]:
   with self.assertRaises(frappe.ValidationError):flow.respond(app.name,req.id,fields,files)
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.ValidationError):flow.respond(app.name,req.id,files={'license_document':[self.license]})
  self.assertEqual(j.one('SELECT state FROM tt_scope_information_request WHERE id=%s',(req.id,)).state,'Open');self.assertFalse(j.rows('SELECT id FROM tt_scope_information_response WHERE request_id=%s',(req.id,)))
 def test_email_assistance_requires_explicit_authorization_and_separate_approvals(self):
  frappe.set_user(self.user)
  with self.assertRaises(frappe.ValidationError):flow.request_assistance(self.services[:2],False)
  c=flow.request_assistance(self.services[:2],True);self.assertEqual(flow.request_assistance(self.services[:2],True)['id'],c['id']);frappe.set_user(users['reviewer'])
  state=flow.assistance_detail(c['id']);self.assertFalse(state['professional']['identity_access'])
  with self.assertRaises(frappe.ValidationError):flow.assisted_upload(c['id'],'Identification','id.pdf',base64.b64encode(professional.download(self.cv).data).decode())
  auth=flow.assisted_upload(c['id'],'Authorization','fictional-authorization.pdf',base64.b64encode(professional.download(self.cv).data).decode())
  flow.assisted_save(c['id'],self.payload,state['professional']['revision']);policy=policies.current();args=dict(case=c['id'],authorization_file=auth['id'],source_reference='FICTIONAL-EMAIL-MESSAGE-REFERENCE',received_on=frappe.utils.today(),terms_version=policy['terms_version'],privacy_version=policy['privacy_version'],attestations={k:True for k in ('authorization','accuracy','adult','terms','privacy','registration_consent','care_languages')})
  result=flow.assisted_submit(**args);self.assertTrue(result['submitted']);self.assertTrue(flow.assisted_submit(**args)['idempotent']);self.assertEqual(j.one('SELECT status FROM tt_application WHERE user=%s',(self.user,)).status,'Pending');self.assertNotIn('Tele Tena Clinician',frappe.get_roles(self.user));self.assertEqual(len(j.rows('SELECT name FROM `tabTele Tena Vetting Scope Application` WHERE clinician=%s',(self.user,))),2)
  self.assertFalse(j.rows('SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s',(self.user,)));self.assertEqual(j.one('SELECT reviewer FROM tt_assisted_submission WHERE case_id=%s',(c['id'],)).reviewer,users['reviewer']);self.assertEqual(j.one('SELECT declaration_version FROM tt_professional_submission WHERE user=%s',(self.user,)).declaration_version,'professional-accuracy-email-v1')
 def test_assisted_submit_missing_proof_or_other_actor_denied(self):
  c=flow.request_assistance(self.services[:2],True)
  for user in (self.user,users['patient'],'Guest'):
   frappe.set_user(user)
   with self.assertRaises(frappe.PermissionError):flow.assistance_detail(c['id'])
  frappe.set_user(users['reviewer'])
  with self.assertRaises(frappe.ValidationError):flow.assisted_submit(c['id'],'missing','source','',policies.current()['terms_version'],policies.current()['privacy_version'],{})
  self.assertFalse(j.rows('SELECT id FROM tt_assisted_submission WHERE case_id=%s',(c['id'],)))

if __name__=='__main__':
 try:unittest.main(defaultTest='ApplicationFlow')
 finally:frappe.db.rollback();frappe.destroy()
