"""Project-specific web export with complete source checks and bounded responses.
No metadata-only success; unknown formats/missing windows are explicit failures.
"""
import hashlib,json,re
from urllib.parse import urlencode
from .replay_format import normalize,source_keys,MAX_BYTES
class ExportError(ValueError):pass

def export_recording(project,recording,fetch):
 if not re.fullmatch(r'[1-9][0-9]*',str(project)) or not re.fullmatch('[a-f0-9-]{36}',recording):raise ExportError('invalid_recording_reference')
 base='/api/environments/'+str(project)+'/session_recordings/'+recording+'/snapshots'
 status,raw=fetch('/api/projects/'+str(project)+'/session_recordings/'+recording+'/',65536)
 if status!=200:raise ExportError('recording_metadata_http_'+str(status))
 try:meta=json.loads(raw)
 except ValueError:raise ExportError('recording_metadata_invalid') from None
 if str(meta.get('id',meta.get('session_id','')))!=recording:raise ExportError('recording_identity_mismatch')
 status,raw=fetch(base+'?blob_v2=true',65536)
 if status!=200:raise ExportError('source_manifest_http_'+str(status))
 try:sources=json.loads(raw)['sources'];keys=source_keys(sources)
 except (ValueError,KeyError,TypeError):raise ExportError('source_manifest_unsupported') from None
 if len(keys)>20:raise ExportError('source_budget_exceeded')
 blobs={};hashes={};total=0
 for key in keys:
  status,raw=fetch(base+'?'+urlencode({'source':'blob_v2','start_blob_key':key,'end_blob_key':key,'decompress':'true'}),MAX_BYTES)
  if status!=200:raise ExportError('source_segment_http_'+str(status))
  total+=len(raw)
  if total>MAX_BYTES:raise ExportError('complete_recording_size_limit')
  if b'TT_SECRET_' in raw or b'/private/' in raw or b'OTP-CANARY' in raw:raise ExportError('archive_sensitive_canary')
  blobs[key]=raw;hashes[key]=hashlib.sha256(raw).hexdigest()
 result=normalize(sources,blobs)
 status,raw=fetch(base+'?blob_v2=true',65536)
 if status!=200:raise ExportError('source_manifest_recheck_unavailable')
 try:after=json.loads(raw)['sources']
 except (ValueError,KeyError):raise ExportError('source_manifest_recheck_invalid') from None
 if sources!=after:raise ExportError('source_manifest_changed_during_export')
 result.update(provider='posthog-eu-blob-v2',provider_recording_id=recording,source_sha256=hashes,captured_at=meta.get('start_time'),provider_end_time=meta.get('end_time'),source_bytes=total)
 return result
