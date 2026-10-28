import {useEffect,useRef,useState} from 'react';
import {Link,useLocation} from 'react-router-dom';
import {Bell} from 'lucide-react';
import {useNotifications} from '../hooks/useNotifications';
import type {Notice} from '../hooks/useNotifications';
import {useLocale} from '../hooks/useLocale';
import {UserNotifications} from './UserNotifications';
import {Button} from './ui';
import './ClinicianNotifications.css';
export function ClinicianNotifications(){
 const{w}=useLocale(),location=useLocation(),feed=useNotifications(),[open,setOpen]=useState(false),[failure,setFailure]=useState(false),[popup,setPopup]=useState<Notice|null>(null),announced=useRef(new Set<string>());
 const call=location.pathname.includes('/consultation/')||location.pathname.endsWith('/room');
 useEffect(()=>{if(call||popup)return;const next=feed.items?.find(item=>item.source==='offer'&&!item.read&&!announced.current.has(item.id)&&item.created&&Date.now()-Date.parse(item.created)<15*60*1000);if(next){announced.current.add(next.id);setPopup(next);}},[feed.items,call,popup]);
 useEffect(()=>{if(popup&&feed.items?.find(n=>n.source==='offer'&&n.id===popup.id)?.read)setPopup(null);},[feed.items,popup]);
 const mark=async(item:Notice)=>{try{await feed.mark(item);setPopup(null);setFailure(false);}catch{setFailure(true);}};
 return <><UserNotifications onOpenChange={setOpen}/>{popup&&!call&&!open&&!popup.read&&<aside className="clinician-notification-popup" role="status"><Bell size={22}/><div><strong>{w('Your offer was accepted')}</strong><p>{w(popup.appointment_state==='Booked'?'The appointment is confirmed. Open its details to prepare or join.':popup.payment_mode==='Offline'?'Your offer was selected. Open the appointment for direct-payment verification and acceptance.':'Your offer was selected. Open the appointment to review its current status.')}</p><Link className="text-link" to={popup.href!} onClick={()=>void mark(popup)}>{w('View consultation')}</Link></div><Button variant="quiet" aria-label={w('Dismiss notification')} onClick={()=>void mark(popup)}>×</Button>{failure&&<p>{w('We could not mark this notification as read. Try again.')}</p>}</aside>}</>;
}
