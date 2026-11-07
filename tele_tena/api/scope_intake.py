"""Connect explicit service selections to independent, immutable scope reviews."""
import base64
import hashlib
import json
import uuid

import frappe
from tele_tena.api import journey, vetting, professional
from tele_tena.api.journey import actor, rows, fail, text


def _copy_license(application, submission, user, copied_by=None):
    """Copy only selected, safe license documents from the exact submitted version.

    This is an internal snapshot operation, not a reviewer upload or owner
    impersonation. Identification documents are never eligible for this copy.
    """
    payload = json.loads(submission.payload)
    for evidence_id in payload.get('license_files', []):
        found = rows('''SELECT filename,mime,content,content_sha256,created
            FROM tt_professional_evidence WHERE id=%s AND user=%s AND purpose='License' ''',
            (evidence_id, user))
        if not found or found[0].mime not in ('application/pdf','image/jpeg','image/png'):
            continue
        evidence = found[0]
        content = bytes(evidence.content)
        if hashlib.sha256(content).hexdigest() != evidence.content_sha256:
            fail('The saved license evidence needs an integrity review.', 'scope_evidence_integrity')
        from tele_tena.api.history_documents import validated
        filename, _mime, content = validated(evidence.filename, base64.b64encode(content).decode())
        if rows('''SELECT name FROM `tabTele Tena Scope Evidence`
            WHERE scope_application=%s AND evidence_type='License or registration'
            AND content_sha256=%s''', (application, evidence.content_sha256)):
            continue
        revision = frappe.db.sql('''SELECT COALESCE(MAX(revision),0)+1
            FROM `tabTele Tena Scope Evidence` WHERE scope_application=%s
            AND evidence_type='License or registration' ''', (application,))[0][0]
        name = uuid.uuid4().hex
        now = frappe.utils.now_datetime()
        frappe.db.sql('''INSERT INTO `tabTele Tena Scope Evidence`
            (name,owner,creation,modified,modified_by,docstatus,idx,scope_application,
             clinician,evidence_type,filename,revision,content_size,content_sha256,uploaded_by,uploaded_at)
            VALUES (%s,%s,%s,%s,%s,0,0,%s,%s,'License or registration',%s,%s,%s,%s,%s,%s)''',
            (name,user,now,now,actor(),application,user,filename,revision,len(content),
             evidence.content_sha256,copied_by or user,evidence.created))
        frappe.db.sql('INSERT INTO tt_scope_evidence_content (evidence,content) VALUES (%s,FROM_BASE64(%s))', (name,base64.b64encode(content).decode()))
        journey.audit(actor(), 'ScopeLicenseSnapshotLinked', {'application':application,
            'submission':submission.id,'source_evidence':evidence_id,'evidence':name})


def submit_selected_scopes(user, services, recovery=False, assisted_actor=None):
    """Internal only. Caller authorizes owner completion or a versioned patch.

    Existing applications/decisions/scopes are left intact. A recovered selection
    is not an approval, nor a new applicant declaration or external verification.
    """
    journey.one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    claims = journey._initial_application_profile(user)
    submitted = rows('''SELECT id,payload FROM tt_professional_submission WHERE user=%s
        ORDER BY created DESC,id DESC LIMIT 1''', (user,))
    application = journey.one('SELECT statement,submitted_at FROM tt_application WHERE user=%s', (user,))
    results = []
    for service in services:
        definition = rows('''SELECT name FROM `tabTele Tena Service`
            WHERE name=%s AND vetting_required=1 AND catalog_status IN ('Draft','Active')''', (service,))
        if not definition:
            continue  # Legacy/closed definitions require their existing policy.
        existing = vetting._scope_application(user, service, lock=True)
        if existing:
            results.append({'name':existing[0].name,'existing':True})
            continue
        if rows('SELECT name FROM `tabTele Tena Service Scope` WHERE clinician=%s AND service=%s', (user,service)):
            continue  # Never reopen or reinterpret an existing manual decision.
        if not all(claims.get(k) for k in ('professional_category','qualification','issuing_institution')):
            if recovery:
                continue  # Remains visible as a missing intake; no invented claims.
            fail('Complete your professional qualification and institution before requesting scope review.', 'scope_qualification_required')
        if recovery and not professional.cv_available(user) and not rows('SELECT clinician FROM tt_resume_evidence WHERE clinician=%s',(user,)):
            continue  # Reviewer sees the selection, but no complete intake is invented.
        values = {k:v for k,v in claims.items() if k in vetting.APPLICANT_FIELDS}
        values.update(population_adults=True, applicant_statement=application.statement or '')
        # Reuse validation/storage without changing the authenticated actor/roles.
        result = vetting._save_scope_application(user,service,values,submit=True)
        if submitted:
            if assisted_actor:_copy_license(result['name'],submitted[0],user,copied_by=assisted_actor)
            else:_copy_license(result['name'],submitted[0],user)
        if recovery and application.submitted_at:
            frappe.db.sql('UPDATE `tabTele Tena Vetting Scope Application` SET submitted_at=%s WHERE name=%s',
                          (application.submitted_at,result['name']))
        journey.audit(actor(), 'ScopeIntakeRecovered' if recovery else 'OnboardingScopeSubmitted',
                      {'application':result['name'],'clinician':user,'service':service})
        if not recovery:
            from tele_tena.operations.runtime import safe_record
            safe_record('application.scope_created',result['name'],user=user)
        results.append(result)
    return results


@journey.command
def prepare_review(clinician, service, reason):
    """Reviewer-initiated review; never bypasses structured approval gates."""
    reviewer = actor('Tele Tena Approver')
    reason = text(reason,1000)
    journey.one('SELECT id FROM tt_gate WHERE id=1 FOR UPDATE')
    journey.approved(clinician,lock=True)
    definition = journey.one('SELECT vetting_required FROM `tabTele Tena Service` WHERE name=%s', (service,))
    if not definition.vetting_required:
        result = journey.review_service_scope(clinician,service,'Approved')
        journey.audit(reviewer,'ManualServiceScopeGrant',{'clinician':clinician,'service':service,'reason':reason})
        return result
    existing = vetting._scope_application(clinician,service,lock=True)
    if existing:
        if frappe.db.get_value('Tele Tena Vetting Scope Application',existing[0].name,'status')=='Draft':
            fail('This service application is still a draft. Ask the clinician to submit it before review.', 'scope_review_draft')
        return {'application':existing[0].name,'status':'Review required'}
    results = submit_selected_scopes(clinician,[service])
    if not results:
        fail('This scope already has a decision or is not open for review. Review its existing history.', 'scope_review_unavailable')
    journey.audit(reviewer,'ReviewerScopeReviewInitiated',{'clinician':clinician,'service':service,
        'application':results[0]['name'],'reason':reason})
    return {'application':results[0]['name'],'status':'Review required'}


@journey.query()
def reviewable_services():
    actor('Tele Tena Approver')
    # Draft definitions may receive applications, but never an approval until
    # their independent medical-lead catalog review has passed.
    from tele_tena.review import enabled
    return rows('''SELECT name AS id,service_label AS label FROM `tabTele Tena Service`
        WHERE (vetting_required=1 AND catalog_status IN ('Draft','Active'))
        OR (active=1 AND (catalog_status='Active' OR (catalog_status='Legacy test' AND %s=1)))
        ORDER BY service_label,name''', (int(enabled() or frappe.local.site=='erp.localhost'),))
