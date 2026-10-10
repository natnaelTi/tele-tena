import {FileText, Headphones, Video, ShieldCheck, Lock, Users} from 'lucide-react';
import {Card} from './ui';
import {date,money} from './Domain';
import {useLocale} from '../hooks/useLocale';
import './ConsultationDetails.css';

/** Appointment facts use the accepted snapshot, never a newer profile. */
export function ConversationFacts({item,clinician,status}:{item:any;clinician:boolean;status:string}){
  const {w}=useLocale();
  const identity=clinician?item.patient_identity:item.clinician;
  return <><div className="conversation-participant"><span className="conversation-avatar" aria-hidden="true">{Array.from(identity||w('Private patient')).slice(0,1).join('')}</span><div><h3>{identity}</h3><p>{item.service}</p><p>{item.booked_minutes} {w('minutes')} · ETB {money(item.price)}</p></div></div>
    <dl className="encounter-facts"><dt>{w('Time')}</dt><dd>{date(item.start,item.timezone)} – {new Intl.DateTimeFormat(undefined,{hour:'numeric',minute:'2-digit',timeZone:item.timezone||'UTC'}).format(new Date(item.end))}</dd><dt>{w('Timezone')}</dt><dd>{item.timezone||w('Unavailable')}</dd><dt>{w('Format')}</dt><dd>{w(item.format==='audio'?'Audio':'Video')}</dd><dt>{w('Session status')}</dt><dd>{status}</dd><dt>{w('Payment')}</dt><dd>ETB {money(item.price)} · {w(item.reservation_state||'Unavailable')}</dd></dl>
  </>;
}
export function DisclosureSnapshot({disclosure}:{disclosure:any}){
  const {w}=useLocale();
  return <Card className="encounter-disclosure"><h2>{w('Disclosure used at booking')}</h2><dl className="encounter-facts"><dt>{w('Preferred name')}</dt><dd>{disclosure.name||w('Not shared')}</dd><dt>{w('Your request')}</dt><dd className="prewrap">{disclosure.request||w('Not shared')}</dd><dt>{w('Saved history')}</dt><dd className="prewrap">{disclosure.history||w('Not shared')}</dd><dt>{w('Applies to')}</dt><dd>{w('This encounter only')}</dd></dl></Card>;
}
export function PreparationPanel(){
  const {w}=useLocale();
  return <Card className="consultation-preparation"><h2>{w('Before you join')}</h2>{[{Icon:Headphones,title:'Find a private space',body:'Use headphones if possible.'},{Icon:Video,title:'Check your connection',body:'Audio-only is available if video is unstable.'},{Icon:FileText,title:'Your notes',body:'Shared summaries appear here after completion.'}].map(({Icon,title,body})=><div className="preparation-row" key={title}><span aria-hidden="true"><Icon size={20}/></span><div><h3>{w(title)}</h3><p>{w(body)}</p></div></div>)}</Card>;
}
export function RecordedCallTiming({item}:{item:any}){
  const {w}=useLocale();
  return <details className="recorded-call-timing"><summary>{w('Call activity')}</summary><dl className="encounter-facts"><dt>{w('Call state')}</dt><dd>{w(({Ended:'Call ended',Open:'In progress',NotStarted:'Not started'} as Record<string,string>)[item.call_state]||'Unavailable')}</dd><dt>{w('Call ended')}</dt><dd>{item.call_ended_at?date(item.call_ended_at,item.timezone):w('Unavailable')}</dd><dt>{w('Connected time')}</dt><dd>{w('Unavailable')}</dd></dl><p className="supporting">{w('Booked duration is not measured connected time.')}</p></details>;
}

/** N08: labels explain access without receiving either adult's private notes. */
export function SharedCarePrivacy(){
  const {w}=useLocale();
  return <Card className="shared-care-privacy"><h2>{w("Your privacy")}</h2>{[{Icon:Users,title:"Shared summary",body:"Only content published to you appears here."},{Icon:Lock,title:"Private intake",body:"Not visible to the other participant."},{Icon:ShieldCheck,title:"Private clinical note",body:"Not included in this shared view."}].map(({Icon,title,body})=><div className="preparation-row" key={title}><span aria-hidden="true"><Icon size={20}/></span><div><h3>{w(title)}</h3><p>{w(body)}</p></div></div>)}<p className="supporting">{w("A shared relationship never grants automatic access to another adult’s medical history.")}</p></Card>;
}
