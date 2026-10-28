import {createContext,useCallback,useContext,useEffect,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import {api} from '../api';
import {useSession} from './useSession';
export type Notice={href?:string;id:string;source:'user'|'booking'|'offer';kind:string;title:string;category:string;appointment:string|null;created:string;read:boolean;appointment_state?:string;payment_mode?:string};
type Feed={items:Notice[]|null;error:boolean;partial:boolean;refresh:()=>Promise<void>;mark:(item:Notice)=>Promise<void>};
const Context=createContext<Feed|null>(null);
export function NotificationsProvider({children}:{children:ReactNode}){const{session}=useSession();return <FeedForUser key={session?.user||'guest'} clinician={session?.profile?.kind==='clinician'} enabled={!!session}>{children}</FeedForUser>;}
function FeedForUser({children,enabled,clinician}:{children:ReactNode;enabled:boolean;clinician:boolean}){
 const[items,setItems]=useState<Notice[]|null>(null),[error,setError]=useState(false),[partial,setPartial]=useState(false);
 const active=useRef(true),flight=useRef<Promise<void>|null>(null),abort=useRef<AbortController|null>(null),known=useRef(new Set<string>()),last=useRef<{general:Notice[];offers:Notice[]}>({general:[],offers:[]});
 const refresh=useCallback(()=>{if(!enabled)return Promise.resolve();if(flight.current)return flight.current;
  const controller=new AbortController();abort.current=controller;const timeout=setTimeout(()=>controller.abort(),8000);
  flight.current=(async()=>{try{
   const [general,offers]=await Promise.allSettled([api<Notice[]>('tele_tena.notifications.feed',{},false,controller.signal),clinician?api<{items:{id:string;appointment:string;accepted_at:string;read:boolean;appointment_state:string;payment_mode:string}[]}>('tele_tena.api.open_requests.clinician_notifications',{},false,controller.signal):Promise.resolve({items:[]})]);
   if(!active.current)return;
   const failed=general.status==='rejected',offerFailed=offers.status==='rejected';
   if(!failed)last.current.general=general.value;
   if(!offerFailed)last.current.offers=offers.value.items.map(n=>({id:n.id,source:'offer',kind:'OfferAccepted',title:'Your Offer Was Accepted',category:'offers',appointment:n.appointment,created:n.accepted_at,read:n.read,appointment_state:n.appointment_state,payment_mode:n.payment_mode,href:'/clinician/consultations/'+n.appointment}));
   if(failed&&(!clinician||offerFailed)){setError(true);return;}
   const next=[...last.current.general,...last.current.offers].sort((a,b)=>b.created.localeCompare(a.created));
   const payments=next.some(n=>n.kind.startsWith('Payment')&&!known.current.has(n.source+n.id));
   for(const n of next)known.current.add(n.source+n.id);
   setItems(next);setError(false);setPartial(failed||offerFailed);
   if(payments)window.dispatchEvent(new Event('teletena:payment-update'));
  }catch{if(active.current)setError(true);}finally{clearTimeout(timeout);flight.current=null;}})();return flight.current;
 },[enabled,clinician]);
 useEffect(()=>{active.current=true;void refresh();const timer=setInterval(()=>void refresh(),5000);const resume=()=>{if(document.visibilityState==='visible')void refresh();};window.addEventListener('focus',resume);window.addEventListener('online',resume);document.addEventListener('visibilitychange',resume);return()=>{active.current=false;clearInterval(timer);abort.current?.abort();window.removeEventListener('focus',resume);window.removeEventListener('online',resume);document.removeEventListener('visibilitychange',resume);};},[refresh]);
 const mark=useCallback(async(item:Notice)=>{await api(item.source==='offer'?'tele_tena.api.open_requests.read_clinician_notification':'tele_tena.notifications.mark_read',item.source==='offer'?{offer_id:item.id}:{id:item.id,source:item.source},true);if(active.current)setItems(old=>old?.map(n=>n.source===item.source&&n.id===item.id?{...n,read:true}:n)||null);await refresh();},[refresh]);
 return <Context.Provider value={{items,error,partial,refresh,mark}}>{children}</Context.Provider>;
}
export function useNotifications(){const value=useContext(Context);if(!value)throw new Error('Notification provider unavailable');return value;}
