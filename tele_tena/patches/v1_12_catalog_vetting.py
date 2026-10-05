"""Add controlled adult-care catalog definitions without changing history."""
import frappe


CATALOG_VERSION = 'tele-tena-adult-catalog-1'
SOURCES = (
    'WHO mhGAP guideline, third edition (2023); https://www.who.int/publications/i/item/9789240084278',
    'APA psychotherapy approaches; https://www.apa.org/topics/psychotherapy/approaches',
    'Ethiopia Ministry of Health licensing references require local reviewer interpretation.',
)


def _seed_doctype(doctype, key, fields):
    if frappe.db.exists(doctype, key):
        return
    frappe.get_doc({'doctype': doctype, 'catalog_key': key, **fields}).insert()


def execute():
    # Newly introduced service definitions are drafts. Existing services remain
    # historical/review fixtures, still linked to their original appointments.
    if frappe.db.has_column('Tele Tena Service', 'catalog_status'):
        frappe.db.sql("UPDATE `tabTele Tena Service` SET catalog_status='Legacy test' WHERE catalog_status IS NULL OR catalog_status=''")
    categories = {
        'psychotherapy': 'Psychotherapy', 'counseling': 'Counseling',
        'relationship-care': 'Relationship care', 'psychiatry': 'Psychiatric consultation',
    }
    for key, label in categories.items():
        _seed_doctype('Tele Tena Service Category', key, dict(label_en=label,
            definition='Broad patient navigation category; not a diagnosis.',
            status='Draft', source_reference='Proposed category; pending medical lead review.',
            terminology_version=CATALOG_VERSION))
    formats = {'individual': 'Individual', 'couple': 'Couple', 'family': 'Family', 'group': 'Group'}
    for key, label in formats.items():
        _seed_doctype('Tele Tena Participant Format', key, dict(label_en=label,
            definition='Participant structure. Only individual workflows are supported for booking in this pilot.',
            status='Draft', source_reference=SOURCES[1], terminology_version=CATALOG_VERSION))
    approaches = {
        'cognitive-behavioral': 'Cognitive behavioral approach',
        'interpersonal': 'Interpersonal approach', 'psychodynamic': 'Psychodynamic approach',
        'humanistic': 'Humanistic/person-centered approach', 'behavioral': 'Behavioral approach',
        'integrative': 'Integrative approach', 'problem-management': 'Problem-management support',
        'stress-management': 'Stress-management approach', 'supportive-counseling': 'Supportive counseling',
    }
    for key, label in approaches.items():
        _seed_doctype('Tele Tena Treatment Approach', key, dict(label_en=label,
            definition='Controlled approach term; selection does not establish competence or authorize a service scope.',
            evidence_requirements='Applicant evidence is reviewed individually under proposed rubric v1.0.',
            status='Draft', source_reference='; '.join(SOURCES[:2]), terminology_version=CATALOG_VERSION))
    concerns = {
        'anxiety-related': 'Anxiety-related difficulties', 'low-mood': 'Low mood', 'stress': 'Stress',
        'grief-loss': 'Grief and loss', 'life-transitions': 'Life transitions',
        'relationship-difficulties': 'Relationship difficulties', 'communication': 'Communication concerns',
        'premarital-preparation': 'Premarital preparation',
    }
    for key, label in concerns.items():
        _seed_doctype('Tele Tena Support Topic', key, dict(label_en=label,
            definition='Patient-facing navigation term; not a diagnosis or clinical inference.',
            status='Draft', source_reference=SOURCES[0], terminology_version=CATALOG_VERSION))
    services = [
        ('initial-psychotherapy', 'Initial psychotherapy consultation', 'psychotherapy'),
        ('ongoing-psychotherapy', 'Ongoing individual psychotherapy', 'psychotherapy'),
        ('individual-counselling', 'Individual counseling', 'counseling'),
        ('stress-adjustment-support', 'Stress and life-change support', 'counseling'),
        ('grief-support', 'Grief and bereavement support', 'counseling'),
        ('relationship-counselling', 'Relationship counseling', 'relationship-care'),
        ('premarital-counselling', 'Premarital counseling', 'relationship-care'),
        ('separation-support', 'Support during separation or divorce', 'relationship-care'),
        ('psychiatric-assessment', 'Psychiatric assessment', 'psychiatry'),
        ('psychiatric-follow-up', 'Psychiatric follow-up', 'psychiatry'),
    ]
    source = '; '.join(SOURCES)
    for key, label, category in services:
        if frappe.db.exists('Tele Tena Service', key):
            continue
        frappe.get_doc({'doctype': 'Tele Tena Service', 'service_key': key, 'service_label': label,
            'active': 0, 'catalog_status': 'Draft', 'category': category,
            'description': 'Proposed adult individual-care definition awaiting local clinical review.',
            'population_restriction': 'Adults only', 'participant_structure': 'individual',
            'supported_formats': 'audio\nvideo', 'definition_version': CATALOG_VERSION,
            'catalog_source': source, 'clinical_review_status': 'Not reviewed',
            'vetting_required': 1, 'required_workflows': 'individual-consultation\nprivate-notes\npatient-summary',
            'min_duration_minutes': 20, 'max_duration_minutes': 90}).insert()
    # A future schema illustrates safe extension without enabling diagnostics.
    if not frappe.db.exists('Tele Tena Service Attribute Definition', {'service': 'psychiatric-assessment', 'field_key': 'specimen_type'}):
        for key, label in (('specimen_type', 'Specimen type'),
                           ('preparation_requirements', 'Preparation requirements'),
                           ('expected_turnaround', 'Expected turnaround')):
            frappe.get_doc({'doctype': 'Tele Tena Service Attribute Definition',
                'service': 'psychiatric-assessment', 'definition_version': CATALOG_VERSION,
                'field_key': key, 'label_en': label, 'data_type': 'Text', 'visibility': 'Public metadata',
                'sensitivity': 'Ordinary', 'active': 0}).insert()
