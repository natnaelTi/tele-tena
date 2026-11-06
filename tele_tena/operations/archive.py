"""Private archive lifecycle; production playback is gated on actual provider proof."""
import json,hashlib,gzip,io
from datetime import timedelta,datetime,timezone
import frappe
from . import runtime as rt,storage,providers

def text(value):
 from tele_tena.localization import translate,request_locale
 return translate(value,request_locale())

def status():
 c=rt.config();proof=providers.archive_capability()
 rows=frappe.db.sql('SELECT state,COUNT(*) n,COALESCE(SUM(size_bytes),0) bytes FROM tt_ops_archive GROUP BY state',as_dict=True)
 sizes=sorted(x[0] for x in frappe.db.sql("SELECT size_bytes FROM tt_ops_archive WHERE state='Verified' AND size_bytes>0 ORDER BY captured DESC LIMIT 1000"))
 storage_state='Ready'
 try:used=storage.usage()
 except (ValueError,OSError):used=None;storage_state='Unavailable'
 limit=c['archive_bytes'];oldest=frappe.db.sql("SELECT MIN(captured) at FROM tt_ops_archive WHERE state IN ('Capturing','Pending','Failed','Incomplete')",as_dict=True)[0].at
 recent=frappe.db.sql('SELECT COUNT(*) FROM tt_ops_archive WHERE captured>=%s',(rt.now()-timedelta(days=7),))[0][0]
 measured=None
 if sizes:
  mean=sum(sizes)//len(sizes);measured={'sample_size':len(sizes),'median_bytes':sizes[len(sizes)//2],'p95_bytes':sizes[min(len(sizes)-1,int(len(sizes)*.95))],'mean_bytes':mean,'last_seven_days_recordings':recent,'configured_daily_limit_90_day_bytes':mean*c['replays_per_day']*90,'limitation':text('Observed compressed archives only; short or synthetic sessions are not a production capacity guarantee.')}
 from .capture import installed
 chunk_states=frappe.db.sql('SELECT state,COUNT(*) n,COALESCE(SUM(size_bytes),0) bytes FROM tt_ops_chunk GROUP BY state',as_dict=True) if installed() else []
 late=bool(oldest and rt.now()-oldest>timedelta(days=7))
 return {'available':bool(c['archive'] and proof and storage_state=='Ready'),'playback_available':bool(proof and storage_state=='Ready'),'project_proof_verified':proof,'site_export_enabled':c['archive'],'site_capture_enabled':c['replay'],'reason':text('Actual project settled export and independent playback verification required.') if not proof else text('Project format verified; site collection/export activation remains explicit.'),'states':rows,'chunks':chunk_states,'used_bytes':used,'storage_state':storage_state,'available_bytes':max(0,limit-used) if used is not None else None,'limit_bytes':limit,'index_entries':sum(int(x.n) for x in rows),'index_limit':c['replay_index_limit'],'raw_retention_days':90,'capacity_estimate':measured,'capacity_note':text('No verified recording samples on this site.') if not measured else text('Measured compressed samples; inspect collection coverage and duration before sizing production.'),'oldest_unarchived':oldest,'export_warning':late,'capture_counters':frappe.db.sql("SELECT day,kind,n FROM tt_ops_counter WHERE kind LIKE %s AND day>=%s",('replay_%',(rt.now()-timedelta(days=7)).date()),as_dict=True),'provider_deletions':frappe.db.sql('SELECT provider_state,COUNT(*) n FROM tt_ops_deleted GROUP BY provider_state',as_dict=True),'recordings':frappe.db.sql('SELECT id,captured,expires,state,size_bytes,failure_code,tries FROM tt_ops_archive ORDER BY captured DESC LIMIT 100',as_dict=True),'last_retention':frappe.db.sql("SELECT at FROM tt_ops_heartbeat WHERE name='retention'",as_dict=True)}

def tombstone(id,reason='Expired',clock=None):
 clock=clock or rt.now()
 if len(id)!=64 or any(x not in '0123456789abcdef' for x in id):raise ValueError('invalid_archive_id')
 # Journal is retained when restoring DB backups; original capture age is always checked.
 with storage.locked():
  if not deleted(id):
   p=storage.root()/'deletions.jsonl'
   import os
   fd=os.open(p,os.O_CREAT|os.O_APPEND|os.O_WRONLY,0o600)
   with os.fdopen(fd,'w') as f:f.write(json.dumps({'id':id,'reason':reason,'at':clock.isoformat()})+'\n')
 frappe.db.sql('INSERT IGNORE INTO tt_ops_deleted VALUES (%s,%s,%s,%s)',(id,clock,reason,'Pending'))
 rows=frappe.db.sql('SELECT object_key FROM tt_ops_archive WHERE id=%s',(id,),as_dict=True)
 if rows and rows[0].object_key:storage.delete(rows[0].object_key,'replay')
 frappe.db.sql("UPDATE tt_ops_archive SET tries=IF(state='Expired',tries,0),next_try=IF(state='Expired',next_try,NULL),state='Expired',object_key=NULL,modified=%s WHERE id=%s",(clock,id))
 from .capture import discard
 discard(id)
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
 scan_orphans(clock)
 frappe.db.sql("INSERT INTO tt_ops_heartbeat VALUES ('retention',%s,'{}') ON DUPLICATE KEY UPDATE at=VALUES(at)",(clock,))
def export_tick():
 c=rt.config()
 if not c['archive']:return
 from .capture import installed
 ready=" AND NOT EXISTS (SELECT 1 FROM tt_ops_chunk k WHERE k.capture_id=tt_ops_archive.id AND k.state IN ('Pending','Retry'))" if installed() else ''
 for row in frappe.db.sql("SELECT * FROM tt_ops_archive WHERE state IN ('Pending','Failed','Incomplete') AND captured<%s AND (next_try IS NULL OR next_try<=%s) AND tries<%s"+ready+" ORDER BY captured LIMIT 1 FOR UPDATE",(rt.now()-timedelta(hours=25),rt.now(),c['retry_budget']),as_dict=True):
  if deleted(row.id):continue
  from .capture import installed
  if installed() and frappe.db.sql('SELECT id FROM tt_ops_capture WHERE id=%s',(row.id,)):
   states={x.state for x in frappe.db.sql('SELECT state FROM tt_ops_chunk WHERE capture_id=%s',(row.id,),as_dict=True)}
   if states & {'Pending','Retry'}:continue
   if not states or states & {'Expired','Incomplete','Discarded','Exhausted'}:
    frappe.db.sql("UPDATE tt_ops_archive SET state='Incomplete',failure_code='capture_incomplete',tries=%s WHERE id=%s",(c['retry_budget'],row.id));continue
  try:
   from .replay_format import FORMAT
   result=providers.archive_export(row)
   captured=datetime.fromisoformat(result['captured_at'].replace('Z','+00:00')).astimezone(timezone.utc).replace(tzinfo=None);expires=captured+timedelta(days=90)
   if captured>rt.now():raise ValueError('capture_timestamp_invalid')
   if expires<=rt.now():tombstone(row.id,clock=rt.now());continue
   result['teletena_archive_id']=row.id
   compressed=gzip.compress(json.dumps(result).encode(),mtime=0);key=storage.put(compressed,c['recording_bytes'],c['archive_bytes'],'replay')
   frappe.db.sql("UPDATE tt_ops_archive SET state='Verified',tries=0,next_try=NULL,captured=%s,expires=%s,sha256=%s,format_version=%s,player_version='teletena-sandbox-web-v1',object_key=%s,size_bytes=%s,verified=%s,modified=%s,failure_code=NULL WHERE id=%s",(captured,expires,hashlib.sha256(compressed).hexdigest(),FORMAT,key,len(compressed),rt.now(),rt.now(),row.id))
  except (providers.ArchiveUnverified,providers.Unconfigured,providers.ProviderUnavailable,ValueError,KeyError) as error:
   frappe.db.sql("UPDATE tt_ops_archive SET state='Incomplete',failure_code=%s,tries=tries+1,next_try=%s,modified=%s WHERE id=%s",(('project_export_unverified' if isinstance(error,providers.ArchiveUnverified) else 'archive_provider_unavailable' if isinstance(error,(providers.Unconfigured,providers.ProviderUnavailable)) else 'archive_format_incomplete'),rt.now()+timedelta(hours=min(24,2**row.tries)),rt.now(),row.id))
   rt.incident('archive_export_unverified')

def playback_payload(id):
 rt.reviewer()
 rows=frappe.db.sql('SELECT * FROM tt_ops_archive WHERE id=%s',(id,),as_dict=True)
 if not rows or not providers.archive_capability():return {'available':False,'reason':'Archive project proof is incomplete.'}
 row=rows[0]
 if row.state!='Verified' or row.expires<=rt.now() or deleted(id):return {'available':False,'reason':'This recording is unavailable or expired.'}
 raw=storage.read(row.object_key,'replay')
 if hashlib.sha256(raw).hexdigest()!=row.sha256:raise ValueError('archive_integrity_failure')
 with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:data=f.read(10*1024**2+1)
 if len(data)>10*1024**2:raise ValueError('archive_size_limit')
 result=json.loads(data)
 if result.get('format')!='teletena-web-replay-v1':raise ValueError('archive_player_version_unsupported')
 if not isinstance(result.get('events'),list) or not {2,4}.issubset({e.get('type') for e in result['events'] if isinstance(e,dict)}):raise ValueError('archive_event_integrity_failure')
 return {'available':True,'recording':result,'player_version':row.player_version}

def player_response(locale=None):
 rt.reviewer()
 from pathlib import Path
 from werkzeug.wrappers import Response
 import secrets
 from tele_tena.localization import translate,request_locale
 locale=locale if locale in ('en','am','om') else request_locale()
 labels={'play':translate('Play',locale),'pause':translate('Pause',locale),'timeline':translate('Replay Timeline',locale),'blocked':translate('Private Element Blocked',locale),'unavailable':translate('Replay interaction unavailable',locale),'unsupported':translate('Unsupported or incomplete recording',locale)}
 safe_labels=json.dumps(labels).replace('<',chr(92)+'u003c')
 nonce=secrets.token_hex(24);code='window.__teletenaPlayerLabels='+safe_labels+';'+(Path(__file__).parent/'player.js').read_text()
 policy="default-src 'none'; script-src 'nonce-"+nonce+"'; style-src 'unsafe-inline'; img-src 'none'; media-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'; frame-ancestors 'self'; sandbox allow-scripts"
 html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Private Replay</title><body><script nonce="'+nonce+'">'+code+'</script></body></html>'
 return Response(html,content_type='text/html; charset=utf-8',headers={'Content-Security-Policy':policy,'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

def process_provider_deletions():
 if not providers.archive_capability():return
 c=rt.config()
 rows=frappe.db.sql("SELECT a.*,d.provider_state FROM tt_ops_archive a JOIN tt_ops_deleted d ON d.id=a.id WHERE d.provider_state IN ('Pending','ProviderAccepted','Unknown') AND a.tries<%s AND (a.next_try IS NULL OR a.next_try<=UTC_TIMESTAMP(6)) LIMIT 5 FOR UPDATE",(c['retry_budget'],),as_dict=True)
 for row in rows:
  state=row.provider_state
  try:
   if state=='Pending':providers.archive_delete_provider(row.provider_id);state='ProviderAccepted'
   else:state='ConfirmedAbsent' if providers.archive_provider_absent(row.provider_id) else 'Pending' if state=='Unknown' else state
  except providers.Unconfigured:pass
  except (providers.ProviderUnavailable,providers.ArchiveUnverified):
   state='Unknown';rt.incident('archive_provider_deletion_unavailable')
  frappe.db.sql('UPDATE tt_ops_deleted SET provider_state=%s WHERE id=%s',(state,row.id))
  frappe.db.sql('UPDATE tt_ops_archive SET tries=tries+1,next_try=DATE_ADD(UTC_TIMESTAMP(6),INTERVAL 1 DAY) WHERE id=%s',(row.id,))

def retry_export(id):
 rt.reviewer();c=rt.config()
 if not c['archive'] or not providers.archive_capability():return {'state':'Disabled'}
 rows=frappe.db.sql('SELECT * FROM tt_ops_archive WHERE id=%s FOR UPDATE',(id,),as_dict=True)
 if not rows or deleted(id) or rows[0].expires<=rt.now():raise ValueError('archive_retry_unavailable')
 if rows[0].state not in ('Pending','Failed','Incomplete'):raise ValueError('archive_retry_state')
 from .capture import installed
 if installed():
  items=frappe.db.sql('SELECT * FROM tt_ops_chunk WHERE capture_id=%s',(id,),as_dict=True)
  if any(x.state in ('Discarded','Expired','Incomplete') for x in items):raise ValueError('capture_cannot_be_reconstructed')
  for item in items:
   if item.state=='Exhausted':
    raw=storage.read(item.object_key,'capture')
    if hashlib.sha256(raw).hexdigest()!=item.digest:raise ValueError('capture_integrity_failure')
 if not rt.count('replay_manual_retries',10):raise ValueError('manual_retry_limit')
 if installed():frappe.db.sql("UPDATE tt_ops_chunk SET state='Retry',tries=0,next_try=%s WHERE capture_id=%s AND state='Exhausted'",(rt.now(),id))
 # Do not move completion/ingestion buffers or policy deadlines earlier.
 next_try=max(rows[0].next_try or rt.now(),rt.now())
 frappe.db.sql("UPDATE tt_ops_archive SET state='Pending',tries=0,next_try=%s WHERE id=%s",(next_try,id))
 return {'state':'Pending','retry_after':str(next_try)}


def scan_orphans(clock=None,full=False):
 """Bounded regular scan; operator full scan is mandatory after private restore.
 Only app-owned content-addressed replay objects; never other private files.
 """
 clock=clock or rt.now();folder=storage.archive_root();paths=sorted(folder.glob('replay-*'))
 prior=frappe.db.sql("SELECT details FROM tt_ops_heartbeat WHERE name='archive_orphan_scan'",as_dict=True)
 after=json.loads(prior[0].details).get('after','') if prior and not full else ''
 pending=[p for p in paths if p.name>after] or paths
 selected=pending if full else pending[:25];deleted_count=0
 from .capture import installed
 for path in selected:
  key=path.name[7:]
  if len(key)!=64 or any(c not in '0123456789abcdef' for c in key) or path.is_symlink():continue
  if frappe.db.sql('SELECT id FROM tt_ops_archive WHERE object_key=%s LIMIT 1',(key,)):continue
  if not full and clock.replace(tzinfo=timezone.utc).timestamp()-path.stat().st_mtime<3600:continue
  try:
   raw=storage.read(key,'replay')
   if len(raw)>rt.config()['recording_bytes'] or hashlib.sha256(raw).hexdigest()!=key:raise ValueError('orphan_integrity')
   with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:data=f.read(10*1024**2+1)
   if len(data)>10*1024**2:raise ValueError('orphan_size')
   data=json.loads(data);captured=datetime.fromisoformat(data['captured_at'].replace('Z','+00:00')).astimezone(timezone.utc).replace(tzinfo=None)
   if captured+timedelta(days=90)>clock:continue
   id=data.get('teletena_archive_id')
   provider=data.get('provider_recording_id','')
   import re
   if isinstance(id,str) and re.fullmatch('[a-f0-9]{64}',id) and re.fullmatch('[a-f0-9-]{36}',provider):
    frappe.db.sql("INSERT IGNORE INTO tt_ops_archive (id,provider_id,captured,expires,state,size_bytes,modified) VALUES (%s,%s,%s,%s,'Expired',0,%s)",(id,provider,captured,captured+timedelta(days=90),clock));tombstone(id,'Expired',clock)
   storage.delete(key,'replay');deleted_count+=1
  except (ValueError,KeyError,OSError):rt.incident('archive_orphan_integrity_unavailable')
 details=json.dumps({'after':selected[-1].name if selected else '', 'objects_checked':len(selected),'expired_orphans_deleted':deleted_count,'full_scan':full})
 frappe.db.sql("INSERT INTO tt_ops_heartbeat VALUES ('archive_orphan_scan',%s,%s) ON DUPLICATE KEY UPDATE at=VALUES(at),details=VALUES(details)",(clock,details))
 return {'checked':len(selected),'deleted':deleted_count}
