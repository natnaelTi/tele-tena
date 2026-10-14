"""Read-only narrow Selfmade repair guard. Never installs, uninstalls or edits apps."""
import argparse
import hashlib
import importlib.metadata as md
import json
import os
from pathlib import Path
import subprocess
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from dependency_checkpoint import canonical,identity,installed_details,private_write

PINS={'requests':'2.32.5','cryptography':'46.0.7','oauthlib':'3.2.2','websockets':'15.0.1','boto3':'1.43.113','botocore':'1.43.113','s3transfer':'0.19.2'}
SOURCE='7acdf6c8596c3a4f741675d2bb51dab6e6b95b14'
PROVENANCE={'pypika':('0.48.9','2c50e6142b2d61d2d243e466fdd5dc03b3d918f2','2e20dcdf385c05b6ee2dbfdaa3f69a6dca83b15562bcd8f4dc3e57c39d3759bc'),'gunicorn':('23.0.0','bb554053bb87218120d76ab6676af7015680e8b6','e05c000e9e3e2b10dc1c4f180c72332979b6eac418ec67fc7c66f789dc6af853')}


def read_private(path):
 if path.is_symlink() or path.stat().st_uid!=os.getuid() or path.stat().st_mode&0o077:raise ValueError('Evidence must be an owned private file: '+path.name)
 return json.loads(path.read_text())


def audit_candidate(audit,proposed):
 missing=set(audit['missing_bench_app_metadata'])
 if missing-{'frappe_pawapay'}:raise ValueError('Unaudited Bench app metadata')
 pawapay=[r for r in audit['app_declared_dependency_edges'] if r['requires_from']=='frappe_pawapay']
 if missing and {(r['dependency'],r['constraint']) for r in pawapay}!={('http-message-signatures','<2.0,>=1.0'),('http-sfv','<1.0,>=0.9')}:raise ValueError('Missing explicit PaWaPay source requirements')
 unresolved=audit['unresolved_source_inputs']
 if any(r['owner']!='frappe' or r['reason']!='Direct source requirement needs private provenance review' for r in unresolved):raise ValueError('Unresolved source requirements')
 # Known Frappe direct requirements are independently provenance-protected.
 before=audit['installed_packages'];after={n:dict(r) for n,r in before.items() if n!='frappe-bench'}
 for n,v in PINS.items():
  if n not in before:raise ValueError('Unexpected missing repair distribution: '+n)
  after[n]={'version':v,'identity':None}
 for n,row in proposed.items():after[n]=row
 for row in audit['focused_requirement_edges']+audit['app_declared_dependency_edges']:
  owner=canonical(row['requires_from']);dep=row['dependency']
  if owner=='frappe-bench':continue
  if row['source']=='distribution' and owner in PINS:continue # replacement metadata checked separately
  constraint='~=1.43.113' if owner=='ecommerce-integrations' and dep=='boto3' else row['constraint']
  if row['direct_url_requirement'] and dep not in PROVENANCE:raise ValueError('Unreviewed direct source requirement')
  if dep not in after or after[dep]['version'] not in SpecifierSet(constraint):raise ValueError('Incompatible requirement: '+owner+' -> '+dep+' '+constraint)
 return after


def check_plan(before,report,app_path,audit):
 proposed={};requirements={}
 for item in report['install']:
  name=canonical(item['metadata']['name'])
  if name in proposed:raise ValueError('Duplicate plan distribution')
  if name not in set(PINS)|{'ecommerce-integrations'}:raise ValueError('Unrelated replacement/addition: '+name)
  expected=before['ecommerce-integrations']['version'] if name=='ecommerce-integrations' else PINS[name]
  if item['metadata']['version']!=expected:raise ValueError('Unreviewed version: '+name)
  source=identity(item.get('download_info')) if item.get('is_direct') else None
  if name=='ecommerce-integrations' and source!={'editable':True,'path':str(app_path.resolve())}:raise ValueError('Amazon editable identity differs')
  if name!='ecommerce-integrations' and source:raise ValueError('Unexpected direct package source')
  proposed[name]={'version':expected,'identity':source};requirements[name]=item['metadata'].get('requires_dist') or []
 if 'ecommerce-integrations' not in proposed:raise ValueError('Amazon metadata must be rebuilt')
 required={n for n,v in PINS.items() if before.get(n,{}).get('version')!=v}
 if not required.issubset(proposed):raise ValueError('Plan omits required version repairs')
 if 'boto3' not in requirements or 'botocore' not in requirements or 's3transfer' not in requirements:raise ValueError('SDK pair and transfer metadata required in upgrade plan')
 after=audit_candidate(audit,proposed)
 for owner,raw_requirements in requirements.items():
  for raw in raw_requirements:
   req=Requirement(raw)
   if req.marker and not req.marker.evaluate({'extra':''}):continue
   name=canonical(req.name)
   if req.url:raise ValueError('Unreviewed direct dependency')
   if name not in after or after[name]['version'] not in req.specifier:raise ValueError('Replacement metadata incompatible: '+owner+' -> '+name)
 if not any(Requirement(raw).name.lower()=='boto3' and str(Requirement(raw).specifier)=='~=1.43.113' for raw in requirements['ecommerce-integrations']):raise ValueError('Amazon source patch metadata absent')
 return proposed


def check_preserved(before,after,approved):
 if 'frappe-bench' in after:raise ValueError('Duplicate application Bench distribution remains')
 expected={n:row for n,row in before.items() if n!='frappe-bench'};expected.update(approved)
 for name,row in expected.items():
  if after.get(name)!=row:raise ValueError('Version/identity changed outside approved plan: '+name)
 if set(after)!=set(expected):raise ValueError('Unplanned package addition/removal')


def source_commits(bench):
 return {app:subprocess.check_output(['git','-C',str(bench/'apps'/app),'rev-parse','HEAD'],text=True).strip() for app in (bench/'sites/apps.txt').read_text().split()}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['snapshot','plan','verify']);p.add_argument('directory',type=Path);p.add_argument('--bench',type=Path,required=True);p.add_argument('--audit',type=Path);p.add_argument('--launchers',type=Path);p.add_argument('--report',type=Path);p.add_argument('--amazon-commit');p.add_argument('--stage',action='store_true');p.add_argument('--amazon-path',type=Path);a=p.parse_args();bench=a.bench.resolve();original_app=bench/'apps/ecommerce_integrations';app=a.amazon_path.resolve() if a.amazon_path else original_app
  
 try:
  import sys
  if a.stage and (Path(sys.prefix).resolve()==bench/'env' or app==original_app):raise ValueError('Staging requires copied environment and separate Amazon worktree')
  if not a.stage and (Path(sys.prefix).resolve()!=bench/'env' or app!=original_app):raise ValueError('Production guard requires exact original environment/app paths')
  if a.action=='snapshot':
   if not a.audit or not a.launchers:raise ValueError('Audit and live launcher evidence required')
   audit=read_private(a.audit);launchers=read_private(a.launchers);before=installed_details()
   if set(audit['bench_apps'])!=set((bench/'sites/apps.txt').read_text().split()):raise ValueError('Bench app list differs from audit')
   if before!=audit['installed_packages']:raise ValueError('Audit does not match current package snapshot')
   if not launchers.get('safe_to_remove_duplicate') or launchers['bench']!=str(bench):raise ValueError('Loaded launchers/runtime consumers not verified')
   if before.get('frappe-bench',{}).get('version')!='5.29.0':raise ValueError('Unexpected duplicate Bench version')
   for name,(version,commit,source_hash) in PROVENANCE.items():
    direct=json.loads(md.distribution(name).read_text('direct_url.json') or '{}')
    if before.get(name)!={'version':version,'identity':{'editable':False,'source_hash':source_hash}} or direct.get('vcs_info',{}).get('commit_id')!=commit:raise ValueError('Direct-source provenance differs: '+name)
   commits=source_commits(bench)
   if commits['ecommerce_integrations']!=SOURCE or subprocess.check_output(['git','-C',str(original_app),'status','--porcelain'],text=True).strip():raise ValueError('Amazon source must be clean at reviewed baseline')
   audit_candidate(audit,{})
   a.directory.mkdir(mode=0o700,parents=True,exist_ok=False)
   for filename,value in [('packages.json',before),('audit.json',audit),('launchers.json',launchers),('app-commits.json',commits),('context.json',{'bench':str(bench),'app':str(app),'stage':a.stage})]:private_write(a.directory,filename,json.dumps(value,indent=2))
   constraints=''.join(f'{name}=={row["version"]}\n' for name,row in sorted(before.items()) if name not in set(PINS)|{'frappe-bench','ecommerce-integrations'})
   private_write(a.directory,'constraints.txt',constraints);private_write(a.directory,'repair-pins.txt',''.join(f'{n}=={v}\n' for n,v in PINS.items()))
   print('PASS: private full baseline, direct-source identities, all-app intersections and loaded launchers recorded');return
  if a.directory.is_symlink() or a.directory.stat().st_mode&0o077:raise ValueError('Snapshot directory must be private')
  before=read_private(a.directory/'packages.json');audit=read_private(a.directory/'audit.json');context=read_private(a.directory/'context.json')
  if context!={'bench':str(bench),'app':str(app),'stage':a.stage}:raise ValueError('Snapshot belongs to another Bench')
  if a.action=='plan':
   if not a.report:raise ValueError('Pip report required')
   approved=check_plan(before,read_private(a.report),app,audit);private_write(a.directory,'approved.json',json.dumps(approved,indent=2));print('PASS: only reviewed7 versions/Amazon metadata; unrelated identities and urllib3/Click remain protected')
  else:
   if not a.amazon_commit:raise ValueError('Pinned Amazon patch commit required')
   approved=read_private(a.directory/'approved.json');check_preserved(before,installed_details(),approved)
   launchers=read_private(a.directory/'launchers.json');link=Path(sys.prefix)/'bin/bench'
   if not link.is_symlink() or link.resolve()!=Path(launchers['external_cli']).resolve():raise ValueError('Application/staging Bench compatibility link must point to the healthy external CLI')
   expected=read_private(a.directory/'app-commits.json');expected['ecommerce_integrations']=SOURCE if a.stage else a.amazon_commit
   if subprocess.check_output(['git','-C',str(app),'rev-parse','HEAD'],text=True).strip()!=a.amazon_commit:raise ValueError('Amazon worktree does not contain reviewed patch commit')
   if source_commits(bench)!=expected:raise ValueError('App commit changed outside approved Amazon patch')
   subprocess.run([os.sys.executable,'-m','pip','check'],check=True)
   print('PASS: exact approved repair, all protected versions/editable identities/app commits, clean pip check')
 except (ValueError,OSError,KeyError,json.JSONDecodeError,subprocess.CalledProcessError) as e:raise SystemExit('FAIL: '+str(e)) from None
if __name__=='__main__':main()
