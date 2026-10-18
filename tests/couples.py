"""Persisted two-adult authorization and single-charge regressions; synthetic only."""
import concurrent.futures
import threading
import importlib.util
import json
import secrets
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('presentation_fixtures', Path(__file__).with_name('presentation.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
import frappe
from tele_tena.api import couples, journey, presentation, consultations, clinic_access
from tele_tena.patches import v1_33_couples_consultations, v1_34_shared_change_consent, v1_35_individual_followup


class Couples(unittest.TestCase):
    # Reuse fixture helpers, not individual-session test methods. The parent
    # suite runs separately with its individual service unchanged.
    fund_patient = base.Presentation.fund_patient
    make_schedule = base.Presentation.make_schedule
    slots = base.Presentation.slots
    setUp = base.Presentation.setUp

    @classmethod
    def setUpClass(cls):
        base.Presentation.setUpClass.__func__(cls)
        v1_33_couples_consultations.execute()
        v1_34_shared_change_consent.execute()
        v1_35_individual_followup.execute()
        base.fixtures.login('admin')
        service = frappe.get_doc('Tele Tena Service', base.fixtures.PREFIX)
        service.participant_structure = 'couple'
        service.save()
        frappe.db.commit()

    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        frappe.set_user('Administrator')
        plans = frappe.db.sql('SELECT id FROM tt_couple_plan WHERE payer IN %s',
                              (tuple(base.fixtures.USERS.values()),), pluck=True)
        if plans:
            appointments = frappe.db.sql('SELECT appointment FROM tt_couple_plan WHERE id IN %s AND appointment IS NOT NULL', (tuple(plans),), pluck=True)
            if appointments:
                frappe.db.sql("DELETE c FROM tt_shared_change_consent c JOIN tt_reschedule_proposal r ON r.id=c.change_id WHERE c.kind='reschedule' AND r.appointment IN %s", (tuple(appointments),))
                frappe.db.sql("DELETE c FROM tt_shared_change_consent c JOIN tt_consultation_extension e ON e.id=c.change_id WHERE c.kind='extension' AND e.appointment IN %s", (tuple(appointments),))
                frappe.db.sql('DELETE FROM tt_note_recipient WHERE appointment IN %s', (tuple(appointments),))
            frappe.db.sql("DELETE FROM tt_shared_change_consent WHERE kind='invitation' AND change_id IN %s", (tuple(plans),))
            frappe.db.sql('DELETE FROM tt_couple_participant WHERE plan IN %s', (tuple(plans),))
            frappe.db.sql('DELETE FROM tt_couple_plan WHERE id IN %s', (tuple(plans),))
        frappe.db.commit()
        base.Presentation.tearDownClass.__func__(cls)

    def consented_plan(self, book=True):
        prior = journey.rows('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],))
        self.reserved_before = int(prior[0].reserved) if prior else 0
        self.fund_patient('p1', 10000)
        offering = base.fixtures.Integration.offers['c1']
        type(self)._plan_sequence = getattr(type(self), '_plan_sequence', 0) + 1
        day, _, _ = self.make_schedule(day=base.day_offset(14 + type(self)._plan_sequence), mode='automatic')
        slot = self.slots(offering, day)[0]
        base.fixtures.login('p1')
        one = {'request':'First adult private intake'}
        invitation = couples.invite(offering, slot['start'], one['request'],
            {'name':False,'history':False}, one, True, secrets.token_hex(16))
        base.fixtures.login('p2')
        two = {'request':'Second adult private intake'}
        consent = couples.consent(invitation['token'], two['request'],
            {'name':False,'history':False}, two, True)
        self.assertNotIn(one['request'], json.dumps(consent))
        base.fixtures.login('p1')
        booked = couples.confirm(invitation['id']) if book else {'id':None}
        frappe.db.commit()
        return invitation, booked['id'], one, two

    def test_booking_notices_are_individual_and_neutral(self):
        from tele_tena import booking_notifications
        invitation,appointment,one,two=self.consented_plan()
        booking_notifications.create(appointment,'Booked')
        notices=journey.rows('SELECT user,event,channel,state FROM tt_booking_notice WHERE appointment=%s',(appointment,))
        self.assertEqual({item.user for item in notices},{base.fixtures.USERS[key] for key in ('p1','p2','c1')})
        self.assertEqual(len(notices),3)
        for key in ('p1','p2','c1'):
            base.fixtures.login(key)
            own=[item for item in booking_notifications.notices() if item.appointment==appointment]
            self.assertEqual(len(own),1)
            self.assertNotIn(one['request'],json.dumps(own,default=str))
            self.assertNotIn(two['request'],json.dumps(own,default=str))
            self.assertNotIn('patient',own[0]);self.assertNotIn('clinician',own[0])
        base.fixtures.login('admin')
        self.assertFalse(any(item.appointment==appointment for item in booking_notifications.notices()))

    def test_concurrent_couple_confirmation_reserves_once(self):
        invitation, _, _, _ = self.consented_plan(book=False)
        barrier = threading.Barrier(2)
        def confirm(_):
            base.fixtures.connect()
            try:
                base.fixtures.login('p1')
                barrier.wait(timeout=10)
                result = couples.confirm(invitation['id'])
                frappe.db.commit()
                return result['id']
            finally:
                frappe.destroy()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(confirm, (0, 1)))
        frappe.db.rollback()
        self.assertEqual(results[0], results[1])
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s',
                                    (base.fixtures.USERS['p1'],)).reserved, self.reserved_before + 600)
        self.assertEqual(len(journey.rows('SELECT id FROM tt_ledger WHERE reference=%s',
                                          ('booking:'+results[0],))), 1)

    def test_shared_extension_consents_and_payer_reservation(self):
        from tele_tena.api import extensions
        before = journey.rows('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],))
        previous_reserved = int(before[0].reserved) if before else 0
        _, appointment, _, _ = self.consented_plan()
        base.fixtures.login('c1')
        # Open only this owned test call; media is tested independently.
        with patch.object(consultations, '_window', return_value=True), patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid','key','secret')), patch('tele_tena.livekit.participant_token', return_value='test-only-token'):
            consultations.join(appointment)
        proposal = extensions.propose_extension(appointment, secrets.token_hex(16))
        base.fixtures.login('p1')
        self.assertTrue(extensions.respond_extension(appointment, proposal['id'], 'accept')['awaiting_participants'])
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],)).reserved, previous_reserved + 600)
        base.fixtures.login('p2')
        self.assertTrue(extensions.respond_extension(appointment, proposal['id'], 'accept')['awaiting_payer'])
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],)).reserved, previous_reserved + 600)
        base.fixtures.login('p1')
        self.assertEqual(extensions.respond_extension(appointment, proposal['id'], 'accept')['state'], 'Accepted')
        self.assertTrue(extensions.respond_extension(appointment, proposal['id'], 'accept')['idempotent'])
        self.assertEqual(len(journey.rows('SELECT id FROM tt_journal WHERE event_ref=%s', ('extension-reserve:'+proposal['id'],))), 1)
        base.fixtures.login('p2')
        with self.assertRaises(frappe.PermissionError):
            extensions.start_extension(appointment, proposal['id'])
        base.fixtures.login('c1')
        with patch('tele_tena.livekit.close_room'):
            consultations.end(appointment)
        # An accepted block that never started is released exactly once.
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],)).reserved, previous_reserved + 600)
        self.assertEqual(len(journey.rows('SELECT id FROM tt_journal WHERE event_ref=%s', ('extension-release:'+proposal['id'],))), 1)

    def test_started_shared_extension_settles_with_one_earning(self):
        from datetime import timedelta
        from tele_tena.api import extensions
        _, appointment, _, _ = self.consented_plan()
        base.fixtures.login('c1')
        with patch.object(consultations, '_window', return_value=True), patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid','key','secret')), patch('tele_tena.livekit.participant_token', return_value='test-only-token'):
            consultations.join(appointment)
        proposal = extensions.propose_extension(appointment, secrets.token_hex(16))
        base.fixtures.login('p2')
        extensions.respond_extension(appointment, proposal['id'], 'accept')
        base.fixtures.login('p1')
        extensions.respond_extension(appointment, proposal['id'], 'accept')
        base.fixtures.login('c1')
        block = journey.one('SELECT * FROM tt_consultation_extension WHERE id=%s', (proposal['id'],))
        with patch.object(extensions, '_now', return_value=block.start_after + timedelta(seconds=1)):
            self.assertEqual(extensions.start_extension(appointment, proposal['id'])['state'], 'Started')
            self.assertTrue(extensions.start_extension(appointment, proposal['id'])['idempotent'])
        with patch('tele_tena.livekit.close_room'):
            consultations.end(appointment)
        presentation.save_note_draft(appointment, 'Private fictional clinical note', '', summary_recipients=[])
        presentation.finalize_consultation(appointment, False)
        self.assertTrue(presentation.finalize_consultation(appointment, False)['idempotent'])
        earning = journey.one('SELECT gross_minor,state FROM tt_earning WHERE appointment=%s', (appointment,))
        self.assertEqual(earning.gross_minor, 600 + int(block.amount_minor))
        self.assertEqual(earning.state, 'Pending')
        self.assertEqual(journey.one('SELECT state FROM tt_consultation_extension WHERE id=%s', (proposal['id'],)).state, 'Settled')
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],)).reserved, self.reserved_before)
        self.assertEqual(len(journey.rows('SELECT id FROM tt_earning WHERE appointment=%s', (appointment,))), 1)

    def test_shared_reschedule_requires_all_three(self):
        before = journey.rows('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],))
        previous_reserved = int(before[0].reserved) if before else 0
        _, appointment, _, _ = self.consented_plan()
        item = journey.one('SELECT * FROM tt_appointment WHERE id=%s', (appointment,))
        day = item.start.date()
        slot = next(s for s in self.slots(item.offering, day) if journey.instant(s['start']) > item.end)
        base.fixtures.login('p1')
        proposal = presentation.propose_reschedule(appointment, slot['start'], secrets.token_hex(16))
        base.fixtures.login('p2')
        self.assertTrue(presentation.respond_to_reschedule(appointment, proposal['id'], 'accept')['awaiting_participants'])
        self.assertEqual(journey.one('SELECT start FROM tt_appointment WHERE id=%s', (appointment,)).start, item.start)
        base.fixtures.login('c1')
        self.assertEqual(presentation.respond_to_reschedule(appointment, proposal['id'], 'accept')['state'], 'Accepted')
        self.assertTrue(presentation.respond_to_reschedule(appointment, proposal['id'], 'accept')['idempotent'])
        self.assertEqual(journey.one('SELECT start FROM tt_appointment WHERE id=%s', (appointment,)).start, journey.instant(slot['start']))
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],)).reserved, previous_reserved + 600)
        self.assertEqual(len(journey.rows('SELECT id FROM tt_ledger WHERE reference=%s', ('booking:'+appointment,))), 1)

    def test_shared_reschedule_decline_and_expiry_keep_original(self):
        _, appointment, _, _ = self.consented_plan()
        item = journey.one('SELECT * FROM tt_appointment WHERE id=%s', (appointment,))
        slot = next(s for s in self.slots(item.offering, item.start.date()) if journey.instant(s['start']) > item.end)
        base.fixtures.login('p1')
        proposal = presentation.propose_reschedule(appointment, slot['start'], secrets.token_hex(16))
        base.fixtures.login('p2')
        self.assertEqual(presentation.respond_to_reschedule(appointment, proposal['id'], 'decline')['state'], 'Declined')
        base.fixtures.login('c1')
        with self.assertRaises(frappe.ValidationError):
            presentation.respond_to_reschedule(appointment, proposal['id'], 'accept')
        base.fixtures.login('p1')
        proposal = presentation.propose_reschedule(appointment, slot['start'], secrets.token_hex(16))
        # Controlled timing for only this owned proposal; no global clock change.
        frappe.db.sql('UPDATE tt_reschedule_proposal SET expires_at=UTC_TIMESTAMP(6)-INTERVAL 1 SECOND WHERE id=%s', (proposal['id'],))
        base.fixtures.login('p2')
        self.assertEqual(presentation.respond_to_reschedule(appointment, proposal['id'], 'accept')['state'], 'Expired')
        self.assertEqual(journey.one('SELECT start FROM tt_appointment WHERE id=%s', (appointment,)).start, item.start)

    def test_shared_reschedule_unavailable_after_votes(self):
        _, appointment, _, _ = self.consented_plan()
        item = journey.one('SELECT * FROM tt_appointment WHERE id=%s', (appointment,))
        slot = next(s for s in self.slots(item.offering, item.start.date()) if journey.instant(s['start']) > item.end)
        base.fixtures.login('p1')
        proposal = presentation.propose_reschedule(appointment, slot['start'], secrets.token_hex(16))
        base.fixtures.login('p2')
        presentation.respond_to_reschedule(appointment, proposal['id'], 'accept')
        base.fixtures.login('c1')
        # Real proposal revalidation, controlled disappearance of this slot.
        with patch('tele_tena.api.scheduling.validate_slot', side_effect=frappe.ValidationError):
            result = presentation.respond_to_reschedule(appointment, proposal['id'], 'accept')
        self.assertEqual(result['state'], 'Unavailable')
        self.assertEqual(journey.one('SELECT start FROM tt_appointment WHERE id=%s', (appointment,)).start, item.start)

    def test_invitation_decline_preserves_funds_and_hides_identity(self):
        invitation, _, _, _ = self.consented_plan(book=False)
        # This test's invitation already has consent; decline must not revoke it.
        base.fixtures.login('p2')
        with self.assertRaises(frappe.PermissionError):
            couples.decline_invitation(invitation['token'])
        base.fixtures.login('p1')
        source = journey.one('SELECT * FROM tt_couple_plan WHERE id=%s', (invitation['id'],))
        another = couples.invite(source.offering, journey.iso(source.start), 'New private invitation',
            {'name':False,'history':False}, {'request':'New private invitation'}, True, secrets.token_hex(16))
        before = journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],))
        base.fixtures.login('p2')
        self.assertEqual(couples.decline_invitation(another['token'])['state'], 'Declined')
        self.assertTrue(couples.decline_invitation(another['token'])['idempotent'])
        base.fixtures.login('p1')
        visible = couples.get_plan(another['id'])
        self.assertEqual(visible['state'], 'Declined')
        self.assertNotIn(base.fixtures.USERS['p2'], json.dumps(visible))
        self.assertEqual(journey.one('SELECT available,reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],)), before)

    def test_couple_consent_single_charge_and_recipient_isolation(self):
        invitation, appointment, one, two = self.consented_plan()
        self.assertTrue(couples.confirm(invitation['id'])['idempotent'])
        self.assertEqual(couples.get_plan(invitation['id'])['appointment'], appointment)
        base.fixtures.login('c2')
        with self.assertRaises(frappe.PermissionError):
            couples.get_plan(invitation['id'])
        base.fixtures.login('p1')
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],)).reserved, self.reserved_before + 600)
        base.fixtures.login('p2')
        detail = presentation.appointment_detail(appointment)
        self.assertEqual(detail['disclosure'], two)
        self.assertNotIn(one['request'], json.dumps(detail, default=str))
        self.assertFalse(detail['you_pay'])
        with self.assertRaises(frappe.PermissionError):
            clinic_access.eligible_clinics_for_summary(appointment)
        base.fixtures.login('c2')
        with self.assertRaises(frappe.PermissionError):
            presentation.appointment_detail(appointment)
        base.fixtures.login('c1')
        people = couples.participants(invitation['id'])
        recipient = next(p.id for p in people if p.user == base.fixtures.USERS['p2'])
        # Provider operations mocked here; real hosted media is a separate gate.
        with patch.object(consultations, '_window', return_value=True), patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid','key','secret')), patch('tele_tena.livekit.participant_token', return_value='private-test-token'):
            joined = consultations.join(appointment)
        self.assertEqual(len(joined['participants']), 3)
        with patch('tele_tena.livekit.close_room') as close:
            consultations.end(appointment)
            self.assertEqual(len(set(close.call_args.args[1])), 3)
        presentation.save_note_draft(appointment, 'Clinician private note', 'Summary for second adult', summary_recipients=[recipient])
        presentation.finalize_consultation(appointment, True)
        self.assertTrue(presentation.finalize_consultation(appointment, True)['idempotent'])
        self.assertEqual(len(journey.rows('SELECT id FROM tt_earning WHERE appointment=%s',(appointment,))), 1)
        base.fixtures.login('p1')
        first = presentation.appointment_detail(appointment)
        self.assertEqual(couples.my_plans()[0]['appointment_state'], 'Completed')
        self.assertNotIn('Summary for second adult', json.dumps(first, default=str))
        self.assertNotIn('Clinician private note', json.dumps(first, default=str))
        base.fixtures.login('p2')
        second = presentation.appointment_detail(appointment)
        self.assertIn('Summary for second adult', json.dumps(second, default=str))
        self.assertNotIn('Clinician private note', json.dumps(second, default=str))
        self.assertNotIn(base.fixtures.USERS['p1'], json.dumps(second, default=str))
        before = len(couples.participants(invitation['id']))
        v1_33_couples_consultations.execute()
        v1_34_shared_change_consent.execute()
        self.assertEqual(len(couples.participants(invitation['id'])), before)

    def test_couple_withdrawal_closure_failure_retry_keeps_reservation(self):
        from datetime import datetime, timedelta, timezone
        invitation, appointment, _, _ = self.consented_plan()
        base.fixtures.login('c1')
        with patch.object(consultations, '_window', return_value=True), patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid','key','secret')), patch('tele_tena.livekit.participant_token', return_value='private-test-token'):
            consultations.join(appointment)
        # Clock control leaves the stored scheduled instants and fee policy intact.
        after_start = journey.one('SELECT start FROM tt_appointment WHERE id=%s',(appointment,)).start + timedelta(minutes=1)
        class ControlledClock:
            @staticmethod
            def now(tz=None):
                return after_start.replace(tzinfo=timezone.utc)
        base.fixtures.login('p2')
        with patch.object(couples, 'datetime', ControlledClock), patch('tele_tena.livekit.close_room', side_effect=RuntimeError('provider unavailable')):
            with self.assertRaises(frappe.ValidationError):
                couples.withdraw(invitation['id'])
        self.assertFalse(couples.ready(appointment))
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s',(base.fixtures.USERS['p1'],)).reserved, self.reserved_before + 600)
        with patch('tele_tena.livekit.close_room') as close:
            self.assertTrue(couples.withdraw(invitation['id'])['idempotent'])
            self.assertEqual(len(set(close.call_args.args[1])), 3)
        base.fixtures.login('c1')
        presentation.save_note_draft(appointment, 'Private', '', summary_recipients=[])
        with self.assertRaises(frappe.ValidationError):
            presentation.finalize_consultation(appointment, False)
        self.assertEqual(journey.rows('SELECT id FROM tt_earning WHERE appointment=%s',(appointment,)), [])
        with self.assertRaises(frappe.ValidationError):
            consultations.join(appointment)

    def test_individual_followup_draft_and_amendment_are_recipient_scoped(self):
        invitation, appointment, _, _ = self.consented_plan()
        base.fixtures.login('c1')
        recipient = next(p.id for p in couples.participants(invitation['id']) if p.user == base.fixtures.USERS['p2'])
        with patch.object(consultations, '_window', return_value=True), patch('tele_tena.livekit._credentials', return_value=('wss://example.invalid','key','secret')), patch('tele_tena.livekit.participant_token', return_value='private-test-token'):
            consultations.join(appointment)
        with patch('tele_tena.livekit.close_room'):
            consultations.end(appointment)
        with self.assertRaises(frappe.ValidationError):
            presentation.save_note_draft(appointment,'Private','',followup_text='Private next step')
        with self.assertRaises(frappe.ValidationError):
            presentation.save_note_draft(appointment,'Private','',followup_text='Private next step',followup_recipient='unknown')
        first = presentation.save_note_draft(appointment,'Private','',followup_text='Private next step',followup_recipient=recipient)
        self.assertTrue(presentation.save_note_draft(appointment,'Private','',followup_text='Private next step',followup_recipient=recipient)['idempotent'])
        base.fixtures.login('p2')
        self.assertEqual(presentation.appointment_detail(appointment)['individual_followup_revisions'], [])
        base.fixtures.login('c1')
        # Omitted optional fields from an older client preserve the saved content.
        self.assertTrue(presentation.save_note_draft(appointment,'Private','')['idempotent'])
        self.assertEqual(presentation.appointment_detail(appointment)['private_note']['revision'],first['revision'])
        presentation.finalize_consultation(appointment)
        presentation.finalize_consultation(appointment)
        base.fixtures.login('p1')
        self.assertNotIn('Private next step', json.dumps(presentation.appointment_detail(appointment),default=str))
        base.fixtures.login('p2')
        visible = presentation.appointment_detail(appointment)['individual_followup_revisions']
        self.assertEqual(len(visible),1)
        self.assertEqual(visible[0]['text'],'Private next step')
        self.assertNotIn('private_note',presentation.appointment_detail(appointment))
        base.fixtures.login('c1')
        presentation.save_note_draft(appointment,'Private','',followup_text='Amended next step',followup_recipient=recipient)
        presentation.finalize_consultation(appointment)
        base.fixtures.login('p2')
        self.assertEqual([r['text'] for r in presentation.appointment_detail(appointment)['individual_followup_revisions']],['Private next step','Amended next step'])
        self.assertEqual(len(journey.rows('SELECT id FROM tt_earning WHERE appointment=%s',(appointment,))),1)
        base.fixtures.login('c2')
        with self.assertRaises(frappe.PermissionError):
            presentation.appointment_detail(appointment)
        v1_35_individual_followup.execute()
        self.assertEqual(len(journey.rows('SELECT revision FROM tt_note_followup WHERE appointment=%s AND published=1',(appointment,))),2)

    def test_couple_withdrawal_before_start_releases_once(self):
        invitation, appointment, _, _ = self.consented_plan()
        base.fixtures.login('p2')
        couples.withdraw(invitation['id'])
        self.assertTrue(couples.withdraw(invitation['id'])['idempotent'])
        with self.assertRaises(frappe.PermissionError):
            presentation.appointment_detail(appointment)
        item = journey.one('SELECT state FROM tt_appointment WHERE id=%s',(appointment,))
        self.assertEqual(item.state, 'Cancelled')
        wallet = journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s',(base.fixtures.USERS['p1'],))
        self.assertEqual(wallet.reserved, self.reserved_before)
        self.assertEqual(len(journey.rows('SELECT id FROM tt_ledger WHERE reference=%s',('release:'+appointment,))), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
