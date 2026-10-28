"""Single-use disposable Frappe16 fixture, never a presentation/hosted seeder."""
assert __name__=='__main__', 'This fixture may run only as an explicit local CLI, never by import'

import os,sys,json,secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BENCH=Path('/home/frappe/teletena-compat/bench');SITE='teletena-payments-v147-fresh.localhost';OUT=Path('/home/frappe/teletena-offline-sprint')
os.chdir(BENCH/'sites');sys.path.insert(0,str(ROOT));import frappe
frappe.init(site=SITE);frappe.connect();frappe.set_user('Administrator');frappe.local.lang='en'
assert not frappe.db.sql('SELECT user FROM tt_profile LIMIT 1'),'Refusing any existing profile dataset'
from frappe.installer import update_site_config
for k,v in {'tele_tena_review_enabled':True,'tele_tena_review_site':SITE,'tele_tena_simulation_enabled':True,'tele_tena_patient_registration_enabled':True,'tele_tena_clinician_registration_enabled':True,'tele_tena_phone_otp_enabled':True}.items():update_site_config(k,v)
frappe.conf.update(tele_tena_review_enabled=True,tele_tena_review_site=SITE,tele_tena_simulation_enabled=True)
from tele_tena.api import journey as j,care_languages as languages,direct_payments as pay,scheduling
from frappe.utils.password import update_password
people={'patient':('Liya Tadesse','Patient'),'other_patient':('Abel Girma','Patient'),'clinician':('Mekonnen Abate','Clinician'),'reviewer':('Meron Assefa','Approver')};manifest={}
for kind,(name,role) in people.items():
 user=kind+'@offline-test.invalid';password=secrets.token_urlsafe(28);doc=frappe.get_doc({'doctype':'User','email':user,'first_name':name,'send_welcome_email':0,'user_type':'Website User'});doc.insert();doc.add_roles('Tele Tena '+role);update_password(user,password);manifest[kind]={'user':user,'password':password}
for kind in ('patient','other_patient','clinician'):
 frappe.set_user(manifest[kind]['user']);j.save_profile('clinician' if kind=='clinician' else 'patient',people[kind][0],True,history='' if kind=='clinician' else 'Adult care background for this private development test only',languages=['en','am'] if kind=='clinician' else [])
 if kind=='clinician':j.apply('Fictional professional identity for isolated workflow verification; no real credentials')
reviewer=manifest['reviewer']['user'];clinician=manifest['clinician']['user'];frappe.set_user(reviewer);j.review(clinician,'Approved');j.save_service('offline-counseling-test','Individual Counseling');from tele_tena.api.service_policy import set_immediate_policy
set_immediate_policy('offline-counseling-test',True,'Explicit synthetic immediate-care policy for isolated matching verification; not clinical authorization','offline-immediate-policy');j.review_service_scope(clinician,'offline-counseling-test','Approved')
frappe.set_user(clinician);languages.save_claims([{'code':'en','proficiency':3,'explanation':'Synthetic language self-assessment'},{'code':'am','proficiency':3,'explanation':'Synthetic language self-assessment'}]);pay.save_payee('+251911000123',0,'Fictional receiving number; no transfers or delivery authorized')
frappe.set_user(reviewer)
for code in ('en','am'):languages.decide(clinician,code,'Approved','Synthetic human-decision fixture, not a real language verification')
manifest['offerings']={}
for mode in ('automatic','manual'):
 frappe.set_user(clinician);offer=j.publish('offline-counseling-test',180000,30,title='Individual Counseling' if mode=='automatic' else 'Stress and Life Transitions',retry_key='offline-fixture:'+mode,care_languages=['en','am']);manifest['offerings'][mode]=offer['offering'];scheduling.save_schedule(offer['offering'],'Weekly Consultations','Africa/Addis_Ababa','video',mode,5,30,0,0,[{'weekday':day,'start':'00:00','end':'23:59'} for day in range(7)],[],status='Published',auto_requests=True)
frappe.set_user('Administrator');pay.configure('Offline',pay.config().revision,'Disposable verification site only; native presentation and hosted modes unchanged');frappe.set_user(manifest['patient']['user']);languages.preference('am');frappe.db.commit();frappe.destroy()
fd=os.open(OUT/'test-accounts.json',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as out:json.dump(manifest,out)
print('PASS dedicated empty site prepared through account/profile/review/scope/language/offering/schedule commands. No existing demo accounts changed; credentials private; no outbound transport.')
