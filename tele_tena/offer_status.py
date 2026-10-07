"""Presentation states derived from persisted offer and request facts."""


def effective_offer_state(offer_state, request_state, valid_until, current_time):
    # Preserve accepted and explicitly closed outcomes even after their expiry.
    if offer_state != 'Active':
        return offer_state
    if valid_until <= current_time:
        return 'Expired'
    if request_state != 'Open':
        return 'Superseded'
    return 'Active'


def offer_patient_label(disclosure):
    # The snapshot is the only identity source. Never use the account profile.
    return str(disclosure.get('name') or 'Patient · alias')[:120]
