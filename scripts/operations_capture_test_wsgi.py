"""Isolated loopback integration transport, never a hosted application entrypoint.
Requires the pre-existing fixed synthetic clone and explicit test environment flag.
Provider proof/activation is substituted only here; authorization/consent is real.
"""
import os,json,hashlib
from pathlib import Path
assert os.environ.get('TELE_TENA_LOCAL_REPLAY_TEST')=='1'
from scripts.offline_payment_test_wsgi import application,SITE,test_sites
assert SITE=='teletena-payments-v147-fresh.localhost'
assert test_sites==Path('/home/frappe/teletena-communications-release/jobs/sites')
from tele_tena.operations import runtime as rt,capture,providers
original=rt.config

def test_config():
    value=original()
    return {**value,'replay':True,'archive':True,'analytics':False,'errors':False,'alerts':False,'environment':'staging'}
rt.config=test_config
capture.capability=lambda:True
providers.archive_capability=lambda:True

def unavailable(*args,**kwargs):raise providers.Unconfigured('isolated_transport_no_provider')
providers.archive_export=unavailable
providers.archive_delete_provider=unavailable
providers.archive_provider_absent=unavailable
providers.posthog_event=unavailable
providers.bugsink_error=unavailable
providers.telegram=unavailable

def accepted(session,chunk,events):
    # No provider I/O. Only sizes/counts, no raw recording/identity/file metadata.
    raw=json.dumps(events,separators=(',',':')).encode()
    file=Path('/home/frappe/teletena-operations-proof/v154-worker-transport.jsonl')
    fd=os.open(file,os.O_CREAT|os.O_APPEND|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as stream:stream.write(json.dumps({'transport':'synthetic-local','bytes':len(raw),'events':len(events),'sha256':hashlib.sha256(raw).hexdigest()})+'\n')
    return 'ProviderAccepted'
providers.replay_snapshot=accepted
