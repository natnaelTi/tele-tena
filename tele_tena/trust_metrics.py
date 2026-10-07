"""Small, explicit trust indicators. Patient experience is not clinical efficacy."""
from decimal import Decimal, ROUND_HALF_UP

SESSION_EXPERIENCE_VERSION = 'session-experience-v1'
SESSION_EXPERIENCE_WINDOW_DAYS = 365
SESSION_EXPERIENCE_MINIMUM_SAMPLE = 5


def summarize_session_experience(sample_count, mean_rating):
    """Return a privacy-preserving, sample-aware patient experience indicator."""
    count = max(0, int(sample_count or 0))
    if count < SESSION_EXPERIENCE_MINIMUM_SAMPLE or mean_rating is None:
        return {
            'status': 'new' if count == 0 else 'more_feedback_needed',
            'sample_count': count,
            'average': None,
            'metric_version': SESSION_EXPERIENCE_VERSION,
            'observation_window_days': SESSION_EXPERIENCE_WINDOW_DAYS,
            'minimum_sample': SESSION_EXPERIENCE_MINIMUM_SAMPLE,
        }
    average = float(Decimal(str(mean_rating)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
    return {
        'status': 'available',
        'sample_count': count,
        'average': average,
        'metric_version': SESSION_EXPERIENCE_VERSION,
        'observation_window_days': SESSION_EXPERIENCE_WINDOW_DAYS,
        'minimum_sample': SESSION_EXPERIENCE_MINIMUM_SAMPLE,
    }
