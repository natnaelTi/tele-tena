"""Build locked frontend dependencies and publish app-owned Frappe static assets.
Run as normal bench user: python3 apps/tele_tena/scripts/build_review.py
No site configuration or credentials are read by this build.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

APP = Path(__file__).resolve().parents[1]
FRONTEND = APP / 'frontend'
# Reject local env files: Vite otherwise embeds VITE_* values automatically.
assert not list(FRONTEND.glob('.env*')), 'Remove frontend .env files before a release build'
env = {k: v for k, v in os.environ.items() if not k.startswith('VITE_')}
subprocess.run(['npm', 'ci'], cwd=FRONTEND, env=env, check=True)
subprocess.run(['npm', 'run', 'build'], cwd=FRONTEND, env=env, check=True)
dist = FRONTEND / 'dist'
(dist / 'licenses').mkdir(exist_ok=True)
for font in ('manrope', 'noto-sans-ethiopic'):
    shutil.copyfile(FRONTEND / 'node_modules/@fontsource' / font / 'LICENSE', dist / 'licenses' / (font + '.txt'))
manifest = json.loads((dist / 'manifest.webmanifest').read_text())
manifest.update(id='/teletena/', start_url='/teletena/', scope='/teletena/')
for icon in manifest['icons']:
    icon['src'] = '/assets/tele_tena/review/' + icon['src'].lstrip('/')
(dist / 'manifest.webmanifest').write_text(json.dumps(manifest, indent=2) + '\n')
offline = dist / 'offline.html'
offline.write_text(offline.read_text().replace('src="/brand/', 'src="/assets/tele_tena/review/brand/').replace('href="/"', 'href="/teletena/"'))
source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=APP, text=True).strip()
worker = dist / 'sw.js'
worker.write_text(worker.read_text().replace('tele-tena-public-v2', 'tele-tena-public-' + source[:12]))
lock = hashlib.sha256((FRONTEND / 'package-lock.json').read_bytes()).hexdigest()
(dist / 'release.json').write_text(json.dumps({'source_commit': source, 'frontend_lock_sha256': lock,
    'files': {str(p.relative_to(dist)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(dist.rglob('*')) if p.is_file() and p.name != 'release.json'}}, indent=2) + '\n')
target = APP / 'tele_tena/public/review'
# Retain old hashed assets for open clients; never auto-reload an active call.
shutil.copytree(dist, target, dirs_exist_ok=True)
print('Built Frappe assets for source commit ' + source)
