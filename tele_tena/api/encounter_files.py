"""Explicit recipient-scoped snapshots; no generic File or clinic authorization."""
import json,uuid
import frappe
from tele_tena.api.journey import actor,profile,rows,fail,query,command
VERSION='encounter-disclosure-v1'


def selected_files(patient,ids,lock=False):
    if not isinstance(ids,list) or len(ids)>100 or any(not isinstance(id,str) or len(id)!=36 for id in ids) or len(set(ids))!=len(ids):fail('Choose your own history files','history_files_invalid')
    if lock:frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE',(patient,))
    result=[]
    for id in sorted(ids):
        found=rows('SELECT id,filename,content_sha256,content_size FROM tt_history_document WHERE id=%s AND patient=%s'+(' FOR UPDATE' if lock else ''),(id,patient))
        if not found:fail('A selected file is no longer available. Review your sharing choices.','history_files_changed')
        result.append(dict(found[0]))
    return result


def grant_booking(appointment,patient,clinician,disclosure):
    for item in disclosure.get('files',[]):
        selected_files(patient,[item['id']],lock=True)
        file=rows('SELECT * FROM tt_history_document WHERE id=%s AND patient=%s FOR UPDATE',(item['id'],patient))[0]
        if file.content_sha256!=item['content_sha256']:fail('History changed;review sharing again','history_files_changed')
        id=str(uuid.uuid4())
        frappe.db.sql('''INSERT INTO tt_history_grant
          (id,document_id,appointment,patient,recipient,version,filename,mime,content,content_sha256,created)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))''',
          (id,file.id,appointment,patient,clinician,VERSION,file.filename,file.mime,file.content,file.content_sha256))
        frappe.db.sql("INSERT INTO tt_history_grant_event VALUES (%s,%s,%s,'Granted',UTC_TIMESTAMP(6))",(str(uuid.uuid4()),id,patient))


@query()
def grants(appointment=None):
    user=actor()
    return rows('''SELECT g.id,g.appointment,g.document_id,g.filename,g.content_sha256,g.version,g.created,g.revoked_at,doctor.display_name AS recipient_label,
      CASE WHEN g.patient=%s THEN 'owner' ELSE 'recipient' END access_kind
      FROM tt_history_grant g JOIN tt_appointment a ON a.id=g.appointment JOIN tt_profile doctor ON doctor.user=g.recipient
      WHERE (g.patient=%s OR (g.recipient=%s AND a.clinician=%s AND g.revoked_at IS NULL AND a.state NOT IN ('Cancelled','Declined','Expired')))
      AND (%s IS NULL OR g.appointment=%s) ORDER BY g.created DESC LIMIT 100''',
      (user,user,user,user,appointment or None,appointment or None))


@query()
def download(id):
    user=actor();found=rows('''SELECT g.*,a.state FROM tt_history_grant g JOIN tt_appointment a ON a.id=g.appointment
      WHERE g.id=%s AND (g.patient=%s OR (g.recipient=%s AND a.clinician=%s AND g.revoked_at IS NULL
        AND a.state NOT IN ('Cancelled','Declined','Expired')))''',(id,user,user,user))
    if not found:frappe.throw('File unavailable',frappe.PermissionError)
    from werkzeug.wrappers import Response
    from urllib.parse import quote
    file=found[0]
    return Response(bytes(file.content),mimetype=file.mime,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Disposition':"attachment; filename*=UTF-8''"+quote(file.filename,safe=''),'Content-Security-Policy':"sandbox; default-src 'none'"})


@command
def revoke(id):
    patient=profile('patient').user
    found=rows('SELECT revoked_at FROM tt_history_grant WHERE id=%s AND patient=%s FOR UPDATE',(id,patient))
    if not found:frappe.throw('Sharing unavailable',frappe.PermissionError)
    if not found[0].revoked_at:
        frappe.db.sql('UPDATE tt_history_grant SET revoked_at=UTC_TIMESTAMP(6) WHERE id=%s',(id,))
        frappe.db.sql("INSERT INTO tt_history_grant_event VALUES (%s,%s,%s,'Revoked',UTC_TIMESTAMP(6))",(str(uuid.uuid4()),id,patient))
    return {'revoked':True,'previously_seen_cannot_be_recalled':True,'snapshot_retained_pending_governance':True}
