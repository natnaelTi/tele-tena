"""Small, explicit trust indicators. Patient experience is not clinical efficacy."""
from decimal import Decimal, ROUND_HALF_UP

SESSION_EXPERIENCE_VERSION = 'session-experience-v1'
SESSION_EXPERIENCE_WINDOW_DAYS = 365
SESSION_EXPERIENCE_MINIMUM_SAMPLE = 5
RESPONSE_BEHAVIOR_VERSION = 'immediate-request-response-v1'
RESPONSE_BEHAVIOR_WINDOW_DAYS = 90
CLINICIAN_CANCELLATION_VERSION = 'clinician-cancellation-v1'
CLINICIAN_CANCELLATION_WINDOW_DAYS = 365
OPERATIONAL_MINIMUM_SAMPLE = 5


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


def summarize_response_behavior(presented_count, offered_count):
    """Offer response among immediate requests fetched by an available clinician."""
    sample = max(0, int(presented_count or 0))
    responses = max(0, int(offered_count or 0))
    if responses > sample:
        raise ValueError('Response count cannot exceed eligible requests presented')
    rate = None
    if sample >= OPERATIONAL_MINIMUM_SAMPLE:
        rate = float((Decimal(responses * 100) / Decimal(sample)).quantize(
            Decimal('0.1'), rounding=ROUND_HALF_UP))
    return {
        'status': 'available' if rate is not None else ('new' if sample == 0 else 'more_data_needed'),
        'sample_count': sample,
        'response_count': responses,
        'rate_percent': rate,
        'metric_version': RESPONSE_BEHAVIOR_VERSION,
        'observation_window_days': RESPONSE_BEHAVIOR_WINDOW_DAYS,
        'minimum_sample': OPERATIONAL_MINIMUM_SAMPLE,
    }


def summarize_clinician_cancellations(completed_count, clinician_cancelled_count):
    """Count only completed sessions and clinician-attributed cancellations."""
    completed = max(0, int(completed_count or 0))
    cancelled = max(0, int(clinician_cancelled_count or 0))
    sample = completed + cancelled
    rate = None
    if cancelled > sample:
        raise ValueError('Clinician cancellations cannot exceed the observation count')
    if sample >= OPERATIONAL_MINIMUM_SAMPLE:
        rate = float((Decimal(cancelled * 100) / Decimal(sample)).quantize(
            Decimal('0.1'), rounding=ROUND_HALF_UP))
    return {
        'status': 'available' if rate is not None else ('new' if sample == 0 else 'more_data_needed'),
        'sample_count': sample,
        'clinician_cancelled_count': cancelled,
        'rate_percent': rate,
        'metric_version': CLINICIAN_CANCELLATION_VERSION,
        'observation_window_days': CLINICIAN_CANCELLATION_WINDOW_DAYS,
        'minimum_sample': OPERATIONAL_MINIMUM_SAMPLE,
    }
