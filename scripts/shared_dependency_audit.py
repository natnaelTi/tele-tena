"""Read-only all-distribution AND all-Bench-app requirement audit; no secrets/install."""
import argparse
import ast
import configparser
import importlib.metadata as md
import json
from pathlib import Path
import tomllib
from packaging.requirements import Requirement, InvalidRequirement
from dependency_checkpoint import canonical, installed_details

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bench',type=Path);args=parser.parse_args()
focus={'urllib3','cryptography','click','requests','oauthlib','websockets','boto3','botocore','frappe-bench','http-message-signatures','http-sfv','pypika','gunicorn','s3transfer','jmespath'}
installed=installed_details();rows=[];conflicts=[];source_edges=[];unresolved=[]

def edge(owner,version,raw,kind):
    try:r=Requirement(raw)
    except InvalidRequirement:
        unresolved.append({'owner':owner,'source':kind,'reason':'Unparsed requirement; inspect privately'});return
    if r.marker and not r.marker.evaluate({'extra':''}):return
    dep=canonical(r.name);version_found=installed.get(dep,{}).get('version')
    valid=bool(version_found and (not r.specifier or version_found in r.specifier))
    row={'requires_from':owner,'owner_version':version,'source':kind,'dependency':dep,'constraint':str(r.specifier),'installed':version_found,'satisfied':valid,'direct_url_requirement':bool(r.url)}
    if r.url:unresolved.append({'owner':owner,'source':kind,'reason':'Direct source requirement needs private provenance review'})
    if dep in focus:rows.append(row)
    if kind!='distribution':source_edges.append(row)
    if not valid:conflicts.append(row)

for d in md.distributions():
    name=canonical(d.metadata['Name'])
    for raw in d.requires or []:edge(name,d.version,raw,'distribution')
bench_apps=(args.bench/'sites/apps.txt').read_text().split() if args.bench else []
missing=[app for app in bench_apps if canonical(app) not in installed]
for app in bench_apps:
    root=args.bench/'apps'/app;version=installed.get(canonical(app),{}).get('version');found=False
    project=root/'pyproject.toml'
    if project.exists():
        data=tomllib.loads(project.read_text()).get('project',{})
        if 'dependencies' in data:
            found=True
            for raw in data['dependencies']:edge(app,version,raw,'pyproject.toml')
    cfg=root/'setup.cfg'
    if cfg.exists():
        data=configparser.ConfigParser();data.read(cfg)
        if data.has_option('options','install_requires'):
            found=True
            for raw in data.get('options','install_requires').splitlines():
                if raw.strip():edge(app,version,raw.strip(),'setup.cfg')
    req=root/'requirements.txt'
    if req.exists():
        found=True
        for line,raw in enumerate(req.read_text().splitlines(),1):
            raw=raw.strip()
            if not raw or raw.startswith('#'):continue
            if raw.startswith('-'):
                unresolved.append({'owner':app,'source':'requirements.txt:'+str(line),'reason':'Nested/option requirement; inspect privately'})
            else:edge(app,version,raw,'requirements.txt:'+str(line))
    setup=root/'setup.py'
    if not found and setup.exists():
        for node in ast.walk(ast.parse(setup.read_text())):
            if isinstance(node,ast.keyword) and node.arg=='install_requires':
                try:values=ast.literal_eval(node.value)
                except (ValueError,TypeError):continue
                if isinstance(values,list) and all(isinstance(raw,str) for raw in values):
                    found=True
                    for raw in values:edge(app,version,raw,'setup.py literal')
        if not found:unresolved.append({'owner':app,'source':'setup.py','reason':'Dynamic requirements need private review; code was not executed'})
print(json.dumps({'bench_apps':bench_apps,'missing_bench_app_metadata':missing,'installed_packages':installed,'focused_requirement_edges':rows,'app_declared_dependency_edges':source_edges,'all_active_conflicts':conflicts,'unresolved_source_inputs':unresolved,'optional_extras':'Not inferred; operator must identify deployed extras and CLI/service environments.'},indent=2))
