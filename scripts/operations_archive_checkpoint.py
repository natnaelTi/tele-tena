"""Private checkpoint for bound operations config/proofs and optional archive volume.
No credentials are printed. Run only with target writers stopped; no restoration.
"""
import argparse,hashlib,json,os,re,shutil,tarfile
from pathlib import Path

def private(path,directory=False):
    path=Path(path)
    assert path.is_absolute() and not any(p.is_symlink() for p in (path,*path.parents)), 'Unsafe private path'
    info=path.stat();assert info.st_uid==os.geteuid() and not info.st_mode&0o077,'Private ownership/mode required'
    assert path.is_dir() if directory else path.is_file(),'Required private artifact missing'
    return path

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def snapshot(bench,site,directory):
    assert (bench/'sites'/site).resolve().parent==(bench/'sites').resolve(),'Invalid site'
    assert not directory.exists() and not directory.is_symlink(),'Retained checkpoint must not be overwritten'
    directory.mkdir(mode=0o700)
    config=json.loads((bench/'sites'/site/'site_config.json').read_text());bound=config.get('tele_tena_operations_config_file');files={};values={}
    if bound:
        source=private(bound);values=json.loads(source.read_text());files['providers.json']=source
        for name in ('archive_proof_file','replay_activation_file'):
            if values.get(name):files[name+'.json']=private(values[name])
    journal=bench/'sites'/site/'private/teletena-operations/deletions.jsonl'
    if journal.exists():files['deletions.jsonl']=private(journal.absolute())
    manifest={'site':site,'files':{},'volume':None}
    for name,path in files.items():
        target=directory/name;shutil.copyfile(path,target);target.chmod(0o600)
        manifest['files'][name]={'source':str(path),'sha256':digest(target)}
    if values.get('archive_directory'):
        volume=private(values['archive_directory'],True);entries={}
        for path in sorted(volume.iterdir()):
            assert re.fullmatch('replay-[a-f0-9]{64}',path.name),'Unexpected archive-volume entry'
            private(path);entries[path.name]=digest(path)
        target=directory/'archive-volume.tar'
        with tarfile.open(target,'w') as archive:
            for name in entries:archive.add(volume/name,arcname=name,recursive=False)
        target.chmod(0o600);manifest['volume']={'source':str(volume),'entries':entries,'sha256':digest(target)}
    path=directory/'manifest.json';path.write_text(json.dumps(manifest,indent=2));path.chmod(0o600)
    verify(directory)
    return {'private_files':len(files),'archive_objects':len(manifest['volume']['entries']) if manifest['volume'] else 0}

def verify(directory):
    private(directory,True);manifest=json.loads(private(directory/'manifest.json').read_text())
    for name,record in manifest['files'].items():
        assert Path(name).name==name and digest(private(directory/name))==record['sha256'],'Private checkpoint mismatch'
        assert digest(private(record['source']))==record['sha256'],'Bound private state changed; stop and inspect'
    if manifest['volume']:
        volume=manifest['volume'];file=private(directory/'archive-volume.tar');assert digest(file)==volume['sha256'],'Archive-volume checksum mismatch'
        with tarfile.open(file,'r') as archive:
            members=archive.getmembers();assert len(members)==len(volume['entries']),'Archive member count mismatch'
            assert all(m.isfile() and m.name in volume['entries'] for m in members),'Unsafe archive member'
            for member in members:
                h=hashlib.sha256()
                stream=archive.extractfile(member)
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
                assert h.hexdigest()==volume['entries'][member.name],'Archive object checksum mismatch'
        source=private(volume['source'],True)
        assert set(p.name for p in source.iterdir())==set(volume['entries']),'Archive-volume inventory changed'
        for name,expected in volume['entries'].items():assert digest(private(source/name))==expected,'Live archive object changed'
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('snapshot','verify'));p.add_argument('--bench',type=Path);p.add_argument('--site');p.add_argument('--directory',type=Path,required=True);a=p.parse_args()
    if a.action=='snapshot':
        assert a.bench and a.site,'Explicit bench and site required';result=snapshot(a.bench.absolute(),a.site,a.directory.absolute())
        print('PASS private operations checkpoint:',json.dumps(result))
    else:verify(a.directory.absolute());print('PASS retained private operations checkpoint verified; no secret values printed.')
if __name__=='__main__':main()
