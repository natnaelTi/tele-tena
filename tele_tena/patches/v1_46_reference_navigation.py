"""Additive proposed navigation metadata; prior reference identities/snapshots remain valid."""
import gzip,json
from pathlib import Path
import frappe

def execute():
    columns={'priority_et':'TINYINT NOT NULL DEFAULT 0','priority_source':'VARCHAR(500)','priority_review_status':"VARCHAR(30) NOT NULL DEFAULT 'Proposed'",'group_key':'VARCHAR(120)','group_label':'VARCHAR(160)','description':'TEXT'}
    for name,definition in columns.items():
        if not frappe.db.sql('SHOW COLUMNS FROM tt_reference LIKE %s',(name,)):frappe.db.sql_ddl(f'ALTER TABLE tt_reference ADD COLUMN `{name}` {definition}')
    root=Path(__file__).resolve().parents[1]/'reference_data'
    from tele_tena.professional_reference import import_records
    with gzip.open(root/'competency-v2.json.gz','rt') as f:records=json.load(f)
    import_records(records)
    for r in records:frappe.db.sql("UPDATE tt_reference SET group_key=%s,group_label=%s,description=%s WHERE id=%s AND group_key IS NULL",(r['group_key'],r['group_label'],r['description'],r['id']))
    # An explicit seed marker prevents a repeated migration from undoing reviewer choices.
    for r in json.loads((root/'ethiopia-priority-v1.json').read_text())['entries']:
        frappe.db.sql("UPDATE tt_reference SET priority_et=1,priority_source=%s WHERE id=%s AND priority_source IS NULL AND country='ET'",(r['source_url'],r['id']))
