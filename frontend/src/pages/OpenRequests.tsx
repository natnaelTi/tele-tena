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
import { RequestProgress } from '../components/RequestProgress';

type Service = {id:string;label:string};
type Offer = {id:string;clinician_name:string;clinician_id:string;specialty:string;start:string;timezone:string;duration_minutes:number;consultation_format:string;price_minor:number;price_source:string;state:string;valid_until:string};
type PatientRequest = {id:string;state:string;urgency:string;service:string;category:string;language:string;consultation_format:string;request_text:string;disclosure_snapshot:Disclosure;max_price_minor:number|null;published_at:string;expires_at:string;earliest_start?:string|null;latest_start?:string|null;timezone?:string;first_offer_at:string|null;appointment?:string|null;current_wave?:number;offers:Offer[]};
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
  const isLiveRequest=(request:PatientRequest)=>request.state==='Open'&&new Date(request.expires_at).getTime()>Date.now();
  const liveRequests=requests.filter(isLiveRequest);
  const historyRequests=requests.filter(request=>!isLiveRequest(request));
  const renderRequest=(req:PatientRequest)=>(
    <article className="request-card" key={req.id}><header><strong>{req.urgency==='immediate'?'As soon as possible':'Scheduled request'} · {req.category}</strong><span>{req.state==='Open'&&new Date(req.expires_at).getTime()<=Date.now()?'Expired':req.state}</span><Link className="text-link" to={'/patient/requests/'+encodeURIComponent(req.id)}>{w('Open request details')}</Link></header><RequestProgress state={isLiveRequest(req)?'Open':req.state==='Open'?'Expired':req.state} hasOffer={req.offers.some(o=>o.state==='Active'&&new Date(o.valid_until).getTime()>Date.now())} wave={req.current_wave}/><p>{req.request_text}</p>{req.state==='Matched'&&req.appointment&&<Link className="button primary" to={'/patient/consultations/'+req.appointment}>View appointment</Link>}{req.state==='Open'&&Date.now()-new Date(req.published_at).getTime()>180000&&req.urgency==='immediate'&&<InlineNotice>No offer has arrived within three minutes. You can keep waiting, schedule for later, or browse clinicians. This does not broaden your request.</InlineNotice>}{req.state==='Open'&&Date.now()-new Date(req.published_at).getTime()>180000&&req.urgency==='immediate'&&showFallback[req.id]!==false&&<div className="request-fallback"><Button variant="secondary" onClick={()=>setShowFallback({...showFallback,[req.id]:false})}>Continue waiting</Button><Button variant="secondary" onClick={()=>{setNarrative(req.request_text);setService(req.service);setLanguage(req.language);setFormat(req.consultation_format as 'video'|'audio');setUrgency('scheduled');document.getElementById('request-composer')?.scrollIntoView({behavior:'smooth'});}}>Schedule for later</Button><Link to="/patient/discovery" className="text-link">Browse clinicians</Link></div>}{req.state==='Open'&&<p className="supporting">Waiting for eligible clinicians · closes {new Date(req.expires_at).toLocaleString()}</p>}{req.offers.filter(o=>o.state==='Active').map(offer=><div className="request-offer" key={offer.id}><div><strong>{offer.clinician_name}</strong><span>{offer.specialty} · {offer.consultation_format} · {offer.duration_minutes} minutes</span><time>{new Date(offer.start).toLocaleString(undefined,{timeZone:offer.timezone})} · {offer.timezone}</time><Link to={'/patient/clinicians/'+offer.clinician_id} target="_blank" rel="noreferrer" className="text-link">View clinician profile</Link></div><strong>ETB {money(offer.price_minor)}</strong><p>This offer is available until {new Date(offer.valid_until).toLocaleTimeString()}.</p><Button variant="secondary" onClick={()=>setSelectedDisclosure({request:req,offer})}>Review and accept</Button><Button variant="quiet" onClick={()=>void action.run(async()=>{await journeyApi.respondOffer(req.id,offer.id,'decline');await requestResource.refresh();})}>Decline</Button></div>)}{req.state==='Open'&&<>{(req.current_wave||1)<3&&<Button variant="secondary" onClick={()=>void action.run(async()=>{const result=await journeyApi.findMoreOptions(req.id);await requestResource.refresh();if(!result?.notified)throw new Error('No additional clinicians currently meet your requirements. Your request remains open; you can keep waiting or browse clinicians.');})}>Find more options</Button>}<Button variant="quiet" onClick={()=>void action.run(async()=>{await journeyApi.cancelRequest(req.id);await requestResource.refresh();})}>Cancel request</Button></>}</article>
  );
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
    <section className="open-request-list"><h2>Your requests</h2>{requestResource.error?<InlineNotice tone="danger">Requests could not be loaded. <Button onClick={()=>void requestResource.refresh()}>Retry</Button></InlineNotice>:!requestResource.data?<Skeleton/>:requests.length?<>{liveRequests.length?liveRequests.map(renderRequest):<EmptyState title="No open requests yet.">If you want clinicians to respond with times, you can post a private request here.</EmptyState>}{historyRequests.length>0&&<details className="request-history"><summary>{w('Previous requests')} ({historyRequests.length})</summary>{historyRequests.map(renderRequest)}</details>}</>:<EmptyState title="No open requests yet.">If you want clinicians to respond with times, you can post a private request here.</EmptyState>}</section>
    {selectedDisclosure&&<div className="request-confirm-overlay" role="presentation"><section className="request-confirm" role="dialog" aria-modal="true" aria-labelledby="request-confirm-title"><h2 id="request-confirm-title">Review this offer</h2><p><strong>{selectedDisclosure.offer.clinician_name}</strong> · {selectedDisclosure.offer.specialty}</p><p>{new Date(selectedDisclosure.offer.start).toLocaleString(undefined,{timeZone:selectedDisclosure.offer.timezone})} · {selectedDisclosure.offer.duration_minutes} minutes · {selectedDisclosure.offer.consultation_format} · {selectedDisclosure.offer.timezone}</p><p><strong>Total price: ETB {money(selectedDisclosure.offer.price_minor)}</strong></p><h3>What will be shared</h3><div className="disclosure-preview">{Object.values(selectedDisclosure.request.disclosure_snapshot).map((value,i)=><p key={i}>{value}</p>)}</div><p className="supporting">Accepting confirms this appointment and reserves the amount from your balance. If your balance is short, add funds and return to the offer while it remains available.</p><div className="dialog-actions"><Button loading={action.busy} onClick={()=>void action.run(async()=>{const attempt=crypto.randomUUID();try{await journeyApi.respondOffer(selectedDisclosure.request.id,selectedDisclosure.offer.id,'accept',undefined,selectedDisclosure.request.disclosure_snapshot);}catch(error){await journeyApi.recordOfferAcceptFailure(selectedDisclosure.request.id,selectedDisclosure.offer.id,attempt,(error as any)?.code||'other_supported_failure').catch(()=>undefined);throw error;}setSelectedDisclosure(null);await requestResource.refresh();})}>Accept offer</Button><Button variant="secondary" onClick={()=>setSelectedDisclosure(null)}>Back</Button><Link to="/patient/payments" className="text-link">Add funds</Link></div>{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}</section></div>}
  </>;
}

export function PatientRequestDetail(){
  const {requestId=''}=useParams();
  const {w}=useLocale();
  const detail=usePolling<PatientRequest>(()=>journeyApi.myRequestDetail(requestId));
  const action=useAction();
  const [selectedOffer,setSelectedOffer]=useState<Offer|null>(null);
  const request=detail.data;
  const detailErrorCode=(detail.errorDetail as {code?:string}|null)?.code;
  const detailErrorMessage=detailErrorCode==='request_unavailable'?w('Request unavailable.'):
    detailErrorCode==='session_required'?w('Your sign-in session ended. Sign in again to view this request.'):
    detailErrorCode==='permission_denied'?w('You do not have permission to view this request.'):
    w('Could not load this request. Check your connection and try again.');
  const live=!!request&&request.state==='Open'&&new Date(request.expires_at).getTime()>Date.now();
  return <>
    <p><Link className="text-link" to="/patient/requests">← {w('Back to requests')}</Link></p>
    <PageTitle title={w('Request details')} description={w('Your request and its private responses.')}/>
    {detail.error?<InlineNotice tone="danger">{detailErrorMessage} {detailErrorCode!=='request_unavailable'&&<Button variant="quiet" onClick={()=>void detail.refresh()}>{w('Retry')}</Button>}</InlineNotice>:!request?<Skeleton/>:<>
      <article className="request-card request-detail-card">
        <header><strong>{request.urgency==='immediate'?w('As soon as possible'):w('Schedule for later')} · {request.category}</strong><span>{request.state==='Open'&&!live?w('Expired'):request.state}</span></header>
        <RequestProgress state={live?'Open':request.state==='Open'?'Expired':request.state} hasOffer={request.offers.some(offer=>offer.state==='Active'&&new Date(offer.valid_until).getTime()>Date.now())} wave={request.current_wave}/>
        <dl className="offer-facts"><div><dt>{w('Language')}</dt><dd>{request.language.toUpperCase()}</dd></div><div><dt>{w('Session format')}</dt><dd>{request.consultation_format}</dd></div>{request.urgency==='scheduled'&&request.earliest_start&&request.latest_start&&<div><dt>{w('Requested time window')}</dt><dd>{new Date(request.earliest_start).toLocaleString(undefined,{timeZone:request.timezone})} – {new Date(request.latest_start).toLocaleString(undefined,{timeZone:request.timezone})}<br/>{request.timezone}</dd></div>}{request.max_price_minor!==null&&<div><dt>{w('Maximum total price')}</dt><dd>ETB {money(request.max_price_minor)}</dd></div>}<div><dt>{w('Published')}</dt><dd>{new Date(request.published_at).toLocaleString(undefined,{timeZone:request.timezone})}<br/>{request.timezone}</dd></div><div><dt>{w('Closes')}</dt><dd>{new Date(request.expires_at).toLocaleString(undefined,{timeZone:request.timezone})}<br/>{request.timezone}</dd></div></dl>
        {request.appointment&&<Link className="button primary" to={'/patient/consultations/'+request.appointment}>{w('View appointment')}</Link>}
        {live&&<p className="supporting">{w('Waiting for eligible clinicians')} · {w('No request requirements are broadened automatically.')}</p>}{live&&request.urgency==='immediate'&&Date.now()-new Date(request.published_at).getTime()>180000&&<InlineNotice>{w('No offer has arrived within three minutes. You can continue waiting, schedule for later, or browse clinicians.')}</InlineNotice>}
        <section className="request-disclosure-history"><h2>{w('What clinicians saw')}</h2><div className="disclosure-preview">{Object.values(request.disclosure_snapshot).map((value,index)=><p key={index}>{value}</p>)}</div></section>
        {live&&<div className="actions">{(request.current_wave||1)<3&&<Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.findMoreOptions(request.id);await detail.refresh();})}>{w('Find more options')}</Button>}<Button variant="quiet" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.cancelRequest(request.id);await detail.refresh();},w('Request cancelled'))}>{w('Cancel request')}</Button></div>}
      </article>
      <section className="open-request-list"><h2>{w('Offers')}</h2>{request.offers.length?request.offers.map(offer=><article className="request-offer" key={offer.id}>
        <div><strong>{offer.clinician_name}</strong><span>{offer.specialty} · {offer.consultation_format} · {offer.duration_minutes} {w('minutes')}</span><time>{new Date(offer.start).toLocaleString(undefined,{timeZone:offer.timezone})} · {offer.timezone}</time><Link to={'/patient/requests/'+encodeURIComponent(request.id)+'/offers/'+encodeURIComponent(offer.id)} className="text-link">{w('Review offer details')}</Link><Link to={'/patient/clinicians/'+offer.clinician_id} target="_blank" rel="noreferrer" className="text-link">{w('View clinician profile')}</Link></div>
        <strong>ETB {money(offer.price_minor)}</strong><span>{offer.state==='Active'&&new Date(offer.valid_until).getTime()>Date.now()?w('Offer available until')+' '+new Date(offer.valid_until).toLocaleString():w(offer.state)}</span>
        {offer.state==='Active'&&live&&<div className="actions"><Button variant="secondary" onClick={()=>setSelectedOffer(offer)}>{w('Review and accept')}</Button><Button variant="quiet" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.respondOffer(request.id,offer.id,'decline');await detail.refresh();})}>{w('Decline')}</Button></div>}
      </article>):<EmptyState title={w('No offers yet')}>{live?w('We will show eligible clinician offers here.'):w('This request has no available offers.')}</EmptyState>}</section>
      {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
      {selectedOffer&&<div className="request-confirm-overlay" role="presentation"><section className="request-confirm" role="dialog" aria-modal="true" aria-labelledby="request-detail-confirm-title"><h2 id="request-detail-confirm-title">{w('Review this offer')}</h2><p><strong>{selectedOffer.clinician_name}</strong> · {selectedOffer.specialty}</p><p>{new Date(selectedOffer.start).toLocaleString(undefined,{timeZone:selectedOffer.timezone})} · {selectedOffer.duration_minutes} {w('minutes')} · {selectedOffer.consultation_format} · {selectedOffer.timezone}</p><p><strong>{w('Total price')}: ETB {money(selectedOffer.price_minor)}</strong></p><h3>{w('What you’ll share')}</h3><div className="disclosure-preview">{Object.values(request.disclosure_snapshot).map((value,index)=><p key={index}>{value}</p>)}</div><p className="supporting">{w('Accepting confirms this appointment and reserves the amount from your balance.')}</p><div className="dialog-actions"><Button loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.respondOffer(request.id,selectedOffer.id,'accept',undefined,request.disclosure_snapshot);setSelectedOffer(null);await detail.refresh();})}>{w('Accept offer')}</Button><Button variant="secondary" onClick={()=>setSelectedOffer(null)}>{w('Back')}</Button><Link to="/patient/payments" className="text-link">{w('Add funds')}</Link></div></section></div>}
    </>}
  </>;
}

export function PatientRequestOfferDetail(){
  const {requestId='',offerId=''}=useParams();
  const {w}=useLocale();
  const detail=usePolling<PatientRequest>(()=>journeyApi.myRequestDetail(requestId));
  const action=useAction();
  const request=detail.data;
  const offer=request?.offers.find(item=>item.id===offerId);
  const live=!!request&&request.state==='Open'&&new Date(request.expires_at).getTime()>Date.now();
  const available=!!offer&&offer.state==='Active'&&new Date(offer.valid_until).getTime()>Date.now()&&live;
  const detailErrorCode=(detail.errorDetail as {code?:string}|null)?.code;
  const detailErrorMessage=detailErrorCode==='request_unavailable'?w('Request unavailable.'):
    detailErrorCode==='session_required'?w('Your sign-in session ended. Sign in again to view this request.'):
    detailErrorCode==='permission_denied'?w('You do not have permission to view this request.'):
    w('Could not load this request. Check your connection and try again.');
  const accept=()=>void action.run(async()=>{
    if(!request||!offer)throw new Error(w('This offer is no longer available.'));
    await journeyApi.respondOffer(request.id,offer.id,'accept',undefined,request.disclosure_snapshot);
    await detail.refresh();
  });
  return <>
    <p><Link className="text-link" to={'/patient/requests/'+encodeURIComponent(requestId)}>← {w('Back to request')}</Link></p>
    <PageTitle title={w('Review offer details')} description={w('Check the appointment, total price and sharing choices before you decide.')}/>
    {detail.error?<InlineNotice tone="danger">{detailErrorMessage} {detailErrorCode!=='request_unavailable'&&<Button variant="quiet" onClick={()=>void detail.refresh()}>{w('Retry')}</Button>}</InlineNotice>:!request?<Skeleton/>:!offer?<InlineNotice tone="danger">{w('This offer is no longer available.')}</InlineNotice>:<>
      <article className="request-card request-detail-card">
        <header><strong>{offer.clinician_name}</strong><span>{w(offer.state)}</span></header>
        <p>{offer.specialty}</p>
        <dl className="offer-facts">
          <div><dt>{w('Proposed time')}</dt><dd>{new Date(offer.start).toLocaleString(undefined,{timeZone:offer.timezone})}<br/>{offer.timezone}</dd></div>
          <div><dt>{w('Session format')}</dt><dd>{offer.consultation_format} · {offer.duration_minutes} {w('minutes')}</dd></div>
          <div><dt>{w('Total price')}</dt><dd>ETB {money(offer.price_minor)}</dd></div>
          <div><dt>{w('Offer available until')}</dt><dd>{new Date(offer.valid_until).toLocaleString(undefined,{timeZone:offer.timezone})}<br/>{offer.timezone}</dd></div>
        </dl>
        <Link className="text-link" to={'/patient/clinicians/'+offer.clinician_id} target="_blank" rel="noreferrer">{w('View clinician profile')}</Link>
        <section className="request-disclosure-history"><h2>{w('What you’ll share')}</h2><p className="supporting">{w('This is the disclosure snapshot you accepted when you published the request.')}</p><div className="disclosure-preview">{Object.values(request.disclosure_snapshot).map((value,index)=><p key={index}>{value}</p>)}</div></section>
        {offer.state==='Accepted'&&request.appointment&&<Link className="button primary" to={'/patient/consultations/'+request.appointment}>{w('View appointment')}</Link>}
        {available&&<><InlineNotice>{w('Accepting confirms this appointment and reserves the amount from your balance. We will check the offer and time again when you accept.')}</InlineNotice><div className="actions"><Button loading={action.busy} onClick={accept}>{w('Accept offer')}</Button><Link className="text-link" to="/patient/payments">{w('Add funds')}</Link></div></>}
        {offer.state==='Active'&&!available&&<InlineNotice tone="info">{w('This offer is no longer available. Return to your request to see other options.')}</InlineNotice>}
        {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
      </article>
      <Link className="text-link" to={'/patient/requests/'+encodeURIComponent(request.id)}>{w('View all offers for this request')}</Link>
    </>}
  </>;
}

export function ClinicianRequestInbox(){
  const {w}=useLocale();

  const inbox=usePolling<InboxRequest[]>(()=>journeyApi.clinicianRequests());
  const practice=useResource(loadPractice);
  const [offerPage,setOfferPage]=useState(0);
  const offers=usePolling(()=>journeyApi.clinicianOffers(offerPage));
  const [offerView,setOfferView]=useState<'Active'|'History'>('Active');
  const action=useAction();
  const fetchedIds=useRef(new Set<string>());
  const [offerStarts,setOfferStarts]=useState<Record<string,string>>({});
  const [offerPrices,setOfferPrices]=useState<Record<string,string>>({});
  const [service,setService]=useState<Record<string,string>>({});
  const availableOfferings=(practice.data?.offerings||[]) as {id:string;label:string;price:number;minutes:number}[];
  const hasRequestOffering=(request:InboxRequest)=>availableOfferings.some(item=>item.label===request.category);
  useEffect(()=>{const ids=(inbox.data||[]).map(item=>item.id).filter(id=>!fetchedIds.current.has(id));if(!ids.length)return;void journeyApi.acknowledgeInboxFetch(ids).then(()=>ids.forEach(id=>fetchedIds.current.add(id))).catch(()=>undefined);},[inbox.data]);
  return <>
    <PageTitle title={w('Requests')} description="Respond only to requests matched to your approved services and languages." />
    {practice.error&&<InlineNotice tone="danger">{w('Approved services could not be loaded.')} <Button onClick={()=>void practice.refresh()}>{w('Retry')}</Button></InlineNotice>}
    {inbox.error?<InlineNotice tone="danger">Requests could not be loaded. <Button onClick={()=>void inbox.refresh()}>Retry</Button></InlineNotice>:!inbox.data?<Skeleton/>:inbox.data.length?inbox.data.map(req=><article className="request-card clinician-request" key={req.id}><header><strong>{req.urgency==='immediate'?'As soon as possible':'Schedule for later'} · {req.category}</strong><span>{req.language.toUpperCase()} · {req.consultation_format}</span></header><div className="disclosure-preview">{Object.values(req.disclosure_snapshot).map((value,i)=><p key={i}>{value}</p>)}</div><p className="supporting">The patient chose what to share for this request. Do not use it outside this response.</p>{req.own_offer_id&&<InlineNotice>Your offer is visible only to this patient and you. It remains available until {req.own_offer_until?new Date(req.own_offer_until).toLocaleTimeString():"its expiry"}. <Button variant="quiet" onClick={()=>void action.run(async()=>{await journeyApi.withdrawOffer(req.own_offer_id!);await inbox.refresh();await offers.refresh();})}>Withdraw offer</Button></InlineNotice>}{req.suggested_start&&<InlineNotice tone="info">Earliest feasible start: {new Date(req.suggested_start).toLocaleString(undefined,{timeZone:req.suggested_timezone})} · {req.suggested_timezone}. <Button variant="secondary" onClick={()=>setOfferStarts({...offerStarts,[req.id]:localDateTimeInput(req.suggested_start!)})}>Use suggested time</Button></InlineNotice>}{!practice.data?<p className="supporting" role="status">{w('Loading approved services…')}</p>:hasRequestOffering(req)?<Select label="Your approved service" value={service[req.id]||''} onChange={e=>setService({...service,[req.id]:e.target.value})}><option value="">{w('Choose a service')}</option>{availableOfferings.filter(x=>x.label===req.category).map(x=><option key={x.id} value={x.id}>{x.label} · {x.minutes} min · ETB {money(x.price)}</option>)}</Select>:<InlineNotice tone="info">{w('No approved offering is ready for this request. Check your service scope and published offering.')}</InlineNotice>}<TextField label="Proposed start (your device time)" type="datetime-local" value={offerStarts[req.id]||''} onChange={e=>setOfferStarts({...offerStarts,[req.id]:e.target.value})}/><TextField label="Total price (ETB)" inputMode="decimal" value={offerPrices[req.id]||''} placeholder={String((availableOfferings.find(x=>x.id===service[req.id])?.price||0)/100)} onChange={e=>setOfferPrices({...offerPrices,[req.id]:e.target.value})}/><p className="supporting">Requested range: {new Date(req.earliest_start).toLocaleString()} – {new Date(req.latest_start).toLocaleString()} · offer expires {new Date(req.expires_at).toLocaleTimeString()}</p><Button loading={action.busy} onClick={()=>void action.run(async()=>{if(!service[req.id]||!offerStarts[req.id])throw new Error('Choose an approved service and proposed start time.');const start=new Date(offerStarts[req.id]).toISOString();const amount=offerPrices[req.id]?etbToMinor(offerPrices[req.id]):null;await journeyApi.submitOffer({request_id:req.id,offering:service[req.id],start,price_minor:amount});await inbox.refresh();await offers.refresh();})} disabled={!!req.own_offer_id||!practice.data||!hasRequestOffering(req)||!service[req.id]||!offerStarts[req.id]}>Send offer</Button>{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}</article>):<EmptyState title="No requests match your approved services right now.">When an eligible patient publishes a request, it will appear here. Patient details stay limited to their chosen disclosure.</EmptyState>}
    <section className="clinician-offer-workspace" aria-label="Your offers"><h2>Your offers</h2><div className="segmented" aria-label="Offer views">{(['Active','History'] as const).map(view=><Button variant={offerView===view?'primary':'secondary'} key={view} onClick={()=>{setOfferView(view);setOfferPage(0);}} aria-pressed={offerView===view}>{view}</Button>)}</div>
    {offers.error?<InlineNotice tone="danger">Your offers could not be loaded. <Button onClick={()=>void offers.refresh()}>Retry</Button></InlineNotice>:!offers.data?<Skeleton/>:<>
      {offers.data.items.filter(item=>offerView==='Active'?item.state==='Active':item.state!=='Active').map(item=><article className="request-card" key={item.id}><header><strong>{item.patient_label} · {item.category}</strong><span>{item.state==='Superseded'?'Not selected / request closed':item.state}</span></header>
        <RequestProgress state={item.state} clinician/>
        <dl className="offer-facts"><div><dt>Proposed time</dt><dd>{new Date(item.start).toLocaleString(undefined,{timeZone:item.timezone})} · {item.timezone}</dd></div><div><dt>Duration / format</dt><dd>{item.duration_minutes} minutes · {item.consultation_format}</dd></div><div><dt>Total fee</dt><dd>ETB {money(item.price_minor)} · {item.price_source==='custom'?'Custom quote':'Published fee'}</dd></div><div><dt>Offer expires</dt><dd>{new Date(item.valid_until).toLocaleString()}</dd></div></dl>
        {item.state==='Accepted'&&item.appointment&&<Link className="button primary" to={'/clinician/consultations/'+item.appointment}>Open consultation details</Link>}
        {item.state==='Active'&&<Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.withdrawOffer(item.id);await offers.refresh();await inbox.refresh();})}>Withdraw offer</Button>}
      </article>)}
      {!offers.data.items.some(item=>offerView==='Active'?item.state==='Active':item.state!=='Active')&&<EmptyState title={offerView==='Active'?'No active offers on this page.':'No closed offers on this page.'}>Quotes stay private. Accepted and closed outcomes remain in your history.</EmptyState>}
      <div className="actions"><Button variant="secondary" disabled={offerPage===0} onClick={()=>setOfferPage(Math.max(0,offerPage-1))}>Previous offers</Button><span>Page {offerPage+1}</span><Button variant="secondary" disabled={!offers.data.has_more} onClick={()=>setOfferPage(offerPage+1)}>More offers</Button></div>
    </>}{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}</section>
  </>;
}

export function PublicClinicianProfile(){
  const {t,w}=useLocale();
  const {clinicianId=''}=useParams();
  const load=useCallback(()=>journeyApi.publicClinician(clinicianId),[clinicianId]);
  const resource=useResource(load);
  if(resource.error)return <InlineNotice tone="danger">This clinician profile is unavailable or no longer approved.</InlineNotice>;
  if(!resource.data)return <Skeleton/>;
  return <>
    <PageTitle eyebrow="CLINICIAN PROFILE" title={resource.data.display_name} description="Approved services and published appointment options." />
    <InlineNotice>{resource.data.approval_meaning}</InlineNotice>
    <section className="trust-indicators" aria-labelledby="trust-indicators-title"><h2 id="trust-indicators-title">{t("trustIndicators")}</h2><dl>
      <div><dt>{t("professionalReview")}</dt><dd>{t("manuallyReviewedScopes")}</dd></div>
      <div><dt>{t("responseBehavior")}</dt><dd>{resource.data.trust_indicators.responsiveness.rate_percent===null
        ? resource.data.trust_indicators.responsiveness.status==="new"?t("noRequestHistory"): <>{t("trustInsufficientData")} · {resource.data.trust_indicators.responsiveness.sample_count} {t("immediateRequestsPresented")}</>
        : <>{resource.data.trust_indicators.responsiveness.rate_percent}% {t("offerResponseRate")} · {resource.data.trust_indicators.responsiveness.response_count}/{resource.data.trust_indicators.responsiveness.sample_count} {t("immediateRequestsPresented")}</>}</dd></div>
      <div><dt>{t("reliability")}</dt><dd>{resource.data.trust_indicators.reliability.rate_percent===null
        ? resource.data.trust_indicators.reliability.status==="new"?t("noAppointmentHistory"): <>{t("trustInsufficientData")} · {resource.data.trust_indicators.reliability.sample_count} {t("completedAndCancelledSessions")}</>
        : <>{resource.data.trust_indicators.reliability.rate_percent}% · {resource.data.trust_indicators.reliability.clinician_cancelled_count}/{resource.data.trust_indicators.reliability.sample_count} {t("clinicianCancellations")}</>}</dd></div>
      <div><dt>{t("sessionExperienceMetric")}</dt><dd>{resource.data.trust_indicators.session_experience.average===null
        ? <>{t(resource.data.trust_indicators.session_experience.status==="new"?"sessionExperienceNew":"sessionExperienceMore")} · {resource.data.trust_indicators.session_experience.sample_count} {t("evidenceCount")}</>
        : <>{resource.data.trust_indicators.session_experience.average} / 5 · {resource.data.trust_indicators.session_experience.sample_count} {t("evidenceCount")}</>}</dd></div>
    </dl><p className="supporting">{t("sessionExperienceExplainer")}</p></section>
    {resource.data.services.length?resource.data.services.map((service:any)=><article className="request-card" key={service.offering}><header><strong>{service.label}</strong><span>{t("approvedScope")}</span></header><p>{service.minutes} minutes · {service.consultation_format} · ETB {money(service.price)} · {service.timezone}</p><Link className="button secondary" to={'/patient/book/'+service.offering}>{w('Choose a time')}</Link></article>):<EmptyState title="No published service times are available yet." />}
  </>;
}
