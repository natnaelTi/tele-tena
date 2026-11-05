"""Private archive lifecycle; production playback is gated on actual provider proof."""
import json,hashlib
from datetime import timedelta
import frappe
from . import runtime as rt,storage,providers

def status():
 c=rt.config();rows=frappe.db.sql('SELECT state,COUNT(*) n,COALESCE(SUM(size_bytes),0) bytes FROM tt_ops_archive GROUP BY state',as_dict=True)
 return {'available':False,'reason':'Actual project export and independent playback verification required.','states':rows,'used_bytes':storage.usage(),'limit_bytes':c['archive_bytes'],'raw_retention_days':90,'capacity_estimate':None,'capacity_note':'No verified real recording samples; a production capacity estimate is not available.','oldest_unarchived':frappe.db.sql("SELECT MIN(captured) at FROM tt_ops_archive WHERE state IN ('Pending','Failed','Incomplete')",as_dict=True)[0].at,'last_retention':frappe.db.sql("SELECT at FROM tt_ops_heartbeat WHERE name='retention'",as_dict=True)}
def tombstone(id,reason='Expired',clock=None):
 clock=clock or rt.now()
 if len(id)!=64 or any(x not in '0123456789abcdef' for x in id):raise ValueError('invalid_archive_id')
 # Journal is retained when restoring DB backups; original capture age is always checked.
 with storage.locked():
  p=storage.root()/'deletions.jsonl'
  import os
  fd=os.open(p,os.O_CREAT|os.O_APPEND|os.O_WRONLY,0o600)
  with os.fdopen(fd,'w') as f:f.write(json.dumps({'id':id,'reason':reason,'at':clock.isoformat()})+'\n')
 frappe.db.sql('INSERT IGNORE INTO tt_ops_deleted VALUES (%s,%s,%s,%s)',(id,clock,reason,'Pending'))
 rows=frappe.db.sql('SELECT object_key FROM tt_ops_archive WHERE id=%s',(id,),as_dict=True)
 if rows and rows[0].object_key:storage.delete(rows[0].object_key,'replay')
 frappe.db.sql("UPDATE tt_ops_archive SET state='Expired',object_key=NULL,modified=%s WHERE id=%s",(clock,id))
def deleted(id):
 if frappe.db.sql('SELECT id FROM tt_ops_deleted WHERE id=%s',(id,)):return True
 p=storage.root()/'deletions.jsonl'
 if p.exists():
  with p.open() as f:
   for line in f:
    try:
     if json.loads(line).get('id')==id:return True
    except ValueError:continue
 return False
def retention(clock=None):
 clock=clock or rt.now()
 for row in frappe.db.sql("SELECT id FROM tt_ops_archive WHERE expires<=%s AND state<>'Expired' LIMIT 100",(clock,),as_dict=True):tombstone(row.id,clock=clock)
 # Restored/deleted rows may have an expiry in the future: tombstone wins.
 for row in frappe.db.sql("SELECT id FROM tt_ops_archive WHERE state<>'Expired' LIMIT 500",as_dict=True):
  if deleted(row.id):tombstone(row.id,'UserDeleted',clock)
 frappe.db.sql("INSERT INTO tt_ops_heartbeat VALUES ('retention',%s,'{}') ON DUPLICATE KEY UPDATE at=VALUES(at)",(clock,))
def export_tick():
 c=rt.config()
 if not c['archive']:return
 for row in frappe.db.sql("SELECT * FROM tt_ops_archive WHERE state IN ('Pending','Failed','Incomplete') AND captured<DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 25 HOUR) AND (next_try IS NULL OR next_try<=UTC_TIMESTAMP(6)) AND tries<%s LIMIT 5 FOR UPDATE",(c['retry_budget'],),as_dict=True):
  if deleted(row.id):continue
  try:providers.archive_export(row)
  except providers.ArchiveUnverified:
   frappe.db.sql("UPDATE tt_ops_archive SET state='Incomplete',failure_code='project_export_unverified',tries=tries+1,next_try=DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 1 DAY),modified=UTC_TIMESTAMP(6) WHERE id=%s",(row.id,))
   rt.incident('archive_export_unverified')
