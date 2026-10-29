"""Real database, synthetic private bytes; rollback-only payment/photo fixtures."""
from direct_payments import *
import hashlib
from tele_tena.api import profile_photos as photos,professional,presentation
from tele_tena.patches.v1_49_patient_photo_sharing import execute
class AttachmentPhotos(DirectPayment):
 def image(self,color='blue'):
  from PIL import Image
  stream=io.BytesIO();Image.new('RGB',(64,64),color).save(stream,format='PNG');return base64.b64encode(stream.getvalue()).decode()
 def test_current_patient_preference_restricts_projection_and_bytes(self):
  result,_=self.book();app=result['id'];frappe.set_user(users['patient']);photos.upload('private.png',self.image());self.assertTrue(photos.sharing()['share_photo'])
  frappe.set_user(users['counselor']);self.assertTrue(presentation.appointment_detail(app)['photo_url']);self.assertEqual(photos.encounter_photo(app).mimetype,'image/jpeg')
  frappe.set_user(users['patient']);photos.set_sharing(0);self.assertFalse(photos.sharing()['share_photo']);execute();self.assertFalse(photos.sharing()['share_photo'])
  frappe.set_user(users['counselor']);self.assertIsNone(presentation.appointment_detail(app)['photo_url'])
  with self.assertRaises(frappe.PermissionError):photos.encounter_photo(app)
 def test_replacement_deletion_and_private_metadata(self):
  result,_=self.book();app=result['id'];frappe.set_user(users['patient']);first=photos.upload('legal-name-private.png',self.image());frappe.set_user(users['counselor']);before=photos.encounter_photo(app);self.assertIn('no-store',before.headers['Cache-Control']);self.assertNotIn('legal-name',before.headers['Content-Disposition'])
  frappe.set_user(users['patient']);photos.upload('replacement.png',self.image('green'));frappe.set_user(users['counselor']);self.assertNotEqual(before.data,photos.encounter_photo(app).data)
  frappe.set_user(users['patient']);photos.remove();frappe.set_user(users['counselor'])
  with self.assertRaises(frappe.PermissionError):photos.encounter_photo(app)
  with self.assertRaises(frappe.PermissionError):photos.download(first['url'].split('=')[-1])
 def test_receipt_authorized_parties_and_denials(self):
  result,_=self.book();r=self.receipt(result['payment']);file=next(x['evidence'] for x in r['history'] if x['evidence']);response=pay.receipt(file);self.assertIn('no-store',response.headers['Cache-Control']);self.assertEqual(response.mimetype,'image/png')
  frappe.set_user(users['counselor']);self.assertEqual(pay.receipt(file).data,response.data)
  other=j.one("SELECT user FROM tt_profile WHERE kind='clinician' AND user<>%s LIMIT 1",(users['counselor'],)).user
  for user in ['Guest',users['reviewer'],other,users['couple_partner']]:
   frappe.set_user(user)
   with self.assertRaises(frappe.PermissionError):pay.receipt(file)
   with self.assertRaises(frappe.PermissionError):photos.encounter_photo(result['id'])
 def test_identity_reviewer_and_other_evidence_remain_separate(self):
  frappe.set_user(users['counselor']);file=professional.upload('Identification','fictional-id.png',self.image())['id'];self.assertEqual(professional.download(file).mimetype,'image/png')
  frappe.set_user(users['reviewer'])
  with self.assertRaises(frappe.PermissionError):professional.download(file)
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):professional.download(file)
 def test_new_default_does_not_rewrite_other_preferences(self):
  frappe.set_user(users['patient']);before=j.one('SELECT share_name,share_history,history FROM tt_profile WHERE user=%s',(users['patient'],));photos.set_sharing(0);execute();execute();self.assertFalse(photos.patient_sharing(users['patient']));after=j.one('SELECT share_name,share_history,history FROM tt_profile WHERE user=%s',(users['patient'],));self.assertEqual(before,after)
 def test_clinician_photo_in_appointment_record_and_history(self):
  result,_=self.book();app=result['id'];frappe.set_user(users['counselor']);photos.upload('clinician.png',self.image(),1);frappe.set_user(users['patient']);self.assertTrue(next(a for a in j.appointments() if a.id==app).photo_url);self.assertTrue(presentation.appointment_detail(app)['photo_url']);self.assertEqual(photos.encounter_photo(app).mimetype,'image/jpeg')
  super().test_finalization_does_not_credit_direct_payment_again()
  provider=j.one('SELECT public_id FROM tt_profile WHERE user=%s',(users['counselor'],)).public_id
  self.assertTrue(any(c.clinician_id==provider and c.photo_url for c in j.previous_clinicians()))
  with self.assertRaises(frappe.PermissionError):photos.encounter_photo(app,'another-participant')
 def test_legacy_cv_preview_revalidates_and_is_owner_only(self):
  from frappe.utils.pdf import PdfWriter
  writer=PdfWriter();writer.add_blank_page(width=400,height=300);stream=io.BytesIO();writer.write(stream);content=stream.getvalue();frappe.set_user(users['counselor'])
  frappe.db.sql('DELETE FROM tt_resume_evidence WHERE clinician=%s',(users['counselor'],))
  frappe.db.sql('INSERT INTO tt_resume_evidence (clinician,filename,content,content_size,content_sha256,revision,uploaded_by,uploaded_at) VALUES (%s,%s,FROM_BASE64(%s),%s,%s,1,%s,UTC_TIMESTAMP(6))',(users['counselor'],'fictional-cv.pdf',base64.b64encode(content).decode(),len(content),hashlib.sha256(content).hexdigest(),users['counselor']))
  response=professional.legacy_cv();self.assertEqual(response.mimetype,'application/pdf');self.assertIn('no-store',response.headers['Cache-Control'])
  frappe.db.sql('UPDATE tt_resume_evidence SET content=%s WHERE clinician=%s',(b'%PDF-1.4 unsafe %%EOF',users['counselor']))
  with self.assertRaises(frappe.ValidationError):professional.legacy_cv()
  frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):professional.legacy_cv()
 def test_new_patient_persists_default_without_old_consent_rewrite(self):
  from unittest.mock import patch
  frappe.set_user('Administrator');email='photo-'+str(uuid.uuid4())+'@offline-test.invalid'
  with patch('frappe.sendmail',side_effect=AssertionError('Unexpected delivery')):
   user=frappe.get_doc({'doctype':'User','email':email,'first_name':'Fictional Photo Patient','send_welcome_email':0,'user_type':'Website User'}).insert();user.add_roles('Tele Tena Patient')
  frappe.set_user(email);j.save_profile('patient','Fictional Photo Patient',1)
  self.assertTrue(photos.sharing()['share_photo']);self.assertEqual(j.one('SELECT share_photo FROM tt_patient_photo_preference WHERE user=%s',(email,)).share_photo,1)
 def test_private_offer_cards_project_only_public_clinician_photo(self):
  from tele_tena.api.open_requests import my_requests
  frappe.set_user(users['counselor']);photos.upload('fictional-professional.png',self.image(),1);provider=j.one('SELECT public_id FROM tt_profile WHERE user=%s',(users['counselor'],)).public_id
  frappe.set_user(users['patient']);offers=[o for r in my_requests() for o in r.offers];self.assertTrue(any(o.clinician_id==provider and o.photo_url for o in offers));self.assertTrue(all('photo_clinician' not in o for o in offers))
  frappe.set_user(users['counselor'])
  with self.assertRaises(frappe.PermissionError):my_requests()
 def test_couple_photo_preferences_and_recipient_isolation(self):
  from tele_tena.api import couples
  super().test_couples_payment_keeps_payer_consent_and_language_separate()
  plan=j.one('SELECT * FROM tt_couple_plan WHERE payer=%s AND retry_key=%s',(users['couple_payer'],'couples-payment-language'))
  app=j.one('SELECT * FROM tt_appointment WHERE id=%s',(plan.appointment,));people=couples.participants(plan.id)
  for person in people:
   frappe.set_user(person.user);photos.upload('private-participant.png',self.image());photos.set_sharing(person.user==users['couple_payer'])
  frappe.set_user(app.clinician);detail=presentation.appointment_detail(app.id);self.assertEqual(sum(bool(p['photo_url']) for p in detail['couple_participants']),1)
  payer=next(p for p in people if p.user==users['couple_payer']);partner=next(p for p in people if p.user==users['couple_partner'])
  self.assertEqual(photos.encounter_photo(app.id,payer.id).mimetype,'image/jpeg')
  with self.assertRaises(frappe.PermissionError):photos.encounter_photo(app.id,partner.id)
  frappe.set_user(partner.user)
  with self.assertRaises(frappe.PermissionError):photos.encounter_photo(app.id,payer.id)
  frappe.set_user(payer.user);photos.set_sharing(0);frappe.set_user(app.clinician)
  with self.assertRaises(frappe.PermissionError):photos.encounter_photo(app.id,payer.id)
  from unittest.mock import patch
  frappe.set_user(partner.user);photos.set_sharing(1)
  with patch.object(frappe.db,'commit'):couples.withdraw(plan.id)
  self.assertTrue(photos.patient_sharing(partner.user));frappe.set_user(app.clinician)
  with self.assertRaises(frappe.PermissionError):photos.encounter_photo(app.id,partner.id)
if __name__=='__main__':
 try:unittest.main(defaultTest='AttachmentPhotos')
 finally:frappe.db.rollback();frappe.destroy()
