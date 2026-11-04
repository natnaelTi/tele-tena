"""Direct-payment follow-up is not a wallet dispute. Rollback-only real DB."""
from direct_payments import *
from unittest.mock import patch
from tele_tena import accounting

class Boundaries(DirectPayment):
 def test_direct_followup_notifies_both_parties_once_without_wallet_dispute(self):
  with patch('tele_tena.booking_notifications.wake_dispatch'):
   result,_=self.book();id=result['payment'];self.receipt(id)
   before=j.one('SELECT COUNT(*) n FROM tt_dispute').n;journal=j.one('SELECT COUNT(*) n FROM tt_journal').n
   frappe.db.sql('UPDATE tt_appointment SET start=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 2 HOUR),end=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 HOUR) WHERE id=%s',(result['id'],))
   first=pay.raise_issue(id,'Please check my submitted receipt.','follow-up');again=pay.raise_issue(id,'Please check my submitted receipt.','follow-up')
   self.assertEqual(first['state'],'ReconciliationRequired');self.assertEqual(first['history'],again['history'])
   self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_dispute').n,before);self.assertEqual(j.one('SELECT COUNT(*) n FROM tt_journal').n,journal)
   notices=j.rows("SELECT user,channel FROM tt_booking_notice WHERE appointment=%s AND event='PaymentReconciliation'",(result['id'],))
   self.assertEqual({(x.user,x.channel) for x in notices},{(u,ch) for u in (users['patient'],users['counselor']) for ch in ('email','sms')});self.assertEqual(len(notices),4)
   system=j.rows("SELECT user FROM tt_user_notification WHERE appointment=%s AND kind='PaymentReconciliation'",(result['id'],));self.assertEqual({x.user for x in system},{users['patient'],users['counselor']});self.assertEqual(len(system),2)
   with self.assertRaises(frappe.ValidationError):accounting.open_earning_dispute(result['id'],'Not a wallet transaction')
   self.assertEqual(frappe.local.response['tele_tena_error'],'wallet_dispute_unavailable')
   frappe.set_user(users['counselor'])
   with self.assertRaises(frappe.ValidationError):pay.review(id,'dispute','old-client','No wallet custody')
   self.assertEqual(frappe.local.response['tele_tena_error'],'direct_dispute_unavailable')
   pay.review(id,'reconcile','clinician-follow-up','Checking external transfer')
   frappe.set_user(users['reviewer'])
   with self.assertRaises(frappe.PermissionError):pay.detail(id)
 def test_wallet_mode_capability_and_original_wallet_dispute_stay_available(self):
  result,_=self.book('Wallet');self.assertTrue(pay.capabilities()['wallet_disputes'])
  # The wallet command reaches its real earning lookup rather than the direct-mode guard.
  with self.assertRaises(frappe.PermissionError):accounting.open_earning_dispute(result['id'],'No completed earning yet')
  self.assertNotEqual(frappe.local.response.get('tele_tena_error'),'wallet_dispute_unavailable')
  frappe.set_user('Administrator');c=pay.config();pay.configure('Offline',c.revision,'Rollback-only capability test',transition_plan='Preserve historical wallet obligations and their original dispute rules. No production changes.')
  self.assertFalse(pay.capabilities()['wallet_disputes']);frappe.set_user(users['patient'])
  with self.assertRaises(frappe.PermissionError):accounting.open_earning_dispute(result['id'],'Still no completed earning')
  self.assertNotEqual(frappe.local.response.get('tele_tena_error'),'wallet_dispute_unavailable')

if __name__=='__main__':
 try:unittest.main(defaultTest=['Boundaries.test_direct_followup_notifies_both_parties_once_without_wallet_dispute','Boundaries.test_wallet_mode_capability_and_original_wallet_dispute_stay_available'])
 finally:frappe.db.rollback();frappe.destroy()
