import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { journeyApi } from '../journey-api';
import type { Disclosure } from '../journey-api';
import { PageTitle, money } from '../components/Domain';
import { Button, Checkbox, EmptyState, InlineNotice, Select, Skeleton, TextField } from '../components/ui';
import { useSession } from '../hooks/useSession';
import { useLocale } from '../hooks/useLocale';
import { useAction } from '../hooks/useAction';
import { useResource } from '../hooks/useResource';
import { api } from '../api';

type Service = {id:string;label:string};
type Offer = {id:string;clinician_name:string;clinician_id:string;specialty:string;start:string;timezone:string;duration_minutes:number;consultation_format:string;price_minor:number;price_source:string;state:string;valid_until:string};
type PatientRequest = {id:string;state:string;urgency:string;service:string;category:string;language:string;consultation_format:string;request_text:string;disclosure_snapshot:Disclosure;max_price_minor:number|null;published_at:string;expires_at:string;first_offer_at:string|null;current_wave?:number;offers:Offer[]};
type InboxRequest = {id:string;urgency:string;language:string;consultation_format:string;request_text:string;disclosure_snapshot:Disclosure;max_price_minor:number|null;earliest_start:string;latest_start:string;timezone:string;expires_at:string;category:string;suggested_start?:string|null;suggested_timezone?:string;own_offer_id?:string|null;own_offer_start?:string|null;own_offer_price?:number|null;own_offer_until?:string|null};
function etbToMinor(value:string){if(!/^\d{1,7}(?:\.\d{1,2})?$/.test(value.trim()))throw new Error('Enter a price in ETB with up to two decimal places.');const [whole,fraction='']=value.trim().split('.');const minor=BigInt(whole)*100n+BigInt((fraction+'00').slice(0,2));if(minor<1n||minor>100000000n)throw new Error('Enter a supported positive price.');return Number(minor)}
function localDateTimeInput(value:string){const date=new Date(value);const pad=(part:number)=>String(part).padStart(2,'0');return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`}
function freshRequestKey(){const key=crypto.randomUUID();try{sessionStorage.setItem('teletena-open-request-retry',key)}catch{}return key}

const loadPractice=()=>api<any>('practice');
const loadServices=()=>journeyApi.services();
function usePolling<T>(loader:()=>Promise<T>, delay=5000) {
  const loaderRef=useRef(loader);loaderRef.current=loader;
  const stableLoader=useCallback(()=>loaderRef.current(),[]);
  const resource=useResource(stableLoader);
  useEffect(()=>{const timer=window.setInterval(()=>void resource.refresh(),delay);return()=>window.clearInterval(timer);},[delay,resource.refresh]);
  return resource;
}

export function PatientOpenRequests(){
  const {w}=useLocale();
  const location=useLocation();
  const requestDraft=(location.state as {requestDraft?:{request_text?:string;service?:string;service_label?:string;language?:string;format?:'audio'|'video'}}|null)?.requestDraft;
  const {session}=useSession();
  const services=useResource(loadServices);
  const requestResource=usePolling<PatientRequest[]>(()=>journeyApi.myRequests());

  const action=useAction();
  const [service,setService]=useState(()=>requestDraft?.service||'');
  const [narrative,setNarrative]=useState(()=>requestDraft?.request_text||'');
  const [urgency,setUrgency]=useState<'immediate'|'scheduled'>('immediate');
  const [language,setLanguage]=useState(()=>requestDraft?.language||'en');
  const [format,setFormat]=useState<'video'|'audio'>(requestDraft?.format||'video');
  const [sharing,setSharing]=useState({name:!!session?.profile?.share_name,history:!!session?.profile?.share_history});
  const [earliest,setEarliest]=useState('');
  const [latest,setLatest]=useState('');
  const [maxPrice,setMaxPrice]=useState('');
  const [selectedDisclosure,setSelectedDisclosure]=useState<{request:PatientRequest;offer:Offer}|null>(null);
  const [requestKey,setRequestKey]=useState(()=>{try{return sessionStorage.getItem('teletena-open-request-retry')||freshRequestKey()}catch{return crypto.randomUUID()}});
  const [showFallback,setShowFallback]=useState<Record<string,boolean>>({});
  const [publicationMessage,setPublicationMessage]=useState('');
  useEffect(()=>{if(!service&&requestDraft?.service_label&&services.data){const match=services.data.find(item=>item.label===requestDraft.service_label);if(match)setService(match.id);}},[requestDraft?.service_label,service,services.data]);
  const publish=()=>void action.run(async()=>{
    if(!service||!narrative.trim())throw new Error('Add a service and a short description first.');
    const payload={service,request_text:narrative,urgency,language,consultation_format:format,sharing,retry_key:requestKey,timezone_name:Intl.DateTimeFormat().resolvedOptions().timeZone||'Africa/Addis_Ababa',earliest_start:urgency==='scheduled'?new Date(earliest).toISOString():null,latest_start:urgency==='scheduled'?new Date(latest).toISOString():null,max_price_minor:maxPrice?etbToMinor(maxPrice):null};
    let publication:any;try{publication=await journeyApi.publishRequest(payload)}catch(error){if((error as any)?.code!=='request_retry_changed')throw error;const retry=freshRequestKey();setRequestKey(retry);publication=await journeyApi.publishRequest({...payload,retry_key:retry})}
    setPublicationMessage(publication?.eligible_supply===0?'Your request is saved, but no clinicians currently meet every selected requirement. Keep waiting or browse available clinicians.':'Your request is saved. We’ll show offers here when eligible clinicians respond. An enqueued notice does not confirm that it was seen.');
    setNarrative('');setRequestKey(freshRequestKey());await requestResource.refresh();
  });
  const requests=requestResource.data||[];
  return <>
    <PageTitle title={w('Open a care request')} description="Describe what you’re looking for. Eligible clinicians can respond privately." />
    <InlineNotice>{w('Open requests are not an emergency response service.')} The clinicians who receive your request can read the words you enter; avoid names and details that identify you.</InlineNotice>
    <section className="open-request-composer" id="request-composer">
      <h2>{w('What would you like help with?')}</h2>
      <label className="field">Describe what you are looking for<textarea rows={4} maxLength={2000} value={narrative} onChange={e=>setNarrative(e.target.value)} placeholder="A few words about the support you’re seeking" /></label>
      <Select label={w('Suggested service category')} value={service} onChange={e=>setService(e.target.value)}><option value="">Choose a service</option>{services.data?.map((x:Service)=><option key={x.id} value={x.id}>{x.label}</option>)}</Select>
      <div className="open-request-grid">
        <Select label={w('When would you like care?')} value={urgency} onChange={e=>setUrgency(e.target.value as typeof urgency)}><option value="immediate">{w('As soon as possible')}</option><option value="scheduled">{w('Schedule for later')}</option></Select>
        <Select label="Language" value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="am">Amharic</option><option value="om">Afaan Oromo</option></Select>
        <Select label={w('Session format')} value={format} onChange={e=>setFormat(e.target.value as typeof format)}><option value="video">Video</option><option value="audio">Audio</option></Select>
        <TextField label="Maximum total price (ETB, optional)" inputMode="decimal" value={maxPrice} onChange={e=>setMaxPrice(e.target.value)} />
      </div>
      {urgency==='scheduled'&&<div className="open-request-grid"><TextField label="Earliest time" type="datetime-local" value={earliest} onChange={e=>setEarliest(e.target.value)} /><TextField label="Latest time" type="datetime-local" value={latest} onChange={e=>setLatest(e.target.value)} /></div>}
      <fieldset className="open-request-sharing"><legend>{w('What clinicians will see')}</legend><p>{narrative.trim()||'Your request description will appear here.'}</p><Checkbox label={w('Include my preferred name')} checked={sharing.name} onChange={e=>setSharing({...sharing,name:e.target.checked})}/><Checkbox label={w('Include my saved history')} checked={sharing.history} onChange={e=>setSharing({...sharing,history:e.target.checked})}/><p className="supporting">These choices start from your privacy defaults. Your request text is visible to its recipients even when your name is not shared.</p></fieldset>
      <Button loading={action.busy} onClick={publish}>{w('Publish request')}</Button>
      {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}{publicationMessage&&<InlineNotice tone="success">{publicationMessage}</InlineNotice>}
    </section>
    <section className="open-request-list"><h2>Your requests</h2>{requestResource.error?<InlineNotice tone="danger">Requests could not be loaded. <Button onClick={()=>void requestResource.refresh()}>Retry</Button></InlineNotice>:!requestResource.data?<Skeleton/>:requests.length?requests.map(req=><article className="request-card" key={req.id}><header><strong>{req.urgency==='immediate'?'As soon as possible':'Scheduled request'} · {req.category}</strong><span>{req.state==='Open'&&new Date(req.expires_at).getTime()<=Date.now()?'Expired':req.state}</span></header><p>{req.request_text}</p>{req.state==='Open'&&Date.now()-new Date(req.published_at).getTime()>180000&&req.urgency==='immediate'&&<InlineNotice>No offer has arrived within three minutes. You can keep waiting, schedule for later, or browse clinicians. This does not broaden your request.</InlineNotice>}{req.state==='Open'&&Date.now()-new Date(req.published_at).getTime()>180000&&req.urgency==='immediate'&&showFallback[req.id]!==false&&<div className="request-fallback"><Button variant="secondary" onClick={()=>setShowFallback({...showFallback,[req.id]:false})}>Continue waiting</Button><Button variant="secondary" onClick={()=>{setNarrative(req.request_text);setService(req.service);setLanguage(req.language);setFormat(req.consultation_format as 'video'|'audio');setUrgency('scheduled');document.getElementById('request-composer')?.scrollIntoView({behavior:'smooth'});}}>Schedule for later</Button><Link to="/patient/discovery" className="text-link">Browse clinicians</Link></div>}{req.state==='Open'&&<p className="supporting">Waiting for eligible clinicians · closes {new Date(req.expires_at).toLocaleString()}</p>}{req.offers.filter(o=>o.state==='Active').map(offer=><div className="request-offer" key={offer.id}><div><strong>{offer.clinician_name}</strong><span>{offer.specialty} · {offer.consultation_format} · {offer.duration_minutes} minutes</span><time>{new Date(offer.start).toLocaleString(undefined,{timeZone:offer.timezone})} · {offer.timezone}</time><Link to={'/patient/clinicians/'+offer.clinician_id} target="_blank" rel="noreferrer" className="text-link">View clinician profile</Link></div><strong>ETB {money(offer.price_minor)}</strong><p>This offer is available until {new Date(offer.valid_until).toLocaleTimeString()}.</p><Button variant="secondary" onClick={()=>setSelectedDisclosure({request:req,offer})}>Review and accept</Button><Button variant="quiet" onClick={()=>void action.run(async()=>{await journeyApi.respondOffer(req.id,offer.id,'decline');await requestResource.refresh();})}>Decline</Button></div>)}{req.state==='Open'&&<>{(req.current_wave||1)<3&&<Button variant="secondary" onClick={()=>void action.run(async()=>{const result=await journeyApi.findMoreOptions(req.id);await requestResource.refresh();if(!result?.notified)throw new Error('No additional clinicians currently meet your requirements. Your request remains open; you can keep waiting or browse clinicians.');})}>Find more options</Button>}<Button variant="quiet" onClick={()=>void action.run(async()=>{await journeyApi.cancelRequest(req.id);await requestResource.refresh();})}>Cancel request</Button></>}</article>):<EmptyState title="No open requests yet.">If you want clinicians to respond with times, you can post a private request here.</EmptyState>}</section>
    {selectedDisclosure&&<div className="request-confirm-overlay" role="presentation"><section className="request-confirm" role="dialog" aria-modal="true" aria-labelledby="request-confirm-title"><h2 id="request-confirm-title">Review this offer</h2><p><strong>{selectedDisclosure.offer.clinician_name}</strong> · {selectedDisclosure.offer.specialty}</p><p>{new Date(selectedDisclosure.offer.start).toLocaleString(undefined,{timeZone:selectedDisclosure.offer.timezone})} · {selectedDisclosure.offer.duration_minutes} minutes · {selectedDisclosure.offer.consultation_format} · {selectedDisclosure.offer.timezone}</p><p><strong>Total price: ETB {money(selectedDisclosure.offer.price_minor)}</strong></p><h3>What will be shared</h3><div className="disclosure-preview">{Object.values(selectedDisclosure.request.disclosure_snapshot).map((value,i)=><p key={i}>{value}</p>)}</div><p className="supporting">Accepting confirms this appointment and reserves the amount from your balance. If your balance is short, add funds and return to the offer while it remains available.</p><div className="dialog-actions"><Button loading={action.busy} onClick={()=>void action.run(async()=>{const attempt=crypto.randomUUID();try{await journeyApi.respondOffer(selectedDisclosure.request.id,selectedDisclosure.offer.id,'accept',undefined,selectedDisclosure.request.disclosure_snapshot);}catch(error){await journeyApi.recordOfferAcceptFailure(selectedDisclosure.request.id,selectedDisclosure.offer.id,attempt,(error as any)?.code||'other_supported_failure').catch(()=>undefined);throw error;}setSelectedDisclosure(null);await requestResource.refresh();})}>Accept offer</Button><Button variant="secondary" onClick={()=>setSelectedDisclosure(null)}>Back</Button><Link to="/patient/payments" className="text-link">Add funds</Link></div>{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}</section></div>}
  </>;
}

export function ClinicianRequestInbox(){
  const {w}=useLocale();

  const inbox=usePolling<InboxRequest[]>(()=>journeyApi.clinicianRequests());
  const practice=useResource(loadPractice);
  const action=useAction();
  const [offerStarts,setOfferStarts]=useState<Record<string,string>>({});
  const [offerPrices,setOfferPrices]=useState<Record<string,string>>({});
  const [service,setService]=useState<Record<string,string>>({});
  const availableOfferings=(practice.data?.offerings||[]) as {id:string;label:string;price:number;minutes:number}[];
  return <>
    <PageTitle title={w('Requests')} description="Respond only to requests matched to your approved services and languages." />
    {inbox.error?<InlineNotice tone="danger">Requests could not be loaded. <Button onClick={()=>void inbox.refresh()}>Retry</Button></InlineNotice>:!inbox.data?<Skeleton/>:inbox.data.length?inbox.data.map(req=><article className="request-card clinician-request" key={req.id}><header><strong>{req.urgency==='immediate'?'As soon as possible':'Schedule for later'} · {req.category}</strong><span>{req.language.toUpperCase()} · {req.consultation_format}</span></header><div className="disclosure-preview">{Object.values(req.disclosure_snapshot).map((value,i)=><p key={i}>{value}</p>)}</div><p className="supporting">The patient chose what to share for this request. Do not use it outside this response.</p>{req.own_offer_id&&<InlineNotice>Your offer is visible only to this patient and you. It remains available until {req.own_offer_until?new Date(req.own_offer_until).toLocaleTimeString():"its expiry"}. <Button variant="quiet" onClick={()=>void action.run(async()=>{await journeyApi.withdrawOffer(req.own_offer_id!);await inbox.refresh();})}>Withdraw offer</Button></InlineNotice>}{req.suggested_start&&<InlineNotice tone="info">Earliest feasible start: {new Date(req.suggested_start).toLocaleString(undefined,{timeZone:req.suggested_timezone})} · {req.suggested_timezone}. <Button variant="secondary" onClick={()=>setOfferStarts({...offerStarts,[req.id]:localDateTimeInput(req.suggested_start!)})}>Use suggested time</Button></InlineNotice>}<Select label="Your approved service" value={service[req.id]||''} onChange={e=>setService({...service,[req.id]:e.target.value})}><option value="">Choose a service</option>{availableOfferings.filter(x=>x.label===req.category).map(x=><option key={x.id} value={x.id}>{x.label} · {x.minutes} min · ETB {money(x.price)}</option>)}</Select><TextField label="Proposed start (your device time)" type="datetime-local" value={offerStarts[req.id]||''} onChange={e=>setOfferStarts({...offerStarts,[req.id]:e.target.value})}/><TextField label="Total price (ETB)" inputMode="decimal" value={offerPrices[req.id]||''} placeholder={String((availableOfferings.find(x=>x.id===service[req.id])?.price||0)/100)} onChange={e=>setOfferPrices({...offerPrices,[req.id]:e.target.value})}/><p className="supporting">Requested range: {new Date(req.earliest_start).toLocaleString()} – {new Date(req.latest_start).toLocaleString()} · offer expires {new Date(req.expires_at).toLocaleTimeString()}</p><Button loading={action.busy} onClick={()=>void action.run(async()=>{if(!service[req.id]||!offerStarts[req.id])throw new Error('Choose an approved service and proposed start time.');const start=new Date(offerStarts[req.id]).toISOString();const amount=offerPrices[req.id]?etbToMinor(offerPrices[req.id]):null;await journeyApi.submitOffer({request_id:req.id,offering:service[req.id],start,price_minor:amount});await inbox.refresh();})} disabled={!!req.own_offer_id}>Send offer</Button>{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}</article>):<EmptyState title="No requests match your approved services right now.">When an eligible patient publishes a request, it will appear here. Patient details stay limited to their chosen disclosure.</EmptyState>}
    <Link className="text-link" to="/clinician/account">Set your care languages</Link>
  </>;
}

export function PublicClinicianProfile(){
  const {w}=useLocale();
  const {clinicianId=''}=useParams();
  const load=useCallback(()=>journeyApi.publicClinician(clinicianId),[clinicianId]);
  const resource=useResource(load);
  if(resource.error)return <InlineNotice tone="danger">This clinician profile is unavailable or no longer approved.</InlineNotice>;
  if(!resource.data)return <Skeleton/>;
  return <>
    <PageTitle eyebrow="CLINICIAN PROFILE" title={resource.data.display_name} description="Approved services and published appointment options." />
    <InlineNotice>{resource.data.approval_meaning}</InlineNotice>
    {resource.data.services.length?resource.data.services.map((service:any)=><article className="request-card" key={service.offering}><header><strong>{service.label}</strong><span>Approved for this service</span></header><p>{service.minutes} minutes · {service.consultation_format} · ETB {money(service.price)} · {service.timezone}</p><Link className="button secondary" to={'/patient/book/'+service.offering}>{w('Choose a time')}</Link></article>):<EmptyState title="No published service times are available yet." />}
  </>;
}
