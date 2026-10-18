import {useCallback,useEffect,useRef,useState} from 'react';
import {Link,useLocation} from 'react-router-dom';
import {Bell} from 'lucide-react';
import {api} from '../api';
import {useResource} from '../hooks/useResource';
import {useLocale} from '../hooks/useLocale';
import {Button,Dialog,EmptyState,InlineNotice,Skeleton} from './ui';
import './ClinicianNotifications.css';
type Notification={id:string;appointment:string;accepted_at:string|null;read:boolean;kind?:'booking';label?:string};
export function ClinicianNotifications(){
 const {w}=useLocale(),location=useLocation();const load=useCallback(async()=>{const [offers,updates]=await Promise.all([api<{items:Notification[]}>('tele_tena.api.open_requests.clinician_notifications'),api<any[]>('tele_tena.booking_notifications.notices')]);const offered=new Set(offers.items.map(item=>item.appointment));return{items:[...offers.items,...updates.filter(item=>item.channel==='in_app'&&item.state==='Available'&&!offered.has(item.appointment)).map(item=>({id:item.id,appointment:item.appointment,accepted_at:item.created,read:!!item.read_at,kind:'booking' as const,label:item.appointment_state==='Booked'?'Appointment confirmed':item.appointment_state==='PendingConfirmation'?'Awaiting clinician approval':'View appointment update'}))]};},[]);
 const data=useResource(load),[open,setOpen]=useState(false),[failure,setFailure]=useState(false),[popup,setPopup]=useState<Notification|null>(null);
 const announced=useRef(new Set<string>()),trigger=useRef<HTMLButtonElement|null>(null);
 const call=location.pathname.includes('/consultation/')||location.pathname.endsWith('/room');
 useEffect(()=>{const timer=window.setInterval(()=>{if(navigator.onLine)void data.refresh();},5000);return()=>window.clearInterval(timer);},[data.refresh]);
 useEffect(()=>{if(call||popup)return;const next=data.data?.items.find(item=>item.kind!=='booking'&&!item.read&&!announced.current.has(item.id)&&item.accepted_at&&Date.now()-Date.parse(item.accepted_at)<15*60*1000);if(next){announced.current.add(next.id);setPopup(next);}},[data.data,call,popup]);
 const mark=async(item:Notification)=>{setFailure(false);try{await api(item.kind==='booking'?'tele_tena.booking_notifications.mark_read':'tele_tena.api.open_requests.read_clinician_notification',item.kind==='booking'?{id:item.id}:{offer_id:item.id},true);if(popup?.id===item.id)setPopup(null);await data.refresh();}catch{setFailure(true);}};
 const unread=data.data?.items.filter(item=>!item.read).length||0;
 return <><Button variant="quiet" aria-label={w('Notifications')} title={w('Notifications')} onClick={event=>{trigger.current=event.currentTarget;setOpen(true);}}><Bell size={20}/>{unread>0&&<span className="notification-count">{unread}</span>}</Button>
 <Dialog open={open} onOpenChange={value=>{setOpen(value);if(!value)requestAnimationFrame(()=>trigger.current?.focus());}} title={w('Notifications')} description={w('Accepted offers and your consultation links.')}>
 {data.error?<InlineNotice tone="danger">{w('Notifications could not be loaded.')} <Button onClick={()=>void data.refresh()}>{w('Retry')}</Button></InlineNotice>:!data.data?<Skeleton/>:data.data.items.length?data.data.items.map(item=><article className="clinician-notification" key={item.id}><strong>{w(item.label||'Your offer was accepted')}</strong>{item.accepted_at&&<time>{new Date(item.accepted_at).toLocaleString()}</time>}<Link className="text-link" to={'/clinician/consultations/'+item.appointment} onClick={()=>{void mark(item);setOpen(false);}}>{w('View consultation')}</Link>{!item.read&&<Button variant="quiet" onClick={()=>void mark(item)}>{w('Mark as read')}</Button>}</article>):<EmptyState title={w('No notifications yet')}/>}
 {failure&&<InlineNotice tone="danger">{w('We could not mark this notification as read. Try again.')}</InlineNotice>}</Dialog>
 {popup&&!call&&!open&&<aside className="clinician-notification-popup" role="status"><Bell size={22}/><div><strong>{w('Your offer was accepted')}</strong><p>{w('The appointment is confirmed. Open its details to prepare or join.')}</p><Link className="text-link" to={'/clinician/consultations/'+popup.appointment} onClick={()=>void mark(popup)}>{w('View consultation')}</Link></div><Button variant="quiet" aria-label={w('Dismiss notification')} onClick={()=>void mark(popup)}>×</Button>{failure&&<p>{w('We could not mark this notification as read. Try again.')}</p>}</aside>}</>;
}
