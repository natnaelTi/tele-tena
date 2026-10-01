"""Read-only inventory, no config contents or secrets. Run on the target host.
python3 remote_preflight.py --bench /absolute/path/to/bench
For Docker, first identify the deployment project and run inside its built backend
image with a read-only checkout; this script neither invokes Docker nor changes it.
"""
import argparse
import ast
import json
from pathlib import Path
import platform
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--bench', type=Path)
args = parser.parse_args()

def command(argv, cwd=None):
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=15)
        return result.stdout.strip() if result.returncode == 0 else 'unavailable'
    except (OSError, subprocess.TimeoutExpired):
        return 'unavailable'

result = {'os': platform.platform(), 'python': platform.python_version(),
          'container_indicator': Path('/.dockerenv').exists(),
          'versions': {name: command([name, '--version']) for name in ('node', 'npm', 'redis-server', 'mariadb', 'bench')},
          'process_managers_present': [name for name in ('docker', 'supervisorctl', 'systemctl', 'nginx', 'caddy') if shutil.which(name)]}
if args.bench:
    root = args.bench.resolve()
    result['bench'] = str(root)
    result['apps'] = {}
    for app in ('frappe', 'erpnext', 'tele_tena'):
        location = root / 'apps' / app
        if location.is_dir():
            result['apps'][app] = {'sha': command(['git', 'rev-parse', 'HEAD'], location),
                                   'branch': command(['git', 'branch', '--show-current'], location)}
    # Site names are enough; never read/print site_config or docker environment.
    for app in result['apps']:
        init = root / 'apps' / app / app / '__init__.py'
        if init.is_file():
            for node in ast.parse(init.read_text()).body:
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets):
                    result['apps'][app]['version'] = ast.literal_eval(node.value)
    result['sites'] = sorted(p.parent.name for p in (root / 'sites').glob('*/site_config.json'))
    python = root / 'env/bin/python'
    if python.exists():
        result['bench_python'] = command([str(python), '--version'])
    result['asset_directory_exists'] = (root / 'sites/assets').is_dir()
print(json.dumps(result, indent=2))
print('Also report: proposed dedicated site/hostname; proxy and TLS termination; worker/scheduler status; Redis/database topology; build/image pipeline; backup/restore procedure. Do not send secrets, config dumps or docker inspect environment output.')
