"""Local-only synthetic password login check; credentials never printed or persisted."""
import os
import secrets
import sys
from pathlib import Path
import requests

bench = Path(__file__).resolve().parents[3]
os.chdir(bench / "sites")
sys.path.insert(0, str(bench / 'apps/frappe'))
import frappe
from frappe.utils.password import update_password

frappe.init(site='erp.localhost', sites_path=str(bench / 'sites'))
frappe.connect()
user = 'foundation-check@example.invalid'
password = secrets.token_urlsafe(32)
try:
    frappe.set_user('Administrator')
    if not frappe.db.exists('User', user):
        frappe.get_doc(dict(doctype='User', email=user, first_name='Synthetic Foundation', send_welcome_email=0, user_type='Website User')).insert()
    update_password(user, password)
    frappe.db.commit()
    client = requests.Session()
    base = 'http://127.0.0.1:5173'
    path = '/api/method/tele_tena.api.system.status'
    guest = client.get(base + path)
    assert guest.status_code == 403, guest.status_code
    login = client.post(base + '/api/method/login', data={'usr': user, 'pwd': password})
    assert login.status_code == 200, login.status_code
    result = client.get(base + path)
    assert result.status_code == 200, result.status_code
    data = result.json()['message']
    assert data['site'] == 'erp.localhost' and data['user'] == user
    client.post(base + '/api/method/logout')
    print('PASS: proxy guest 403, password login, authenticated 200, correct site and user')
finally:
    frappe.set_user('Administrator')
    frappe.delete_doc('User', user)
    frappe.db.commit()
    frappe.destroy()
