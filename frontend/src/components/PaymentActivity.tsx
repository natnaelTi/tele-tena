import {Link} from 'react-router-dom';
import {Wallet,ArrowRight} from 'lucide-react';
import {date,money} from './Domain';
import {useLocale} from '../hooks/useLocale';
import './PaymentActivity.css';
/** Persisted activity; a stored demo event never implies a bank transfer. */
export default function PaymentActivity({items}:{items:{activity_id?:string;kind:string;amount:number;created:string}[]}) {
  const {w}=useLocale();
  return <ul className="payment-activity-list">{items.map((item,index)=>{
    const content=<><span className="payment-activity-icon" aria-hidden="true"><Wallet size={20}/></span><span className="payment-activity-description"><strong>{w(item.kind)}</strong><span>{date(item.created)}</span></span><span className="payment-activity-amount">ETB {money(item.amount)}</span>{item.activity_id&&<ArrowRight size={18} aria-hidden="true"/>}</>;
    return <li key={item.activity_id||index}>{item.activity_id?<Link to={'/patient/payments/transactions/'+encodeURIComponent(item.activity_id)} aria-label={`${w('Transaction details')}: ${w(item.kind)}, ETB ${money(item.amount)}`}>{content}</Link>:<div>{content}</div>}</li>;
  })}</ul>;
}
