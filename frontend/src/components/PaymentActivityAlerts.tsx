import {useEffect,useRef,useState} from 'react';
import {Link} from 'react-router-dom';
import {Bell} from 'lucide-react';
import {api} from '../api';
import {useSession} from '../hooks/useSession';
import {useLocale} from '../hooks/useLocale';
import {Button} from './ui';
import './PaymentActivityAlerts.css';
type Notice={id:string;source:'user'|'booking';kind:string;title:string;href?:string;created:string;read:boolean};
const kinds=new Set(['PaymentSubmitted','PaymentVerified','PaymentCorrection','PaymentReconciliation']);
export default function PaymentActivityAlerts(){const{session}=useSession();return session&&(session.roles.includes('Tele Tena Patient')||session.roles.includes('Tele Tena Clinician'))?<PaymentAlertsForUser key={session.user}/>:null;}
function PaymentAlertsForUser(){
 const{w}=useLocale(),[pending,setPending]=useState<Notice[]>([]),[error,setError]=useState(false),seen=useRef(new Set<string>()),started=useRef(Date.now());
 useEffect(()=>{let active=true,running=false;const load=async()=>{if(running||!navigator.onLine)return;running=true;try{const items=await api<Notice[]>('tele_tena.notifications.feed');if(!active)return;const fresh=items.filter(item=>kinds.has(item.kind)&&!!item.href&&!item.read&&Date.parse(item.created)>=started.current-1000&&!seen.current.has(item.source+item.id));for(const item of fresh)seen.current.add(item.source+item.id);if(fresh.length){setPending(old=>[...old,...fresh.reverse()]);window.dispatchEvent(new Event('teletena:payment-update'));}}catch{/* The durable inbox remains available; avoid a disruptive global connection alert. */}finally{running=false;}};void load();const timer=setInterval(()=>void load(),5000);const focus=()=>void load();window.addEventListener('focus',focus);window.addEventListener('online',focus);return()=>{active=false;clearInterval(timer);window.removeEventListener('focus',focus);window.removeEventListener('online',focus);};},[]);
 const current=pending[0];if(!current)return null;
 async function dismiss(){try{await api('tele_tena.notifications.mark_read',{id:current.id,source:current.source},true);setPending(old=>old.filter(n=>n.id!==current.id));setError(false);}catch{setError(true);}}
 return <aside className="payment-activity-alert" role="status" aria-live="polite" aria-atomic="true"><Bell size={22} aria-hidden="true"/><div><strong>{w(current.title)}</strong><p>{w(current.kind==='PaymentSubmitted'?'Payment information has arrived. Open the payment page to check the receipt and record your decision.':current.kind==='PaymentVerified'?'The clinician has recorded receipt verification. Your payment status updates automatically; appointment acceptance may still be required.':'There is an update to your payment. Open its history for the next step.')}</p><Link className="text-link" to={current.href!} onClick={()=>void dismiss()}>{w(current.kind==='PaymentSubmitted'?'Review Payment':'View Payment')}</Link>{error&&<p>{w('This notification could not be marked as read. Try again.')}</p>}</div><Button variant="quiet" aria-label={w('Dismiss Payment Notification')} onClick={()=>void dismiss()}>×</Button></aside>;
}
