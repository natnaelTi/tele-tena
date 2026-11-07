"""Read-only status of protected metadata emitted by a fully verified native backup.
Never scans arbitrary backup filenames or treats a recent SQL file as completeness.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,os,hashlib,re
SCHEMA='teletena-verified-backup-v1'
FILES=('database.sql.gz','public-files.tar','private-files.tar','site-config.json')

def private(path,directory=False):
 p=Path(path)
 if not p.is_absolute() or any(x.is_symlink() for x in (p,*p.parents)):raise ValueError('unsafe_path')
 s=p.stat()
 if s.st_uid!=os.geteuid() or s.st_mode&0o077 or (not p.is_dir() if directory else not p.is_file()):raise ValueError('unsafe_mode')
 return p

def timestamp(value):
 t=datetime.fromisoformat(value)
 if t.tzinfo is None:raise ValueError('timezone_required')
 return t.astimezone(timezone.utc)

def observe(directory,site,started,verified):
 """Called only after BackupGenerator plus full gzip/TAR/config integrity checks."""
 directory=private(directory,True);completed=datetime.now(timezone.utc)
 if set(verified)!=set(FILES):raise ValueError('complete_bundle_required')
 items={}
 for name in FILES:
  path=private(directory/name);s=path.stat();v=verified[name]
  if s.st_size!=v['bytes'] or not re.fullmatch('[a-f0-9]{64}',v['sha256']):raise ValueError('verified_artifact_changed')
  items[name]={**v,'mtime_ns':s.st_mtime_ns}
 data={'schema':SCHEMA,'site':site,'started_at':started.isoformat(),'completed_at':completed.isoformat(),'files':items,'verification':'Full gzip, TAR payload, SQL/config and SHA-256 validation at creation'}
 target=directory/'backup-observation.json';fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'w') as stream:json.dump(data,stream,indent=2)
 return data

def read(directory,site,max_age_hours=24,clock=None):
 if not directory:return {'status':'Unavailable','reason':'No verified backup source configured'}
 unknown={'status':'Unknown','reason':'Verified backup metadata is missing, invalid or no longer matches the artifacts'}
 try:
  if type(max_age_hours) is not int or not 1<=max_age_hours<=168:raise ValueError('age_limit')
  directory=private(directory,True);file=private(directory/'backup-observation.json');manifest=private(directory/'verified-manifest.json')
  if file.stat().st_size>16384 or manifest.stat().st_size>16384:raise ValueError('metadata_size')
  data=json.loads(file.read_text());verified=json.loads(manifest.read_text())
  if data.get('schema')!=SCHEMA or data.get('site')!=site or set(data['files'])!=set(FILES) or set(verified)!=set(FILES):raise ValueError('metadata_identity')
  now=clock or datetime.now(timezone.utc);start=timestamp(data['started_at']);end=timestamp(data['completed_at'])
  if start>end or end>now:raise ValueError('metadata_clock')
  for name in FILES:
   s=private(directory/name).stat();item=data['files'][name]
   if item['bytes']!=s.st_size or item['mtime_ns']!=s.st_mtime_ns or verified[name]!={k:item[k] for k in ('bytes','sha256')} or not re.fullmatch('[a-f0-9]{64}',item['sha256']):raise ValueError('artifact_changed')
  age=int((now-start).total_seconds())
  return {'status':'Current' if age<=max_age_hours*3600 else 'Stale','started_at':start.isoformat(),'verified_at':end.isoformat(),'age_seconds':age,'max_age_hours':max_age_hours,'reason':'Complete native backup integrity was verified at creation; current protected metadata and file statistics match'}
 except (OSError,ValueError,KeyError,TypeError):return unknown

def status():
 import frappe
 from .providers import settings
 c=settings();return read(c.get('verified_backup_directory'),frappe.local.site,c.get('backup_max_age_hours',24))
