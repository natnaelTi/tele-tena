"""Add isolated private phone-authentication storage without changing existing data."""
import os
import secrets

import frappe
from pathlib import Path


def execute():
    from tele_tena.schema import PHONE_AUTH_TABLES

    for name, columns in PHONE_AUTH_TABLES.items():
        frappe.db.sql_ddl(
            f'CREATE TABLE IF NOT EXISTS `tt_{name}` ({columns}) ENGINE=InnoDB'
        )
    frappe.db.sql('INSERT IGNORE INTO tt_otp_gate (id) VALUES (1)')
    if not frappe.db.exists('Role', 'Tele Tena Applicant'):
        frappe.get_doc(dict(doctype='Role', role_name='Tele Tena Applicant', desk_access=0)).insert()
    key_path = Path(frappe.get_site_path('private', 'tele_tena_otp.key'))
    key_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if key_path.is_symlink():
        frappe.throw('OTP key path may not be a symbolic link')
    if not key_path.exists():
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(secrets.token_hex(32) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
    os.chmod(key_path, 0o600)
