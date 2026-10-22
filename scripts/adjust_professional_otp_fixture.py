"""Controlled expiry/cooldown of one private synthetic challenge; no public API."""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BENCH=Path('/home/frappe/teletena-compat/bench');SITE='teletena-guest-first-test.localhost'
fixture=json.loads(Path('/home/frappe/teletena-onboarding-sprint/challenge.json').read_text())
assert fixture['contact'].endswith('@onboarding.invalid')
os.chdir(BENCH/'sites');sys.path.insert(0,str(ROOT))
import frappe
frappe.init(site=SITE);frappe.connect()
from tele_tena.api.phone_auth import _keyed
matched=frappe.db.sql("SELECT id FROM tt_otp_challenge WHERE id=%s AND phone_digest=%s AND purpose='contact_email'",(fixture['id'],_keyed('contact:email',fixture['contact'])))
assert matched,'Only the explicitly captured synthetic challenge may change'
frappe.db.sql('UPDATE tt_otp_challenge SET created=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 61 SECOND),expires=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 SECOND) WHERE id=%s',(fixture['id'],));frappe.db.commit();frappe.destroy()
