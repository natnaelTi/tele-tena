"""One separately authorized read of the original accepted-deletion test recording."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tele_tena.operations.proof import ProofRun, ProofBlocked

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    run=ProofRun(a.root);m,c=run.checked()
    if not m.get('amendments',{}).get('deletion_readback',{}).get('approved'):
        raise ProofBlocked('one_read_amendment_required')
    rows=m['recordings']
    if len(rows)!=1:raise ProofBlocked('exact_original_recording_required')
    row=rows[0];identifier=row['id']
    action=m['actions'].get('provider-delete-retry-2-'+identifier,{})
    if action.get('http_status')!=204:raise ProofBlocked('accepted_original_delete_required')
    path='/api/projects/'+str(c['posthog_project_id'])+'/session_recordings/'+identifier+'/'
    status,raw=run.request('provider-delete-confirm-owner-amendment-'+identifier,'posthog_api',path,
        costs={'posthog_admin_gets':1,'deletion_readback_amendment':1},maximum=65536)
    # Report only the HTTP result and explicit deletion booleans, never metadata/body.
    explicit_deleted=False
    if status==200:
        try:
            body=json.loads(raw);explicit_deleted=isinstance(body,dict) and body.get('deleted') is True
        except ValueError:pass
    with run.locked():
        m,c=run.checked();row=next(x for x in m['recordings'] if x['id']==identifier)
        row['provider_deletion']='ConfirmedAbsent' if status==404 else 'Accepted204Unverified'
        row['extra_readback_http_status']=status
        row['extra_readback_deleted_boolean']=explicit_deleted
        run._write(run.manifest,m)
    print('Exact original post-deletion read HTTP:',status,'; explicit deleted flag:',explicit_deleted)
    print('Removal verified.' if status==404 else 'Removal remains unverified; no further read or deletion authorized.')

if __name__=='__main__':main()
