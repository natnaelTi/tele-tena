"""Stopped-site replay retention after restore. Retain the latest deletion journal first.
Only replay metadata/objects expire; no provider I/O or business-record deletion.
"""
import argparse
import os
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bench', type=Path, required=True)
    parser.add_argument('--site', required=True)
    parser.add_argument('--confirm-stopped-site', required=True,
                        help='Repeat the exact site after stopping all its writers')
    args = parser.parse_args()
    bench = args.bench.resolve()
    site = bench / 'sites' / args.site
    assert site.resolve().parent == bench / 'sites', 'Invalid site'
    assert args.confirm_stopped_site == args.site, 'Explicit stopped-site confirmation required'
    assert site.is_dir(), 'Site missing'
    os.chdir(bench / 'sites')
    sys.path.insert(0, str(bench / 'apps' / 'frappe'))
    import frappe
    frappe.init(site=args.site, sites_path=str(bench / 'sites'))
    frappe.connect()
    try:
        assert frappe.conf.get('maintenance_mode'), 'Site must be in maintenance mode'
        from tele_tena.operations import archive
        # Expiry is checked again on playback. Drain batches before reopening the site.
        while True:
            remaining = frappe.db.sql("SELECT COUNT(*) FROM tt_ops_archive WHERE expires<=%s AND state<>'Expired'", (archive.rt.now(),))[0][0]
            if not remaining:
                break
            archive.retention()
        for row in frappe.db.sql("SELECT id FROM tt_ops_archive WHERE state<>'Expired'", as_dict=True):
            if archive.deleted(row.id):
                archive.tombstone(row.id, 'UserDeleted')
        result = archive.scan_orphans(full=True)
        frappe.db.commit()
        print('PASS stopped-site replay retention and full orphan scan; objects checked:', result['checked'])
    finally:
        frappe.db.rollback()
        frappe.destroy()

if __name__ == '__main__':
    main()
