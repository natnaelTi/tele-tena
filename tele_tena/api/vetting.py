"""Human-led professional and per-service scope vetting."""
import base64
import hashlib
import json
import re
import uuid

import frappe

from tele_tena.api import journey
from tele_tena.api.journey import actor, fail, integer, one, rows, text

RUBRIC_VERSION = 'proposed-1.0'
MAX_SCOPE_EVIDENCE_BYTES = 5 * 1024 * 1024
SCOPE_EVIDENCE_TYPES = {
    'Qualification', 'License or registration', 'Scope training',
    'Approach experience', 'Other supporting evidence',
}
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
            if not value:
                result[key] = None
            else:
                try:
                    result[key] = frappe.utils.getdate(value).isoformat()
                except (TypeError, ValueError):
                    fail('Enter a valid credential expiry date.')
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
        result = rows('''SELECT a.*,p.display_name,s.service_label,
            (SELECT d.name FROM `tabTele Tena Vetting Assessment` d WHERE d.scope_application=a.name
             ORDER BY d.decided_at DESC,d.creation DESC LIMIT 1) AS latest_assessment
            FROM `tabTele Tena Vetting Scope Application` a
            JOIN tt_profile p ON p.user=a.clinician JOIN `tabTele Tena Service` s ON s.name=a.service
            ORDER BY FIELD(a.status,'Submitted','Resubmitted','Clarification','Draft'),a.submitted_at''')
        for item in result:
            item.resume_uploaded = bool(rows('SELECT 1 FROM tt_resume_evidence WHERE clinician=%s', (item.clinician,)))
            item.scope_evidence = _scope_evidence_rows(item.name)
            item.appeals = _appeal_history(item.name)
        return result
    user = _applicant(user)
    result = rows('''SELECT a.name,a.service,s.service_label,a.status,a.reverification_of,
        ss.status AS service_scope_status,a.professional_category,a.qualification,
        a.issuing_institution,a.registration_number,a.issuing_authority,a.jurisdiction,a.credential_expiry,
        a.experience_years,a.approach_keys,a.population_adults,a.independent_practice,a.clinic_affiliations,
        a.relevant_training,a.applicant_statement,a.applicant_response,a.clarification_request,
        a.decision_reason,a.restrictions,a.submitted_at,a.decided_at,a.rubric_version,
        (SELECT d.name FROM `tabTele Tena Vetting Assessment` d WHERE d.scope_application=a.name
         ORDER BY d.decided_at DESC,d.creation DESC LIMIT 1) AS latest_assessment
        FROM `tabTele Tena Vetting Scope Application` a JOIN `tabTele Tena Service` s ON s.name=a.service
        LEFT JOIN `tabTele Tena Service Scope` ss ON ss.clinician=a.clinician AND ss.service=a.service
        WHERE a.clinician=%s ORDER BY a.modified DESC''', (user,))
    for item in result:
        item.scope_evidence = _scope_evidence_rows(item.name)
        item.appeals = _appeal_history(item.name)
        item.credential_expired = bool(item.credential_expiry and
            frappe.utils.getdate(item.credential_expiry) < frappe.utils.getdate())
        item.scope_eligible = journey.service_scope_is_current(user, item.service)
    return result


def _appeal_history(application):
    return rows('''SELECT name,basis_assessment,status,applicant_statement,submitted_at,reviewer_reason,decided_at
        FROM `tabTele Tena Vetting Appeal` WHERE scope_application=%s ORDER BY sequence''',
        (application,))


@journey.query()
def scope_appeals():
    reviewer = actor('Tele Tena Approver')
    return rows('''SELECT a.name,a.scope_application,a.clinician,p.display_name,
        s.service_label,a.basis_assessment,a.sequence,a.applicant_statement,a.submitted_at,
        d.decision AS basis_decision,d.findings AS basis_reason
        FROM `tabTele Tena Vetting Appeal` a
        JOIN `tabTele Tena Vetting Scope Application` app ON app.name=a.scope_application
        JOIN tt_profile p ON p.user=a.clinician
        JOIN `tabTele Tena Service` s ON s.name=app.service
        JOIN `tabTele Tena Vetting Assessment` d ON d.name=a.basis_assessment
        WHERE a.status='Submitted' ORDER BY a.submitted_at,a.name''')


@journey.command
def submit_scope_appeal(application, statement):
    user = _applicant()
    statement = text(statement, 1600)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item = rows('''SELECT name,clinician,status FROM `tabTele Tena Vetting Scope Application`
        WHERE name=%s FOR UPDATE''', (application,))
    if not item or item[0].clinician != user:
        frappe.throw('Scope application unavailable', frappe.PermissionError)
    current = item[0]
    decisions = rows('''SELECT name,decision FROM `tabTele Tena Vetting Assessment`
        WHERE scope_application=%s ORDER BY decided_at DESC,creation DESC LIMIT 1 FOR UPDATE''',
        (current.name,))
    if not decisions:
        fail('The latest recorded decision is not eligible for reconsideration.',
             'appeal_decision_mismatch')
    prior = rows('''SELECT name,status,applicant_statement FROM `tabTele Tena Vetting Appeal`
        WHERE basis_assessment=%s''', (decisions[0].name,))
    if prior:
        # Safe retries return the original appeal; the unique assessment link
        # ensures only one applicant statement can be recorded for this basis.
        if prior[0].applicant_statement != statement:
            fail('This decision already has a reconsideration request; its original statement is preserved.',
                 'appeal_payload_mismatch')
        return {'id': prior[0].name, 'status': prior[0].status, 'idempotent': True}
    if current.status not in ('Rejected', 'Suspended', 'Expired') or decisions[0].decision != current.status:
        fail('Only the latest rejected, suspended, or expired scope decision can be reconsidered.',
             'appeal_decision_mismatch')
    count = rows('''SELECT COALESCE(MAX(sequence),0) AS sequence
        FROM `tabTele Tena Vetting Appeal` WHERE scope_application=%s''', (current.name,))
    now = frappe.utils.now_datetime()
    appeal = frappe.get_doc({'doctype':'Tele Tena Vetting Appeal',
        'scope_application':current.name,'clinician':user,
        'basis_assessment':decisions[0].name,'sequence':int(count[0].sequence or 0)+1,
        'applicant_statement':statement,'submitted_at':now,'status':'Submitted'})
    frappe.local.tele_tena_vetting_appeal_action = True
    try:
        appeal.insert()
    finally:
        frappe.local.tele_tena_vetting_appeal_action = False
    journey.audit(user, 'ScopeAppealSubmitted', {'application':current.name,
        'appeal':appeal.name,'basis_assessment':decisions[0].name})
    return {'id':appeal.name,'status':'Submitted','idempotent':False}


@journey.command
def review_scope_appeal(appeal, decision, reason):
    reviewer = actor('Tele Tena Approver')
    if decision not in ('Upheld', 'Reopen'):
        fail('Choose whether to uphold the decision or reopen the application.')
    reason = text(reason, 1600)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    locked = rows('''SELECT name,scope_application,clinician,basis_assessment,status
        FROM `tabTele Tena Vetting Appeal` WHERE name=%s FOR UPDATE''', (appeal,))
    if not locked:
        frappe.throw('Appeal unavailable', frappe.PermissionError)
    item = locked[0]
    if item.status != 'Submitted':
        final_status = 'Reopened' if decision == 'Reopen' else decision
        if item.status == final_status and rows('''SELECT name FROM `tabTele Tena Vetting Appeal`
                WHERE name=%s AND reviewer=%s AND reviewer_reason=%s''',
                (item.name, reviewer, reason)):
            return {'status':item.status,'idempotent':True}
        fail('This appeal already has a recorded outcome.', 'appeal_already_reviewed')
    application = rows('''SELECT name,status,clinician FROM `tabTele Tena Vetting Scope Application`
        WHERE name=%s FOR UPDATE''', (item.scope_application,))
    assessment = rows('''SELECT decision FROM `tabTele Tena Vetting Assessment`
        WHERE name=%s AND scope_application=%s''', (item.basis_assessment,item.scope_application))
    if (not application or application[0].clinician != item.clinician or not assessment
            or application[0].status != assessment[0].decision
            or application[0].status not in ('Rejected','Suspended','Expired')):
        fail('The underlying scope decision changed; this appeal needs a fresh reviewer assessment.',
             'appeal_basis_changed')
    now = frappe.utils.now_datetime()
    frappe.local.tele_tena_vetting_appeal_action = True
    try:
        frappe.db.set_value('Tele Tena Vetting Appeal', item.name, {
            'status':'Upheld' if decision == 'Upheld' else 'Reopened',
            'reviewer':reviewer,'reviewer_reason':reason,'decided_at':now}, update_modified=False)
    finally:
        frappe.local.tele_tena_vetting_appeal_action = False
    if decision == 'Reopen':
        frappe.db.sql('''UPDATE `tabTele Tena Vetting Scope Application`
            SET status='Clarification',clarification_request=%s,reviewer=%s,
                modified=%s,modified_by=%s WHERE name=%s''',
            ('Reconsideration reopened: ' + reason, reviewer, now, reviewer, item.scope_application))
    journey.audit(reviewer, 'ScopeAppealReviewed', {'application':item.scope_application,
        'appeal':item.name,'decision':decision,'basis_assessment':item.basis_assessment})
    return {'status':'Upheld' if decision == 'Upheld' else 'Reopened','idempotent':False}


def _scope_evidence_rows(application):
    return rows('''SELECT name AS id,scope_application,evidence_type,filename,revision,
        content_size,uploaded_at FROM `tabTele Tena Scope Evidence`
        WHERE scope_application=%s ORDER BY evidence_type,revision DESC''', (application,))


def _authorized_scope_application(application, user=None):
    user = user or actor()
    reviewer = user != 'Guest' and 'Tele Tena Approver' in frappe.get_roles(user)
    result = rows('''SELECT name,clinician,status,service FROM `tabTele Tena Vetting Scope Application`
        WHERE name=%s''', (application,))
    if not result or (not reviewer and result[0].clinician != user):
        frappe.throw('Scope evidence unavailable', frappe.PermissionError)
    item = result[0]
    return item


@journey.command
def upload_scope_evidence(application, evidence_type, filename, content_base64):
    user = _applicant()
    scope = _authorized_scope_application(application, user)
    # Serialize evidence revisions against this application's submit/review
    # transition without serializing unrelated applicants.
    locked = rows('''SELECT name,status FROM `tabTele Tena Vetting Scope Application`
        WHERE name=%s AND clinician=%s FOR UPDATE''', (scope.name, user))
    if not locked:
        frappe.throw('Scope evidence unavailable', frappe.PermissionError)
    if locked[0].status not in ('Draft', 'Clarification'):
        fail('Evidence can be changed only by the applicant while the application is a draft or requests clarification.',
             'scope_evidence_locked')
    if evidence_type not in SCOPE_EVIDENCE_TYPES:
        fail('Choose a supported evidence type.')
    if not isinstance(filename, str) or len(filename) > 255 or not filename.lower().endswith('.pdf'):
        fail('Upload a PDF document.')
    filename = re.sub(r'[^A-Za-z0-9 ._()-]', '_', filename.split('/')[-1].split('\\')[-1])[:180]
    if not isinstance(content_base64, str) or len(content_base64) > ((MAX_SCOPE_EVIDENCE_BYTES + 2) // 3) * 4 + 8:
        fail('The PDF must be 5 MiB or smaller.')
    try:
        content = base64.b64decode(content_base64, validate=True)
    except (ValueError, TypeError):
        fail('The PDF data could not be read.')
    if (not content or len(content) > MAX_SCOPE_EVIDENCE_BYTES or not content.startswith(b'%PDF-')
            or b'%%EOF' not in content[-1024:]):
        fail('The uploaded file is not a valid PDF within the 5 MiB limit.')
    prior = rows('''SELECT MAX(revision) revision FROM `tabTele Tena Scope Evidence`
        WHERE scope_application=%s AND evidence_type=%s''', (scope.name, evidence_type))
    revision = int(prior[0].revision or 0) + 1
    now = frappe.utils.now_datetime()
    digest = hashlib.sha256(content).hexdigest()
    doc = frappe.get_doc({'doctype': 'Tele Tena Scope Evidence',
        'scope_application': scope.name, 'clinician': user, 'evidence_type': evidence_type,
        'filename': filename, 'revision': revision, 'content_size': len(content),
        'content_sha256': digest, 'uploaded_by': user, 'uploaded_at': now})
    frappe.local.tele_tena_scope_evidence_action = True
    try:
        doc.insert()
    finally:
        frappe.local.tele_tena_scope_evidence_action = False
    frappe.db.sql('INSERT INTO tt_scope_evidence_content (evidence,content) VALUES (%s,%s)',
                  (doc.name, content))
    journey.audit(user, 'ScopeEvidenceUploaded', {'application': scope.name,
        'evidence': doc.name, 'type': evidence_type, 'revision': revision, 'size': len(content)})
    return {'id': doc.name, 'revision': revision, 'uploaded': True}


@frappe.whitelist()
def download_scope_evidence(evidence):
    user = actor()
    item = rows('''SELECT name,scope_application,clinician,filename FROM `tabTele Tena Scope Evidence`
        WHERE name=%s''', (evidence,))
    if not item:
        frappe.throw('Scope evidence unavailable', frappe.PermissionError)
    record = item[0]
    reviewer = user != 'Guest' and 'Tele Tena Approver' in frappe.get_roles(user)
    if not reviewer and (record.clinician != user or not set(frappe.get_roles(user)).intersection(
            {'Tele Tena Applicant', 'Tele Tena Clinician'})):
        frappe.throw('Scope evidence unavailable', frappe.PermissionError)
    content = rows('SELECT content FROM tt_scope_evidence_content WHERE evidence=%s', (record.name,))
    if not content:
        frappe.throw('Scope evidence unavailable', frappe.DoesNotExistError)
    frappe.local.response.filename = record.filename
    frappe.local.response.filecontent = bytes(content[0].content)
    frappe.local.response.type = 'download'
    frappe.local.response.display_content_as = 'attachment'


@journey.query()
def vetting_services():
    user = actor()
    if not set(frappe.get_roles(user)).intersection({'Tele Tena Applicant', 'Tele Tena Clinician'}):
        frappe.throw('Clinician application access required', frappe.PermissionError)
    return rows("""SELECT name AS id,service_label AS label,category,description,definition_version
        FROM `tabTele Tena Service` WHERE active=1 AND catalog_status='Active' AND vetting_required=1
        ORDER BY service_label""")


@journey.command
def save_scope_application(service, values, submit=False, reverification_of=None):
    user = _applicant()
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    definition = one('''SELECT name,active,catalog_status,vetting_required FROM `tabTele Tena Service`
        WHERE name=%s''', (service,))
    if not definition.active or definition.catalog_status != 'Active' or not definition.vetting_required:
        fail('This service scope is not currently open for professional applications.', 'scope_not_open')
    form = _validated_form(values)
    if reverification_of:
        base = rows('''SELECT name,clinician,service,status FROM `tabTele Tena Vetting Scope Application`
            WHERE name=%s FOR UPDATE''', (reverification_of,))
        if (not base or base[0].clinician != user or base[0].service != service
                or base[0].status not in ('Approved','Expired')):
            frappe.throw('Only your approved or formally expired application for this service can be re-verified.',
                         frappe.PermissionError)
        scopes = rows('''SELECT name FROM `tabTele Tena Service Scope`
            WHERE clinician=%s AND service=%s AND status=%s FOR UPDATE''',
            (user, service, 'Approved' if base[0].status == 'Approved' else 'Revoked'))
        latest_decision = rows('''SELECT decision FROM `tabTele Tena Vetting Assessment`
            WHERE scope_application=%s ORDER BY decided_at DESC,creation DESC LIMIT 1''', (reverification_of,))
        expected_decision = 'Approved' if base[0].status == 'Approved' else 'Expired'
        if not scopes or not latest_decision or latest_decision[0].decision != expected_decision:
            fail('This service scope is not eligible for credential re-verification.', 'scope_not_approved')
        existing = rows('''SELECT name,status,reverification_of,reverification_payload_hash
            FROM `tabTele Tena Vetting Scope Application`
            WHERE clinician=%s AND service=%s AND reverification_of=%s FOR UPDATE''',
            (user, service, reverification_of))
    else:
        existing = _scope_application(user, service, lock=True)
    if existing:
        prior = one('''SELECT status,reverification_of,reverification_payload_hash
            FROM `tabTele Tena Vetting Scope Application` WHERE name=%s FOR UPDATE''',
            (existing[0].name,))
        if reverification_of and prior.reverification_of != reverification_of:
            fail('This renewal is linked to a different approved application.', 'renewal_reference_mismatch')
        payload_hash = hashlib.sha256(json.dumps(form, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if reverification_of and submit and prior.status in ('Submitted', 'Resubmitted', 'Approved'):
            if prior.reverification_payload_hash != payload_hash:
                fail('A submitted renewal cannot be changed. Use its clarification or reconsideration path.',
                     'scope_application_locked')
            return {'name': existing[0].name, 'status': prior.status, 'idempotent': True}
        if prior.status not in ('Draft', 'Clarification'):
            fail('This scope application is awaiting reviewer action.', 'scope_application_locked')
        name = existing[0].name
        prior_status = prior.status
    else:
        name = uuid.uuid4().hex
        prior_status = 'Draft'
    renewal_ref = reverification_of or (prior.reverification_of if existing else None)
    if submit:
        if not form.get('professional_category') or not form.get('qualification') or not form.get('issuing_institution'):
            fail('Add your professional category, qualification and issuing institution before submission.')
        if not form.get('population_adults'):
            fail('Confirm that this application is limited to adult care.')
        if not rows('SELECT clinician FROM tt_resume_evidence WHERE clinician=%s', (user,)):
            fail('Upload a PDF CV before submitting for review.', 'resume_required')
        if renewal_ref:
            if not form.get('issuing_authority') or not form.get('jurisdiction'):
                fail('Add the issuing authority and jurisdiction for the renewed credential.')
            if form.get('credential_expiry') and frappe.utils.getdate(form['credential_expiry']) < frappe.utils.getdate():
                fail('The renewed credential expiry must be today or later.', 'credential_expired')
            if not rows('''SELECT name FROM `tabTele Tena Scope Evidence`
                WHERE scope_application=%s AND evidence_type='License or registration' LIMIT 1''', (name,)):
                fail('Upload current private license or registration evidence before submitting.',
                     'renewal_evidence_required')
        status = 'Resubmitted' if prior_status == 'Clarification' else 'Submitted'
    else:
        status = prior_status
    now = frappe.utils.now_datetime()
    values = {**form, 'status': status, 'submitted_at': now if submit else None}
    if renewal_ref:
        values['reverification_of'] = renewal_ref
        if submit:
            values['reverification_payload_hash'] = hashlib.sha256(
                json.dumps(form, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
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
        frappe.local.tele_tena_reverification_action = bool(renewal_ref)
        try:
            frappe.db.sql(f'''INSERT INTO `tabTele Tena Vetting Scope Application`
                ({','.join(f'`{column}`' for column in columns)}) VALUES ({placeholders})''', data)
        finally:
            frappe.local.tele_tena_reverification_action = False
    journey.audit(user, 'ScopeReverification' if renewal_ref else 'ScopeApplication',
                  {'service': service, 'status': status, 'prior_application': renewal_ref})
    return {'name': name, 'status': status, 'submitted_at': str(now if submit else ''),
            'idempotent': False}


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
        expiry = frappe.db.get_value('Tele Tena Vetting Scope Application', doc.name, 'credential_expiry')
        if expiry and frappe.utils.getdate(expiry) < frappe.utils.getdate():
            fail('An expired credential cannot support scope approval.', 'credential_expired')
    assessment = frappe.get_doc({'doctype': 'Tele Tena Vetting Assessment',
        'scope_application': doc.name, 'reviewer': reviewer, **flags, 'decision': decision,
        'findings': findings, 'restrictions': restrictions,
        'evidence_revision': (rows('SELECT revision FROM tt_resume_evidence WHERE clinician=%s', (doc.clinician,)) or [frappe._dict(revision=0)])[0].revision,
        'scope_evidence_snapshot': json.dumps([
            {'id': evidence.name, 'type': evidence.evidence_type,
             'revision': evidence.revision, 'sha256': evidence.content_sha256}
            for evidence in rows('''SELECT name,evidence_type,revision,content_sha256
                FROM `tabTele Tena Scope Evidence` WHERE scope_application=%s
                ORDER BY evidence_type,revision''', (doc.name,))
        ], separators=(',', ':'), sort_keys=True),
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
        renewal = frappe.db.get_value('Tele Tena Vetting Scope Application', doc.name, 'reverification_of')
        # Rejection of renewal evidence does not invalidate a different credential
        # that remains current. Explicit suspension or expiry still revokes now.
        if decision == 'Rejected' and renewal:
            return {'status': decision, 'assessment': assessment.name, 'rubric_version': RUBRIC_VERSION}
        scopes = rows("SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s AND service=%s AND status='Approved' FOR UPDATE",
                      (doc.clinician, doc.service))
        for scope in scopes:
            scope_doc = frappe.get_doc('Tele Tena Service Scope', scope.name)
            scope_doc.status = 'Revoked'
            scope_doc.save()
        if decision in ('Suspended', 'Expired'):
            flag_scope_appointments_for_review(clinician=doc.clinician, service=doc.service)
    return {'status': decision, 'assessment': assessment.name, 'rubric_version': RUBRIC_VERSION}


def _scope_review_context(clinician, service):
    latest = rows('''SELECT a.name,a.status,a.credential_expiry,ss.status AS scope_status,
            v.name AS assessment,v.decision
        FROM `tabTele Tena Vetting Scope Application` a
        LEFT JOIN `tabTele Tena Service Scope` ss
          ON ss.clinician=a.clinician AND ss.service=a.service
        LEFT JOIN `tabTele Tena Vetting Assessment` v ON v.scope_application=a.name
        WHERE a.clinician=%s AND a.service=%s AND a.status IN ('Approved','Suspended','Expired')
        ORDER BY v.decided_at DESC,v.creation DESC,a.modified DESC LIMIT 1''', (clinician, service))
    if not latest:
        return {'scope_application':'','eligibility_event':'unavailable:' + clinician + ':' + service,
                'reason_code':'Scope approval unavailable'}
    item = latest[0]
    if item.credential_expiry and frappe.utils.getdate(item.credential_expiry) < frappe.utils.getdate():
        return {'scope_application':item.name,
                'eligibility_event':f'credential-expiry:{item.name}:{item.credential_expiry}',
                'reason_code':'Credential expired'}
    if item.status in ('Suspended', 'Expired') or item.scope_status != 'Approved':
        return {'scope_application':item.name,
                'eligibility_event':item.assessment or f'scope-unavailable:{item.name}',
                'reason_code':'Scope approval withdrawn'}
    return {'scope_application':item.name,
            'eligibility_event':item.assessment or f'scope-unavailable:{item.name}',
            'reason_code':'Scope approval unavailable'}


def flag_scope_appointments_for_review(clinician=None, service=None):
    """Record logistics-only review flags; never change appointment or funds."""
    now = frappe.utils.now_datetime()
    filters, values = ["a.state IN ('Booked','PendingConfirmation')", 'a.start >= %s'], [now]
    if clinician:
        filters.append('a.clinician=%s'); values.append(clinician)
    if service:
        filters.append('o.service=%s'); values.append(service)
    candidates = rows('''SELECT a.id,a.clinician,o.service,a.start
        FROM tt_appointment a JOIN tt_offering o ON o.id=a.offering
        WHERE ''' + ' AND '.join(filters) + '''
        ORDER BY a.start LIMIT 500''', values)
    created = 0
    for appointment in candidates:
        if journey.service_scope_is_current(appointment.clinician, appointment.service):
            continue
        review_context = _scope_review_context(appointment.clinician, appointment.service)
        if rows('''SELECT name FROM `tabTele Tena Scope Appointment Review`
            WHERE appointment=%s AND eligibility_event=%s''',
                (appointment.id, review_context['eligibility_event'])):
            continue
        frappe.db.savepoint('scope_appt_review')
        frappe.local.tele_tena_scope_appointment_review_action = True
        try:
            frappe.get_doc({'doctype':'Tele Tena Scope Appointment Review',
                'appointment':appointment.id,'clinician':appointment.clinician,
                'service':appointment.service,'scheduled_start':appointment.start,
                'scope_application':review_context['scope_application'],
                'eligibility_event':review_context['eligibility_event'],
                'reason_code':review_context['reason_code'],
                'status':'Open','flagged_at':now}).insert()
            created += 1
        except frappe.DuplicateEntryError:
            frappe.db.rollback(save_point='scope_appt_review')
        finally:
            frappe.local.tele_tena_scope_appointment_review_action = False
    return {'flagged':created}


@journey.query()
def scope_appointment_reviews(status='Open', limit=100, start=0):
    actor('Tele Tena Approver')
    if status not in ('Open','Acknowledged','Cleared','All'):
        fail('Choose a valid operational review status.')
    limit = integer(limit, 1, 200); start = integer(start, 0, 100000)
    clause = '' if status == 'All' else 'WHERE r.status=%s'
    params = [] if status == 'All' else [status]
    params.extend([limit, start])
    # No patient identity, disclosure, notes, or request narrative is returned.
    return rows('''SELECT r.name,r.appointment,r.clinician,p.display_name AS clinician_name,
        r.service,s.service_label,r.scheduled_start,r.reason_code,r.status,r.flagged_at,
        r.reviewer,r.reviewer_rationale,r.resolved_at
        FROM `tabTele Tena Scope Appointment Review` r
        JOIN tt_profile p ON p.user=r.clinician AND p.kind='clinician'
        JOIN `tabTele Tena Service` s ON s.name=r.service ''' + clause + '''
        ORDER BY r.flagged_at DESC LIMIT %s OFFSET %s''', params)


@journey.command
def resolve_scope_appointment_review(review, outcome, rationale):
    reviewer = actor('Tele Tena Approver')
    if outcome not in ('Acknowledge','Clear'):
        fail('Choose acknowledge or clear.')
    rationale = text(rationale, 1200)
    one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    item = rows('''SELECT r.name,r.appointment,r.clinician,r.service,r.status,a.state
        FROM `tabTele Tena Scope Appointment Review` r
        JOIN tt_appointment a ON a.id=r.appointment WHERE r.name=%s FOR UPDATE''', (review,))
    if not item:
        frappe.throw('Operational review unavailable', frappe.PermissionError)
    current = item[0]
    if current.status == 'Cleared':
        if outcome == 'Clear' and rows('''SELECT name FROM `tabTele Tena Scope Appointment Review`
            WHERE name=%s AND reviewer=%s AND reviewer_rationale=%s''', (review, reviewer, rationale)):
            return {'status':'Cleared','idempotent':True}
        fail('This operational review is already cleared.')
    if outcome == 'Clear':
        terminal = current.state in ('Cancelled','Expired','Completed','NoShow')
        if not terminal and not journey.service_scope_is_current(current.clinician, current.service):
            fail('The appointment may be cleared only after its scope is current or the appointment is terminal.')
    status = 'Acknowledged' if outcome == 'Acknowledge' else 'Cleared'
    now = frappe.utils.now_datetime()
    frappe.db.sql('''UPDATE `tabTele Tena Scope Appointment Review`
        SET status=%s,reviewer=%s,reviewer_rationale=%s,resolved_at=%s,modified=%s,modified_by=%s
        WHERE name=%s AND status<>'Cleared' ''', (status,reviewer,rationale,now,now,reviewer,review))
    journey.audit(reviewer, 'ScopeAppointmentReview', {'review':review,'appointment':current.appointment,
        'outcome':outcome})
    return {'status':status,'idempotent':False}


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
