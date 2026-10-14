"""Read-only install/update guard. Private snapshots; never installs packages."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote


def canonical(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def identity(data):
    if not data:
        return None
    editable = bool(data.get('dir_info', {}).get('editable'))
    url = urlsplit(data.get('url', ''))
    if url.scheme == 'file' and url.netloc in ('', 'localhost'):
        return {'editable': editable, 'path': str(Path(unquote(url.path)).resolve())}
    # Remote direct URLs can contain credentials; retain a comparison hash only.
    return {'editable': editable, 'source_hash': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}


def installed_details():
    result = {}
    for d in importlib.metadata.distributions():
        if not d.metadata.get('Name'):
            continue
        name = canonical(d.metadata['Name'])
        if name in result:
            raise ValueError('Duplicate installed distribution: ' + name)
        direct = d.read_text('direct_url.json')
        result[name] = {'version': d.version, 'identity': identity(json.loads(direct)) if direct else None}
    return result


def installed():
    return {name: row['version'] for name, row in installed_details().items()}


def check_plan(before, report, mode='install', app_path=None):
    proposed = [canonical(item['metadata']['name']) for item in report['install']]
    if len(set(proposed)) != len(proposed):
        raise ValueError('Duplicate planned distribution')
    if mode not in ('install', 'update'):
        raise ValueError('Unknown mode')
    if ('tele-tena' in before) != (mode == 'update'):
        raise ValueError('Mode does not match existing TeleTena installation')
    conflicts = sorted((set(proposed) & set(before)) - ({'tele-tena'} if mode == 'update' else set()))
    if conflicts:
        raise ValueError('Plan replaces protected distributions: ' + ', '.join(conflicts))
    if mode == 'update' and set(proposed) != {'tele-tena'}:
        raise ValueError('Update mode permits only TeleTena; new dependencies need separate reviewed compatibility evidence')
    if 'tele-tena' not in proposed:
        raise ValueError('Plan must install the intentional tele-tena package')
    if app_path is not None:
        target = next(item for item in report['install'] if canonical(item['metadata']['name']) == 'tele-tena')
        if identity(target.get('download_info')) != {'editable': True, 'path': str(Path(app_path).resolve())}:
            raise ValueError('TeleTena plan must retain the expected local editable app identity')
    return proposed


def check_preserved(before, after, mode='install', approved=None, app_path=None):
    protected = set(before) - ({'tele-tena'} if mode == 'update' else set())
    changed = sorted(name for name in protected if after.get(name) != before[name])
    if changed:
        raise ValueError('Protected package version/editable identity changed or missing: ' + ', '.join(changed))
    if 'tele-tena' not in after:
        raise ValueError('TeleTena not installed')
    if approved:
        extra = set(after) - set(before) - set(approved)
        if extra:
            raise ValueError('Unplanned new distributions: ' + ', '.join(sorted(extra)))
        for name, row in approved.items():
            if after.get(name) != row:
                raise ValueError('Installed distribution differs from accepted plan: ' + name)
    if app_path is not None and after['tele-tena']['identity'] != {'editable': True, 'path': str(Path(app_path).resolve())}:
        raise ValueError('TeleTena editable identity changed')


def private_write(directory, name, value):
    fd = os.open(directory / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'plan', 'verify'])
    parser.add_argument('directory', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--mode', choices=['install', 'update'], default='install')
    parser.add_argument('--app-path', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == 'snapshot':
            before = installed_details()
            if ('tele-tena' in before) != (args.mode == 'update'):
                raise ValueError('Use --mode update for an existing TeleTena install; install mode requires absence')
            target = {'editable': True, 'path': str(args.app_path.resolve())}
            if args.mode == 'update' and before['tele-tena']['identity'] != target:
                raise ValueError('Existing TeleTena editable identity does not match --app-path')
            args.directory.mkdir(mode=0o700, parents=True, exist_ok=False)
            private_write(args.directory, 'packages.json', json.dumps(before, indent=2))
            private_write(args.directory, 'checkpoint.json', json.dumps({'mode': args.mode, 'app_path': target['path']}))
            constraints = ''.join(f'{name}=={row["version"]}\n' for name, row in sorted(before.items()) if not (args.mode == 'update' and name == 'tele-tena'))
            private_write(args.directory, 'constraints.txt', constraints)
            print('PASS: private version/identity snapshot; constraints protect every package except the explicit update target')
            return
        if args.directory.is_symlink() or args.directory.stat().st_uid != os.getuid() or args.directory.stat().st_mode & 0o077:
            raise ValueError('Snapshot must be an owned private directory')
        meta = json.loads((args.directory / 'checkpoint.json').read_text())
        if meta != {'mode': args.mode, 'app_path': str(args.app_path.resolve())}:
            raise ValueError('Mode/app-path differs from snapshot')
        before = json.loads((args.directory / 'packages.json').read_text())
        if args.action == 'plan':
            if not args.report:
                parser.error('--report required')
            report = json.loads(args.report.read_text())
            proposed = check_plan(before, report, args.mode, args.app_path)
            approved = {canonical(item['metadata']['name']): {'version': item['metadata']['version'], 'identity': identity(item.get('download_info'))} for item in report['install']}
            # pip wheel URLs are not installed direct_url identities unless direct=true.
            for item in report['install']:
                if not item.get('is_direct'):
                    approved[canonical(item['metadata']['name'])]['identity'] = None
            private_write(args.directory, 'approved-plan.json', json.dumps(approved, indent=2))
            print('PASS: intentional TeleTena install/update; protected replacements rejected; proposed:', ', '.join(proposed))
        else:
            approved = json.loads((args.directory / 'approved-plan.json').read_text())
            check_preserved(before, installed_details(), args.mode, approved, args.app_path)
            print('PASS: accepted target and every protected version/editable identity preserved')
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        # Diagnostic contains names/reasons only, never report URLs/configuration.
        raise SystemExit('FAIL: ' + str(error)) from None


if __name__ == '__main__':
    main()
