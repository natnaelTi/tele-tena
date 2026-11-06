"""One pinned recorder gateway. Authenticated opt-in only; no business mutations.
Admission/chunks are private, bounded and asynchronous. No provider call in a request.
"""
import hashlib,json,re,uuid
from datetime import timedelta,timezone
from functools import lru_cache
from pathlib import Path
import frappe
from . import runtime as rt, providers, storage, archive
from .replay_projection import project, ProjectionError
POLICY='teletena-masked-web-v2'
MAX_CHUNK=1024*1024

def installed():return bool(frappe.db.sql("SHOW TABLES LIKE 'tt_ops_capture'"))
def code_hash():
    root=Path(__file__).resolve().parents[2]
    paths=('frontend/src/replay-safety.ts','frontend/src/replay-projection.ts','frontend/package-lock.json','tele_tena/api/operations.py','tele_tena/operations/capture.py','tele_tena/operations/replay_projection.py','tele_tena/operations/providers.py','tele_tena/operations/posthog_export.py','tele_tena/operations/replay_format.py','tele_tena/operations/archive.py','tele_tena/operations/storage.py')
    return hashlib.sha256(b''.join((root/p).read_bytes() for p in paths)).hexdigest()
def capability():
    if not installed() or not providers.archive_capability():return False
    value=providers.settings().get('replay_activation_file')
    if not value:return False
    import os
    try:
        path=Path(value)
        if not path.is_absolute() or path.is_symlink() or path.stat().st_uid!=os.geteuid() or path.stat().st_mode&0o077 or path.stat().st_size>8192:return False
        data=json.loads(path.read_text())
        return data.get('policy')==POLICY and data.get('project_id')==str(providers.settings().get('posthog_project_id')) and data.get('capture_code_sha256')==code_hash() and data.get('activation_authorized') is True
    except (OSError,ValueError):return False

def scope():
    user=frappe.session.user
    return rt.pseudonym('capture-auth:'+str(frappe.session.sid)+':'+user+':'+rt.role())
def eligible():
    if frappe.session.user=='Guest':return False
    c=rt.config()
    if not c['replay'] or not c['archive'] or not capability():return False
    pref=frappe.db.sql('SELECT replay,version FROM tt_ops_preference WHERE actor=%s',(rt.pseudonym(frappe.session.user),))
    return bool(pref and pref[0][0] and pref[0][1]=='operations-notice-draft-v2')
def dropped(reason):
    # Enumerated reasons only, no raw error/payload/body.
    frappe.db.sql('INSERT INTO tt_ops_counter VALUES (%s,%s,1) ON DUPLICATE KEY UPDATE n=n+1',(rt.now().date(),'replay_'+reason))
def _uuid(value):
    try:return str(uuid.UUID(value))==value
    except (TypeError,ValueError,AttributeError):return False

@lru_cache(maxsize=8)
def release_styles(release):
    root=Path(__file__).resolve().parents[1]/'public/review'
    manifest=json.loads((root/'release.json').read_text())
    if manifest['source_commit']!=release:raise ValueError('replay_release_changed')
    parts=[]
    for name,digest in manifest['files'].items():
        if name.startswith('assets/') and name.endswith('.css'):
            raw=(root/name).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('release_style_integrity')
            parts.append(raw.decode())
    css='\n'.join(parts)
    # Only owned static release CSS, never browser-supplied CSS. Remove every fetch.
    css=re.sub(r'@import[^;]*;','',css,flags=re.I)
    css=re.sub(r'url\s*\([^)]*\)','none',css,flags=re.I)
    css=re.sub(r'</style','',css,flags=re.I)
    if len(css)>1024*1024:raise ValueError('release_styles_limit')
    classes=sorted(set(re.findall(r'\.([A-Za-z_][A-Za-z0-9_-]{0,80})',css)))
    return {'css':css,'classes':classes}

def admit(provider_id,window_id):
    if not _uuid(provider_id) or not _uuid(window_id):raise ValueError('replay_identifier_invalid')
    if not eligible():return {'state':'Disabled'}
    c=rt.config();owner=rt.pseudonym(frappe.session.user);id=rt.pseudonym('replay:'+provider_id)
    if archive.deleted(id):return {'state':'Stopped'}
    # Serialize admission with quotas/config updates; no application booking locks.
    frappe.db.sql('SELECT id FROM tt_ops_config WHERE id=1 FOR UPDATE')
    existing=frappe.db.sql('SELECT * FROM tt_ops_capture WHERE id=%s',(id,),as_dict=True)
    if existing:
        row=existing[0]
        if archive.deleted(id) or row.owner_actor!=owner or row.session_scope!=scope() or row.window_id!=window_id or row.state!='Active':raise frappe.PermissionError('Replay admission unavailable')
        data=json.loads(storage.read(row.style_key,'styles'))
        return {'state':'Active','id':id,'classes':data['classes'],'stop_at':str(row.stop_at),'max_bytes':c['recording_bytes'],'idempotent':True}
    if frappe.db.sql('SELECT COUNT(*) FROM tt_ops_archive')[0][0]>=c['replay_index_limit']:dropped('index_limited');return {'state':'Limited'}
    if int(id[:8],16)%100>=c['sample_percent']:dropped('sampled');return {'state':'Sampled'}
    if frappe.db.sql("SELECT COUNT(*) FROM tt_ops_capture WHERE owner_actor=%s AND state='Active'",(owner,))[0][0]>=5:dropped('tabs_limited');return {'state':'Limited'}
    if frappe.db.sql("SELECT COUNT(*) FROM tt_ops_archive WHERE state IN ('Capturing','Pending','Failed','Incomplete')")[0][0]>=c['export_queue']:dropped('queue_limited');return {'state':'Limited'}
    if storage.usage()>=c['archive_bytes']:dropped('storage_limited');return {'state':'Limited'}
    if not rt.count('replays',c['replays_per_day']):dropped('daily_limited');return {'state':'Limited'}
    user=frappe.session.user
    synthetic=c['environment']!='production' or rt.role()=='reviewer' or user.endswith('.invalid') or user.startswith('tt-demo-') or user in (frappe.conf.get('tele_tena_ops_synthetic_users') or [])
    context=rt.request_context();mode=frappe.db.sql('SELECT mode FROM tt_payment_config WHERE id=1')[0][0]
    server_recording=str(uuid.uuid4())
    now=rt.now();styles=release_styles(rt.release());style_key=storage.put(json.dumps(styles).encode(),2*1024**2,c['archive_bytes'],'styles')
    frappe.db.sql("INSERT INTO tt_ops_capture (id,owner_actor,session_scope,provider_id,window_id,release_id,role,locale,device,payment_mode,environment,synthetic,captured,stop_at,last_seen,state,style_key) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Active',%s)",(id,owner,scope(),server_recording,window_id,rt.release(),rt.role(),context['locale'],context['device'],mode,c['environment'],int(synthetic),now,now+timedelta(minutes=15),now,style_key))
    frappe.db.sql("INSERT INTO tt_ops_archive (id,provider_id,captured,expires,state,size_bytes,modified) VALUES (%s,%s,%s,%s,'Capturing',0,%s)",(id,server_recording,now,now+timedelta(days=90),now))
    dropped('admitted')
    return {'state':'Active','id':id,'classes':styles['classes'],'stop_at':str(now+timedelta(minutes=15)),'max_bytes':c['recording_bytes']}

def _owned(id,require_scope=True):
    rows=frappe.db.sql('SELECT * FROM tt_ops_capture WHERE id=%s FOR UPDATE',(id,),as_dict=True)
    if not rows or rows[0].owner_actor!=rt.pseudonym(frappe.session.user) or (require_scope and rows[0].session_scope!=scope()):raise frappe.PermissionError('Replay ownership required')
    return rows[0]

def chunk(id,chunk_id,events,route):
    if not _uuid(chunk_id) or not isinstance(events,list) or not 0<len(events)<=200:raise ValueError('replay_chunk_invalid')
    if len(json.dumps(events))>MAX_CHUNK:raise ValueError('replay_chunk_limit')
    frappe.db.sql('SELECT id FROM tt_ops_config WHERE id=1 FOR UPDATE')
    row=_owned(id)
    if archive.deleted(id) or not eligible() or row.state!='Active' or row.stop_at<=rt.now() or row.release_id!=rt.release():return {'state':'Stopped'}
    styles=json.loads(storage.read(row.style_key,'styles'));classes=set(styles['classes']);safe_route=rt.route_template(route);clean=[]
    if sum(x.get('type')==2 for x in events if isinstance(x,dict))>4:raise ProjectionError('snapshot_count_limit')
    for event in events:
        value=project(event,classes,safe_route)
        if not row.captured.replace(tzinfo=timezone.utc).timestamp()*1000-10000<=value['timestamp']<=rt.now().replace(tzinfo=timezone.utc).timestamp()*1000+10000:raise ProjectionError('snapshot_time_invalid')
        # Insert only owned static styles, with stable reserved node IDs.
        if value['type']==2:value['data']['node'].setdefault('childNodes',[]).insert(0,{'type':2,'id':-9000001,'tagName':'style','attributes':{},'childNodes':[{'type':3,'id':-9000002,'textContent':styles['css']}]})
        clean.append(value)
    key=rt.pseudonym('chunk:'+id+':'+chunk_id);content=json.dumps({'schema':'teletena-capture-chunk-v1','chunk_id':key,'events':clean},separators=(',',':')).encode();digest=hashlib.sha256(content).hexdigest()
    old=frappe.db.sql('SELECT digest FROM tt_ops_chunk WHERE id=%s',(key,))
    if old:
        if old[0][0]!=digest:raise ValueError('replay_retry_changed')
        return {'state':'Recorded Locally','idempotent':True}
    c=rt.config()
    if frappe.db.sql('SELECT COUNT(*) FROM tt_ops_chunk WHERE capture_id=%s',(id,))[0][0]>=c['replay_chunks_per_record'] or frappe.db.sql("SELECT COUNT(*) FROM tt_ops_chunk WHERE state IN ('Pending','Retry')")[0][0]>=c['replay_pending_chunks'] or not rt.count('replay_chunks',c['replay_chunks_per_day']):
        dropped('chunks_limited');loss(id,'capacity');return {'state':'Limited'}
    if row.bytes+len(content)>c['recording_bytes']:dropped('bytes_limited');close(id);return {'state':'Limited'}
    try:object_key=storage.put(content,2*MAX_CHUNK,c['archive_bytes'],'capture')
    except (ValueError,OSError):dropped('storage_limited');close(id);return {'state':'Limited'}
    frappe.db.sql("INSERT INTO tt_ops_chunk VALUES (%s,%s,%s,%s,%s,'Pending',0,NULL,%s)",(key,id,digest,object_key,len(content),rt.now()))
    frappe.db.sql('UPDATE tt_ops_capture SET bytes=bytes+%s,last_seen=%s WHERE id=%s',(len(content),rt.now(),id))
    return {'state':'Recorded Locally'}

def loss(id,reason):
    if reason not in ('projection','network','capacity'):raise ValueError('replay_loss_reason_invalid')
    row=_owned(id);_close(row);dropped('client_'+reason)
    frappe.db.sql("UPDATE tt_ops_capture SET state='Incomplete' WHERE id=%s",(id,))
    frappe.db.sql("UPDATE tt_ops_archive SET state='Incomplete',failure_code=%s,tries=%s WHERE id=%s",('client_'+reason,rt.config()['retry_budget'],id))
    discard(id,state='Incomplete')
    return {'state':'Incomplete'}

def close(id):
    row=_owned(id)
    _close(row)
    return {'state':'Closed'}
def _close(row):
    if row.state!='Active':return
    frappe.db.sql("UPDATE tt_ops_capture SET state='Closed' WHERE id=%s",(row.id,))
    frappe.db.sql("UPDATE tt_ops_archive SET state='Pending',next_try=%s WHERE id=%s AND state='Capturing'",(rt.now()+timedelta(hours=25),row.id))
def revoke_owner():
    if not installed():return
    for row in frappe.db.sql("SELECT * FROM tt_ops_capture WHERE owner_actor=%s AND (state='Active' OR id IN (SELECT capture_id FROM tt_ops_chunk WHERE state IN ('Pending','Retry'))) FOR UPDATE",(rt.pseudonym(frappe.session.user),),as_dict=True):
        _close(row);discard(row.id)

def discard(id,state='Revoked'):
    if not installed():return
    frappe.db.sql('UPDATE tt_ops_capture SET state=%s WHERE id=%s',(state,id))
    for item in frappe.db.sql('SELECT * FROM tt_ops_chunk WHERE capture_id=%s AND object_key IS NOT NULL FOR UPDATE',(id,),as_dict=True):
        frappe.db.sql("UPDATE tt_ops_chunk SET state='Discarded',object_key=NULL WHERE id=%s",(item.id,))
        if not frappe.db.sql('SELECT id FROM tt_ops_chunk WHERE object_key=%s LIMIT 1',(item.object_key,)):storage.delete(item.object_key,'capture')

def tick():
    if not installed():return
    for row in frappe.db.sql("SELECT * FROM tt_ops_capture WHERE state='Active' AND (stop_at<=%s OR last_seen<%s) LIMIT 100 FOR UPDATE",(rt.now(),rt.now()-timedelta(minutes=2)),as_dict=True):_close(row)
    c=rt.config()
    # Retention is independent of enable flags. Never resurrect a deleted replay.
    for item in frappe.db.sql("SELECT k.* FROM tt_ops_chunk k JOIN tt_ops_capture s ON s.id=k.capture_id WHERE s.captured<%s OR k.created<%s AND k.state IN ('Pending','Retry') LIMIT 100",(rt.now()-timedelta(days=90),rt.now()-timedelta(days=1)),as_dict=True):
        if item.object_key:storage.delete(item.object_key,'capture')
        frappe.db.sql("UPDATE tt_ops_chunk SET state='Expired',object_key=NULL WHERE id=%s",(item.id,))
    frappe.db.sql('DELETE k FROM tt_ops_chunk k JOIN tt_ops_capture s ON s.id=k.capture_id WHERE s.captured<%s',(rt.now()-timedelta(days=91),))
    frappe.db.sql('DELETE FROM tt_ops_capture WHERE captured<%s',(rt.now()-timedelta(days=91),))
    scan_orphans()
    if not c['replay'] or not capability():return
    frappe.db.sql("UPDATE tt_ops_chunk SET state='Exhausted' WHERE state='Retry' AND tries>=%s",(c['retry_budget'],))
    items=frappe.db.sql("SELECT * FROM tt_ops_chunk WHERE state IN ('Pending','Retry') AND tries<%s AND (next_try IS NULL OR next_try<=%s) ORDER BY created LIMIT 5 FOR UPDATE",(c['retry_budget'],rt.now()),as_dict=True)
    for item in items:
        session=frappe.db.sql('SELECT * FROM tt_ops_capture WHERE id=%s',(item.capture_id,),as_dict=True)[0]
        if archive.deleted(session.id) or session.state in ('Revoked','Incomplete'):state='Discarded'
        else:
            try:
                raw=storage.read(item.object_key,'capture')
                if hashlib.sha256(raw).hexdigest()!=item.digest:raise ValueError('capture_integrity_failure')
                decoded=json.loads(raw)
                if isinstance(decoded,dict) and (decoded.get('schema')!='teletena-capture-chunk-v1' or decoded.get('chunk_id')!=item.id):raise ValueError('capture_chunk_version_invalid')
                providers.replay_snapshot(session,item,decoded['events'] if isinstance(decoded,dict) else decoded);state='ProviderAccepted'
            except (providers.Unconfigured,providers.ProviderUnavailable):state='Retry'
            except (ValueError,OSError):state='Incomplete';rt.incident('replay_chunk_integrity_failure')
        frappe.db.sql('UPDATE tt_ops_chunk SET state=%s,tries=tries+1,next_try=%s WHERE id=%s',(state,rt.now()+timedelta(seconds=min(3600,30*2**item.tries)),item.id))
        if state=='ProviderAccepted':frappe.db.sql('UPDATE tt_ops_archive SET next_try=%s WHERE id=%s',(rt.now()+timedelta(hours=25),session.id))
        if state in ('ProviderAccepted','Discarded'):
            storage.delete(item.object_key,'capture');frappe.db.sql('UPDATE tt_ops_chunk SET object_key=NULL WHERE id=%s',(item.id,))

def scan_orphans(clock=None,full=False):
    """Discard unindexed rollback/restore spool objects after their one-day horizon."""
    clock=clock or rt.now();paths=sorted(storage.root().glob('capture-*'))
    prior=frappe.db.sql("SELECT details FROM tt_ops_heartbeat WHERE name='capture_orphan_scan'",as_dict=True)
    after=json.loads(prior[0].details).get('after','') if prior and not full else ''
    pending=[p for p in paths if p.name>after] or paths;selected=pending if full else pending[:25];removed=0
    for path in selected:
        key=path.name[8:]
        if not re.fullmatch('[a-f0-9]{64}',key) or path.is_symlink():continue
        if frappe.db.sql('SELECT id FROM tt_ops_chunk WHERE object_key=%s LIMIT 1',(key,)):continue
        expired=clock.replace(tzinfo=timezone.utc).timestamp()-path.stat().st_mtime>86400
        if not expired:
            try:
                if path.stat().st_size>2*MAX_CHUNK:continue
                payload=json.loads(path.read_bytes());events=payload.get('events',[]) if isinstance(payload,dict) else payload
                times=[e['timestamp'] for e in events if isinstance(e,dict) and type(e.get('timestamp')) in (int,float)]
                expired=bool(times and min(times)/1000<clock.replace(tzinfo=timezone.utc).timestamp()-90*86400)
            except (ValueError,TypeError):continue
        if expired:storage.delete(key,'capture');removed+=1
    detail=json.dumps({'after':selected[-1].name if selected else '', 'checked':len(selected),'deleted':removed})
    frappe.db.sql("INSERT INTO tt_ops_heartbeat VALUES ('capture_orphan_scan',%s,%s) ON DUPLICATE KEY UPDATE at=VALUES(at),details=VALUES(details)",(clock,detail))
    return {'checked':len(selected),'deleted':removed}
