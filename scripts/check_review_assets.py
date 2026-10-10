"""Check built artifact structure and optional exact credential leakage, without printing secrets."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--site-private', type=Path, help='Optional local private directory; only known provider credential files are read')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1] / 'tele_tena/public/review'
release = json.loads((root / 'release.json').read_text())
for name, digest in release['files'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, 'Artifact hash mismatch'
assert '/assets/tele_tena/review/assets/' in (root / 'index.html').read_text()
manifest = json.loads((root / 'manifest.webmanifest').read_text())
assert manifest['scope'] == manifest['start_url'] == '/teletena/'
files = [p for p in root.rglob('*') if p.is_file()]
assert not any(p.suffix == '.map' or p.name.startswith('.env') or p.name == 'site_config.json' for p in files)
secrets = []
if args.site_private:
    for name, fields in {'tele_tena_livekit.json':['api_key','api_secret'],
                         'tele_tena_sms.json':['api_key'], 'tele_tena_email.json':['username','password']}.items():
        path = args.site_private / name
        if path.exists():
            values = json.loads(path.read_text())
            secrets.extend(str(values[key]).encode() for key in fields if values.get(key))
    account_file = args.site_private / 'tele_tena_review_accounts.json'
    if account_file.exists():
        values = json.loads(account_file.read_text())
        assert isinstance(values, dict), 'Unexpected local account credential format'
        secrets.extend(value.encode() for value in values.values() if isinstance(value, str) and value)
for path in files:
    content = path.read_bytes()
    assert b'127.0.0.1:5173' not in content and b'erp.localhost' not in content, 'Development URL in packaged asset'
    assert not any(secret in content for secret in secrets), 'Credential found in asset (value withheld)'
print('PASS: artifact hashes, application scope, no source maps/config files; exact private credential scan count:', len(secrets))
