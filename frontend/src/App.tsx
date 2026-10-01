import Consultation from './features/consultations/Consultation'
import { useEffect, useEffectEvent, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, phoneAuth, setCsrf, signIn } from './api'
import { journeyApi } from './journey-api'
import type { Application, Appointment, Disclosure, Offer, Service, Session, Window as AvailabilityWindow } from './journey-api'
import { locales } from './i18n'
import type { Key } from './i18n'
import { Button, Card, EmptyState, Field, JourneyNav, Panel, StatusPill, TimezoneNote } from './design-system'
import './App.css'

const money = (minor: number) => `${Math.floor(minor / 100)}.${String(minor % 100).padStart(2, '0')}`
const errorKeys: Record<string, Key> = { outside_join_window: 'callOutsideWindow', consultation_ended: 'callEnded', appointment_inactive: 'callUnavailable', invalid_availability_window: 'invalidAvailabilityWindow', availability_overlap: 'availabilityOverlap', service_scope_required: 'serviceScopeRequired', outside_availability: 'outsideAvailability', appointment_conflict: 'appointmentConflict', insufficient_funds: 'insufficientFunds', approval_required: 'approvalRequired', preview_changed: 'previewChanged', offering_changed: 'offeringChanged', future_required: 'futureRequired', retry_changed: 'retryChanged', concurrent_update: 'concurrentUpdate', invalid_phone: 'invalidPhone', otp_invalid: 'otpInvalid', adult_required: 'adultRequired' }
const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
const date = (utc: string) => new Date(utc).toLocaleString()

export default function App() {
  const [locale, setLocale] = useState<keyof typeof locales>('en')
  const t = (key: Key) => locales[locale][key]
  const [session, setSession] = useState<Session | null>(null)
  const [working, setWorking] = useState(false)
  const [message, setMessage] = useState<Key | ''>('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [adult, setAdult] = useState(false)
  const [history, setHistory] = useState('')
  const [defaultShareName, setDefaultShareName] = useState(false)
  const [defaultShareHistory, setDefaultShareHistory] = useState(false)
  const [scopes, setScopes] = useState<{ clinician: string; service: string; status: string }[]>([])
  const [scopeService, setScopeService] = useState('')
  const [shareName, setShareName] = useState(false)
  const [shareHistory, setShareHistory] = useState(false)
  const [statement, setStatement] = useState('')
  const [services, setServices] = useState<Service[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [offers, setOffers] = useState<Offer[]>([])
  const [balance, setBalance] = useState({ available: 0, reserved: 0 })
  const [serviceId, setServiceId] = useState('general-consultation')
  const [serviceLabel, setServiceLabel] = useState('Synthetic general consultation')
  const [service, setService] = useState('')
  const [filter, setFilter] = useState('')
  const [price, setPrice] = useState('5000')
  const [minutes, setMinutes] = useState('30')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [offer, setOffer] = useState<Offer | null>(null)
  const [windows, setWindows] = useState<{ windows: AvailabilityWindow[]; busy: AvailabilityWindow[] }>({ windows: [], busy: [] })
  const [loadFailed, setLoadFailed] = useState(false)
  const [request, setRequest] = useState('')
  const [preview, setPreview] = useState<Disclosure | null>(null)
  const [retryKey, setRetryKey] = useState(crypto.randomUUID())
  const [depositKey, setDepositKey] = useState(crypto.randomUUID())
  const [activeTab, setActiveTab] = useState('login')
  const patient = session?.roles.includes('Tele Tena Patient')
  const clinician = session?.roles.includes('Tele Tena Clinician')
  const approver = session?.roles.includes('Tele Tena Approver')
  const applicant = !clinician && session?.profile?.kind === 'clinician'
  const kind = session?.profile?.kind || (patient ? 'patient' : 'clinician')
  const navItems = approver
    ? [{ id: 'approvals', label: t('navApprovals') }, { id: 'catalog', label: t('navCatalog') }]
    : patient
      ? [{ id: 'profile', label: t('navProfile') }, { id: 'care', label: t('navCare') }, { id: 'appointments', label: t('navAppointments') }]
      : clinician
        ? [{ id: 'profile', label: t('navProfile') }, { id: 'practice', label: t('navPractice') }, { id: 'appointments', label: t('navAppointments') }]
        : applicant ? [{ id: 'application', label: t('application') }] : []
  const workspace = approver ? t('workspaceAdmin') : patient ? t('workspacePatient') : clinician ? t('workspaceClinician') : t('workspaceApplicant')

  function clearPrivateState() {
    setSession(null); setCsrf(''); setName(''); setAdult(false); setHistory(''); setStatement('')
    setApplications([]); setAppointments([]); setOffers([]); setOffer(null); setRequest(''); setPreview(null)
    setBalance({ available: 0, reserved: 0 }); setWindows({ windows: [], busy: [] })
    setShareName(false); setShareHistory(false); setDefaultShareName(false); setDefaultShareHistory(false); setScopes([])
  }
  async function refresh(loadProfile = false, resetSharing = false, resetTab = false) {
    const current = await journeyApi.session()
    setCsrf(current.csrf_token); setSession(current)
    if (resetTab) setActiveTab(current.roles.includes('Tele Tena Approver') ? 'approvals' : current.roles.includes('Tele Tena Patient') ? 'profile' : current.roles.includes('Tele Tena Clinician') ? 'profile' : current.profile?.kind === 'clinician' ? 'application' : 'profile')
    if (loadProfile && current.profile) {
      setPreview(null); setRetryKey(crypto.randomUUID())
      setName(current.profile.display_name); setHistory(current.profile.history); setAdult(true)
      setDefaultShareName(Boolean(current.profile.share_name)); setDefaultShareHistory(Boolean(current.profile.share_history))
      if (resetSharing) { setShareName(Boolean(current.profile.share_name)); setShareHistory(Boolean(current.profile.share_history)) }
    }
    setServices(await journeyApi.services())
    if (current.roles.includes('Tele Tena Patient')) {
      setOffers(await journeyApi.discover(filter))
      if (current.profile) setBalance(await journeyApi.wallet())
    }
    if (current.roles.includes('Tele Tena Approver') || current.profile?.kind === 'clinician') {
      setApplications(await journeyApi.applications())
    }
    if (current.roles.includes('Tele Tena Approver')) setScopes(await journeyApi.serviceScopes())
    if (current.profile) setAppointments(await journeyApi.appointments())
    setLoadFailed(false)
  }
  const hydrate = useEffectEvent(async () => { try { await refresh(true, true, true) } catch { clearPrivateState(); setLoadFailed(true) } })
  useEffect(() => { void Promise.resolve().then(() => hydrate()) }, [])
  function retryHydrate() { void refresh(true, true, true).catch(() => { clearPrivateState(); setLoadFailed(true) }) }
  function change(update: () => void) { setPreview(null); setRetryKey(crypto.randomUUID()); update() }
  async function run(action: () => Promise<void>) {
    setWorking(true); setMessage('')
    try { await action(); setMessage('success') } catch (error) { setMessage(error instanceof ApiError ? errorKeys[error.code] || 'failure' : 'failure') }
    finally { setWorking(false) }
  }
  function submit(event: FormEvent, action: () => Promise<void>) { event.preventDefault(); void run(action) }
  const button = (key: Key) => <Button type="submit" disabled={working}>{t(key)}</Button>
  const disclosureView = (value: Disclosure) => <dl>{(['request', 'name', 'history'] as const).map(key => value[key] !== undefined && <div key={key}><dt>{t((key + 'Field') as Key)}</dt><dd>{value[key] || '—'}</dd></div>)}</dl>

  return <main>
    <header><h1>{t('title')}</h1><label className="locale-control">{t('language')} <select aria-label={t('language')} value={locale} onChange={e => setLocale(e.target.value as keyof typeof locales)}><option value="en">English</option><option value="am">አማርኛ</option><option value="om">Afaan Oromo</option></select></label></header>
    <p className="banner">{t('warning')}</p><p className="notice">{t('review')}</p>
    <p className="status-message" data-kind={message && message !== 'success' ? 'error' : undefined} role="status" aria-live="polite" aria-atomic="true">{working ? t('loading') : message ? t(message) : ''}</p>
    {loadFailed && <Panel role="alert"><p>{t('loadingError')}</p><Button onClick={retryHydrate}>{t('refresh')}</Button></Panel>}
    {!session ? <><Panel><h2>{t('login')}</h2><p>{t('credentials')}</p><form onSubmit={e => submit(e, async () => { await signIn(email, password); setPassword(''); await refresh(true, true, true) })}>
      <Field id="login-email" label={t('email')}><input id="login-email" type="email" autoComplete="username" required value={email} onChange={e => setEmail(e.target.value)} /></Field>
      <label>{t('password')}<input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></label>{button('login')}
    </form></Panel><PhoneOnboarding t={t} run={run} authenticated={() => refresh(true, true, true)} /></> : <>
      <div className="top-actions"><span>{t('authenticated')}: {session.user}</span><div className="inline-actions"><button className="secondary" disabled={working} onClick={() => void run(async () => { await journeyApi.logout(); clearPrivateState() })}>{t('logout')}</button><button className="secondary" disabled={working} onClick={() => void run(() => refresh())}>{t('refresh')}</button></div></div>
      <div className="page-heading"><div><h2>{workspace}</h2><p>{approver ? t('navApprovals') : patient ? t('navCare') : clinician ? t('navPractice') : t('application')}</p></div></div>
      <JourneyNav items={navItems} active={activeTab} onChange={setActiveTab} label={t('navLabel')} />
      {(patient || clinician) && activeTab === 'profile' && <section><h2>{t('profile')} · {t(kind)}</h2><form onSubmit={e => submit(e, async () => {
        await journeyApi.saveProfile({ kind, display_name: name, adult, history, share_name: defaultShareName, share_history: defaultShareHistory }); await refresh(true)
      })}>
        <label>{t('name')}<input required maxLength={120} value={name} onChange={e => change(() => setName(e.target.value))} /></label>
        <label className="check"><input type="checkbox" checked={adult} onChange={e => setAdult(e.target.checked)} />{t('adult')}</label>
        {patient && <><label>{t('history')}<textarea maxLength={4000} value={history} onChange={e => change(() => setHistory(e.target.value))} /></label><p>{t('defaults')}</p>
          <label className="check"><input type="checkbox" checked={defaultShareName} onChange={e => setDefaultShareName(e.target.checked)} />{t('shareName')}</label>
          <label className="check"><input type="checkbox" checked={defaultShareHistory} onChange={e => setDefaultShareHistory(e.target.checked)} />{t('shareHistory')}</label></>}{button('save')}
      </form></section>}
      {approver && activeTab === 'catalog' && <>
        <section><h2>{t('catalog')}</h2><form onSubmit={e => submit(e, async () => { await journeyApi.saveService(serviceId, serviceLabel); await refresh() })}>
          <label>{t('serviceId')}<input required pattern="[a-z0-9-]+" value={serviceId} onChange={e => setServiceId(e.target.value)} /></label>
          <label>{t('serviceLabel')}<input required value={serviceLabel} onChange={e => setServiceLabel(e.target.value)} /></label>{button('saveService')}
        </form></section>
      </>}
      {approver && activeTab === 'approvals' && <>
        <section><h2>{t('approvals')}</h2><label>{t('scopeService')}<select aria-label={t('scopeService')} value={scopeService} onChange={e => setScopeService(e.target.value)}><option value="">{t('choose')}</option>{services.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}</select></label>{applications.length === 0 && <p>{t('empty')}</p>}{applications.map(a => <article key={a.user}><h3>{a.user}</h3><p>{a.statement}</p><p>{t('status')}: {t(a.status.toLowerCase() as Key)}</p>
          <button disabled={working} onClick={() => void run(async () => { await journeyApi.reviewApplication(a.user, 'Approved'); await refresh() })}>{t('approve')}</button>{' '}
          <button disabled={working} onClick={() => void run(async () => { await journeyApi.reviewApplication(a.user, 'Rejected'); await refresh() })}>{t('reject')}</button>
          <p>{t('serviceScopes')}: {scopes.filter(scope => scope.clinician === a.user).map(scope => `${scope.service}: ${scope.status === 'Approved' ? t('approved') : t('scopeRevoked')}`).join(', ') || t('empty')}</p>
          <button disabled={working || !scopeService} onClick={() => void run(async () => { await journeyApi.reviewServiceScope(a.user, scopeService, 'Approved'); await refresh() })}>{t('approveScope')}</button>{' '}
          <button disabled={working || !scopeService} onClick={() => void run(async () => { await journeyApi.reviewServiceScope(a.user, scopeService, 'Revoked'); await refresh() })}>{t('revokeScope')}</button>
        </article>)}</section>
      </>}
      {clinician && session.profile && activeTab === 'practice' && <>
        <section><h2>{t('application')}</h2>{applications.map(a => <p key={a.user}>{t('status')}: <StatusPill tone={a.status === 'Approved' ? 'neutral' : 'warning'}>{t(a.status.toLowerCase() as Key)}</StatusPill></p>)}
          <form onSubmit={e => submit(e, async () => { await journeyApi.apply(statement); await refresh() })}><label>{t('statement')}<textarea required maxLength={2000} value={statement} onChange={e => setStatement(e.target.value)} /></label>{button('apply')}</form>
        </section>
        <section><h2>{t('offering')}</h2><form onSubmit={e => submit(e, async () => { await journeyApi.publish(service, price, minutes); await refresh() })}>
          <label>{t('service')}<select aria-label={t('service')} required value={service} onChange={e => setService(e.target.value)}><option value="">{t('choose')}</option>{services.map(s => <option value={s.id} key={s.id}>{s.label}</option>)}</select></label>
          <label>{t('price')}<input type="number" min="1" max="100000000" step="1" required value={price} onChange={e => setPrice(e.target.value)} /></label>
          <label>{t('minutes')}<input type="number" min="5" max="240" step="1" required value={minutes} onChange={e => setMinutes(e.target.value)} /></label>{button('publish')}
        </form></section>
        <section><h2>{t('availability')}</h2><form onSubmit={e => submit(e, async () => { await journeyApi.addAvailability(new Date(start).toISOString(), new Date(end).toISOString()); await refresh() })}>
          <TimezoneNote label={t('timezoneLabel')} timezone={timezone} />
          <label>{t('start')}<input required type="datetime-local" value={start} onChange={e => change(() => setStart(e.target.value))} /></label>
          <label>{t('end')}<input required type="datetime-local" value={end} onChange={e => setEnd(e.target.value)} /></label>{button('addWindow')}
        </form></section>
      </>}
      {applicant && session.profile && activeTab === 'application' && <section><h2>{t('application')}</h2>{applications.map(a => <p key={a.user}>{t('status')}: <StatusPill tone={a.status === 'Rejected' ? 'danger' : 'warning'}>{t(a.status.toLowerCase() as Key)}</StatusPill></p>)}<p>{t('clinicianActivationPending')}</p></section>}
      {patient && session.profile && activeTab === 'care' && <>
        <section><h2>{t('wallet')}</h2><p className="simulation-label">{t('simulationLabel')}</p><p>{t('available')}: ETB {money(balance.available)} · {t('reserved')}: ETB {money(balance.reserved)}</p>
          {session.simulation && <button disabled={working} onClick={() => void run(async () => { await journeyApi.simulatedDeposit(depositKey); setDepositKey(crypto.randomUUID()); await refresh() })}>{t('deposit')}</button>}
        </section>
        <section><h2>{t('discovery')}</h2><label>{t('service')}<select aria-label={t('service')} value={filter} onChange={e => { const next = e.target.value; setFilter(next); setOffer(null); void run(async () => { setOffers(await journeyApi.discover(next)) }) }}><option value="">{t('all')}</option>{services.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}</select></label>
          {offers.length === 0 && <EmptyState>{t('noOffer')}</EmptyState>}{offers.map(o => <Card key={o.id}><h3>{o.display_name} · {o.label}</h3><p>ETB {money(o.price)} · {o.minutes} {t('duration')}</p><Button disabled={working} onClick={() => void run(async () => { change(() => { setOffer(o); setShareName(Boolean(session.profile?.share_name)); setShareHistory(Boolean(session.profile?.share_history)) }); setWindows(await journeyApi.windows(o.id)) })}>{t('choose')}</Button></Card>)}
        </section>
        {offer && <section><h2>{offer.display_name} · {offer.label}</h2><p>ETB {money(offer.price)} · {offer.minutes} {t('duration')}</p><p>{t('timezone')}: {timezone}</p><h3>{t('windows')}</h3>{windows.windows.map(w => <p key={w.start}>{date(w.start)} – {date(w.end)}</p>)}<h3>{t('busy')}</h3>{windows.busy.map(w => <p key={w.start}>{date(w.start)} – {date(w.end)}</p>)}
          <TimezoneNote label={t('timezoneLabel')} timezone={timezone} /><label>{t('start')}<input type="datetime-local" required value={start} onChange={e => change(() => setStart(e.target.value))} /></label>
          <label>{t('request')}<textarea required maxLength={2000} value={request} onChange={e => change(() => setRequest(e.target.value))} /></label><h3>{t('sharing')}</h3>
          <label className="check"><input type="checkbox" checked={shareName} onChange={e => change(() => setShareName(e.target.checked))} />{t('shareName')}</label>
          <label className="check"><input type="checkbox" checked={shareHistory} onChange={e => change(() => setShareHistory(e.target.checked))} />{t('shareHistory')}</label>
          <p>{t('previewNote')}</p><button disabled={working || !request || !start} onClick={() => void run(async () => { const result = await journeyApi.preview(request, { name: shareName, history: shareHistory }); setPreview(result.disclosure) })}>{t('preview')}</button>
          {preview && <><h3>{t('previewTitle')}</h3>{disclosureView(preview)}<button disabled={working} onClick={() => void run(async () => {
            await journeyApi.book({ offering: offer.id, start: new Date(start).toISOString(), request_text: request, sharing: { name: shareName, history: shareHistory }, retry_key: retryKey,
              expected_price: offer.price, expected_minutes: offer.minutes, expected_disclosure: preview })
            await refresh(); setWindows(await journeyApi.windows(offer.id))
          })}>{t('book')}</button></>}
        </section>}
      </>}
      {(patient || clinician) && !session.profile && activeTab === 'profile' && <p className="empty-state">{t('noProfile')}</p>}
      {session.profile && activeTab === 'appointments' && <section><h2>{t('appointments')}</h2><TimezoneNote label={t('timezoneLabel')} timezone={timezone} />{appointments.length === 0 && <EmptyState>{t('empty')}</EmptyState>}{appointments.map(a => <Card key={a.id} data-appointment-id={a.id}><h3>{a.service_label} · {t('booked')}</h3><p>{date(a.start)} – {date(a.end)} · ETB {money(a.price)} · {a.minutes} {t('duration')}</p>{disclosureView(a.disclosure)}<Consultation appointment={a} t={t} /></Card>)}</section>}
    </>}
  </main>
}

function PhoneOnboarding({ t, run, authenticated }: {
  t: (key: Key) => string
  run: (action: () => Promise<void>) => Promise<void>
  authenticated: () => Promise<void>
}) {
  const [purpose, setPurpose] = useState<'patient_signup' | 'clinician_application' | 'login'>('patient_signup')
  const [phone, setPhone] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [adult, setAdult] = useState(false)
  const [statement, setStatement] = useState('')
  const [code, setCode] = useState('')
  const [challenge, setChallenge] = useState('')
  const [requested, setRequested] = useState(false)
  const [requestId, setRequestId] = useState(() => crypto.randomUUID())
  const [csrf, setCsrf] = useState('')
  const signup = purpose !== 'login'

  async function requestCode(event: FormEvent) {
    event.preventDefault()
    await run(async () => {
      const token = csrf || (await phoneAuth<{ csrf_token: string }>('csrf_token', {})).csrf_token
      setCsrf(token)
      const result = await phoneAuth<{ requested: boolean; challenge_id: string }>('request_code',
        { phone, purpose, request_id: requestId }, token)
      setChallenge(result.challenge_id)
      setRequested(true)
    })
  }

  async function verifyCode(event: FormEvent) {
    event.preventDefault()
    await run(async () => {
      await phoneAuth('verify_code', { phone, purpose, challenge_id: challenge, code,
        display_name: displayName, adult: adult ? 1 : 0, statement }, csrf)
      setCode('')
      await authenticated()
    })
  }

  return <section aria-label={t('phoneAccess')}>
    <h2>{t('phoneAccess')}</h2><p>{t('phoneNotice')}</p>
    <form onSubmit={requestCode}>
      <label>{t('phonePurpose')}<select value={purpose} onChange={event => {
        setPurpose(event.target.value as typeof purpose); setChallenge(''); setRequested(false); setCode(''); setRequestId(crypto.randomUUID())
      }}>
        <option value="patient_signup">{t('patientSignup')}</option>
        <option value="clinician_application">{t('clinicianApplication')}</option>
        <option value="login">{t('phoneLogin')}</option>
      </select></label>
      <label>{t('phone')}<input type="tel" inputMode="tel" autoComplete="tel" required value={phone}
        onChange={event => { setPhone(event.target.value); setChallenge(''); setRequested(false); setCode(''); setRequestId(crypto.randomUUID()) }} /></label>
      {signup && <>
        <label>{t('name')}<input required maxLength={120} value={displayName} onChange={event => setDisplayName(event.target.value)} /></label>
        <label className="check"><input type="checkbox" checked={adult} onChange={event => setAdult(event.target.checked)} />{t('adult')}</label>
      </>}
      {purpose === 'clinician_application' && <label>{t('statement')}<textarea required maxLength={2000} value={statement} onChange={event => setStatement(event.target.value)} /></label>}
      <button type="submit">{t('requestCode')}</button>
    </form>
    {requested && <form onSubmit={verifyCode}>
      <p>{t('codeRequested')}</p>
      <label>{t('verificationCode')}<input type="text" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={code} onChange={event => setCode(event.target.value)} /></label>
      <button type="submit" disabled={!challenge}>{t('verifyCode')}</button>
      <button type="button" onClick={() => { setChallenge(''); setRequested(false); setCode(''); setRequestId(crypto.randomUUID()) }}>{t('requestAnotherCode')}</button>
    </form>}
  </section>
}
