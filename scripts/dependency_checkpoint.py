"""Read-only dependency guard for a shared Bench; never installs packages.

Run with the Bench env Python. Snapshot output is private and contains versions,
not pip freeze URLs (which can contain repository credentials).
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re


def canonical(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def installed():
    return {canonical(d.metadata['Name']): d.version
            for d in importlib.metadata.distributions() if d.metadata.get('Name')}


def check_plan(before, report):
    """Reject replacement of any installed distribution, even at same version."""
    proposed = [canonical(item['metadata']['name']) for item in report['install']]
    conflicts = sorted(set(proposed) & set(before))
    if conflicts:
        raise ValueError('Plan replaces existing distributions: ' + ', '.join(conflicts))
    if 'tele-tena' not in proposed:
        raise ValueError('Plan must add tele-tena to a bench without it')
    return proposed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'plan', 'verify'])
    parser.add_argument('directory', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.action == 'snapshot':
        args.directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        before = installed()
        if 'tele-tena' in before:
            raise SystemExit('Existing TeleTena install: use the documented update/rollback procedure')
        for name, content in [('packages.json', json.dumps(before, indent=2)),
                              ('constraints.txt', ''.join(f'{k}=={v}\n' for k, v in sorted(before.items())))]:
            fd = os.open(args.directory / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'w') as stream:
                stream.write(content)
        print('PASS: private package baseline and exact constraints saved')
        return
    before = json.loads((args.directory / 'packages.json').read_text())
    if args.action == 'plan':
        if not args.report:
            parser.error('--report is required for plan')
        proposed = check_plan(before, json.loads(args.report.read_text()))
        print('PASS: additive-only dependency plan; new distributions:', ', '.join(proposed))
    else:
        after = installed()
        changed = sorted(k for k, v in before.items() if after.get(k) != v)
        if changed:
            raise SystemExit('FAIL: existing package versions changed or missing: ' + ', '.join(changed))
        if 'tele-tena' not in after:
            raise SystemExit('FAIL: TeleTena is not installed')
        print('PASS: all pre-existing dependency versions preserved')


if __name__ == '__main__':
    main()
