"""Account-bound OTP possession proof; real database, private in-memory transport."""
from direct_payments import *
from unittest.mock import patch
from datetime import timedelta
from tele_tena.api import contact_auth as auth,phone_auth

class DeliveryContacts(unittest.TestCase):
 def setUp(self):
  frappe.set_user('Administrator');frappe.db.savepoint('delivery_contact');self.user=self.new_user();frappe.set_user(self.user);self.codes={};self.patches=[]
  for item in [patch.object(frappe.db,'commit'),patch('tele_tena.email_delivery.configuration',return_value={'test_transport':True}),patch('tele_tena.email_delivery.send_code',side_effect=self.capture),patch('tele_tena.sms.send_otp',side_effect=self.capture),patch('tele_tena.review.phone_enabled',return_value=True)]:
   item.start();self.patches.append(item)
 def tearDown(self):
  for item in reversed(self.patches):item.stop()
  frappe.set_user('Administrator');frappe.db.rollback(save_point='delivery_contact')
 def new_user(self):
  from tele_tena.account_context import authorized_user_change
  who='contact-owner-'+uuid.uuid4().hex+'@accounts.tele-tena.invalid'
  original=frappe.session.user;frappe.set_user('Administrator')
  with authorized_user_change():frappe.get_doc({'doctype':'User','email':who,'first_name':'Fictional Contact Owner','user_type':'Website User','send_welcome_email':0}).insert()
  frappe.set_user(original);return who
 def capture(self,destination,code):self.codes[destination]=code
 def request(self,contact):return auth.request_delivery_contact('email',contact,uuid.uuid4().hex)
 def test_link_preserves_identity_roles_and_signin_uses_same_account(self):
  email='verified-'+uuid.uuid4().hex+'@offline-test.invalid';roles=frappe.get_roles(self.user);user_count=frappe.db.sql('SELECT COUNT(*) FROM tabUser')[0][0]
  value=self.request(email);self.assertEqual(auth.verify_delivery_contact('email',email,value['challenge_id'],self.codes[email]),{'linked':True})
  self.assertEqual(frappe.session.user,self.user);self.assertEqual(frappe.get_roles(self.user),roles);self.assertEqual(frappe.db.sql('SELECT COUNT(*) FROM tabUser')[0][0],user_count)
  self.assertEqual(auth.delivery_contacts()[0].contact,email)
  with self.assertRaises(frappe.ValidationError):auth.verify_delivery_contact('email',email,value['challenge_id'],self.codes[email])
  self.assertEqual(auth._identity('email',email),self.user)
 def test_link_proof_cannot_be_used_for_public_login_or_different_account(self):
  email='bound-'+uuid.uuid4().hex+'@offline-test.invalid';value=self.request(email);code=self.codes[email]
  with self.assertRaises(frappe.ValidationError):auth.verify_code('email',email,value['challenge_id'],code)
  other=self.new_user();frappe.set_user(other)
  with self.assertRaises(frappe.ValidationError):auth.verify_delivery_contact('email',email,value['challenge_id'],code)
  self.assertFalse(frappe.db.sql('SELECT user FROM tt_contact_identity WHERE contact=%s',(email,)))
  frappe.set_user(self.user);self.assertTrue(auth.verify_delivery_contact('email',email,value['challenge_id'],code)['linked'])
 def test_wrong_expired_codes_and_foreign_sms_are_denied(self):
  email='expiry-'+uuid.uuid4().hex+'@offline-test.invalid';value=self.request(email);actual=self.codes[email];wrong='000000' if actual!='000000' else '111111'
  with self.assertRaises(frappe.ValidationError):auth.verify_delivery_contact('email',email,value['challenge_id'],wrong)
  when=phone_auth._now()+timedelta(seconds=301)
  with patch.object(phone_auth,'_now',return_value=when):
   with self.assertRaises(frappe.ValidationError):auth.verify_delivery_contact('email',email,value['challenge_id'],actual)
  with self.assertRaises(frappe.ValidationError):auth.request_delivery_contact('phone','+14155550100',uuid.uuid4().hex)
  self.assertEqual(len(auth.delivery_contacts()),0)
 def test_contact_owned_by_another_account_is_not_merged_or_replaced(self):
  other=self.new_user();value=self.request(other)
  with self.assertRaises(frappe.ValidationError):auth.verify_delivery_contact('email',other,value['challenge_id'],self.codes[other])
  self.assertEqual(frappe.local.response['tele_tena_error'],'contact_link_unavailable');self.assertFalse(auth.delivery_contacts());self.assertEqual(frappe.session.user,self.user)
 def test_sms_link_single_account_and_rate_limit_preserved(self):
  phone='+251900000'+str(uuid.uuid4().int)[:3];value=auth.request_delivery_contact('phone',phone,uuid.uuid4().hex)
  with self.assertRaises(frappe.ValidationError):auth.request_delivery_contact('phone',phone,uuid.uuid4().hex)
  self.assertTrue(auth.verify_delivery_contact('phone',phone,value['challenge_id'],self.codes[phone])['linked'])
  self.assertEqual(auth._identity('phone',phone),self.user)
  frappe.set_user('Guest')
  with self.assertRaises(frappe.PermissionError):auth.request_delivery_contact('email','not-sent@offline-test.invalid',uuid.uuid4().hex)

if __name__=='__main__':
 try:unittest.main(defaultTest='DeliveryContacts')
 finally:frappe.db.rollback();frappe.destroy()
