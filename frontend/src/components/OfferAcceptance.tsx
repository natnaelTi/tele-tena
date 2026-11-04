import {usePaymentCapabilities} from './DirectPayments';
import {clearReturn} from '../guest-intent';
import {useEffect,useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {api} from '../api';
import {journeyApi,type Disclosure} from '../journey-api';
import {useSession} from '../hooks/useSession';
import {useResource} from '../hooks/useResource';
import {useAction} from '../hooks/useAction';
import {useLocale} from '../hooks/useLocale';
import {Dialog,Checkbox,Button,InlineNotice,Skeleton} from './ui';
import {DisclosurePreview,money,date} from './Domain';
import {FileSharingChoice} from './EncounterFiles';
import {AddFundsDialog} from './AddFundsDialog';
import './OfferAcceptance.css';
export function OfferAcceptance({request,offer,close,refresh,onAccepted}:{request:any;offer:any;close:()=>void;refresh:()=>Promise<unknown>;onAccepted?:(result:{appointment:string})=>void}){
 const capabilities=usePaymentCapabilities(),offline=capabilities.data?.mode==='Offline';
 const {w}=useLocale(),{session}=useSession(),navigate=useNavigate(),action=useAction(),wallet=useResource(journeyApi.wallet);
 const [reviewSharing,setReviewSharing]=useState(!session?.profile?.share_name||!session?.profile?.share_history);
 const [sharing,setSharing]=useState({name:!!session?.profile?.share_name,history:!!session?.profile?.share_history,files:[] as string[]}),[preview,setPreview]=useState<Disclosure|null>(null),[error,setError]=useState(false),[funds,setFunds]=useState(false),[retry,setRetry]=useState(0);
 useEffect(()=>{let current=true;setPreview(null);setError(false);void api<{disclosure:Disclosure}>('tele_tena.api.open_requests.preview_acceptance',{request_id:request.id,offer_id:offer.id,sharing},true).then(value=>{if(current)setPreview(value.disclosure);}).catch(()=>{if(current)setError(true);});return()=>{current=false;};},[sharing,request.id,offer.id,retry]);
 return <><Dialog open onOpenChange={open=>{if(!open&&!action.busy)close();}} title={w('Review This Offer')} description={w('Only this treating clinician receives your selected history and files.')} className="offer-acceptance-dialog">
 <div className="offer-acceptance-summary"><div><strong>{offer.clinician_name}</strong><p>{date(offer.start,offer.timezone)} · {offer.timezone}</p><p>{offer.duration_minutes} {w('minutes')} · {w(offer.consultation_format==='audio'?'Audio':'Video')}</p></div><div><span>{w('Total price')}</span><strong>ETB {money(offer.price_minor)}</strong></div></div>
 <div className={"offer-acceptance-columns"+(!reviewSharing?" sharing-condensed":"")}><section><details open={reviewSharing} onToggle={event=>setReviewSharing(event.currentTarget.open)}><summary>{w('Sharing Choices')}</summary><Checkbox label={w('Share my preferred name')} checked={sharing.name} disabled={action.busy} onChange={event=>setSharing({...sharing,name:event.target.checked})}/><Checkbox label={w('Share my saved text history')} checked={sharing.history} disabled={action.busy} onChange={event=>setSharing({...sharing,history:event.target.checked})}/><details className="offer-file-choices"><summary>{w('Choose History Files (optional)')}{sharing.files.length>0?' · '+sharing.files.length:''}</summary><FileSharingChoice selected={sharing.files} onChange={files=>setSharing({...sharing,files})}/></details></details>
 <p className="supporting">{w(sharing.name?'Your preferred name is shared.':'Your name stays private.')} {w(sharing.history?'Your saved text history is shared with this treating clinician when you accept.':'Your saved text history stays private.')}</p>
 {!offline&&wallet.data&&<div className="offer-balance-check"><span>{w('Available balance')}</span><strong>ETB {money(wallet.data.available)}</strong>{wallet.data.available<offer.price_minor&&<p>{w('Amount to add')}: ETB {money(offer.price_minor-wallet.data.available)}</p>}<Button variant="secondary" disabled={action.busy} onClick={()=>setFunds(true)}>{w('Add funds')}</Button></div>}
 {!offline&&wallet.error&&<InlineNotice tone="danger">{w('Balance could not be loaded.')} <Button variant="quiet" onClick={()=>void wallet.refresh()}>{w('Try again')}</Button></InlineNotice>}
 </section><section aria-label={w('Sharing preview')}>{error?<InlineNotice tone="danger">{w('The sharing preview is unavailable. This offer may have expired.')} <Button variant="quiet" onClick={()=>setRetry(value=>value+1)}>{w('Retry')}</Button></InlineNotice>:preview?(reviewSharing?<DisclosurePreview disclosure={preview}/>:null):<Skeleton/>}</section></div>
 <p className="offer-acceptance-policy">{w(offline?'Choose this offer to continue to private direct-payment instructions. The price, clinician and time are checked again; confirmation requires the applicable payment and appointment approvals.':'Confirming reserves this total from your balance. Adding funds does not hold the offer;eligibility and time are checked again.')}</p>
 <div className="dialog-actions"><Button loading={action.busy} disabled={!capabilities.data||!preview||error||(!offline&&(!wallet.data||wallet.data.available<offer.price_minor))} onClick={()=>void action.run(async()=>{const result:any=await journeyApi.respondOffer(request.id,offer.id,'accept',sharing,preview||undefined,capabilities.data||undefined);await refresh();if(result.appointment){clearReturn();if(result.payment){close();navigate('/patient/direct-payments/'+result.payment);return;}if(onAccepted){onAccepted({appointment:result.appointment});close();return;}const detail=await journeyApi.appointmentDetail(result.appointment);close();navigate(request.urgency==='immediate'&&detail.status==='Booked'&&detail.can_join?'/consultation/'+result.appointment+'/room':'/patient/consultations/'+result.appointment);}else close();})}>{w('Accept offer')}</Button><Button variant="quiet" disabled={action.busy} onClick={close}>{w('Back')}</Button></div>{action.error&&<InlineNotice tone="danger">{w(action.error)}</InlineNotice>}
 </Dialog><AddFundsDialog open={funds} close={()=>setFunds(false)} refresh={async()=>{await wallet.refresh();}}/></>;
}
