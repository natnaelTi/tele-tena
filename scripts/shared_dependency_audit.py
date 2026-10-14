"""Read-only all-distribution requirement audit; no URLs, credentials or installs."""
import importlib.metadata as md
import json
from packaging.requirements import Requirement
from dependency_checkpoint import canonical, installed_details

focus={'urllib3','cryptography','click','requests','oauthlib','websockets','boto3','botocore','frappe-bench'}
installed=installed_details();rows=[];conflicts=[]
for d in md.distributions():
 name=canonical(d.metadata['Name'])
 for raw in d.requires or []:
  r=Requirement(raw)
  if r.marker and not r.marker.evaluate({'extra':''}):continue
  dep=canonical(r.name);version=installed.get(dep,{}).get('version')
  valid=bool(version and (not r.specifier or version in r.specifier))
  row={'requires_from':name,'owner_version':d.version,'dependency':dep,'constraint':str(r.specifier),'installed':version,'satisfied':valid,'direct_url_requirement':bool(r.url)}
  if dep in focus:rows.append(row)
  if not valid:conflicts.append(row)
print(json.dumps({'installed_packages':installed,'focused_requirement_edges':rows,'all_active_conflicts':conflicts,'optional_extras':'Not inferred; operator must identify deployed extras and CLI/service environments.'},indent=2))
