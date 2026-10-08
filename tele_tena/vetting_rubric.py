"""Versioned, human-led scope review criteria.

The current version is intentionally proposed, not medically approved. Adding a
new version requires a code-reviewed immutable definition; scores never decide
scope approval and never override mandatory reviewer gates.
"""
import hashlib
import json

RUBRICS = {
    'proposed-1.0': {
        'status': 'Proposed',
        'title': 'Human-led scope vetting rubric',
        'approval_note': 'Proposed for medical-lead review; not an approved credentialing standard.',
        'scored_criteria': [
            {'key': 'scope_education', 'label': 'Scope-relevant education'},
            {'key': 'supervised_experience', 'label': 'Supervised clinical experience'},
            {'key': 'approach_training', 'label': 'Training in selected approach'},
            {'key': 'adult_population', 'label': 'Adult population experience'},
            {'key': 'ethics_safeguarding', 'label': 'Ethics, privacy and safeguarding understanding'},
            {'key': 'assessment_interview', 'label': 'Consultation or assessment interview'},
        ],
        'score_min': 0,
        'score_max': 3,
        'decision_rule': 'Scores organize evidence only. Human reviewers apply mandatory gates and record each scope decision.',
    },
}


def definition(version='proposed-1.0'):
    try:
        rubric = RUBRICS[version]
    except KeyError:
        raise ValueError('Unknown vetting rubric version') from None
    return {'version': version, **rubric}


def canonical_json(version='proposed-1.0'):
    value = definition(version)
    value.pop('status', None)
    return json.dumps(value, separators=(',', ':'), sort_keys=True)


def digest(version='proposed-1.0'):
    return hashlib.sha256(canonical_json(version).encode()).hexdigest()
