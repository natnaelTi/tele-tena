import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Copy, HeartHandshake, Link2, ShieldCheck, UserRound } from 'lucide-react';
import { journeyApi } from '../journey-api';
import { api } from '../api';
import { Button, Card, Checkbox, EmptyState, InlineNotice, Skeleton, TextField } from '../components/ui';
import { PageTitle } from '../components/Domain';
import { useAction } from '../hooks/useAction';
import { useLocale } from '../hooks/useLocale';
import { useSession } from '../hooks/useSession';

export function RelationshipInvitationEntry() {
  const location = useLocation();
  const navigate = useNavigate();
  const { session, loading, error: sessionError } = useSession();
  const { w } = useLocale();
  const action = useAction();
  const [token] = useState(() => {
    const supplied = new URLSearchParams(window.location.hash.slice(1)).get('invite') || '';
    const passed = (location.state as {relationshipInvitationToken?:string}|null)?.relationshipInvitationToken || '';
    return supplied || passed;
  });
  const [inviter, setInviter] = useState<{inviter_name:string;expires_at:string;notice:string}|null>(null);
  const [adult, setAdult] = useState(false);
  const [decision, setDecision] = useState<'accepted'|'declined'|''>('');
  const [registrationEnabled, setRegistrationEnabled] = useState(false);
  const consumedFragment = useRef(false);

  useEffect(() => {
    if (consumedFragment.current) return;
    consumedFragment.current = true;
    const passed = (location.state as {relationshipInvitationToken?:string}|null)?.relationshipInvitationToken || '';
    if (passed) navigate(location.pathname + location.search, {replace:true,state:null});
  }, [location.pathname, location.search, location.state, navigate]);

  useEffect(() => {
    let active = true;
    void api<{patient_registration:boolean;phone_otp:boolean;email_otp:boolean}>(
      'tele_tena.api.contact_auth.sign_in_options',
    ).then(options => {
      if (active) setRegistrationEnabled(Boolean(options.patient_registration && (options.phone_otp || options.email_otp)));
    }).catch(() => {
      // Fail closed in the copy: existing patients can still sign in, but we
      // must not promise public account creation when site policy is unknown.
      if (active) setRegistrationEnabled(false);
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!token || loading || !session?.profile || session.profile.kind !== 'patient') return;
    let active = true;
    void journeyApi.previewRelationshipInvitation(token)
      .then(value => { if (active) setInviter(value); })
      .catch(() => { if (active) setInviter(null); });
    return () => { active = false; };
  }, [token, loading, session?.profile]);

  useEffect(() => {
    // Keep an unauthenticated fragment available for an explicit return from
    // sign-in/onboarding. Once a patient session exists, remove it before any
    // authenticated API call so it does not remain in browser history.
    if (session?.profile?.kind === 'patient' && window.location.hash.includes('invite='))
      window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search);
  }, [session?.profile]);

  const continueToSignIn = () => navigate('/sign-in?intent=patient&next=%2Frelationship-invitation', {
    state: {relationshipInvitationToken:token},
  });

  if (loading) return <main className="container"><Skeleton/></main>;
  return <main className="container relationship-entry">
    <Card className="relationship-card">
      <HeartHandshake size={28} aria-hidden="true"/>
      <h1>{w('A private adult relationship link')}</h1>
      {sessionError && <InlineNotice tone="danger">{w('We could not check your sign-in. Try again.')}</InlineNotice>}
      {!token && <InlineNotice tone="danger">{w('This invitation link is missing or invalid. Ask for a new link.')}</InlineNotice>}
      {token && !session && <>
        <p>{w(registrationEnabled
          ? 'Sign in or create an adult patient account, then continue to review this invitation. The link does not share health records.'
          : 'Sign in with your patient account to review this invitation. The link does not share health records.')}</p>
        <Button onClick={continueToSignIn}>{w(registrationEnabled
          ? 'Sign in or create a patient account'
          : 'Sign in to review invitation')}</Button>
      </>}
      {token && session && session.profile?.kind !== 'patient' && <InlineNotice tone="danger">{w('This invitation is for patient accounts. Sign in with a patient account to continue.')}</InlineNotice>}
      {token && session?.profile?.kind === 'patient' && !inviter && <>
        <p role="status">{w('Checking this invitation…')}</p>
        <InlineNotice tone="info">{w('If the invitation is expired or already used, ask for a new link.')}</InlineNotice>
      </>}
      {inviter && !decision && <>
        <p>{w('You received an invitation from')} <strong>{inviter.inviter_name}</strong>.</p>
        <p>{w('Accepting links your patient accounts for future shared-care features. It does not share appointments, history, notes, balances, or calls.')}</p>
        <Checkbox label={w('I confirm that I am 18 or older and choose to create this relationship link.')} checked={adult} onChange={event=>setAdult(event.target.checked)}/>
        <div className="actions">
          <Button disabled={!adult||action.busy} loading={action.busy} onClick={()=>void action.run(async()=>{
            await journeyApi.respondToRelationshipInvitation(token,'accept',adult);
            setDecision('accepted');
          },w('Relationship link accepted.'))}>{w('Accept invitation')}</Button>
          <Button variant="secondary" disabled={action.busy} onClick={()=>void action.run(async()=>{
            await journeyApi.respondToRelationshipInvitation(token,'decline',false);
            setDecision('declined');
          })}>{w('Decline invitation')}</Button>
        </div>
      </>}
      {decision && <InlineNotice tone={decision==='accepted'?'success':'info'}>{decision==='accepted'?w('You are now linked. No appointments or records were shared.'):w('Invitation declined.')}</InlineNotice>}
      {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
      <Link className="text-link" to="/patient">{w('Return to your workspace')}</Link>
    </Card>
  </main>;
}

export default function Relationships() {
  const { w } = useLocale();
  const { session } = useSession();
  const patient = session?.profile?.kind === 'patient';
  const load = useCallback(()=>journeyApi.myRelationships(),[]);
  const [data,setData] = useState<any|null>(null);
  const [loadError,setLoadError] = useState(false);
  const [adult,setAdult] = useState(false);
  const [inviteUrl,setInviteUrl] = useState('');
  const [copyStatus,setCopyStatus] = useState('');
  const retryKey = useRef(crypto.randomUUID());
  const action = useAction();
  const refresh = useCallback(async()=>{
    try { setLoadError(false); setData(await load()); }
    catch { setLoadError(true); }
  },[load]);
  useEffect(()=>{ if(patient) void refresh(); },[patient,refresh]);
  if (!patient) return <InlineNotice tone="danger">{w('This page is for patient accounts.')}</InlineNotice>;
  return <>
    <PageTitle title={w('Shared care')} description={w('Create an optional adult relationship link. It does not share clinical records or appointments.')}/>
    {action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
    <div className="relationship-workspace">
      <Card className="relationship-create">
        <div className="relationship-heading"><Link2 size={22}/><h2>{w('Invite an adult you trust')}</h2></div>
        <p>{w('Create a private link and share it directly with the intended person. Anyone who receives the link can try to accept it, so share it carefully.')}</p>
        <Checkbox label={w('I confirm that I am 18 or older and agree to create this link.')} checked={adult} onChange={event=>setAdult(event.target.checked)}/>
        <Button disabled={!adult||action.busy} loading={action.busy} onClick={()=>void action.run(async()=>{
          const result=await journeyApi.createRelationshipInvitation(retryKey.current);
          const base=window.location.origin+(import.meta.env.PROD?'/teletena':'');
          setInviteUrl(`${base}/relationship-invitation#invite=${encodeURIComponent(result.token)}`);
          retryKey.current=crypto.randomUUID();
          await refresh();
        },w('Invitation link created.'))}><HeartHandshake size={18}/>{w('Create invitation link')}</Button>
        {inviteUrl&&<div className="relationship-link-field"><TextField label={w('Private invitation link')} value={inviteUrl} readOnly/><Button variant="secondary" onClick={()=>void navigator.clipboard.writeText(inviteUrl).then(()=>setCopyStatus(w('Invitation link copied.'))).catch(()=>setCopyStatus(w('Copy the link from the field.')))}><Copy size={18}/>{w('Copy link')}</Button><p role="status" className="supporting">{copyStatus||w('This link expires after the time shown in your invitation list.')}</p></div>}
        <div className="relationship-boundary"><ShieldCheck size={18}/><p>{w('A relationship link shares no appointments, health history, notes, balances, or call access. Each person must agree separately. Couple and family appointments are not available yet.')}</p></div>
        {action.error&&<InlineNotice tone="danger">{w('The invitation could not be created. Check your connection, consent, and active invitation limit.')}</InlineNotice>}
      </Card>
      <section className="relationship-list" aria-labelledby="relationship-list-heading">
        <h2 id="relationship-list-heading">{w('Your relationship links')}</h2>
        {loadError&&<InlineNotice tone="danger">{w('Relationships could not be loaded.')} <Button variant="secondary" onClick={()=>void refresh()}>{w('Try again')}</Button></InlineNotice>}
        {!data&&!loadError&&<Skeleton/>}
        {data&&!data.relationships.length&&<EmptyState title={w('No relationship links yet.')}>{w('A link is created only after both adults accept.')}</EmptyState>}
        {data?.relationships.map((item:any)=><Card className="relationship-row" key={item.id}>
          <UserRound size={20}/><div><strong>{item.other_name}</strong><p className="supporting">{w(item.state)} · {w('No records are shared')}</p></div>
          {item.state==='Active'&&<Button variant="danger" disabled={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.revokeRelationship(item.id);await refresh();},w('Relationship link revoked.'))}>{w('Revoke link')}</Button>}
        </Card>)}
        {data?.invitations.length>0&&<details className="relationship-invitations"><summary>{w('Invitation history')} ({data.invitations.length})</summary>{data.invitations.map((item:any)=><div className="relationship-row" key={item.id}><div><strong>{w(item.state)}</strong><p className="supporting">{w('Expires')} {new Date(item.expires_at).toLocaleString()}</p></div>{item.state==='Pending'&&<Button variant="quiet" onClick={()=>void action.run(async()=>{await journeyApi.revokeRelationshipInvitation(item.id);await refresh();})}>{w('Withdraw invitation')}</Button>}</div>)}</details>}
      </section>
    </div>
  </>;
}
