import { useCallback } from 'react';
import { Link } from 'react-router-dom';
import { FileText, CalendarDays } from 'lucide-react';
import { journeyApi, type Appointment } from '../journey-api';
import { useResource } from '../hooks/useResource';
import { useLocale } from '../hooks/useLocale';
import { Button, InlineNotice, Skeleton } from './ui';
import { date } from './Domain';

/** C01: only recipient-authorized, explicitly published records. No clinical text
 * is copied into previews, URLs, browser storage or notifications. */
export function PatientCareLinks({ appointments }: { appointments: Appointment[] | null }) {
  const { w } = useLocale();
  const encounterIds = JSON.stringify((appointments || []).filter(item => item.state === 'Completed')
    .sort((a, b) => b.end.localeCompare(a.end)).slice(0, 5).map(item => item.id));
  const load = useCallback(async () => {
    const records = await Promise.all((JSON.parse(encounterIds) as string[]).map(id => journeyApi.appointmentDetail(id)));
    return records.flatMap(record => {
      const summary = record.patient_summary_revisions?.at(-1);
      const followup = record.individual_followup_revisions?.at(-1);
      return [summary && { id: record.id, kind: 'summary', published: summary.published_at },
        followup && { id: record.id, kind: 'followup', published: followup.published_at }].filter(Boolean) as { id: string; kind: string; published: string }[];
    }).slice(0, 3);
  }, [encounterIds]);
  const records = useResource(load);
  return <section className="patient-dashboard-panel patient-care-links"><h2>{w('Your care record')}</h2>
    {records.error ? <InlineNotice tone="danger">{w('Your care records could not be loaded.')} <Button variant="quiet" onClick={() => void records.refresh()}>{w('Try again')}</Button></InlineNotice> : !appointments || !records.data ? <Skeleton/> : records.data.length ? records.data.map(record => <Link className="patient-care-link" key={record.id + record.kind} to={'/patient/appointments/' + encodeURIComponent(record.id)}>
      <span className="care-record-icon" aria-hidden="true">{record.kind === 'summary' ? <FileText size={20}/> : <CalendarDays size={20}/>}</span><span><strong>{w(record.kind === 'summary' ? 'Session summary' : 'Follow-up')}</strong><small>{date(record.published)}</small></span>
    </Link>) : <><p>{w('Your shared summaries will appear here after a consultation.')}</p><Link className="text-link" to="/patient/appointments">{w('View appointments')}</Link></>}
  </section>;
}
