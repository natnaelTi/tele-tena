"""Bounded PostHog web blob-v2 normalizer. No mobile/unknown formats guessed.
Reference contract: pinned PostHog37babfa, snapshot API blob_v2 + cv2024-10.
Reject missing sources or malformed lines instead of silently omitting content.
"""
import gzip,hashlib,io,json,math
FORMAT='teletena-web-replay-v1'
MAX_BYTES=10*1024**2
class ReplayFormatError(ValueError):pass

def unpack(value,depth=0):
 if depth>150:raise ReplayFormatError('nested_recording_limit')
 if isinstance(value,str) and value.startswith('\x1f\x8b'):
  try:
   with gzip.GzipFile(fileobj=io.BytesIO(value.encode('latin1'))) as f:raw=f.read(MAX_BYTES+1)
   if len(raw)>MAX_BYTES:raise ReplayFormatError('decompressed_recording_limit')
   return unpack(json.loads(raw),depth+1)
  except (ValueError,OSError,UnicodeError):raise ReplayFormatError('invalid_compressed_snapshot') from None
 if isinstance(value,list):return [unpack(x,depth+1) for x in value]
 if isinstance(value,dict):
  if value.get('cv') not in (None,'2024-10'):raise ReplayFormatError('compression_version_unsupported')
  return {k:unpack(v,depth+1) for k,v in value.items() if k!='cv'}
 return value

def source_keys(sources):
 if not isinstance(sources,list) or not sources or len(sources)>1000:raise ReplayFormatError('source_manifest_invalid')
 keys=[]
 for source in sources:
  if not isinstance(source,dict) or source.get('source')!='blob_v2' or str(source.get('blob_key','')).isdigit() is False:raise ReplayFormatError('source_version_unsupported')
  key=str(source['blob_key'])
  if key in keys:raise ReplayFormatError('duplicate_source')
  keys.append(key)
 return keys

def normalize(sources,blobs):
 keys=source_keys(sources)
 if set(keys)!=set(blobs):raise ReplayFormatError('source_segments_incomplete')
 events=[];seen=set();windows={}
 for key in keys:
  raw=blobs[key]
  if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:raise ReplayFormatError('source_size_limit')
  for line in raw.splitlines():
   if not line.strip():continue
   try:entry=json.loads(line)
   except (ValueError,UnicodeError):raise ReplayFormatError('malformed_snapshot_line') from None
   if isinstance(entry,list) and len(entry)==2 and isinstance(entry[0],str):window=entry[0];frames=[entry[1]]
   elif isinstance(entry,dict) and isinstance(entry.get('data'),list):window=entry.get('window_id') or entry.get('windowId');frames=entry['data']
   else:raise ReplayFormatError('snapshot_line_version_unsupported')
   if not isinstance(window,str) or not window or len(window)>100:raise ReplayFormatError('window_identifier_invalid')
   for event in frames:
    event=unpack(event)
    if not isinstance(event,dict) or type(event.get('timestamp')) not in (int,float) or not math.isfinite(event['timestamp']) or event.get('type') not in (0,1,2,3,4,5):raise ReplayFormatError('event_version_unsupported')
    if event.get('type')==3 and event.get('data',{}).get('source') not in (0,1,2,3,4,5,6,8):raise ReplayFormatError('incremental_version_unsupported')
    event={**event,'windowId':window};digest=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
    if digest in seen:continue
    seen.add(digest);events.append(event);windows.setdefault(window,set()).add(event['type'])
    if len(events)>100000:raise ReplayFormatError('event_count_limit')
 if len(windows)!=1:raise ReplayFormatError('multi_window_player_unverified')
 if not events or any(not {2,4}.issubset(types) for types in windows.values()):raise ReplayFormatError('full_snapshot_or_meta_missing')
 events.sort(key=lambda x:x['timestamp']);encoded=json.dumps(events,ensure_ascii=False,separators=(',',':')).encode()
 if len(encoded)>MAX_BYTES:raise ReplayFormatError('normalized_size_limit')
 return {'format':FORMAT,'events':events,'windows':len(windows),'sha256':hashlib.sha256(encoded).hexdigest(),'source_keys':keys}
