import {createContext,useContext,useCallback,useEffect,useState,type ReactNode} from 'react';
import {Link} from 'react-router-dom';
import {Radio,CalendarClock} from 'lucide-react';
import {journeyApi} from '../journey-api';
import {useResource} from '../hooks/useResource';
import {useLocale} from '../hooks/useLocale';
import {ApiError} from '../api';
import {Button,InlineNotice} from './ui';
import './RequestPresence.css';
const PresenceContext=createContext<any>(null);
export function RequestPresenceProvider({enabled,children}:{enabled:boolean;children:ReactNode}) {
 return enabled?<ConnectedPresence>{children}</ConnectedPresence>:children;
}
function ConnectedPresence({children}:{children:ReactNode}) {
  const load = useCallback(() => journeyApi.requestPresence(), []);
  const presence = useResource<any>(load);
  const refresh = presence.refresh;
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<"network" | "session" | "permission" | "update" | null>(null);
  const failureMessage = failure === "network"
    ? "Connection interrupted; request availability may expire."
    : failure === "session"
      ? "Your session expired. Sign in again to update request availability."
      : failure === "permission"
        ? "You don’t have permission to change request availability."
        : failure === "update"
          ? "Could not update request availability. Review the setup items and try again."
          : null;
  const recordFailure = useCallback((error: unknown) => {
    if (error instanceof ApiError && error.code === "no_immediate_capacity") {setFailure(null);void refresh();return;}
    if (error instanceof ApiError && error.code === "session_required") setFailure("session");
    else if (error instanceof ApiError && error.code === "permission_denied") setFailure("permission");
    else if (error instanceof TypeError) setFailure("network");
    else setFailure("update");
    void refresh().catch(() => undefined);
  }, [refresh]);
  useEffect(() => {
    let active=true;
    const renew=()=>{void journeyApi.heartbeatRequestPresence().then(()=>{if(active){setFailure(null);void refresh();}}).catch(error=>{if(active)recordFailure(error);});};
    renew();
    const timer=window.setInterval(renew,30000);
    window.addEventListener('online',renew);
    window.addEventListener('teletena:availability-saved',renew);
    return()=>{active=false;window.clearInterval(timer);window.removeEventListener('online',renew);window.removeEventListener('teletena:availability-saved',renew);};
  },[refresh,recordFailure]);
  const toggle = async (pause=false, manual=false) => {
    setBusy(true);
    try {
      if(pause) await journeyApi.setRequestPresence(false);
      else if(manual) await journeyApi.setRequestPresence(true);
      else if(!presence.data?.ready && presence.data?.automatic) await journeyApi.heartbeatRequestPresence(true);
      else await journeyApi.setRequestPresence(!presence.data?.ready);
      setFailure(null);
      await presence.refresh();
    } catch (error) {
      recordFailure(error);
    } finally { setBusy(false); }
  };
  return <PresenceContext.Provider value={{...presence,busy,failureMessage,toggle}}>{children}</PresenceContext.Provider>;
}
export function RequestAvailabilityCard(){
 const context=useContext(PresenceContext),{w}=useLocale();
 if(!context)return null;
 const {data,busy,failureMessage,toggle,error,refresh}=context;
 const state=error?'error':data?.occupancy|| (data?.ready?'available':data?.reasons?.some((r:string)=>r!=='no_immediate_capacity')?'setup':'paused');
 const title=state==='available'?'Available for requests':state==='in_consultation'?'In consultation':state==='occupied'?'Occupied':state==='setup'?'Complete your request setup':state==='error'?'Availability unavailable':data?.reasons?.includes('no_immediate_capacity')?'Requests paused — No immediate opening':'Requests paused';
 const guidance:Record<string,{label:string;to:string}>={
 approval_required:{label:'Approval required',to:'/clinician/vetting'},language_required:{label:'Add a care language',to:'/clinician/account'},offering_required:{label:'Publish an offering',to:'/clinician/services'},scope_approval_required:{label:'Get approval for a service scope',to:'/clinician/vetting'},published_schedule_required:{label:'Publish availability',to:'/clinician/availability'},immediate_policy_required:{label:'Ask a reviewer about immediate-care policy',to:'/clinician/services'},no_immediate_capacity:{label:'Review availability',to:'/clinician/availability'}};
 return <section className={'request-availability-card state-'+state} aria-label={w('Request availability')}>
 <div className="presence-card-heading"><Radio size={28} aria-hidden="true"/><div><span>{w('Immediate requests')}</span><h2 aria-live="polite">{w(title)}</h2></div><span className="presence-status-dot" aria-hidden="true"/></div>
 {!data&&!error?<p>{w('Checking availability…')}</p>:<p>{w(data?.ready?'You can receive eligible requests while this workspace is connected.':data?.occupancy?'Your booked time is protected. Requests resume when a full session fits.':data?.control_mode==='paused'?'You paused requests. Start again when you are ready.':data?.automatic&&!data?.within_hours?'Automatic availability resumes during your published hours while this workspace is connected.':data?.reasons?.includes('no_immediate_capacity')?'No full session can start within the immediate-care window.':'Complete the steps below or start when you are ready.')}</p>}
 {state==='setup'&&<ul>{data?.reasons?.map((reason:string)=>guidance[reason]&&<li key={reason}><Link to={guidance[reason].to}>{w(guidance[reason].label)}</Link></li>)}</ul>}
 <div className="actions">{error?<Button variant="secondary" onClick={()=>void refresh()}>{w('Retry')}</Button>:<Button loading={busy} disabled={!data||(!data.configured&&!data.ready&&!data.automatic)||(data.automatic&&data.control_mode!=='paused'&&!data.ready)} onClick={()=>void toggle()}>{w(data?.ready?'Pause':data?.automatic?(data.control_mode==='paused'?'Resume automatic availability':'Automatic availability enabled'):'Go available')}</Button>}
 {data?.automatic&&!data.ready&&data.configured&&<Button variant="secondary" loading={busy} onClick={()=>void toggle(false,true)}>{w('Go available now')}</Button>}
 {data?.automatic&&data.control_mode!=='paused'&&!data.ready&&<Button variant="secondary" loading={busy} onClick={()=>void toggle(true)}>{w('Pause requests')}</Button>}
 <Link className="text-link" to="/clinician/availability"><CalendarClock size={18}/>{w('Manage availability')}</Link></div>
 {data?.automatic&&<small>{w('Automatic during published hours · Manual pause always takes priority.')}</small>}
 {failureMessage&&<InlineNotice tone="danger">{w(failureMessage)}</InlineNotice>}
 </section>;
}
