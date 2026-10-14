"""Require and verify a newly created complete private Frappe backup bundle."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import tarfile


def verify(directory):
    directory=Path(directory)
    if directory.is_symlink() or directory.stat().st_uid!=os.getuid() or directory.stat().st_mode & 0o077:
        raise ValueError('Backup directory must be owned and private')
    names=('database.sql.gz','public-files.tar','private-files.tar','site-config.json')
    result={}
    for name in names:
        path=directory/name
        if not path.is_file() or path.is_symlink() or path.stat().st_size==0:
            raise ValueError('Required backup absent/empty/unsafe: '+name)
        with path.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        result[name]={'bytes':path.stat().st_size,'sha256':digest}
    with gzip.open(directory/names[0],'rb') as stream:
        # Consume all bytes to check CRC/truncation; never print database content.
        found=False
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            found=found or b'CREATE TABLE' in chunk or b'INSERT INTO' in chunk
        if not found:raise ValueError('Database archive lacks SQL records')
    for name in names[1:3]:
        with tarfile.open(directory/name,'r:*') as archive:
            for member in archive:
                if member.isfile():
                    with archive.extractfile(member) as stream:
                        for chunk in iter(lambda:stream.read(1024*1024),b''):
                            pass  # validate payload length without writing/printing private content
    config=json.loads((directory/names[3]).read_text())
    if not config.get('db_name'):raise ValueError('Site configuration backup incomplete')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path);args=parser.parse_args()
    try:
        result=verify(args.directory)
        manifest=args.directory/'verified-manifest.json'
        if manifest.exists():
            if manifest.is_symlink() or manifest.stat().st_uid!=os.getuid() or manifest.stat().st_mode & 0o077 or json.loads(manifest.read_text())!=result:
                raise ValueError('Backup no longer matches its protected verified manifest')
        else:
            fd=os.open(manifest,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'w') as stream:json.dump(result,stream,indent=2)
        print('PASS: database, public/private file archives and site config present/readable; private checksums recorded')
    except (ValueError,OSError,tarfile.TarError,EOFError) as e:
        raise SystemExit('FAIL: '+str(e)) from None

if __name__=='__main__':main()
