"""Start native scheduler/RQ against only the named local presentation site.
Isolated loopback queue Redis prevents unrelated workers from consuming its jobs.
No framework edits, global restart, queue draining, or business-job invocation.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import time

BENCH=Path(__file__).resolve().parents[3]
SITE='teletena-mvp-presentation.localhost'
RUNTIME=Path('/home/frappe/teletena-mvp-runtime')
PORT=13917


def alive(pid):
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False


def daemon(name,command,env,cwd):
    pidfile=RUNTIME/(name+'.pid')
    if pidfile.exists() and alive(int(pidfile.read_text())):
        pid=int(pidfile.read_text())
        actual=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        expected=[part.encode() for part in command]
        redis_owned=name=='queue-redis' and b'redis-server 127.0.0.1:13917' in b' '.join(actual) and Path(f'/proc/{pid}/cwd').resolve()==RUNTIME/'redis'
        if not redis_owned and actual[:len(expected)]!=expected:
            raise RuntimeError(name+' PID belongs to a different command; no process changed')
        return
    log=open(RUNTIME/'logs'/(name+'.log'),'ab')
    process=subprocess.Popen(command,cwd=cwd,env=env,stdout=log,stderr=log,start_new_session=True)
    pidfile.write_text(str(process.pid));time.sleep(1)
    if process.poll() is not None:raise RuntimeError(name+' failed; inspect its private runtime log')


def run():
    assert os.environ.get('TELE_TENA_TEST_SITE')==SITE,'Explicit site required'
    assert (BENCH/'sites'/SITE/'site_config.json').exists()
    for folder in ('sites','config','logs','redis'):
        (RUNTIME/folder).mkdir(parents=True,exist_ok=True)
    os.chmod(RUNTIME,0o700)
    for name,target in [('env',BENCH/'env'),('apps',BENCH/'apps'),('sites/assets',BENCH/'sites/assets')]:
        link=RUNTIME/name
        if not link.exists():link.symlink_to(target)
        assert link.resolve()==target.resolve()
    site_directory=RUNTIME/'sites'/SITE
    if site_directory.is_symlink():site_directory.unlink()
    site_directory.mkdir(exist_ok=True)
    # Native get_sites excludes a symlinked site directory. Link its contents
    # instead, so scheduler discovery sees one real directory and preserved data.
    for item in (BENCH/'sites'/SITE).iterdir():
        if item.name=='site_config.json':continue
        link=site_directory/item.name
        if not link.exists():link.symlink_to(item)
        assert link.resolve()==item.resolve()
    (RUNTIME/'sites/apps.txt').write_text((BENCH/'sites/apps.txt').read_text())
    existing=json.loads((BENCH/'sites/common_site_config.json').read_text())
    from_config={'redis_queue':f'redis://127.0.0.1:{PORT}',
                 'redis_cache':existing['redis_cache'],
                 'bench_id':str(BENCH).strip('/').replace('/','-'),
                 'scheduler_tick_interval':10,'scheduler_interval':10,'maintenance_mode':0}
    # Some environments have explicit DB host settings. Copy only needed keys.
    for key in ('db_host','db_port','redis_socketio'):
        if key in existing:from_config[key]=existing[key]
    config=RUNTIME/'sites/common_site_config.json'
    config.write_text(json.dumps(from_config,indent=2));os.chmod(config,0o600)
    redis_pid=RUNTIME/'queue-redis.pid'
    if not redis_pid.exists() or not alive(int(redis_pid.read_text())):
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1',PORT))==0:raise RuntimeError('Queue port already in use; no process changed')
    env=dict(os.environ,FRAPPE_BENCH_ROOT=str(RUNTIME),PYTHONPATH=str(BENCH/'apps/frappe')+':'+str(BENCH/'apps/tele_tena'))
    daemon('queue-redis',['redis-server','--bind','127.0.0.1','--port',str(PORT),'--dir',str(RUNTIME/'redis'),'--appendonly','yes'],env,RUNTIME)
    siteconfig=BENCH/'sites'/SITE/'site_config.json'
    before=RUNTIME/'site-config-before-processing.json'
    if not before.exists():before.write_bytes(siteconfig.read_bytes());os.chmod(before,0o600)
    values=json.loads(siteconfig.read_text())
    values.update(redis_queue=f'redis://127.0.0.1:{PORT}',disable_scheduler=1,pause_scheduler=0)
    siteconfig.write_text(json.dumps(values,indent=2));os.chmod(siteconfig,0o600)
    isolated_config=site_directory/'site_config.json'
    if isolated_config.is_symlink():isolated_config.unlink()
    isolated_values=dict(values,disable_scheduler=0)
    isolated_config.write_text(json.dumps(isolated_values,indent=2));os.chmod(isolated_config,0o600)
    # Shared Bench scheduler sees disable_scheduler=1. Only this native
    # scheduler sees the private override; both use the preserved site DB.
    python=str(BENCH/'env/bin/python')
    base=[python,'-m','frappe.utils.bench_helper','frappe']
    daemon('worker',base+['worker','--queue','short,default,long'],env,RUNTIME/'sites')
    daemon('scheduler',base+['schedule'],env,RUNTIME/'sites')
    print('Native isolated scheduler/worker started for '+SITE+'; loopback queue '+str(PORT)+'. No other service restarted.')

if __name__=='__main__':run()
