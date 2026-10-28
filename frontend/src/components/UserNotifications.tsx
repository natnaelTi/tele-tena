import {useCallback,useEffect,useRef,useState} from 'react';
import {Bell} from 'lucide-react';
import {Link} from 'react-router-dom';
import {api} from '../api';
import {useSession} from '../hooks/useSession';
import {useResource} from '../hooks/useResource';
import {useLocale} from '../hooks/useLocale';
import {Button,Dialog,EmptyState,InlineNotice,Skeleton} from './ui';
import './UserNotifications.css';
type Notice={href?:string;id:string;source:'user'|'booking';kind:string;title:string;category:string;appointment:string|null;created:string;read:boolean};
export function UserNotifications(){
 const {w}=useLocale(),{session}=useSession();
 const load=useCallback(()=>api<Notice[]>('tele_tena.notifications.feed'),[]),resource=useResource(load);
 const [open,setOpen]=useState(false),[error,setError]=useState(false),[filter,setFilter]=useState('all');
 const trigger=useRef<HTMLButtonElement|null>(null);
 useEffect(()=>{const timer=window.setInterval(()=>{if(navigator.onLine)void resource.refresh();},15000);return()=>window.clearInterval(timer);},[resource.refresh]);
 const unread=resource.data?.filter(item=>!item.read).length||0;
 const items=resource.data?.filter(item=>filter==='all'||!item.read)||[];
 const mark=async(item:Notice)=>{try{await api('tele_tena.notifications.mark_read',{id:item.id,source:item.source},true);await resource.refresh();setError(false);}catch{setError(true);}};
 const base=session?.profile?.kind==='clinician'?'/clinician':session?.profile?.kind==='patient'?'/patient':'/admin';
 return <><Button variant="quiet" className="user-notification-trigger" aria-label={w('Notifications')} title={w('Notifications')} aria-haspopup="dialog" onClick={event=>{trigger.current=event.currentTarget;setOpen(true);void resource.refresh();}}><Bell size={21} aria-hidden="true"/>{unread>0&&<span className="notification-count" aria-label={`${unread} ${w('Unread')}`}>{unread}</span>}</Button>
 <Dialog open={open} onOpenChange={value=>{setOpen(value);if(!value)requestAnimationFrame(()=>trigger.current?.focus());}} title={w('Notifications')} description={w('Appointments, follow-ups and updates for your account.')} className="user-notification-pane">
 <div className="notification-tabs" role="group" aria-label={w('Notification filter')}>{['all','unread'].map(value=><Button key={value} variant={filter===value?'primary':'quiet'} aria-pressed={filter===value} onClick={()=>setFilter(value)}>{w(value==='all'?'All':'Unread')}</Button>)}</div>
 {resource.error?<InlineNotice tone="danger">{w('Notifications could not be loaded.')} <Button onClick={()=>void resource.refresh()}>{w('Retry')}</Button></InlineNotice>:!resource.data?<Skeleton/>:items.length?<ul className="user-notification-list">{items.map(item=><li key={item.source+item.id} className={item.read?'is-read':'is-unread'}><div><strong>{w(item.title)}</strong><time dateTime={item.created}>{new Date(item.created).toLocaleString()}</time></div><div className="actions"><Link className="text-link" to={item.href||(item.appointment?base+'/consultations/'+item.appointment:base+'/account')} onClick={()=>{void mark(item);setOpen(false);}}>{w(item.href?.includes('/direct-payments/')?(['PaymentSubmitted','PaymentVerificationReminder'].includes(item.kind)?'Review Payment':'View Payment'):item.appointment?'View Details':'View Account')}</Link>{!item.read&&<Button variant="quiet" onClick={()=>void mark(item)}>{w('Mark as read')}</Button>}</div></li>)}</ul>:<EmptyState title={w(filter==='unread'?'You’re All Caught Up':'No Notifications Yet')}/>}
 {error&&<InlineNotice tone="danger">{w('We could not mark this notification as read. Try again.')}</InlineNotice>}
 {session?.profile?.kind==='patient'&&<Link className="text-link" to="/patient/appointments" onClick={()=>setOpen(false)}>{w('Appointment Updates & Delivery Status')}</Link>}
 </Dialog></>;
}
