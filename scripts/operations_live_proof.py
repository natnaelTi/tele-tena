"""Resume only the approved isolated PlanV1; no production configuration activation.
Every live side effect uses the durable private proof ledger. No automatic retries.
"""
import argparse,json,os,sys
from pathlib import Path
from unittest.mock import patch

def alerts(root,bench,site):
 from tele_tena.operations.proof import ProofRun,ProofBlocked
 run=ProofRun(root);manifest,c=run.checked()
 if not c.get('telegram_chat') or manifest['destinations']['telegram_chat']!=c['telegram_chat']:raise ProofBlocked('telegram_destination_unresolved')
 if site!='teletena-ops-v153-fresh.localhost' or bench.resolve()!=Path('/home/frappe/teletena-compat/bench'):raise ProofBlocked('isolated_proof_site_required')
 os.chdir(bench/'sites');import tele_tena,frappe
 frappe.init(site=site,sites_path=str(bench/'sites'));frappe.connect();frappe.set_user('Administrator')
 from tele_tena.operations import jobs,runtime,providers
 from tele_tena import email_delivery
 settings_file=Path('/home/frappe/frappe/frappe-bench/sites/teletena-mvp-presentation.localhost/private/tele_tena_email.json')
 if settings_file.is_symlink() or settings_file.stat().st_mode&0o077:raise ProofBlocked('private_smtp_configuration_required')
 settings=json.loads(settings_file.read_text());native_email=email_delivery.send_notice;native_telegram=providers.telegram
 config=runtime.config();config.update(alerts=True,owner='',alert_email=c['owner_alert_email'],mobile_channel='Telegram')
 code='synthetic_verification_no_real_incident'
 if frappe.db.sql('SELECT code FROM tt_ops_incident WHERE code<>%s',(code,)):raise ProofBlocked('proof_site_contains_other_incidents')
 def send(channel,message,destination=None):
  phase='alert' if message==manifest['alert_body'] else 'recovery' if message==manifest['recovery_body'] else None
  if phase is None or destination not in (None,c['owner_alert_email']):raise ProofBlocked('unexpected_message_or_recipient')
  key='owner-'+channel+'-'+phase;run.reserve(key,{'emails' if channel=='email' else 'telegram_messages':1})
  try:
   with run.live():result=native_email(destination,message) if channel=='email' else native_telegram(message)
   run.outcome(key,'ProviderAccepted');return result
  except Exception:
   run.outcome(key,'Unknown',error_code='receipt_unverified');raise ProofBlocked('message_outcome_unknown') from None
 try:
  with patch('tele_tena.operations.runtime.config',return_value=config),patch('tele_tena.operations.providers.settings',return_value=c),patch('tele_tena.email_delivery.configuration',return_value=settings),patch('tele_tena.email_delivery.send_notice',side_effect=lambda dest,body:send('email',body,dest)),patch('tele_tena.operations.providers.telegram',side_effect=lambda body:send('telegram',body)):
   # On resume, do not reopen/re-alert an already recovered episode.
   existing=frappe.db.sql('SELECT state FROM tt_ops_incident WHERE code=%s',(code,))
   if not existing:runtime.incident(code,'Critical');frappe.db.commit()
   jobs.send_alerts();frappe.db.commit();jobs.send_alerts();frappe.db.commit()
   current=frappe.db.sql('SELECT state FROM tt_ops_incident WHERE code=%s',(code,))[0][0]
   if current=='Open':runtime.incident(code,recovery=True);frappe.db.commit()
   jobs.send_alerts();frappe.db.commit();jobs.send_alerts();frappe.db.commit()
  states=frappe.db.sql('SELECT channel,phase,state FROM tt_ops_alert',as_dict=True)
  print(json.dumps({'isolated_alert_states':states,'actual_receipt':'Awaiting owner confirmation','production_flags_changed':False}))
 finally:frappe.destroy()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=('alerts',),required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--bench',type=Path,required=True);p.add_argument('--site',required=True);args=p.parse_args()
 try:alerts(args.root,args.bench,args.site)
 except Exception as e:
  from tele_tena.operations.proof import ProofBlocked
  code=str(e) if isinstance(e,ProofBlocked) else 'isolated_phase_unavailable'
  print(json.dumps({'phase':args.phase,'state':'Stopped','error_code':code}));return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
