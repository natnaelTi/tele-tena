import unittest

from tele_tena.trust_metrics import (
    summarize_clinician_cancellations,
    summarize_response_behavior,
    summarize_session_experience,
)


class SessionExperienceMetric(unittest.TestCase):
    def test_hides_aggregate_below_five_completed_ratings(self):
        for count in range(5):
            metric = summarize_session_experience(count, 4.7 if count else None)
            self.assertIsNone(metric['average'])
            self.assertEqual(metric['status'], 'new' if count == 0 else 'more_feedback_needed')
            self.assertEqual(metric['sample_count'], count)

    def test_shows_separate_patient_experience_with_sample_size(self):
        metric = summarize_session_experience(7, 4.7142857)
        self.assertEqual(metric['average'], 4.7)
        self.assertEqual(metric['status'], 'available')
        self.assertEqual(metric['sample_count'], 7)
        self.assertEqual(metric['observation_window_days'], 365)
        self.assertEqual(metric['metric_version'], 'session-experience-v1')
        self.assertEqual(summarize_session_experience(5, '4.65')['average'], 4.7)

    def test_response_rate_counts_only_the_supplied_presented_request_population(self):
        self.assertIsNone(summarize_response_behavior(4, 3)['rate_percent'])
        metric = summarize_response_behavior(5, 3)
        self.assertEqual(metric['rate_percent'], 60.0)
        self.assertEqual(metric['response_count'], 3)
        self.assertEqual(metric['observation_window_days'], 90)
        with self.assertRaises(ValueError):
            summarize_response_behavior(2, 3)

    def test_reliability_uses_attributed_cancellations_and_hides_small_sample_rate(self):
        self.assertIsNone(summarize_clinician_cancellations(2, 1)['rate_percent'])
        metric = summarize_clinician_cancellations(3, 2)
        self.assertEqual(metric['rate_percent'], 40.0)
        self.assertEqual(metric['sample_count'], 5)
        self.assertEqual(metric['clinician_cancelled_count'], 2)
        self.assertEqual(metric['observation_window_days'], 365)


if __name__ == '__main__':
    unittest.main()
