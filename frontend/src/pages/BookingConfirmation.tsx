import {useCallback} from 'react';
import {Link,useParams} from 'react-router-dom';
import {Check,Clock} from 'lucide-react';
import {journeyApi} from '../journey-api';
import {useResource} from '../hooks/useResource';
import {useLocale} from '../hooks/useLocale';
import {PageTitle,date,money} from '../components/Domain';
import {Button,InlineNotice,Skeleton} from '../components/ui';
import './BookingConfirmation.css';

/** Confirmation is read from the authorized appointment, including on refresh. */
export default function BookingConfirmation(){
  const {id=''}=useParams();
  const {w}=useLocale();
  const detail=useResource(useCallback(()=>journeyApi.appointmentDetail(id),[id]));
  if(detail.error)return <InlineNotice tone="danger">{w('This appointment could not be loaded. Check your access and try again.')} <Button variant="secondary" onClick={()=>void detail.refresh()}>{w('Retry')}</Button></InlineNotice>;
  if(!detail.data)return <Skeleton/>;
  const item=detail.data;
  const pending=item.status==='PendingConfirmation';
  const confirmed=item.status==='Booked';
  if(!confirmed&&!pending)return <><PageTitle title={w('Appointment updated')} description={w('Open the appointment for its current status.')}/><Link className="button primary" to={'/patient/consultations/'+id}>{w('View appointment')}</Link></>;
  const Icon=pending?Clock:Check;
  return <><PageTitle title={w(pending?'Awaiting clinician confirmation':'Your appointment is confirmed')} description={date(item.start,item.timezone)}/>
    <div className="booking-confirmation-layout"><section className="booking-confirmation-main"><span className="booking-confirmation-symbol" aria-hidden="true"><Icon size={28}/></span><h2>{item.clinician}</h2><p>{item.service} · {item.booked_minutes} {w('minutes')} · {w(item.format==='audio'?'Audio':'Video')}</p>
      <dl className="summary-list"><dt>{w('Reserved')}</dt><dd>ETB {money(item.price)}</dd><dt>{w('Shared identity')}</dt><dd>{item.disclosure.name||w('Name not shared')}</dd><dt>{w('Timezone')}</dt><dd>{item.timezone||w('Unavailable')}</dd>{pending&&<><dt>{w('Response deadline')}</dt><dd>{item.expires_at?date(item.expires_at,item.timezone):w('Unavailable')}</dd></>}</dl>
      <Link className="button primary" to={'/patient/consultations/'+id}>{w('View appointment')}</Link>
    </section><aside className="booking-confirmation-next"><h2>{w('What happens next')}</h2><p>{w(pending?'Your time and funds are reserved while the clinician responds. If the request expires or is declined, the reservation is released.':'Your consultation is in Appointments. Open its details for the join window and device check.')}</p><Link className="text-link" to="/patient/appointments">{w('All appointments')}</Link></aside></div>
  </>;
}
