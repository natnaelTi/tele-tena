import { Link, useParams } from 'react-router-dom';
import { api } from '../api';
import { PageTitle, date, money } from '../components/Domain';
import { Card, InlineNotice, Skeleton, StatusBadge } from '../components/ui';
import { useLocale } from '../hooks/useLocale';
import { useSession } from '../hooks/useSession';
import { useResource } from '../hooks/useResource';

type ActivityDetail = {
  activity_id: string;
  kind: string;
  created: string;
  amount_minor: number;
  currency: string;
  state: string;
  source?: string;
  account_changes?: { bucket: string; delta_minor: number }[];
  gross_minor?: number;
  fee_minor?: number;
  net_minor?: number;
  release_at?: string | null;
  cancelled_at?: string | null;
  appointment?: { id: string; start: string; timezone: string; service_label: string; state: string; price: number; minutes: number } | null;
  external_transfer?: false;
};

export default function FinancialActivityDetail() {
  const { activityId = '' } = useParams();
  const { w } = useLocale();
  const { session } = useSession();
  const role = session?.profile?.kind === 'clinician' ? 'clinician' : 'patient';
  const resource = useResource<ActivityDetail>(() => api('tele_tena.api.financial_activity.transaction_detail', { activity_id: activityId }));
  const item = resource.data;
  const errorCode = (resource.errorDetail as { code?: string } | null)?.code;
  const href = role === 'clinician' ? '/clinician/earnings' : '/patient/payments';
  const label = (bucket: string) => ({
    available: w('Available balance'), reserved: w('Reserved for appointments'),
    pending: w('Pending earnings'), earnings_available: w('Available earnings'),
    payout_reserved: w('Payout requested'),
  } as Record<string, string>)[bucket] || w('Balance change');
  return <>
    <p><Link className="text-link" to={href}>← {role === 'clinician' ? w('Back to earnings') : w('Back to payments')}</Link></p>
    <PageTitle title={w('Transaction details')} description={w('A record of how this amount changed your balance.')}/>
    {resource.error ? <InlineNotice tone="danger">
      {errorCode === 'transaction_unavailable' || errorCode === 'permission_denied'
        ? w('Transaction unavailable.')
        : errorCode === 'session_required' ? w('Your sign-in session ended. Sign in again to view this transaction.')
        : w('Could not load this transaction. Check your connection and try again.')}
    </InlineNotice> : !item ? <Skeleton/> : <>
      <Card className="transaction-detail">
        <header><strong>{w(item.kind)}</strong><StatusBadge>{w(item.state)}</StatusBadge></header>
        <p className="supporting">{date(item.created)}</p>
        <h2>ETB {money(item.amount_minor)}</h2>
        {item.gross_minor !== undefined && <dl className="offer-facts">
          <div><dt>{w('Gross')}</dt><dd>ETB {money(item.gross_minor)}</dd></div>
          <div><dt>{w('Fee')}</dt><dd>ETB {money(item.fee_minor || 0)}</dd></div>
          <div><dt>{w('Net')}</dt><dd>ETB {money(item.net_minor || 0)}</dd></div>
          {item.release_at && <div><dt>{w(item.state === 'Released' ? 'Released at' : 'Expected release')}</dt><dd>{date(item.release_at)}</dd></div>}
        </dl>}
        {item.account_changes?.length ? <section><h3>{w('Balance changes')}</h3><ul className="transaction-changes">{item.account_changes.map(change=><li key={change.bucket}><span>{label(change.bucket)}</span><strong>{change.delta_minor > 0 ? '+' : '−'}ETB {money(Math.abs(change.delta_minor))}</strong></li>)}</ul></section> : null}
        {item.appointment && <section><h3>{w('Related appointment')}</h3><p>{item.appointment.service_label} · {date(item.appointment.start)} · {item.appointment.minutes} {w('minutes')}</p><StatusBadge>{w(item.appointment.state)}</StatusBadge><p><Link className="text-link" to={`/${role}/consultations/${item.appointment.id}`}>{w('View appointment')}</Link></p></section>}
        {role === 'clinician' && item.activity_id.startsWith('payout-') && <p className="supporting">{w('No external transfer was made.')}</p>}
        {item.source === 'simulation_log' && <p className="supporting">{w('This is an earlier activity record. Its original history is preserved.')}</p>}
      </Card>
    </>}
  </>;
}
