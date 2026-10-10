"""Persisted two-adult authorization and single-charge regressions; synthetic only."""
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
from tele_tena.patches import v1_33_couples_consultations


class Couples(base.Presentation):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        v1_33_couples_consultations.execute()
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
                frappe.db.sql('DELETE FROM tt_note_recipient WHERE appointment IN %s', (tuple(appointments),))
            frappe.db.sql('DELETE FROM tt_couple_participant WHERE plan IN %s', (tuple(plans),))
            frappe.db.sql('DELETE FROM tt_couple_plan WHERE id IN %s', (tuple(plans),))
        frappe.db.commit()
        super().tearDownClass()

    def consented_plan(self):
        self.fund_patient('p1', 10000)
        offering = base.fixtures.Integration.offers['c1']
        day, _, _ = self.make_schedule(mode='automatic')
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
        booked = couples.confirm(invitation['id'])
        frappe.db.commit()
        return invitation, booked['id'], one, two

    def test_couple_consent_single_charge_and_recipient_isolation(self):
        invitation, appointment, one, two = self.consented_plan()
        self.assertTrue(couples.confirm(invitation['id'])['idempotent'])
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s', (base.fixtures.USERS['p1'],)).reserved, 600)
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
        self.assertNotIn('Summary for second adult', json.dumps(first, default=str))
        self.assertNotIn('Clinician private note', json.dumps(first, default=str))
        base.fixtures.login('p2')
        second = presentation.appointment_detail(appointment)
        self.assertIn('Summary for second adult', json.dumps(second, default=str))
        self.assertNotIn('Clinician private note', json.dumps(second, default=str))
        self.assertNotIn(base.fixtures.USERS['p1'], json.dumps(second, default=str))
        before = len(couples.participants(invitation['id']))
        v1_33_couples_consultations.execute()
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
        self.assertEqual(journey.one('SELECT reserved FROM tt_wallet WHERE patient=%s',(base.fixtures.USERS['p1'],)).reserved, 600)
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
        self.assertEqual(wallet.reserved, 0)
        self.assertEqual(len(journey.rows('SELECT id FROM tt_ledger WHERE reference=%s',('release:'+appointment,))), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
