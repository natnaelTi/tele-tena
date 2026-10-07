type Props = {state:string;hasOffer?:boolean;wave?:number;clinician?:boolean};

/** Motion describes server facts; it never advances matching or invents an ETA. */
export function RequestProgress({state,hasOffer=false,wave=1,clinician=false}:Props){
  const closed=!['Open','Active'].includes(state);
  const confirmed=state==='Matched'||state==='Accepted';
  const words=confirmed?['Appointment confirmed']:closed?[state==='Superseded'?'Offer closed':state]:clinician?
    ['Your offer is with the patient','Waiting for their decision','Your proposed time will be rechecked']:
    hasOffer?['An offer is ready to review','Compare the time and fee','The next step is yours']:
    wave>1?['Reaching more eligible clinicians','Your care requirements stay in place','Waiting for a response']:
    ['Looking for a good fit','Reaching eligible clinicians','Waiting for a response'];
  const description=confirmed?'Open the appointment to review the agreed details and join window.':closed?
    'This outcome is retained in your history.':clinician?'No appointment is confirmed until the patient accepts. Your quote is private.':
    'We aim to connect you within three minutes. Availability and your choice may take longer.';
  return <section className={`request-progress ${closed?'settled':''}`} aria-label="Request progress">
    <span className="request-beacon" aria-hidden="true"><span/><span/><span/>{confirmed?'✓':clinician?'↗':'…'}</span>
    <div><div className="request-progress-words" aria-hidden="true">{words.map((word,i)=><span key={word} style={{animationDelay:`${i*4}s`,animationDuration:`${words.length*4}s`}}>{word}</span>)}</div>
      <strong className="sr-only">{words[0]}</strong><p>{description}</p></div>
  </section>;
}
