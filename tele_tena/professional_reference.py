"""Versioned reference imports. Listed is not accredited, approved or affiliated."""
import gzip
import json
from pathlib import Path
import frappe


def import_records(records):
    from tele_tena.api.journey import fail
    count=0
    for r in records:
        if r.get('kind') not in ('profession','specialty','domain','issuer','authority','facility') or not r.get('id') or not r.get('label') or not r.get('source_url') or not r.get('permitted_use'):fail('Reference import requires typed identifiers and provenance.')
        values=(r['id'],r['kind'],r['label'][:240],json.dumps(r.get('aliases',[]),ensure_ascii=False),(r.get('country') or ''),(r.get('region') or '')[:140],r.get('entity_type','')[:80],r.get('source_id',r['id']),r['source_url'],r.get('accessed','2026-10-22'),r['permitted_use'],'Listed')
        # Never overwrites reviewer edits, pending submissions or merged references.
        frappe.db.sql('''INSERT IGNORE INTO tt_reference (id,kind,label,aliases,country,region,entity_type,source_id,source_url,accessed,permitted_use,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',values)
        # Additive aliases only. Never replaces an existing alias, reviewer label,
        # decision, merge or other metadata; reviewed/manual records stay untouched.
        if r.get('aliases'):
            old=frappe.db.sql("SELECT aliases FROM tt_reference WHERE id=%s AND status='Listed' AND submitted_by IS NULL AND merged_into IS NULL AND source_id=%s FOR UPDATE",(r['id'],r.get('source_id',r['id'])))
            if old:
                previous=json.loads(old[0][0]);aliases=list(dict.fromkeys(previous+r['aliases']))
                if aliases!=previous:frappe.db.sql('UPDATE tt_reference SET aliases=%s WHERE id=%s',(json.dumps(aliases,ensure_ascii=False),r['id']))
        count+=1
    return count


def import_bundled():
    directory=Path(__file__).parent/'reference_data'
    for file in sorted(directory.glob('*.json.gz')):
        with gzip.open(file,'rt') as f:import_records(json.load(f))
    # Reuse native clinic identities without changing their verification/affiliation.
    for clinic in frappe.db.sql('SELECT name,clinic_name,jurisdiction,status,submitted_by FROM `tabTele Tena Clinic`',as_dict=True):
        frappe.db.sql('''INSERT IGNORE INTO tt_reference (id,kind,label,aliases,region,entity_type,source_id,source_url,accessed,permitted_use,status,submitted_by,clinic)
            VALUES (%s,'facility',%s,'[]',%s,'Existing TeleTena clinic',%s,'https://teletena.local/internal-clinic',CURRENT_DATE,'Existing private catalog; no new verification',%s,%s,%s)''',('clinic:'+clinic.name,clinic.clinic_name,clinic.jurisdiction,clinic.name,'Reviewed' if clinic.status=='Verified' else 'Pending',clinic.submitted_by,clinic.name))
