import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { HeartHandshake, ShieldCheck } from 'lucide-react';
import { journeyApi, type Disclosure } from '../journey-api';
import { useResource } from '../hooks/useResource';
import { useAction } from '../hooks/useAction';
import { useLocale } from '../hooks/useLocale';
import { useSession } from '../hooks/useSession';
import { Button, Card, Checkbox, EmptyState, InlineNotice, Skeleton, TextField } from '../components/ui';
import { DisclosurePreview, date, money } from '../components/Domain';
import { AddFundsDialog } from '../components/AddFundsDialog';

export default function Couples() {
  const {w}=useLocale();const location=useLocation();const navigate=useNavigate();
  const [token]=useState(()=>(location.state as {coupleToken?:string}|null)?.coupleToken||'');
  const plans=useResource(journeyApi.couplePlans);const wallet=useResource(journeyApi.wallet);const action=useAction();
  const [addFunds,setAddFunds]=useState(false);
  const [pay,setPay]=useState<string|null>(null);
  useEffect(()=>{if(token)navigate(location.pathname,{replace:true,state:null});},[token,navigate,location.pathname]);
  useEffect(()=>{const timer=window.setInterval(()=>void plans.refresh(),10000);return()=>window.clearInterval(timer);},[plans.refresh]);
  const invitation=token?`${window.location.origin}${import.meta.env.PROD?'/teletena':''}/couple-invitation#consent=${encodeURIComponent(token)}`:'';
  return <div className="shared-care-page"><header><HeartHandshake size={24}/><h1>{w('Shared care')}</h1><p>{w('Two adults, separate consent and privacy.')}</p></header>
    {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
    {invitation&&<Card><h2>{w('Private invitation link')}</h2><p>{w('Share this link directly with the intended adult. Anyone holding it can try to accept it.')}</p><TextField label={w('Private invitation link')} value={invitation} readOnly/><Button variant="secondary" onClick={()=>void action.run(async()=>navigator.clipboard.writeText(invitation),w('Invitation link copied.'))}>{w('Copy link')}</Button></Card>}
    {plans.error?<InlineNotice tone="danger">{w('This step could not be loaded. Try again.')} <Button onClick={()=>void plans.refresh()}>{w('Retry')}</Button></InlineNotice>:!plans.data?<Skeleton/>:!plans.data.length?<EmptyState title={w('No shared sessions yet.')}><Link to="/patient/discovery">{w('Find care')}</Link></EmptyState>:plans.data.map(plan=><Card key={plan.id}>
      <h2>{plan.service}</h2><p>{plan.clinician} · {date(plan.start,plan.timezone)}</p>
      <div className="shared-care-columns"><section><h3>{w('Participants')}</h3><p>{w('Your consent')}: {w(plan.you_consented?'Ready':'Withdrawn')}</p><p>{w('Adults who consented')}: {plan.participant_count} / 2</p><p>{w(plan.appointment_state==='Completed'?'Completed':plan.appointment_state==='Cancelled'?'Cancelled':plan.call_state==='Ended'?'Call ended':plan.state==='Booked'?'Confirmed':plan.state==='Consented'?'Ready to confirm':plan.state==='Invited'?'Waiting for consent':plan.state)}</p><ShieldCheck size={20}/><p>{w('Your private intake is not visible to the other adult.')}</p></section><section><h3>{w('Session & payment')}</h3><p>{plan.minutes} {w('minutes')} · ETB {money(plan.price)}</p><p>{w(plan.you_pay?'You pay the total session price.':'Your wallet is not charged for this session.')}</p>
      {plan.state==='Consented'&&plan.you_pay&&<><Checkbox label={w('I authorize the total session payment.')} checked={pay===plan.id} onChange={event=>setPay(event.target.checked?plan.id:null)}/>{wallet.data&&wallet.data.available<plan.price&&<InlineNotice>{w('Add funds before confirming. The time will be checked again.')} <Button variant="secondary" onClick={()=>setAddFunds(true)}>{w("Add funds")}</Button></InlineNotice>}<Button disabled={pay!==plan.id||action.busy} loading={action.busy} onClick={()=>void action.run(async()=>{const booked=await journeyApi.coupleConfirm(plan.id);navigate('/patient/consultations/'+booked.id);},'')}>{w('Confirm appointment')}</Button></>}
      {plan.appointment&&plan.you_consented&&<Link className="button primary" to={'/patient/consultations/'+plan.appointment}>{w('View consultation')}</Link>}
      {['Invited','Consented','Booked'].includes(plan.state)&&!['Completed','Cancelled','Expired'].includes(plan.appointment_state)&&plan.you_consented&&<details><summary>{w('Withdraw consent')}</summary><p>{w('Before the scheduled start, withdrawal cancels the session and releases its reservation. After the start, the call ends and the fee requires review.')}</p><Button variant="danger" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.coupleWithdraw(plan.id);await plans.refresh();await wallet.refresh();},'')}>{w('Withdraw consent')}</Button></details>}
      </section></div></Card>)}
    <AddFundsDialog open={addFunds} close={()=>setAddFunds(false)} refresh={wallet.refresh}/>
  </div>;
}

export function CoupleInvitation() {
  const {w}=useLocale();const location=useLocation();const navigate=useNavigate();const {session,loading}=useSession();
  const [token]=useState(()=>new URLSearchParams(window.location.hash.slice(1)).get('consent')||(location.state as {coupleInvitationToken?:string}|null)?.coupleInvitationToken||'');
  const [step,setStep]=useState(0);const [request,setRequest]=useState('');const [adult,setAdult]=useState(false);const [sharing,setSharing]=useState({name:false,history:false});const [preview,setPreview]=useState<Disclosure|null>(null);const action=useAction();
  const load=useCallback(()=>session?.profile?.kind==='patient'&&token?journeyApi.coupleInvitation(token):Promise.resolve(null),[session?.profile?.kind,token]);const invitation=useResource(load);
  useEffect(()=>{window.history.replaceState(window.history.state,'',window.location.pathname);},[]);
  if(loading)return <main className="container"><Skeleton/></main>;
  return <main className="container guided-content shared-invitation"><p className="eyebrow">{w("SHARED CARE")} · {w("STEP")} {step+2} {w("OF")} 4</p><div className="step-progress" aria-label={`${w("Step")} ${step+2} ${w("of")} 4`}>{[0,1,2,3].map(value=><span key={value} data-complete={value<=step+1}/>)}</div><h1>{w(step?"Your private intake":"Your invitation")}</h1><p>{w(step?"This intake is private to you and the treating clinician.":"You choose whether to take part. Accepting an invitation does not share your care records.")}</p>
    {!session?<><p>{w('Each adult signs in independently before choosing what to share.')}</p><Button onClick={()=>navigate('/sign-in?intent=patient&next=%2Fcouple-invitation',{state:{coupleInvitationToken:token}})}>{w('Sign in to review invitation')}</Button></>:session.profile?.kind!=='patient'?<InlineNotice>{w('This invitation is for patient accounts. Sign in with a patient account to continue.')}</InlineNotice>:invitation.error?<InlineNotice tone="danger">{w('This invitation is no longer available.')}</InlineNotice>:!invitation.data?<Skeleton/>:<Card>
      <h2>{invitation.data.service}</h2><p>{invitation.data.clinician} · {date(invitation.data.start,invitation.data.timezone)} · ETB {money(invitation.data.price)}</p><p>{w('Your wallet is not charged for this session.')}</p>
      {step===0?<><h3>{w("Your choice")}</h3><p>{w("You will have your own account, intake, and consent choices.")}</p><div className="actions"><Button onClick={()=>setStep(1)}>{w("Review my choices")}</Button><Link className="text-link" to="/patient/couples">{w("Not now")}</Link></div></>:<><label className="field">{w('What would you like the clinician to understand?')}<textarea rows={4} maxLength={2000} value={request} onChange={event=>{setRequest(event.target.value);setPreview(null);}}/></label>
      <p>{w('Your private intake is not visible to the other adult.')}</p>
      <Checkbox label={w('Share my preferred name')} checked={sharing.name} onChange={event=>{setSharing({...sharing,name:event.target.checked});setPreview(null);}}/>
      <Checkbox label={w('Share my saved history')} checked={sharing.history} onChange={event=>{setSharing({...sharing,history:event.target.checked});setPreview(null);}}/>
      <Checkbox label={w('I am 18 or older and freely consent to this shared consultation.')} checked={adult} onChange={event=>setAdult(event.target.checked)}/>
      {preview&&<DisclosurePreview disclosure={preview}/>}{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
      <div className="actions"><Button variant="secondary" onClick={()=>setStep(0)}>{w("Back")}</Button><Button variant="secondary" disabled={!request.trim()} loading={action.busy} onClick={()=>void action.run(async()=>setPreview((await journeyApi.preview(request,sharing)).disclosure),'')}>{w('Preview')}</Button><Button disabled={!preview||!adult||action.busy} loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.coupleConsent({token,request_text:request,sharing,expected_disclosure:preview,adult_confirmed:adult});navigate('/patient/couples');},'')}>{w('Save my choices')}</Button></div></>}
    </Card>}
  </main>;
}
