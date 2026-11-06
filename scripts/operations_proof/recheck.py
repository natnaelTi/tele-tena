"""Resume the same authorized run after its exact 25-hour deadline.
No new capture, errors, maps or messages. No daemon/scheduler is installed.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tele_tena.operations.proof import ProofRun, ProofBlocked


def deletion_keys(manifest, config, identifier):
    """One explicit credential-corrected retry of a known403; never unknown I/O."""
    key = 'provider-delete-' + identifier
    prior = manifest['actions'].get(key)
    if not prior or prior.get('http_status') != 403:
        return key, 'provider-delete-confirm-' + identifier
    row = next(x for x in manifest['recordings'] if x['id'] == identifier)
    current = hashlib.sha256(config.get('posthog_delete_key', '').encode()).hexdigest()
    if (not row.get('deletion_retry_authorized')
            or not row.get('denied_key_observed_sha256')
            or (current == row['denied_key_observed_sha256']
                and not row.get('deletion_permission_change_confirmed'))):
        raise ProofBlocked('corrected_delete_key_and_owner_confirmation_required')
    attempt = row.get('deletion_retry_authorized_attempts', 1)
    if type(attempt) is not int or attempt not in (1, 2):
        raise ProofBlocked('bounded_delete_retry_authorization_required')
    if attempt == 2:
        previous = manifest['actions'].get('provider-delete-retry-1-' + identifier, {})
        if previous.get('state') != 'HTTPResponse' or previous.get('http_status') != 403:
            raise ProofBlocked('known_denial_required_for_next_retry')
    return 'provider-delete-retry-' + str(attempt) + '-' + identifier, 'provider-delete-confirm-retry-' + str(attempt) + '-' + identifier


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--delete-verified-tests', action='store_true')
    args = parser.parse_args()
    run = ProofRun(args.root)
    manifest, config = run.checked()
    repo = Path(__file__).resolve().parents[2]
    if not manifest['recordings']:
        print('No live recordings exist; no recheck or deletion performed.')
        return
    for recording in manifest['recordings']:
        due = recording.get('recheck_due_at')
        if not due or datetime.now(timezone.utc) < datetime.fromisoformat(due):
            print('PENDING 25-hour checkpoint; due UTC:', due)
            return
    subprocess.run([sys.executable, str(repo / 'scripts/operations_proof/export.py'),
                    '--root', str(args.root), '--output', str(args.output), '--settled'], check=True)
    complete = True
    for recording in run.checked()[0]['recordings']:
        if recording.get('settled_export') != 'Complete':
            print('Settled export incomplete; playback/deletion stopped.')
            complete = False
            continue
        # Resume from this exact verified artifact, not a previous provisional file.
        name = recording['archive_path']
        if Path(name).name != name or not name.endswith('-settled.json.gz'):
            raise ProofBlocked('settled_artifact_required')
        with gzip.open(args.output / name, 'rb') as stream:
            content = stream.read(10 * 1024**2 + 1)
        if len(content) > 10 * 1024**2:
            raise ProofBlocked('recording_size_limit')
        data = json.loads(content)
        if data['sha256'] != recording['settled_sha256']:
            raise ProofBlocked('settled_artifact_mismatch')
        run._write(args.output / 'normalized-recording.json', data)
        env = dict(os.environ, TELE_TENA_PROOF_ROOT=str(args.output),
                   NODE_PATH='/home/frappe/teletena-browser-tools/node_modules')
        result = subprocess.run(['node', str(repo / 'scripts/operations_proof/playback.cjs')],
                                env=env, capture_output=True)
        if result.returncode:
            print('Independent playback failed; deletion stopped.')
            complete = False
            continue
        playback = json.loads((args.output / 'playback-result.json').read_text())
        if (playback.get('state') != 'Rendered' or playback.get('network_requests') != 0
                or playback.get('sha256') != recording['settled_sha256']):
            raise ProofBlocked('independent_playback_not_verified')
        with run.locked():
            manifest, config = run.checked()
            row = next(x for x in manifest['recordings'] if x['id'] == recording['id'])
            row['settled_playback'] = 'VerifiedOffline'
            row['player_version'] = 'teletena-sandbox-web-v1'
            run._write(run.manifest, manifest)
        print('Settled complete export and independent playback verified.')
        if not args.delete_verified_tests:
            complete = False
            continue
        identifier = recording['id']
        path = '/api/projects/' + str(config['posthog_project_id']) + '/session_recordings/' + identifier + '/'
        manifest, config = run.checked()
        key, confirm_key = deletion_keys(manifest, config, identifier)
        if key not in manifest['actions']:
            status, _ = run.request(key, 'posthog_api', path, method='DELETE',
                                    costs={'recording_deletes': 1}, maximum=65536)
            print('New test recording DELETE HTTP status:', status)
        key = confirm_key
        manifest, config = run.checked()
        if key not in manifest['actions']:
            status, _ = run.request(key, 'posthog_api', path,
                                    costs={'deletion_confirmation_gets': 1}, maximum=65536)
            if status == 404:
                with run.locked():
                    manifest, config = run.checked()
                    row = next(x for x in manifest['recordings'] if x['id'] == identifier)
                    row['provider_deletion'] = 'ConfirmedAbsent'
                    run._write(run.manifest, manifest)
                print('Exact new test recording deletion confirmed absent.')
            else:
                print('Provider deletion remains unverified; no automatic resend.')
        row = next(x for x in run.checked()[0]['recordings'] if x['id'] == identifier)
        complete = complete and row.get('provider_deletion') == 'ConfirmedAbsent'
    if not complete:
        print('Checkpoint incomplete; no certificate or activation created.')
        return
    # Retain only proof metadata. Do not bind this certificate to any site/config.
    proof = {'project_id': str(config['posthog_project_id']), 'format': 'teletena-web-replay-v1',
             'settled_export': True, 'independent_playback': True, 'provider_deletion_verified': True,
             'player_sha256': hashlib.sha256((repo / 'tele_tena/operations/player.js').read_bytes()).hexdigest(),
             'verified_at': datetime.now(timezone.utc).isoformat(), 'production_activation': False}
    run._write(args.root / 'archive-proof-v1.json', proof)
    # Only this run's synthetic raw proof artifacts. Keep ledger, checksums, result.
    for recording in run.checked()[0]['recordings']:
        digest = hashlib.sha256(recording['id'].encode()).hexdigest()
        for phase in ('provisional', 'settled'):
            (args.output / ('replay-' + digest + '-' + phase + '.json.gz')).unlink(missing_ok=True)
    for name in ('normalized-recording.json', 'live-capture-frames.json'):
        (args.output / name).unlink(missing_ok=True)
    with run.locked():
        manifest, config = run.checked()
        manifest['authorization']['status'] = 'Completed'
        manifest['authorization']['completed_at'] = datetime.now(timezone.utc).isoformat()
        manifest['phase'] = 'Completed'
        run._write(run.manifest, manifest)
    print('Proof completed; private certificate is unbound. One-run authorization closed. Production remains disabled.')


if __name__ == '__main__':
    main()
