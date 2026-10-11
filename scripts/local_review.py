"""Scoped lifecycle for the existing local MVP preview; never migrates or seeds.
Run with the Bench Python. Database and shared cache Redis must already be up.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.request

REPO = Path(__file__).resolve().parents[1]
BENCH = REPO.parents[1]
RUNTIME = Path('/home/frappe/teletena-mvp-runtime')
SITE = 'teletena-mvp-presentation.localhost'
URL = 'http://127.0.0.1:8017/teletena/'
WEB_PID = RUNTIME / 'web.pid'


def owned_pid(name):
    file = RUNTIME / (name + '.pid')
    if not file.exists():
        return None
    pid = int(file.read_text().strip())
    proc = Path('/proc') / str(pid)
    if not proc.exists():
        return None
    command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
    cwd = (proc / 'cwd').resolve()
    if name == 'web':
        valid = 'gunicorn' in command and 'scripts.review_test_wsgi:application' in command and '127.0.0.1:8017' in command and cwd == BENCH / 'sites'
        environment = (proc / 'environ').read_bytes().split(b'\0')
        valid = valid and ('TELE_TENA_TEST_SITE=' + SITE).encode() in environment
    elif name == 'queue-redis':
        valid = 'redis-server 127.0.0.1:13917' in command and cwd == RUNTIME / 'redis'
    else:
        valid = 'frappe.utils.bench_helper' in command and cwd == RUNTIME / 'sites' and (' worker ' if name == 'worker' else ' schedule') in command
    if not valid:
        raise RuntimeError(f'{name} PID is not owned by this preview; no signal sent')
    return pid


def status():
    print('Site:', SITE, '\nBench:', BENCH, '\nURL:', URL)
    print('Source:', subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip())
    manifest = json.loads((REPO / 'tele_tena/public/review/release.json').read_text())
    print('Packaged source:', manifest['source_commit'])
    for name in ('web', 'queue-redis', 'worker', 'scheduler'):
        print(name + ':', owned_pid(name) or 'stopped')
    try:
        with urllib.request.urlopen(URL, timeout=5) as response:
            print('HTTP:', response.status)
    except Exception:
        print('HTTP: unreachable')


def stop():
    # Scheduler first; worker drains its current job; queue remains until it exits.
    for name in ('scheduler', 'web', 'worker', 'queue-redis'):
        pid = owned_pid(name)
        if not pid:
            continue
        os.kill(pid, signal.SIGTERM)
        for _ in range(60):
            proc = Path('/proc') / str(pid)
            if not proc.exists() or ') Z ' in (proc / 'stat').read_text():
                break
            time.sleep(0.5)
        else:
            raise RuntimeError(f'{name} still stopping; queue retained, no force kill')
        (RUNTIME / (name + '.pid')).unlink(missing_ok=True)
    print('Only owned preview services stopped; shared Bench unchanged.')


def start():
    if not (BENCH / 'sites' / SITE / 'site_config.json').exists():
        raise RuntimeError('Expected presentation site absent; no new site created')
    RUNTIME.mkdir(exist_ok=True)
    with socket.socket() as probe:
        occupied = probe.connect_ex(('127.0.0.1', 8017)) == 0
    if occupied and not owned_pid('web'):
        raise RuntimeError('Port 8017 belongs to another process; no process changed')
    env = dict(os.environ, TELE_TENA_TEST_SITE=SITE)
    subprocess.run([str(BENCH / 'env/bin/python'), str(REPO / 'scripts/start_presentation_processing.py')], env=env, cwd=REPO, check=True)
    if not owned_pid('web'):
        command = [str(BENCH / 'env/bin/gunicorn'), '--daemon', '--bind', '127.0.0.1:8017', '--workers', '2', '--pid', str(WEB_PID), '--pythonpath', str(REPO), '--chdir', str(BENCH / 'sites'), '--error-logfile', str(RUNTIME / 'logs/web.log'), 'scripts.review_test_wsgi:application']
        subprocess.run(command, env=env, cwd=REPO, check=True)
    for _ in range(20):
        try:
            with urllib.request.urlopen(URL, timeout=2) as response:
                if response.status == 200:
                    status()
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError('Preview did not become ready; inspect private runtime logs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'status', 'stop'))
    args = parser.parse_args()
    try:
        {'start': start, 'stop': stop, 'status': status}[args.action]()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
