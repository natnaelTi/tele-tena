"""Human-led professional and per-service scope vetting."""
import json
import uuid

import frappe

from tele_tena.api import journey
from tele_tena.api.journey import actor, fail, integer, one, rows, text

RUBRIC_VERSION = 'proposed-1.0'
APPLICANT_FIELDS = {
    'professional_category': 80, 'qualification': 180, 'issuing_institution': 180,
    'registration_number': 100, 'issuing_authority': 180, 'jurisdiction': 120,
    'credential_expiry': 10, 'experience_years': 2, 'approach_keys': 800,
    'population_adults': 1, 'independent_practice': 1, 'clinic_affiliations': 1000,
    'relevant_training': 2000, 'applicant_statement': 2000, 'applicant_response': 2000,
}


def _applicant(user=None):
    user = user or actor()
    if user == 'Guest' or not set(frappe.get_roles(user)).intersection({'Tele Tena Applicant', 'Tele Tena Clinician'}):
        frappe.throw('Clinician application access required', frappe.PermissionError)
    if not frappe.db.get_value('User', user, 'enabled'):
        frappe.throw('Account unavailable', frappe.PermissionError)
    if not rows("SELECT user FROM tt_profile WHERE user=%s AND kind='clinician'", (user,)):
        frappe.throw('Clinician profile required', frappe.PermissionError)
    return user


def _scope_application(user, service, lock=False):
    query = '''SELECT name FROM `tabTele Tena Vetting Scope Application`
        WHERE clinician=%s AND service=%s ORDER BY creation DESC LIMIT 1''' + (' FOR UPDATE' if lock else '')
    return rows(query, (user, service))


def _validated_form(values):
    if isinstance(values, str):
        try:
            values = json.loads(values)
        except ValueError:
            fail('Review the application fields and try again.')
    if not isinstance(values, dict) or set(values) - APPLICANT_FIELDS.keys():
        fail('Application contains unsupported fields.')
    result = {}
    for key, maximum in APPLICANT_FIELDS.items():
        if key not in values:
            continue
        value = values[key]
        if key in ('experience_years',):
            result[key] = integer(value, 0, 60)
        elif key in ('population_adults', 'independent_practice'):
            result[key] = int(journey.boolean(value))
        elif key == 'credential_expiry':
            if value and (not isinstance(value, str) or len(value) != 10):
                fail('Enter a valid credential expiry date.')
            result[key] = value or None
        elif key == 'approach_keys':
            keys = sorted(set(x.strip() for x in str(value or '').splitlines() if x.strip()))
            if len(keys) > 20 or any(not frappe.db.exists('Tele Tena Treatment Approach', {'catalog_key': x, 'status': 'Active'}) for x in keys):
                fail('Choose treatment approaches from the reviewed catalog only.')
            result[key] = '\n'.join(keys)
        else:
            result[key] = text(value or '', maximum, required=False)
    return result


@journey.query()
def my_scope_applications():
    user = actor()
    if 'Tele Tena Approver' in frappe.get_roles(user):
        result = rows('''SELECT a.*,p.display_name,s.service_label FROM `tabTele Tena Vetting Scope Application` a
            JOIN tt_profile p ON p.user=a.clinician JOIN `tabTele Tena Service` s ON s.name=a.service
            ORDER BY FIELD(a.status,'Submitted','Resubmitted','Clarification','Draft'),a.submitted_at''')
        for item in result:
            item.resume_uploaded = bool(rows('SELECT 1 FROM tt_resume_evidence WHERE clinician=%s', (item.clinician,)))
        return result
    user = _applicant(user)
    return rows('''SELECT a.name,a.service,s.service_label,a.status,a.professional_category,a.qualification,
        a.issuing_institution,a.registration_number,a.issuing_authority,a.jurisdiction,a.credential_expiry,
        a.experience_years,a.approach_keys,a.population_adults,a.independent_practice,a.clinic_affiliations,
        a.relevant_training,a.applicant_statement,a.applicant_response,a.clarification_request,
        a.decision_reason,a.restrictions,a.submitted_at,a.decided_at,a.rubric_version
        FROM `tabTele Tena Vetting Scope Application` a JOIN `tabTele Tena Service` s ON s.name=a.service
        WHERE a.clinician=%s ORDER BY a.modified DESC''', (user,))


@journey.query()
def vetting_services():
    user = actor()
    if not set(frappe.get_roles(user)).intersection({'Tele Tena Applicant', 'Tele Tena Clinician'}):
        frappe.throw('Clinician application access required', frappe.PermissionError)
    return rows("""SELECT name AS id,service_label AS label,category,description,definition_version
        FROM `tabTele Tena Service` WHERE active=1 AND catalog_status='Active' AND vetting_required=1
        ORDER BY service_label""")


@journey.command
def save_scope_application(service, values, submit=False):
    user = _applicant()
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    definition = one('''SELECT name,active,catalog_status,vetting_required FROM `tabTele Tena Service`
        WHERE name=%s''', (service,))
    if not definition.active or definition.catalog_status != 'Active' or not definition.vetting_required:
        fail('This service scope is not currently open for professional applications.', 'scope_not_open')
    form = _validated_form(values)
    existing = _scope_application(user, service, lock=True)
    if existing:
        prior = one('SELECT status FROM `tabTele Tena Vetting Scope Application` WHERE name=%s FOR UPDATE',
                    (existing[0].name,))
        if prior.status not in ('Draft', 'Clarification'):
            fail('This scope application is awaiting reviewer action.', 'scope_application_locked')
        name = existing[0].name
        prior_status = prior.status
    else:
        name = uuid.uuid4().hex
        prior_status = 'Draft'
    if submit:
        if not form.get('professional_category') or not form.get('qualification') or not form.get('issuing_institution'):
            fail('Add your professional category, qualification and issuing institution before submission.')
        if not form.get('population_adults'):
            fail('Confirm that this application is limited to adult care.')
        if not rows('SELECT clinician FROM tt_resume_evidence WHERE clinician=%s', (user,)):
            fail('Upload a PDF CV before submitting for review.', 'resume_required')
        status = 'Resubmitted' if prior_status == 'Clarification' else 'Submitted'
    else:
        status = prior_status
    now = frappe.utils.now_datetime()
    values = {**form, 'status': status, 'submitted_at': now if submit else None}
    if existing:
        updates = ','.join(f'`{key}`=%s' for key in values)
        frappe.db.sql(f'''UPDATE `tabTele Tena Vetting Scope Application` SET {updates},
            modified=%s,modified_by=%s WHERE name=%s AND clinician=%s AND service=%s
            AND status IN ('Draft','Clarification')''',
            (*values.values(), now, user, name, user, service))
    else:
        columns = ['name','owner','creation','modified','modified_by','docstatus','idx',
                   'clinician','service','rubric_version',*values.keys()]
        data = [name,user,now,now,user,0,0,user,service,RUBRIC_VERSION,*values.values()]
        placeholders = ','.join(['%s'] * len(columns))
        frappe.db.sql(f'''INSERT INTO `tabTele Tena Vetting Scope Application`
            ({','.join(f'`{column}`' for column in columns)}) VALUES ({placeholders})''', data)
    journey.audit(user, 'ScopeApplication', {'service': service, 'status': status})
    return {'name': name, 'status': status, 'submitted_at': str(now if submit else '')}


@journey.command
def review_scope_application(application, decision, identity_reviewed=False,
                             credential_verified=False, qualification_relevant=False,
                             experience_adequate=False, approach_evidence_reviewed=False,
                             adult_scope_appropriate=False, interview_completed=False,
                             findings='', restrictions=''):
    reviewer = actor('Tele Tena Approver')
    if decision not in ('Clarification', 'Approved', 'Rejected', 'Suspended', 'Expired'):
        fail('Choose a supported review decision.')
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    locked = rows('''SELECT name,clinician,service,status FROM `tabTele Tena Vetting Scope Application`
        WHERE name=%s FOR UPDATE''', (application,))
    if not locked:
        frappe.throw('Scope application unavailable', frappe.PermissionError)
    doc = locked[0]
    if doc.status not in ('Submitted', 'Resubmitted', 'Clarification', 'Approved'):
        fail('Only submitted scope applications can be reviewed.')
    findings = text(findings, 2000)
    restrictions = text(restrictions or '', 1000, required=False)
    flags = {key: int(journey.boolean(value)) for key, value in {
        'identity_reviewed': identity_reviewed, 'credential_verified': credential_verified,
        'qualification_relevant': qualification_relevant, 'experience_adequate': experience_adequate,
        'approach_evidence_reviewed': approach_evidence_reviewed,
        'adult_scope_appropriate': adult_scope_appropriate, 'interview_completed': interview_completed,
    }.items()}
    if decision == 'Approved':
        required = ('identity_reviewed', 'credential_verified', 'qualification_relevant',
                    'adult_scope_appropriate', 'interview_completed')
        if not all(flags[key] for key in required):
            fail('A mandatory identity, credential, scope or interview criterion has not passed.',
                 'vetting_mandatory_criterion_failed')
        if not flags['experience_adequate']:
            fail('Record adequate scope-relevant experience before approval.', 'vetting_mandatory_criterion_failed')
        service = one('SELECT vetting_required,clinical_review_status,active FROM `tabTele Tena Service` WHERE name=%s', (doc.service,))
        if not service.vetting_required or service.clinical_review_status != 'Approved' or not service.active:
            fail('The service definition has not completed clinical review.', 'catalog_not_approved')
    assessment = frappe.get_doc({'doctype': 'Tele Tena Vetting Assessment',
        'scope_application': doc.name, 'reviewer': reviewer, **flags, 'decision': decision,
        'findings': findings, 'restrictions': restrictions,
        'evidence_revision': (rows('SELECT revision FROM tt_resume_evidence WHERE clinician=%s', (doc.clinician,)) or [frappe._dict(revision=0)])[0].revision,
        'rubric_version': RUBRIC_VERSION, 'decided_at': frappe.utils.now_datetime()})
    frappe.local.tele_tena_vetting_assessment_action = True
    try:
        assessment.insert()
    finally:
        frappe.local.tele_tena_vetting_assessment_action = False
    frappe.db.sql('''UPDATE `tabTele Tena Vetting Scope Application`
        SET status=%s,reviewer=%s,decision_reason=%s,clarification_request=%s,
            restrictions=%s,decided_by=%s,decided_at=%s,modified=%s,modified_by=%s
        WHERE name=%s''', (decision, reviewer, findings,
        findings if decision == 'Clarification' else '', restrictions, reviewer,
        assessment.decided_at, assessment.decided_at, reviewer, doc.name))
    if decision == 'Approved':
        from tele_tena.api import journey as api
        api.review_service_scope(doc.clinician, doc.service, 'Approved', vetting_action=True)
    elif decision in ('Rejected', 'Suspended', 'Expired'):
        scopes = rows("SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s AND service=%s AND status='Approved' FOR UPDATE",
                      (doc.clinician, doc.service))
        for scope in scopes:
            scope_doc = frappe.get_doc('Tele Tena Service Scope', scope.name)
            scope_doc.status = 'Revoked'
            scope_doc.save()
    return {'status': decision, 'assessment': assessment.name, 'rubric_version': RUBRIC_VERSION}


@journey.command
def assign_scope_reviewer(application, reviewer):
    assigned_by = actor('Tele Tena Approver')
    if not frappe.db.sql('''SELECT hr.parent FROM `tabHas Role` hr JOIN tabUser u ON u.name=hr.parent
            WHERE hr.role='Tele Tena Approver' AND hr.parent=%s AND u.enabled=1''', (reviewer,)):
        fail('Choose an active professional reviewer with the approver role.')
    current = rows('''SELECT name,status FROM `tabTele Tena Vetting Scope Application`
        WHERE name=%s FOR UPDATE''', (application,))
    if not current:
        frappe.throw('Scope application unavailable', frappe.PermissionError)
    if current[0].status not in ('Submitted', 'Resubmitted', 'Clarification'):
        fail('Assign a reviewer only to an application in review.')
    frappe.db.sql('''UPDATE `tabTele Tena Vetting Scope Application`
        SET reviewer=%s,modified=UTC_TIMESTAMP(6),modified_by=%s WHERE name=%s''',
        (reviewer, assigned_by, current[0].name))
    journey.audit(assigned_by, 'ScopeReviewerAssignment', {'application': current[0].name,
                                                            'reviewer': reviewer})
    return {'assigned': True}
