"""Read-only public HTTPS smoke checks; no credentials, signup, or mutations."""
import argparse
import json
from urllib.parse import urlsplit
from urllib.request import urlopen
from urllib.error import HTTPError

parser = argparse.ArgumentParser()
parser.add_argument('origin', help='HTTPS origin, without path; never a credential-bearing URL')
args = parser.parse_args()
origin = args.origin.rstrip('/')
url = urlsplit(origin)
assert url.scheme == 'https' and url.hostname and not any((url.username,url.password,url.path,url.query,url.fragment)), 'Use an HTTPS origin only'

def read(path):
    try:
        with urlopen(origin + path, timeout=20) as response:
            return response.status, response.headers, response.read()
    except HTTPError as error:
        return error.code, error.headers, error.read()

for path in ('/teletena/', '/teletena/patient/appointments', '/teletena/clinician/availability'):
    status, headers, body = read(path)
    assert status == 200 and b'id="root"' in body and b'/assets/tele_tena/review/assets/' in body, 'Built application route failed'
    assert 'no-store' in headers.get('Cache-Control',''), 'Application shell may be cached'
status, headers, body = read('/teletena/sw.js')
assert status == 200 and 'javascript' in headers.get('Content-Type','') and 'no-store' in headers.get('Cache-Control','')
status, _, body = read('/assets/tele_tena/review/manifest.webmanifest')
manifest = json.loads(body)
assert status == 200 and manifest['scope'] == manifest['start_url'] == '/teletena/'
status, headers, _ = read('/api/method/tele_tena.api.journey.wallet')
assert status == 403 and 'no-store' in headers.get('Cache-Control',''), 'Guest/privacy boundary failed'
status, _, body = read('/assets/tele_tena/review/release.json')
assert status == 200
print('PASS: HTTPS public built routes, namespace, manifest, worker headers and guest rejection. Deployed artifact source SHA:', json.loads(body)['source_commit'])
print('Authenticated journeys, private downloads, scheduler, media devices and remote backup/restore still require operator checks.')
