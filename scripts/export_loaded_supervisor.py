"""Read-only Supervisor RPC command evidence; run with supervisorctl's system interpreter."""
import hashlib,json,shlex
from supervisor.options import ClientOptions
options=ClientOptions();options.realize([]);server=options.getServerProxy().supervisor
rows=[]
for row in server.getAllConfigInfo():
 if row['group']!='frappe-bench-workers':continue
 name=row['group']+':'+row['name'];running=server.getProcessInfo(name);command=row['command'];argv=shlex.split(command)
 rows.append({'name':name,'inuse':bool(row['inuse']),'directory':row.get('directory'),'launcher':argv[0] if argv else None,'command_hash':hashlib.sha256(command.encode()).hexdigest(),'pid':running['pid'],'state':running['statename'],'start':running['start']})
print(json.dumps({'source':'Supervisor.getAllConfigInfo/getProcessInfo','supervisor_pid':server.getPID(),'workers':rows},indent=2))
