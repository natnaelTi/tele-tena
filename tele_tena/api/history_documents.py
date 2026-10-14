"""Owner-only history files, separate from the text sharing/disclosure snapshot."""
import base64
import hashlib
import io
import json
import re
import uuid
import warnings
from urllib.parse import quote

import frappe
from PIL import Image
from tele_tena.api.journey import actor,fail,query,rows

MAX_BYTES=5*1024*1024


def owner():
    user=actor()
    profile=rows('SELECT kind FROM tt_profile WHERE user=%s',(user,))
    if profile and profile[0].kind=='patient':return user
    onboarding=rows('SELECT kind,answers,completed FROM tt_onboarding WHERE user=%s',(user,))
    from tele_tena.review import registration_enabled
    if registration_enabled('patient') and onboarding and onboarding[0].kind=='patient' and not onboarding[0].completed and frappe.db.sql('SELECT user FROM tt_contact_identity WHERE user=%s',(user,)):
        answers=json.loads(onboarding[0].answers)
        if answers.get('adult') is True and answers.get('consent') is True:return user
    frappe.throw('Patient access required',frappe.PermissionError)


def validated(filename,encoded):
    if not isinstance(filename,str) or len(filename)>255:fail('Choose a PDF, JPEG or PNG up to 5 MB.','history_file_invalid')
    filename=re.sub(r'[\x00-\x1f\x7f"\\/]', '_',filename)[-180:]
    extension=filename.rsplit('.',1)[-1].lower()
    if extension not in ('pdf','jpg','jpeg','png') or not isinstance(encoded,str) or len(encoded)>((MAX_BYTES+2)//3)*4:
        fail('Choose a PDF, JPEG or PNG up to 5 MB.','history_file_invalid')
    try:
        content=base64.b64decode(encoded,validate=True)
        if not content or len(content)>MAX_BYTES:raise ValueError()
        if extension=='pdf':
            if not content.startswith(b'%PDF-') or b'%%EOF' not in content[-1024:]:raise ValueError()
            from frappe.utils.pdf import PdfReader,pdf_contains_js
            reader=PdfReader(io.BytesIO(content))
            if reader.is_encrypted or pdf_contains_js(content):raise ValueError()
            root=reader.trailer['/Root']
            if any(key in root for key in ('/OpenAction','/AA','/AcroForm','/Collection')) or '/EmbeddedFiles' in root.get('/Names',{}):raise ValueError()
            if not 0<len(reader.pages)<=300:raise ValueError()
            mime='application/pdf'
        else:
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as image:
                    expected='PNG' if extension=='png' else 'JPEG'
                    if image.format!=expected or image.width*image.height>40_000_000 or getattr(image,'n_frames',1)!=1:raise ValueError()
                    image.verify()
            mime='image/png' if extension=='png' else 'image/jpeg'
        return filename,mime,content
    except Exception:
        # No parser exception/body leaks. Clinical bytes are never logged.
        fail('Choose a valid PDF, JPEG or PNG up to 5 MB. PDFs must be unencrypted and non-interactive.','history_file_invalid')


@query()
def list_documents():
    patient=owner()
    return {'documents':rows('SELECT id,filename,mime,content_size,created FROM tt_history_document WHERE patient=%s ORDER BY created DESC,id',(patient,))}


@query('POST')
def upload(filename,content_base64):
    patient=owner();filename,mime,content=validated(filename,content_base64)
    # Owner lock serializes quota checks and same-file retries across requests.
    frappe.db.sql('SELECT name FROM tabUser WHERE name=%s FOR UPDATE',(patient,))
    digest=hashlib.sha256(content).hexdigest()
    existing=rows('SELECT id FROM tt_history_document WHERE patient=%s AND content_sha256=%s AND filename=%s',(patient,digest,filename))
    if existing:return {'id':existing[0].id,'already_uploaded':True}
    configured=frappe.conf.get('tele_tena_history_storage_mb')
    try:quota=int(100 if configured is None else configured)*1024*1024
    except (ValueError,TypeError):fail('Document storage configuration is unavailable.','service_unavailable')
    if quota<0:fail('Document storage configuration is unavailable.','service_unavailable')
    used=int(frappe.db.sql('SELECT COALESCE(SUM(content_size),0) FROM tt_history_document WHERE patient=%s',(patient,))[0][0])
    if used+len(content)>quota:fail('Your document storage is full. Remove an unneeded file before uploading.','history_storage_full')
    id=str(uuid.uuid4())
    frappe.db.sql('''INSERT INTO tt_history_document (id,patient,filename,mime,content,content_size,content_sha256,created)
        VALUES (%s,%s,%s,%s,FROM_BASE64(%s),%s,%s,UTC_TIMESTAMP(6))''',(id,patient,filename,mime,base64.b64encode(content).decode('ascii'),len(content),digest))
    return {'id':id,'already_uploaded':False}


@query()
def download(id):
    patient=owner();found=rows('SELECT filename,mime,content FROM tt_history_document WHERE id=%s AND patient=%s',(id,patient))
    if not found:frappe.throw('Document unavailable',frappe.PermissionError)
    from werkzeug.wrappers import Response
    document=found[0]
    return Response(bytes(document.content),mimetype=document.mime,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Disposition':"attachment; filename*=UTF-8''"+quote(document.filename,safe=''),'Content-Security-Policy':"sandbox; default-src 'none'"})


@query('POST')
def remove(id):
    patient=owner();frappe.db.sql('DELETE FROM tt_history_document WHERE id=%s AND patient=%s',(id,patient))
    return {'removed':True}
