"""Emit safe, exact build-environment metadata; no site configuration is read."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess

APP = Path(__file__).resolve().parents[1]
BENCH = APP.parents[1]
def command(args, cwd=APP):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()
lock = json.loads((APP / 'frontend/package-lock.json').read_text())
result = {'inspected_source_commit': command(['git','rev-parse','HEAD']),
          'product_dependency': {'pr': 7, 'commit': '84bd97296e2030e679f621f7d8776921b65f0ec6'},
          'python': platform.python_version(), 'node': command(['node','--version']),
          'npm': command(['npm','--version']), 'database_client': command(['mariadb','--version']),
          'redis_server': command(['redis-server','--version']),
          'apps': {app: {'commit': command(['git','rev-parse','HEAD'], BENCH / 'apps' / app),
                         'version': importlib.metadata.version(app)} for app in ('frappe','erpnext')},
          'python_packages': {name: importlib.metadata.version(name) for name in
                              ('livekit-api','livekit-protocol','gunicorn','redis','rq','PyMySQL')},
          'frontend_lock_sha256': hashlib.sha256((APP / 'frontend/package-lock.json').read_bytes()).hexdigest(),
          'frontend_packages': {name: value['version'] for name,value in lock['packages'].items() if name and 'version' in value}}
print(json.dumps(result, indent=2))
