import { useLocale } from '../hooks/useLocale';
import { Check, Search, MessageSquare, CircleX } from 'lucide-react';

type Props = {state:string;hasOffer?:boolean;wave?:number;clinician?:boolean;immediate?:boolean;eligibleSupply?:number|null};

/** Motion describes server facts; it never advances matching or invents an ETA. */
export function RequestProgress({state,hasOffer=false,wave=1,clinician=false,immediate=false,eligibleSupply}:Props){
  const {w}=useLocale();
  const closed=!['Open','Active'].includes(state);
  const confirmed=state==='Matched'||state==='Accepted';
  const words=confirmed?['Appointment confirmed']:closed?[state==='Superseded'?'Offer closed':state]:clinician?
    ['Your offer is with the patient','Waiting for their decision','Your proposed time will be rechecked']:
    hasOffer?['An offer is ready to review','Compare the time and fee','The next step is yours']:
    immediate&&eligibleSupply===0?['No eligible clinician at publication','Your requirements stay in place','You can keep waiting or choose later']:
    wave>1?['Reaching more eligible clinicians','Your care requirements stay in place','Waiting for a response']:
    ['Looking for a good fit','Reaching eligible clinicians','Waiting for a response'];
  const description=confirmed?'Open the appointment to review the agreed details and join window.':closed?
    'This outcome is retained in your history.':clinician?'No appointment is confirmed until the patient accepts. Your quote is private.':
    immediate&&eligibleSupply===0?'Matching continues without changing your requirements.':
    hasOffer?'Review the clinician’s proposal. A booking is confirmed only after you accept.':
    'We aim to connect you within three minutes. Availability and your choice may take longer.';
  const Icon=confirmed?Check:closed?CircleX:clinician?MessageSquare:Search;
  return <section className={`request-progress ${closed?'settled':''}`} aria-label="Request progress">
    <span className="request-beacon" aria-hidden="true"><span/><span/><span/><Icon size={26}/></span>
    <div><div className="request-progress-words" aria-hidden="true">{words.map((word,i)=><span key={word} style={{animationDelay:`${i*4}s`,animationDuration:`${words.length*4}s`}}>{w(word)}</span>)}</div>
      <strong className="sr-only">{w(words[0])}</strong><p>{w(description)}</p></div>
  </section>;
}

/** Stages advance only from persisted offer/appointment facts, never a timer. */
export function RequestStageRail({state,hasOffer=false}:{state:string;hasOffer?:boolean}) {
  const {w}=useLocale();
  const step=state==='Matched'?3:state==='Open'?(hasOffer?2:1):0;
  const closed=!['Open','Matched'].includes(state);
  return <ol className="request-stage-rail" aria-label={w('Request progress')}>
    {['Request posted','Clinicians responding','Your choice','Appointment'].map((label,index)=><li key={label} className={!closed?(index<step?'done':index===step?'current':''):undefined} aria-current={!closed&&index===step?'step':undefined}><span aria-hidden="true">{!closed&&index<step?<Check size={16}/>:index+1}</span>{w(label)}</li>)}
  </ol>;
}
