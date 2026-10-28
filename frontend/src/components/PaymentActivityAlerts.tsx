import {useEffect,useRef,useState} from 'react';
import {Link} from 'react-router-dom';
import {Bell} from 'lucide-react';
import {useNotifications} from '../hooks/useNotifications';
import type {Notice} from '../hooks/useNotifications';
import {useSession} from '../hooks/useSession';
import {useLocale} from '../hooks/useLocale';
import {Button} from './ui';
import './PaymentActivityAlerts.css';
const kinds=new Set(['PaymentSubmitted','PaymentVerified','PaymentCorrection','PaymentReconciliation']);
export default function PaymentActivityAlerts(){const{session}=useSession();return session&&(session.roles.includes('Tele Tena Patient')||session.roles.includes('Tele Tena Clinician'))?<PaymentAlertsForUser key={session.user}/>:null;}
function PaymentAlertsForUser(){
 const{w}=useLocale(),feed=useNotifications(),[pending,setPending]=useState<Notice[]>([]),[error,setError]=useState(false),seen=useRef(new Set<string>()),initialized=useRef(false);
 useEffect(()=>{if(!feed.items)return;const fresh=feed.items.filter(item=>kinds.has(item.kind)&&!!item.href&&!item.read&&!seen.current.has(item.source+item.id));for(const item of feed.items)seen.current.add(item.source+item.id);const additions=initialized.current?fresh:fresh.slice(0,1);initialized.current=true;setPending(old=>[...additions,...old.filter(n=>feed.items!.some(i=>i.id===n.id&&i.source===n.source&&!i.read))]);},[feed.items]);
 const current=pending[0];if(!current)return null;
 async function dismiss(){try{await feed.mark(current);setPending(old=>old.filter(n=>n.id!==current.id));setError(false);}catch{setError(true);}}
 return <aside className="payment-activity-alert" role="status" aria-live="polite" aria-atomic="true"><Bell size={22} aria-hidden="true"/><div><strong>{w(current.title)}</strong><p>{w(current.kind==='PaymentSubmitted'?'Payment information has arrived. Open the payment page to check the receipt and record your decision.':current.kind==='PaymentVerified'?'The clinician has recorded receipt verification. Your payment status updates automatically; appointment acceptance may still be required.':'There is an update to your payment. Open its history for the next step.')}</p><Link className="text-link" to={current.href!} onClick={()=>void dismiss()}>{w(current.kind==='PaymentSubmitted'?'Review Payment':'View Payment')}</Link>{error&&<p>{w('This notification could not be marked as read. Try again.')}</p>}</div><Button variant="quiet" aria-label={w('Dismiss Payment Notification')} onClick={()=>void dismiss()}>×</Button></aside>;
}
