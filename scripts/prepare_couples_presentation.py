"""Explicit additive fictional couples setup for the sole local presentation site.
No install hook or HTTP endpoint; credentials are written privately, never printed.
"""
import json
import os
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BENCH = Path(__file__).resolve().parents[3]
os.chdir(BENCH / 'sites')
sys.path.insert(0, str(BENCH / 'apps/frappe'))
import frappe
from frappe.utils.password import update_password
from tele_tena.api import journey, scheduling
from tele_tena.review import write_private

SITE='teletena-mvp-presentation.localhost'
CODE='presentation-couples-counseling'
# Illustrative prices only, centrally named in the presentation setup.
from tele_tena.presentation_data import PRICES

def run():
    assert os.environ.get('TELE_TENA_TEST_SITE')==SITE
    frappe.init(site=SITE,sites_path=str(BENCH/'sites'))
    frappe.connect()
    from frappe.utils.password import get_encryption_key
    get_encryption_key()  # Native site-local initialization; preserves any existing key.
    root=BENCH/'sites'/SITE/'private'
    seed=json.loads((root/'tele_tena_presentation_seed.json').read_text())
    accounts=json.loads((root/'tele_tena_presentation_accounts.json').read_text())
    partner='dawit.bekele@presentation.teletena.invalid'
    marker=root/'tele_tena_couples_presentation.json'
    if marker.exists():
        saved=json.loads(marker.read_text());assert saved['partner']==partner
    elif frappe.db.exists('User',partner):
        raise RuntimeError('Existing unowned account; no credentials or records changed')
    else:
        frappe.set_user('Administrator')
        doc=frappe.get_doc(dict(doctype='User',email=partner,first_name='Dawit Bekele',send_welcome_email=0,user_type='Website User'))
        doc.insert();doc.add_roles('Tele Tena Patient')
        password=secrets.token_urlsafe(24);update_password(partner,password)
        accounts[partner]=password;write_private(root/'tele_tena_presentation_accounts.json',accounts)
        frappe.set_user(partner);journey.save_profile('patient','Dawit Bekele',True)
        frappe.db.commit()
        write_private(marker,{'partner':partner,'fictional':True,'price_minor':PRICES['couples-counseling']})
    frappe.set_user(seed['users']['reviewer'])
    if not frappe.db.exists('Tele Tena Service',CODE):
        journey.save_service(CODE,'Couples counseling')
        service=frappe.get_doc('Tele Tena Service',CODE)
        service.participant_structure='couple';service.save()
    scope=frappe.db.get_value('Tele Tena Service Scope',{'clinician':seed['users']['clinician'],'service':CODE},'status')
    if scope!='Approved':
        # Explicit synthetic reviewer transition; no real qualifications claimed.
        journey.review_service_scope(seed['users']['clinician'],CODE,'Approved')
    frappe.set_user(seed['users']['clinician'])
    offers=journey.rows('SELECT id FROM tt_offering WHERE clinician=%s AND service=%s',(seed['users']['clinician'],CODE))
    if not offers:
        journey.publish(CODE,PRICES['couples-counseling'],60)
        offers=journey.rows('SELECT id FROM tt_offering WHERE clinician=%s AND service=%s',(seed['users']['clinician'],CODE))
    offering=offers[0].id
    if not journey.rows('SELECT id FROM tt_schedule WHERE offering=%s',(offering,)):
        local=datetime.now(ZoneInfo('Africa/Addis_Ababa'))+timedelta(minutes=5)
        scheduling.save_schedule(offering=offering,schedule_name='Shared conversations',timezone_name='Africa/Addis_Ababa',consultation_format='video',confirmation_mode='automatic',minimum_notice_minutes=0,horizon_days=60,buffer_before=0,buffer_after=0,intervals=[{'weekday':day,'start':'08:00','end':'22:00'} for day in range(7)],exceptions=[{'date':local.date().isoformat(),'kind':'replace','start':local.strftime('%H:%M'),'end':'22:00'}] if local.hour<21 else [],status='Published')
    if os.environ.get('TELE_TENA_PREPARE_CALL_WINDOW')=='1':
        # Explicit local test preparation; only this fictional offering's
        # current-date override changes, never any booked instant or balance.
        current=next(s for s in scheduling.schedules() if s['offering']==offering)
        local=datetime.now(ZoneInfo(current['timezone']))+timedelta(minutes=3)
        if local.hour>=21:raise RuntimeError('Prepare the controlled call case during working hours')
        payload={key:current[key] for key in ('offering','schedule_name','consultation_format','confirmation_mode','minimum_notice_minutes','horizon_days','buffer_before','buffer_after','status')}
        exceptions=[dict(date=str(e['date']),kind=e['kind'],start=e.get('start_local'),end=e.get('end_local')) for e in current['exceptions'] if str(e['date'])!=local.date().isoformat()]
        exceptions.append(dict(date=local.date().isoformat(),kind='replace',start=local.strftime('%H:%M'),end='22:00'))
        payload.update(timezone_name=current['timezone'],intervals=[dict(weekday=i['weekday'],start=i['start_local'],end=i['end_local']) for i in current['intervals']],exceptions=exceptions)
        scheduling.save_schedule(**payload)
    frappe.db.commit()
    saved=json.loads(marker.read_text());saved.update(offering=offering)
    write_private(marker,saved)
    print('Additive fictional couples accounts/service/schedule ready; passwords remain in the private account file.')
    frappe.destroy()

if __name__=='__main__':run()
