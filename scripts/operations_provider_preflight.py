"""Private configuration checks; network-free unless explicit Telegram discovery.
Never prints field values, exception messages, provider bodies or token-bearing URLs.
Does not bind sites, enable collection, send messages or set live-test authorization.
"""
import argparse,json,os,re,stat
from pathlib import Path
from urllib.parse import urlsplit

OPTIONAL=('posthog_delete_key','bugsink_api_host','bugsink_project_id','bugsink_source_map_token')
REQUIRED=('owner_alert_email','posthog_host','posthog_token','posthog_api_host','posthog_project_id','posthog_read_key','bugsink_dsn','telegram_token')
def load(path):
 if not path.is_absolute() or path.is_symlink() or path.parent.is_symlink():raise ValueError('file_path')
 if stat.S_IMODE(path.parent.stat().st_mode)!=0o700:raise ValueError('directory_permissions')
 info=path.stat()
 if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o600 or info.st_size>32768:raise ValueError('file_permissions_or_owner')
 content=path.read_bytes()
 try:data=json.loads(content)
 except (UnicodeError,ValueError):raise ValueError('json') from None
 if not isinstance(data,dict):raise ValueError('schema')
 return data,content

def validate(data):
 invalid=[]
 if data.get('verified_backup_directory'):
  folder=Path(str(data['verified_backup_directory']))
  if not folder.is_absolute() or any(p.is_symlink() for p in (folder,*folder.parents)) or not folder.is_dir() or folder.stat().st_uid!=os.geteuid() or folder.stat().st_mode&0o077:invalid.append('verified_backup_directory')
 if 'backup_max_age_hours' in data and (type(data['backup_max_age_hours']) is not int or not 1<=data['backup_max_age_hours']<=168):invalid.append('backup_max_age_hours')
 if data.get('schema')!='teletena-operations-config-v1':invalid.append('schema')
 invalid.extend(k for k in REQUIRED if not isinstance(data.get(k),(str,int)) or not str(data[k]).strip())
 hosts={'https://eu.i.posthog.com':'https://eu.posthog.com','https://us.i.posthog.com':'https://us.posthog.com'}
 if data.get('posthog_host') not in hosts:invalid.append('posthog_host')
 elif data.get('posthog_api_host')!=hosts[data['posthog_host']]:invalid.append('posthog_api_host')
 if not re.fullmatch(r'[1-9][0-9]*',str(data.get('posthog_project_id',''))):invalid.append('posthog_project_id')
 if not re.fullmatch(r'[^@\s,]+@[^@\s,]+\.[^@\s,]+',str(data.get('owner_alert_email',''))):invalid.append('owner_alert_email')
 if data.get('owner_account')!='':invalid.append('owner_account')
 if data.get('live_test_authorized') is not False:invalid.append('live_test_authorized')
 try:
  dsn=urlsplit(data.get('bugsink_dsn',''));api=urlsplit(data.get('bugsink_api_host',''))
  if dsn.scheme!='https' or not dsn.hostname or not dsn.hostname.endswith('.bugsink.com') or not dsn.username or not re.fullmatch(r'/[1-9][0-9]*/?',dsn.path) or dsn.query or dsn.fragment:invalid.append('bugsink_dsn')
  if api.geturl() and (api.scheme!='https' or api.hostname!=dsn.hostname or api.username or api.query or api.fragment):invalid.append('bugsink_api_host')
  if data.get('bugsink_project_id') and str(data['bugsink_project_id'])!=dsn.path.strip('/'):invalid.append('bugsink_project_id')
 except (TypeError,ValueError):invalid.append('bugsink_dsn')
 if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]{20,100}',str(data.get('telegram_token',''))):invalid.append('telegram_token')
 if data.get('telegram_chat') and not re.fullmatch(r'[1-9][0-9]*',str(data['telegram_chat'])):invalid.append('telegram_chat')
 return {'invalid_or_missing_fields':sorted(set(invalid)),'optional_missing_fields':[k for k in OPTIONAL if not data.get(k)],'telegram_setup_missing_fields':[] if data.get('telegram_chat') else ['telegram_chat']}

def discover(path,data,original,fetch=None):
 if data.get('telegram_chat'):return 'Existing Chat Preserved'
 if fetch is None:
  def fetch(token):
   import http.client
   connection=http.client.HTTPSConnection('api.telegram.org',timeout=15)
   try:
    connection.request('GET','/bot'+token+'/getUpdates?limit=100&timeout=0')
    response=connection.getresponse()
    if response.status!=200:return {'ok':False,'http_status':response.status}
    raw=response.read(1048577)
    if len(raw)>1048576:return {'ok':False}
    return json.loads(raw)
   finally:connection.close()
 try:payload=fetch(data['telegram_token'])
 except Exception:return 'Transport or Response Unavailable'
 if not payload.get('ok'):return 'Discovery Unavailable; No Webhook or Consumer Changed'
 matches={str(message['chat']['id']) for item in payload.get('result',[]) for message in [item.get('message',{})] if message.get('chat',{}).get('type')=='private' and message.get('text')=='TeleTena owner alert setup'}
 if not matches:return 'No Matching Private Chat'
 if len(matches)!=1:return 'Multiple Matching Private Chats; Owner Selection Required'
 if path.read_bytes()!=original:return 'Concurrent Configuration Change; Not Saved'
 updated={**data,'telegram_chat':matches.pop()};temporary=path.with_name('.providers-discovery-'+str(os.getpid())+'.tmp')
 try:
  fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'w') as stream:json.dump(updated,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
  if path.read_bytes()!=original:return 'Concurrent Configuration Change; Not Saved'
  temporary.replace(path)
 finally:temporary.unlink(missing_ok=True)
 return 'One Matching Private Chat Saved; No Message Sent'

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);parser.add_argument('--expected-project');parser.add_argument('--discover-telegram',action='store_true');args=parser.parse_args()
 try:data,raw=load(args.config)
 except (OSError,ValueError) as error:
  code=str(error) if isinstance(error,ValueError) and str(error) in ('file_path','directory_permissions','file_permissions_or_owner','json','schema') else 'file_unavailable'
  print(json.dumps({'invalid_or_missing_fields':[code]}));return 1
 result=validate(data)
 if args.expected_project and str(data.get('posthog_project_id'))!=args.expected_project:result['invalid_or_missing_fields'].append('posthog_project_id')
 if not result['invalid_or_missing_fields'] and args.discover_telegram:result['telegram_discovery']=discover(args.config,data,raw)
 print(json.dumps(result));return int(bool(result['invalid_or_missing_fields']))
if __name__=='__main__':raise SystemExit(main())
