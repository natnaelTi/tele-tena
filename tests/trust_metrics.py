import unittest

from tele_tena.trust_metrics import summarize_session_experience


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


if __name__ == '__main__':
    unittest.main()
