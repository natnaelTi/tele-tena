"""Run without Bench: python -m unittest discover -s tests -p offer_status_unit.py."""
import unittest
from datetime import datetime, timedelta
from tele_tena.offer_status import effective_offer_state, offer_patient_label


class OfferStatus(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 7, 9, 0)
        self.future = self.now + timedelta(minutes=5)

    def test_pending_offer_expires_without_a_scheduler_write(self):
        self.assertEqual(effective_offer_state('Active', 'Open', self.now, self.now), 'Expired')
        self.assertEqual(effective_offer_state('Active', 'Open', self.future, self.now), 'Active')

    def test_explicit_outcomes_survive_time_and_request_changes(self):
        for state in ('Accepted', 'Declined', 'Withdrawn', 'Superseded', 'Expired'):
            self.assertEqual(effective_offer_state(state, 'Cancelled', self.now, self.future), state)

    def test_closed_request_has_no_active_offer(self):
        for state in ('Matched', 'Cancelled', 'Expired'):
            self.assertEqual(effective_offer_state('Active', state, self.future, self.now), 'Superseded')

    def test_snapshot_is_the_only_identity_source(self):
        self.assertEqual(offer_patient_label({'request':'Synthetic request','history':'Private'}), 'Patient · alias')
        self.assertEqual(offer_patient_label({'name':'Chosen shared name'}), 'Chosen shared name')
        self.assertEqual(len(offer_patient_label({'name':'x'*200})), 120)
