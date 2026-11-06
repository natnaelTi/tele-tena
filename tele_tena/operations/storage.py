"""Private quota-bounded object adapter. Never serves a public filesystem URL."""
import fcntl,gzip,hashlib,json,os,re,shutil,uuid
from contextlib import contextmanager
from pathlib import Path
import frappe

def root():
 path=Path(frappe.get_site_path('private','teletena-operations'));path.mkdir(mode=0o700,parents=True,exist_ok=True)
 if path.is_symlink():raise ValueError('unsafe_storage')
 return path
@contextmanager
def locked():
 with (root()/'storage.lock').open('a') as f:
  os.chmod(f.name,0o600);fcntl.flock(f,fcntl.LOCK_EX)
  try:yield
  finally:fcntl.flock(f,fcntl.LOCK_UN)
def archive_root():
 from .providers import settings
 value=settings().get('archive_directory')
 if not value:return root()
 path=Path(value)
 if not path.is_absolute() or any(x in ('public','assets','backups') for x in path.parts) or any(x.is_symlink() for x in (path,*path.parents)):raise ValueError('unsafe_archive_volume')
 if not path.is_dir() or path.stat().st_uid!=os.geteuid() or path.stat().st_mode&0o077:raise ValueError('private_archive_volume_required')
 return path

def location(kind):return archive_root() if kind=='replay' else root()
def local_usage():return sum(p.stat().st_size for p in root().iterdir() if p.is_file() and not p.is_symlink())
def usage():
 paths={root(),archive_root()}
 return sum(p.stat().st_size for folder in paths for p in folder.iterdir() if p.is_file() and not p.is_symlink())
def put(content,limit,total,kind='object'):
 if not isinstance(content,bytes) or len(content)>limit:raise ValueError('object_too_large')
 key=hashlib.sha256(content).hexdigest()
 with locked():
  path=location(kind)/(kind+'-'+key)
  if path.exists():return key
  if (local_usage() if kind=='support' else usage())+len(content)>total or shutil.disk_usage(location(kind)).free-len(content)<200*1024*1024:raise ValueError('storage_full')
  fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as out:out.write(content)
 return key
def read(key,kind='object'):
 if not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('invalid_object')
 path=location(kind)/(kind+'-'+key)
 if path.is_symlink():raise ValueError('invalid_object')
 return path.read_bytes()
def delete(key,kind='object'):
 if not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('invalid_object')
 path=location(kind)/(kind+'-'+key)
 if path.is_symlink():raise ValueError('invalid_object')
 path.unlink(missing_ok=True)
def write_spool(payload):
 # Only a pre-scrubbed error schema reaches this private rollback-independent spool.
 raw=json.dumps(payload,separators=(',',':')).encode()
 if len(raw)>16000:return
 with locked():
  pending=list(root().glob('error-*'))
  if len(pending)>=500 or local_usage()+len(raw)>50*1024*1024:return
  path=root()/('error-'+uuid.uuid4().hex)
  fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'wb') as out:out.write(raw)
