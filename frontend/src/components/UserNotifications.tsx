import {useRef,useState} from 'react';
import {Bell} from 'lucide-react';
import {Link} from 'react-router-dom';
import {useNotifications} from '../hooks/useNotifications';
import type {Notice} from '../hooks/useNotifications';
import {useSession} from '../hooks/useSession';
import {useLocale} from '../hooks/useLocale';
import {Button,Dialog,EmptyState,InlineNotice,Skeleton} from './ui';
import './UserNotifications.css';
export function UserNotifications({onOpenChange}:{onOpenChange?:(open:boolean)=>void}={}){
 const {w}=useLocale(),{session}=useSession();
 const resource=useNotifications();
 const [open,setOpen]=useState(false),[error,setError]=useState(false),[filter,setFilter]=useState('all');
 const trigger=useRef<HTMLButtonElement|null>(null);
 const unread=resource.items?.filter(item=>!item.read).length||0;
 const items=resource.items?.filter(item=>filter==='all'||!item.read)||[];
 const mark=async(item:Notice)=>{try{await resource.mark(item);setError(false);}catch{setError(true);}};
 const base=session?.profile?.kind==='clinician'?'/clinician':session?.profile?.kind==='patient'?'/patient':'/admin';
 return <><Button variant="quiet" className="user-notification-trigger" aria-label={w('Notifications')} title={w('Notifications')} aria-haspopup="dialog" onClick={event=>{trigger.current=event.currentTarget;setOpen(true);onOpenChange?.(true);void resource.refresh();}}><Bell size={21} aria-hidden="true"/>{unread>0&&<span className="notification-count" aria-label={`${unread} ${w('Unread')}`}>{unread}</span>}</Button>
 <Dialog open={open} onOpenChange={value=>{setOpen(value);onOpenChange?.(value);if(!value)requestAnimationFrame(()=>trigger.current?.focus());}} title={w('Notifications')} description={w(base==='/clinician'?'Payments, accepted offers, appointments and updates for your practice.':'Appointments, follow-ups and updates for your account.')} className="user-notification-pane">
 <div className="notification-tabs" role="group" aria-label={w('Notification filter')}>{['all','unread'].map(value=><Button key={value} variant={filter===value?'primary':'quiet'} aria-pressed={filter===value} onClick={()=>setFilter(value)}>{w(value==='all'?'All':'Unread')}</Button>)}</div>
 {resource.partial&&<InlineNotice>{w('Some notifications could not be refreshed. Previously loaded updates are shown.')} <Button onClick={()=>void resource.refresh()}>{w('Retry')}</Button></InlineNotice>}
 {resource.error?<InlineNotice tone="danger">{w('Notifications could not be loaded.')} <Button onClick={()=>void resource.refresh()}>{w('Retry')}</Button></InlineNotice>:!resource.items?<Skeleton/>:items.length?<ul className="user-notification-list">{items.map(item=><li key={item.source+item.id} className={item.read?'is-read':'is-unread'}><div><strong>{w(item.title)}</strong><time dateTime={item.created}>{new Date(item.created).toLocaleString()}</time></div><div className="actions"><Link className="text-link" to={item.href||(item.appointment?base+'/consultations/'+item.appointment:base+'/account')} onClick={()=>{void mark(item);setOpen(false);onOpenChange?.(false);}}>{w(item.href?.includes('/direct-payments/')?(['PaymentSubmitted','PaymentVerificationReminder'].includes(item.kind)?'Review Payment':'View Payment'):item.appointment?'View Details':'View Account')}</Link>{!item.read&&<Button variant="quiet" onClick={()=>void mark(item)}>{w('Mark as read')}</Button>}</div></li>)}</ul>:<EmptyState title={w(filter==='unread'?'You’re All Caught Up':'No Notifications Yet')}/>}

 {error&&<InlineNotice tone="danger">{w('We could not mark this notification as read. Try again.')}</InlineNotice>}
 {session?.profile?.kind==='patient'&&<Link className="text-link" to="/patient/appointments" onClick={()=>setOpen(false)}>{w('Appointment Updates & Delivery Status')}</Link>}
 </Dialog></>;
}
