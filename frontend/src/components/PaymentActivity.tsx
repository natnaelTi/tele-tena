import {useState} from 'react';
import {Button} from './ui';
import {Link} from 'react-router-dom';
import {Wallet,ArrowRight} from 'lucide-react';
import {date,money} from './Domain';
import {useLocale} from '../hooks/useLocale';
import './PaymentActivity.css';
/** Persisted activity; a stored demo event never implies a bank transfer. */
export default function PaymentActivity({items}:{items:{activity_id?:string;kind:string;amount:number;created:string}[]}) {
  const {w}=useLocale();
  const [page,setPage]=useState(0);
  const pageCount=Math.max(1,Math.ceil(items.length/5));
  const current=Math.min(page,pageCount-1);
  return <><ul className="payment-activity-list">{items.slice(current*5,current*5+5).map((item,index)=>{
    const content=<><span className="payment-activity-icon" aria-hidden="true"><Wallet size={20}/></span><span className="payment-activity-description"><strong>{w(item.kind)}</strong><span>{date(item.created)}</span></span><span className="payment-activity-amount">ETB {money(item.amount)}</span>{item.activity_id&&<ArrowRight size={18} aria-hidden="true"/>}</>;
    return <li key={item.activity_id||index}>{item.activity_id?<Link to={'/patient/payments/transactions/'+encodeURIComponent(item.activity_id)} aria-label={`${w('Transaction details')}: ${w(item.kind)}, ETB ${money(item.amount)}`}>{content}</Link>:<div>{content}</div>}</li>;
  })}</ul>{pageCount>1&&<nav className="payment-activity-pagination" aria-label={w("Payment activity pages")}><Button variant="quiet" disabled={current===0} onClick={()=>setPage(current-1)} aria-label={w("Previous activity page")}>{w("Back")}</Button><span>{current+1} / {pageCount}</span><Button variant="quiet" disabled={current===pageCount-1} onClick={()=>setPage(current+1)} aria-label={w("Next activity page")}>{w("Next")}</Button></nav>}</>;
}
