"""Reviewer-owned, typed draft service definitions and attribute schemas.

This API edits only Draft definitions. Activating clinical terminology, granting
practice scopes, or enabling a care workflow remains a separate human decision.
"""
import re

import frappe
from frappe.utils import getdate

from tele_tena.api import journey

KEY_RE = re.compile(r'^[a-z][a-z0-9-]{1,79}$')
FIELD_RE = re.compile(r'^[a-z][a-z0-9_]{1,63}$')
FORMATS = {'audio', 'video', 'in_person'}
WORKFLOWS = {
    'individual-consultation', 'private-notes', 'patient-summary',
    'couples-consent', 'family-consent', 'group-consent', 'laboratory-order',
    'specimen-collection', 'result-review',
}
BOOKING_RULES = {'direct-booking', 'scheduled', 'immediate-request'}
APPLICABILITY = {'', 'always', 'scheduled-booking', 'open-request'}
POPULATIONS = {'Adults only', 'All ages', 'Not specified'}

SERVICE_FIELDS = (
    'service_key', 'service_label', 'category', 'description', 'service_label_am',
    'service_label_om', 'synonyms', 'professional_categories',
    'credential_requirements', 'population_restriction', 'participant_structure',
    'supported_formats', 'booking_rules', 'required_consent_schema',
    'location_jurisdiction_policy', 'required_workflows', 'definition_version',
    'catalog_source', 'effective_from', 'effective_until', 'min_duration_minutes',
    'max_duration_minutes', 'catalog_status', 'clinical_review_status',
    'active', 'vetting_required', 'immediate_care_enabled',
)


def _lines(value, allowed, label):
    values = [item.strip() for item in str(value or '').splitlines() if item.strip()]
    if len(values) != len(set(values)) or any(item not in allowed for item in values):
        journey.fail(f'Choose supported {label}.', 'catalog_invalid_value')
    return '\n'.join(values)


def _text(payload, key, label, limit, required=False):
    value = journey.text(payload.get(key, ''), limit, required=required)
    return value


def _date(value, label):
    if not value:
        return None
    try:
        return getdate(value)
    except Exception:
        journey.fail(f'Enter a valid {label}.', 'catalog_invalid_date')


def _integer(value, label):
    if isinstance(value, bool) or not re.fullmatch(r'-?[0-9]+', str(value or '0')):
        journey.fail(f'Enter a whole-number {label}.', 'catalog_invalid_attribute')
    result = int(value or 0)
    if not -2147483648 <= result <= 2147483647:
        journey.fail(f'The {label} is outside the supported range.', 'catalog_invalid_attribute')
    return result


@journey.query()
def definitions():
    journey.actor('Tele Tena Approver')
    services = frappe.db.sql('''SELECT name AS id,service_key,service_label,category,
        description,service_label_am,service_label_om,synonyms,professional_categories,
        credential_requirements,population_restriction,participant_structure,
        supported_formats,booking_rules,required_consent_schema,
        location_jurisdiction_policy,required_workflows,definition_version,catalog_source,
        effective_from,effective_until,min_duration_minutes,max_duration_minutes,
        catalog_status,clinical_review_status,active,vetting_required,immediate_care_enabled
        FROM `tabTele Tena Service` ORDER BY catalog_status,service_label,name''', as_dict=True)
    for item in services:
        item['attributes'] = frappe.db.sql('''SELECT name AS id,field_key,definition_version,
            label_en,label_am,label_om,data_type,allowed_values,required,minimum_value,
            maximum_value,visibility,sensitivity,applicability,filterable,matching_field,active
            FROM `tabTele Tena Service Attribute Definition`
            WHERE service=%s ORDER BY definition_version,field_key''', (item.id,), as_dict=True)
    return {
        'definitions': services,
        'categories': frappe.db.sql('''SELECT catalog_key AS id,label_en AS label,status
            FROM `tabTele Tena Service Category` ORDER BY label_en''', as_dict=True),
        'participant_formats': frappe.db.sql('''SELECT catalog_key AS id,label_en AS label,status
            FROM `tabTele Tena Participant Format` ORDER BY label_en''', as_dict=True),
        'bookable_workflows': ['individual-consultation', 'private-notes', 'patient-summary'],
        'supported_formats': sorted(FORMATS),
    }


@journey.command
def save_draft_definition(payload):
    journey.actor('Tele Tena Approver')
    if isinstance(payload, str):
        try:
            import json
            payload = json.loads(payload)
        except (ValueError, TypeError):
            journey.fail('Review the service definition fields.', 'catalog_invalid_payload')
    if not isinstance(payload, dict):
        journey.fail('Review the service definition fields.', 'catalog_invalid_payload')
    unknown = set(payload) - set(SERVICE_FIELDS) - {'id'}
    if unknown:
        journey.fail('This definition contains unsupported fields.', 'catalog_invalid_payload')
    key = _text(payload, 'service_key', 'service identifier', 80, True)
    if not KEY_RE.fullmatch(key):
        journey.fail('Use a stable lowercase service identifier.', 'catalog_invalid_key')
    service_id = payload.get('id') or key
    if service_id != key:
        journey.fail('A service identifier cannot be changed after creation.', 'catalog_key_immutable')
    existing = frappe.db.sql('''SELECT name,catalog_status,clinical_review_status,active
        FROM `tabTele Tena Service` WHERE name=%s FOR UPDATE''', (key,), as_dict=True)
    if existing and (existing[0].catalog_status != 'Draft' or existing[0].active or
                     existing[0].clinical_review_status != 'Not reviewed'):
        journey.fail('Only draft definitions can be edited here. Published and legacy definitions are preserved.',
                     'catalog_definition_immutable')
    category = _text(payload, 'category', 'category', 80, True)
    if not frappe.db.exists('Tele Tena Service Category', category):
        journey.fail('Choose a service category from the catalog.', 'catalog_category_unavailable')
    participant = _text(payload, 'participant_structure', 'participant format', 80, True)
    if not frappe.db.exists('Tele Tena Participant Format', participant):
        journey.fail('Choose a participant format from the catalog.', 'catalog_participant_unavailable')
    population = payload.get('population_restriction') or 'Adults only'
    if population not in POPULATIONS:
        journey.fail('Choose a supported population restriction.', 'catalog_invalid_value')
    formats = _lines(payload.get('supported_formats'), FORMATS, 'delivery formats')
    workflows = _lines(payload.get('required_workflows'), WORKFLOWS, 'required workflows')
    rules = _lines(payload.get('booking_rules'), BOOKING_RULES, 'booking rules')
    min_duration = journey.integer(str(payload.get('min_duration_minutes') or 0), 0, 240)
    max_duration = journey.integer(str(payload.get('max_duration_minutes') or 0), 0, 240)
    if bool(min_duration) != bool(max_duration) or (min_duration and min_duration > max_duration):
        journey.fail('Set both duration limits, with the minimum no greater than the maximum.',
                     'catalog_duration_range')
    effective_from = _date(payload.get('effective_from'), 'effective date')
    effective_until = _date(payload.get('effective_until'), 'end date')
    if effective_from and effective_until and effective_until < effective_from:
        journey.fail('The end date must be on or after the effective date.', 'catalog_date_range')
    version = _text(payload, 'definition_version', 'definition version', 80, True)
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,79}', version):
        journey.fail('Use a version label with lowercase letters, numbers, dots, or hyphens.',
                     'catalog_invalid_version')
    values = {
        'service_key': key,
        'service_label': _text(payload, 'service_label', 'service name', 120, True),
        'category': category,
        'description': _text(payload, 'description', 'professional description', 2000),
        'service_label_am': _text(payload, 'service_label_am', 'Amharic label', 120),
        'service_label_om': _text(payload, 'service_label_om', 'Afaan Oromo label', 120),
        'synonyms': _text(payload, 'synonyms', 'search terms', 1000),
        'professional_categories': _text(payload, 'professional_categories', 'professional categories', 1000),
        'credential_requirements': _text(payload, 'credential_requirements', 'credential requirements', 2000),
        'population_restriction': population,
        'participant_structure': participant,
        'supported_formats': formats,
        'booking_rules': rules,
        'required_consent_schema': _text(payload, 'required_consent_schema', 'consent schema', 80),
        'location_jurisdiction_policy': _text(payload, 'location_jurisdiction_policy', 'jurisdiction policy', 80),
        'required_workflows': workflows,
        'definition_version': version,
        'catalog_source': _text(payload, 'catalog_source', 'source reference', 2000),
        'effective_from': effective_from,
        'effective_until': effective_until,
        'min_duration_minutes': min_duration,
        'max_duration_minutes': max_duration,
        'catalog_status': 'Draft',
        'clinical_review_status': existing[0].clinical_review_status if existing else 'Not reviewed',
        'active': 0,
        'vetting_required': 1,
        'immediate_care_enabled': 0,
    }
    if existing:
        doc = frappe.get_doc('Tele Tena Service', key)
        for field, value in values.items():
            setattr(doc, field, value)
        doc.save()
    else:
        frappe.get_doc({'doctype': 'Tele Tena Service', **values}).insert()
    return {'id': key, 'status': 'Draft', 'bookable': False, 'definition_version': version}


@journey.command
def submit_for_clinical_review(service):
    journey.actor('Tele Tena Approver')
    service = journey.text(service, 80)
    frappe.db.sql('SELECT name FROM `tabTele Tena Service` WHERE name=%s FOR UPDATE', (service,))
    doc = frappe.get_doc('Tele Tena Service', service)
    if doc.catalog_status != 'Draft' or doc.active:
        journey.fail('Only draft service definitions can enter terminology review.',
                     'catalog_definition_immutable')
    if not doc.service_label or not doc.description or not doc.catalog_source:
        journey.fail('Add a name, professional description, and source reference before review.',
                     'catalog_required_fields')
    if doc.clinical_review_status == 'Approved':
        journey.fail('Clinical review approval is recorded separately.', 'catalog_review_separate')
    if doc.clinical_review_status != 'In review':
        doc.clinical_review_status = 'In review'
        doc.save()
    return {'id': service, 'status': doc.clinical_review_status, 'bookable': False}


@journey.command
def save_attribute_definition(service, payload):
    journey.actor('Tele Tena Approver')
    service = journey.text(service, 80)
    frappe.db.sql('SELECT name FROM `tabTele Tena Service` WHERE name=%s FOR UPDATE', (service,))
    parent = frappe.get_doc('Tele Tena Service', service)
    if parent.catalog_status != 'Draft' or parent.active or parent.clinical_review_status != 'Not reviewed':
        journey.fail('Attributes can be edited only while the service is a draft.',
                     'catalog_definition_immutable')
    if isinstance(payload, str):
        try:
            import json
            payload = json.loads(payload)
        except (ValueError, TypeError):
            journey.fail('Review the attribute fields.', 'catalog_invalid_attribute')
    if not isinstance(payload, dict):
        journey.fail('Review the attribute fields.', 'catalog_invalid_attribute')
    allowed = {'field_key','label_en','label_am','label_om','data_type','allowed_values',
               'required','minimum_value','maximum_value','visibility','sensitivity',
               'applicability','filterable','matching_field','active'}
    if set(payload) - allowed:
        journey.fail('This attribute contains unsupported fields.', 'catalog_invalid_attribute')
    key = _text(payload, 'field_key', 'attribute key', 64, True)
    if not FIELD_RE.fullmatch(key):
        journey.fail('Use a stable lowercase attribute key.', 'catalog_invalid_attribute')
    data_type = payload.get('data_type')
    if data_type not in {'Text','Integer','Date','Boolean','Choice'}:
        journey.fail('Choose a supported attribute type.', 'catalog_invalid_attribute')
    choices = _lines(payload.get('allowed_values'), {v.strip() for v in str(payload.get('allowed_values') or '').splitlines() if v.strip()}, 'choice values')
    choice_values = [v for v in choices.splitlines() if v]
    if data_type == 'Choice' and not choice_values:
        journey.fail('Add at least one allowed value for a choice field.', 'catalog_choice_required')
    if data_type != 'Choice' and choice_values:
        journey.fail('Allowed values are only used by choice fields.', 'catalog_invalid_attribute')
    minimum = _integer(payload.get('minimum_value') or 0, 'minimum')
    maximum = _integer(payload.get('maximum_value') or 0, 'maximum')
    if (minimum or maximum) and data_type != 'Integer':
        journey.fail('Minimum and maximum values apply only to integer fields.', 'catalog_invalid_attribute')
    if minimum and maximum and minimum > maximum:
        journey.fail('Minimum must be less than or equal to maximum.', 'catalog_invalid_attribute')
    visibility = payload.get('visibility')
    sensitivity = payload.get('sensitivity')
    if visibility not in {'Public metadata','Clinician only','Patient private','Reviewer only'}:
        journey.fail('Choose a supported visibility.', 'catalog_invalid_attribute')
    if sensitivity not in {'Ordinary','Sensitive','Clinical'}:
        journey.fail('Choose a supported sensitivity.', 'catalog_invalid_attribute')
    filterable = journey.boolean(payload.get('filterable', False))
    matching = journey.boolean(payload.get('matching_field', False))
    if (filterable or matching) and (visibility != 'Public metadata' or sensitivity != 'Ordinary'):
        journey.fail('Sensitive or private attributes cannot be used in discovery or matching.',
                     'catalog_private_matching_field')
    applicable = payload.get('applicability') or ''
    if applicable not in APPLICABILITY:
        journey.fail('Choose a supported applicability condition.', 'catalog_invalid_attribute')
    existing = frappe.db.sql('''SELECT name FROM `tabTele Tena Service Attribute Definition`
        WHERE service=%s AND definition_version=%s AND field_key=%s FOR UPDATE''',
        (service, parent.definition_version, key), as_dict=True)
    values = {
        'service': service, 'definition_version': parent.definition_version,
        'field_key': key,
        'label_en': _text(payload, 'label_en', 'English attribute label', 120, True),
        'label_am': _text(payload, 'label_am', 'Amharic attribute label', 120),
        'label_om': _text(payload, 'label_om', 'Afaan Oromo attribute label', 120),
        'data_type': data_type, 'allowed_values': choices,
        'required': int(journey.boolean(payload.get('required', False))),
        'minimum_value': minimum or None, 'maximum_value': maximum or None,
        'visibility': visibility, 'sensitivity': sensitivity,
        'applicability': applicable, 'filterable': int(filterable),
        'matching_field': int(matching), 'active': int(journey.boolean(payload.get('active', True))),
    }
    if existing:
        doc = frappe.get_doc('Tele Tena Service Attribute Definition', existing[0].name)
        for field, value in values.items():
            setattr(doc, field, value)
        doc.save()
    else:
        frappe.get_doc({'doctype': 'Tele Tena Service Attribute Definition', **values}).insert()
    return {'service': service, 'field_key': key, 'definition_version': parent.definition_version,
            'active': bool(values['active'])}
