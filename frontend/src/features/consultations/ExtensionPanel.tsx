import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api'
import { Button, InlineNotice } from '../../components/ui'
import type { Key } from '../../i18n'

type Extension = {id:string;state:string;duration_minutes:number;amount_minor:number;expires_at:string;start_after:string}
type ExtensionState = {items:Extension[];can_propose:boolean;can_accept:boolean}

export default function ExtensionPanel({appointment, role, open, t}:{appointment:string;role:'patient'|'clinician';open:boolean;t:(key:Key)=>string}) {
  const [data,setData]=useState<ExtensionState|null>(null)
  const [error,setError]=useState('')
  const [busy,setBusy]=useState(false)
  const busyRef=useRef(false)
  const mounted=useRef(false)
  const load=useCallback(async()=>{
    try { const next=await api<ExtensionState>('tele_tena.api.extensions.extension_status',{appointment}); if(mounted.current)setData(next) }
    catch { if(mounted.current)setError(t('extensionLoadError')) }
  },[appointment,t])
  useEffect(()=>{mounted.current=true;void Promise.resolve().then(load);const timer=window.setInterval(()=>void load(),5000);return()=>{mounted.current=false;window.clearInterval(timer)}},[load])
  const run=async(work:()=>Promise<unknown>)=>{if(busyRef.current)return;busyRef.current=true;setBusy(true);setError('');try{await work();await load()}catch(e){if(mounted.current)setError(e instanceof Error?e.message:t('extensionActionError'))}finally{busyRef.current=false;if(mounted.current)setBusy(false)}}
  if(!open)return null
  const active=data?.items.filter(x=>['Proposed','Accepted','Started'].includes(x.state))||[]
  const current=active[active.length-1]
  const history=data?.items.filter(x=>!['Proposed','Accepted','Started'].includes(x.state))||[]
  const amount=(minor:number)=>`ETB ${(minor/100).toFixed(2)}`
  return <section className="extension-panel" aria-labelledby="extension-title">
    <header><div><h2 id="extension-title">{t('extraTime')}</h2><p>{t('extensionConsent')}</p></div></header>
    {error&&<InlineNotice tone="danger">{error}</InlineNotice>}
    {!current&&role==='clinician'&&data?.can_propose&&<Button variant="secondary" loading={busy} onClick={()=>void run(()=>api('tele_tena.api.extensions.propose_extension',{appointment,retry_key:crypto.randomUUID()},true))}>{t('offerExtraTime')}</Button>}
    {current&&<div className="extension-offer" aria-live="polite"><strong>{t(`extension${current.state}` as Key)}</strong><span>{current.duration_minutes} {t('minutes')} · {amount(current.amount_minor)}</span>
      {current.state==='Proposed'&&role==='patient'&&<><p>{t('extensionOfferExpiry')} {new Date(current.expires_at).toLocaleTimeString()}</p><div className="actions"><Button loading={busy} onClick={()=>void run(()=>api('tele_tena.api.extensions.respond_extension',{appointment,extension_id:current.id,decision:'accept'},true))}>{t('acceptAndReserve')}</Button><Button variant="secondary" disabled={busy} onClick={()=>void run(()=>api('tele_tena.api.extensions.respond_extension',{appointment,extension_id:current.id,decision:'decline'},true))}>{t('Decline')}</Button></div><Link className="text-link" to="/patient/account/payments">{t('addFunds')}</Link></>}
      {current.state==='Proposed'&&role==='clinician'&&<Button variant="secondary" loading={busy} onClick={()=>void run(()=>api('tele_tena.api.extensions.withdraw_extension',{appointment,extension_id:current.id},true))}>{t('withdrawExtension')}</Button>}
      {current.state==='Accepted'&&role==='clinician'&&<><p>{t('extensionStartAfter')} {new Date(current.start_after).toLocaleTimeString()}</p><Button loading={busy} onClick={()=>void run(()=>api('tele_tena.api.extensions.start_extension',{appointment,extension_id:current.id},true))}>{t('startAgreedExtension')}</Button></>}
    </div>}
    {history.length>0&&<details><summary>{t('extensionHistory')}</summary><ul>{history.map(x=><li key={x.id}>{t(`extension${x.state}` as Key)} · {x.duration_minutes} {t('minutes')} · {amount(x.amount_minor)}</li>)}</ul></details>}
  </section>
}
