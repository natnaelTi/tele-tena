"""Read-only live launcher/Bench-library inspection. Never changes Supervisor configuration."""
import argparse,ast,json,os,re,subprocess
from pathlib import Path
NAMES=['frappe-bench-workers:frappe-bench-frappe-long-worker-0','frappe-bench-workers:frappe-bench-frappe-short-worker-0','frappe-bench-workers:frappe-bench-frappe-schedule']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bench',type=Path,required=True);p.add_argument('--external-cli',type=Path,required=True);p.add_argument('--status-file',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--loaded-config',type=Path,required=True);p.add_argument('--no-pending-config-changes',action='store_true');a=p.parse_args();bench=a.bench.resolve();external=a.external_cli.resolve();rows=[];failures=[]
loaded_config=json.loads(a.loaded_config.read_text())
if loaded_config.get('source')!='Supervisor.getAllConfigInfo/getProcessInfo' or not a.no_pending_config_changes:raise SystemExit('FAIL: RPC in-use configuration and resolved pending-config status required')
for name in NAMES:
 line=next((line for line in a.status_file.read_text().splitlines() if line.split() and line.split()[0]==name),'');match=re.search(r'\bRUNNING\s+pid\s+(\d+)',line)
 if not match:raise SystemExit('FAIL: loaded running PID required: '+name)
 pid=int(match.group(1));chain=[];loaded=False
 info=next((row for row in loaded_config['workers'] if row['name']==name),{})
 if not info.get('inuse') or info.get('pid')!=pid or info.get('state')!='RUNNING' or info.get('launcher')!=str(external) or info.get('directory') not in (str(bench),str(bench/'sites')):failures.append('RPC worker/scheduler launcher differs from healthy external CLI')
 while pid>1:
  proc=Path('/proc')/str(pid);argv=(proc/'cmdline').read_bytes().split(b'\0');args=[x.decode(errors='replace') for x in argv if x]
  if not args:raise SystemExit('FAIL: process disappeared; rerun inspection')
  if any(x==str(bench/'env/bin/bench') for x in args):failures.append('Application-env Bench launcher in running ancestry')
  launchers=[x for x in args[:3] if x.startswith('/') and ('/bin/' in x or x.endswith('/supervisord'))]
  module=args[args.index('-m')+1] if '-m' in args and len(args)>args.index('-m')+1 else None
  if len(chain)==0:
   if module!='frappe.utils.bench_helper' or (proc/'cwd').resolve()!=bench/'sites':failures.append('Unexpected loaded Frappe worker/scheduler module or cwd')
   loaded=module=='frappe.utils.bench_helper'
  chain.append({'pid':pid,'launchers':launchers,'python_module':module})
  if any('supervisord' in Path(x).name for x in args[:2]):break
  status=(proc/'status').read_text();pid=int(re.search(r'^PPid:\s+(\d+)',status,re.M).group(1))
 rows.append({'name':name,'process_chain':chain,'frappe_module_loaded':loaded})
# Distinguish runtime dependency imports from dev/test helpers. No source text is emitted.
imports=[];syntax=[]
for app in (bench/'sites/apps.txt').read_text().split():
 root=bench/'apps'/app/app
 if not root.is_dir():root=bench/'apps'/app
 for directory,dirs,files in os.walk(root):
  dirs[:]=[d for d in dirs if d not in {'.git','node_modules','tests','__pycache__','public','frontend','dist'}]
  for filename in files:
   if not filename.endswith('.py') or filename.startswith('test_') or filename.endswith('_test.py'):continue
   file=Path(directory)/filename
   try:tree=ast.parse(file.read_text())
   except (SyntaxError,UnicodeError):syntax.append(str(file.relative_to(bench/'apps')));continue
   for node in ast.walk(tree):
    names=[alias.name for alias in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) else []
    if any(name.split('.')[0] in ('bench','frappe_bench') for name in names):imports.append(str(file.relative_to(bench/'apps')))
if imports or syntax:failures.append('Runtime Bench imports or unparsed Python source require review')
shebang=external.read_text().splitlines()[0]
if not shebang.startswith('#!/') or ' ' in shebang[2:]:raise SystemExit('FAIL: inspect external CLI interpreter manually')
python=Path(shebang[2:]).absolute()
if str(python).startswith(str(bench/'env')):failures.append('External CLI uses application environment')
version=subprocess.check_output([str(python),'-c','import importlib.metadata as m; print(m.version("frappe-bench"))'],text=True).strip()
health=subprocess.run([str(python),'-m','pip','check'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
if version!='5.29.0' or health.returncode:failures.append('External CLI version/environment is not the observed healthy5.29.0')
result={'bench':str(bench),'external_cli':str(external),'external_python':str(python),'external_version':version,'external_pip_check':health.returncode==0,'services':rows,'supervisor_rpc':loaded_config,'no_pending_config_changes':a.no_pending_config_changes,'runtime_bench_imports':sorted(set(imports)),'unparsed_files':syntax,'safe_to_remove_duplicate':not failures,'failures':failures}
fd=os.open(a.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'w') as out:json.dump(result,out,indent=2)
if failures:raise SystemExit('FAIL: launcher/runtime review needed; private report retained')
print('PASS: actual Frappe process ancestry, healthy external CLI, no application-env Bench launchers/runtime imports. No service configuration changed.')
