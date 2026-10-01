import { useCallback, useEffect, useEffectEvent, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { Room as LiveKitRoom } from 'livekit-client'
import { ApiError, api, setCsrf, signIn } from './api'
import { locales } from './i18n'
import type { Key } from './i18n'
import './App.css'

type Profile = { kind: 'patient' | 'clinician'; display_name: string; history: string; share_name: boolean; share_history: boolean }
type Session = { user: string; roles: string[]; profile: Profile | null; csrf_token: string; simulation: boolean }
type Service = { id: string; label: string }
type Offer = { id: string; display_name: string; label: string; price: number; minutes: number }
type Application = { user: string; statement: string; status: 'Pending' | 'Approved' | 'Rejected' }
type Disclosure = { request: string; name?: string; history?: string }
type Appointment = { id: string; start: string; end: string; state: string; price: number; minutes: number; service_label: string; disclosure: Disclosure }
type Window = { start: string; end: string }
const money = (minor: number) => `${Math.floor(minor / 100)}.${String(minor % 100).padStart(2, '0')}`
const errorKeys: Record<string, Key> = { service_scope_required: 'serviceScopeRequired', outside_availability: 'outsideAvailability', appointment_conflict: 'appointmentConflict', insufficient_funds: 'insufficientFunds', approval_required: 'approvalRequired', preview_changed: 'previewChanged', offering_changed: 'offeringChanged', future_required: 'futureRequired', retry_changed: 'retryChanged', concurrent_update: 'concurrentUpdate', outside_join_window: 'callOutsideWindow', consultation_ended: 'callEnded', appointment_inactive: 'callUnavailable', invalid_availability_window: 'invalidAvailabilityWindow', availability_overlap: 'availabilityOverlap' }
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
  const [windows, setWindows] = useState<{ windows: Window[]; busy: Window[] }>({ windows: [], busy: [] })
  const [request, setRequest] = useState('')
  const [preview, setPreview] = useState<Disclosure | null>(null)
  const [retryKey, setRetryKey] = useState(crypto.randomUUID())
  const [depositKey, setDepositKey] = useState(crypto.randomUUID())
  const patient = session?.roles.includes('Tele Tena Patient')
  const clinician = session?.roles.includes('Tele Tena Clinician')
  const approver = session?.roles.includes('Tele Tena Approver')
  const kind = session?.profile?.kind || (patient ? 'patient' : 'clinician')

  function clearPrivateState() {
    setSession(null); setCsrf(''); setName(''); setAdult(false); setHistory(''); setStatement('')
    setApplications([]); setAppointments([]); setOffers([]); setOffer(null); setRequest(''); setPreview(null)
    setBalance({ available: 0, reserved: 0 }); setWindows({ windows: [], busy: [] })
    setShareName(false); setShareHistory(false); setDefaultShareName(false); setDefaultShareHistory(false); setScopes([])
  }
  async function refresh(loadProfile = false, resetSharing = false) {
    const current = await api<Session>('session')
    setCsrf(current.csrf_token); setSession(current)
    if (loadProfile && current.profile) {
      setPreview(null); setRetryKey(crypto.randomUUID())
      setName(current.profile.display_name); setHistory(current.profile.history); setAdult(true)
      setDefaultShareName(Boolean(current.profile.share_name)); setDefaultShareHistory(Boolean(current.profile.share_history))
      if (resetSharing) { setShareName(Boolean(current.profile.share_name)); setShareHistory(Boolean(current.profile.share_history)) }
    }
    setServices(await api<Service[]>('services'))
    if (current.roles.includes('Tele Tena Patient')) {
      setOffers(await api<Offer[]>('discover', filter ? { service: filter } : {}))
      if (current.profile) setBalance(await api('wallet'))
    }
    if (current.roles.includes('Tele Tena Approver') || (current.profile && current.roles.includes('Tele Tena Clinician'))) {
      setApplications(await api('applications'))
    }
    if (current.roles.includes('Tele Tena Approver')) setScopes(await api('service_scopes'))
    if (current.profile) setAppointments(await api('appointments'))
  }
  const hydrate = useEffectEvent(async () => { try { await refresh(true, true) } catch { clearPrivateState() } })
  useEffect(() => { void Promise.resolve().then(() => hydrate()) }, [])
  function change(update: () => void) { setPreview(null); setRetryKey(crypto.randomUUID()); update() }
  async function run(action: () => Promise<void>) {
    setWorking(true); setMessage('')
    try { await action(); setMessage('success') } catch (error) { setMessage(error instanceof ApiError ? errorKeys[error.code] || 'failure' : 'failure') }
    finally { setWorking(false) }
  }
  function submit(event: FormEvent, action: () => Promise<void>) { event.preventDefault(); void run(action) }
  const button = (key: Key) => <button disabled={working}>{t(key)}</button>
  const disclosureView = (value: Disclosure) => <dl>{(['request', 'name', 'history'] as const).map(key => value[key] !== undefined && <div key={key}><dt>{t((key + 'Field') as Key)}</dt><dd>{value[key] || '—'}</dd></div>)}</dl>

  return <main>
    <header><h1>{t('title')}</h1><label>{t('language')} <select aria-label={t('language')} value={locale} onChange={e => setLocale(e.target.value as keyof typeof locales)}><option value="en">English</option><option value="am">አማርኛ</option><option value="om">Afaan Oromo</option></select></label></header>
    <p className="banner">{t('warning')}</p><p className="notice">{t('review')}</p>
    <p role="status">{working ? t('loading') : message ? t(message) : ''}</p>
    {!session ? <section><h2>{t('login')}</h2><p>{t('credentials')}</p><form onSubmit={e => submit(e, async () => { await signIn(email, password); setPassword(''); await refresh(true, true) })}>
      <label>{t('email')}<input type="email" autoComplete="username" required value={email} onChange={e => setEmail(e.target.value)} /></label>
      <label>{t('password')}<input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></label>{button('login')}
    </form></section> : <>
      <nav><span>{t('authenticated')}: {session.user}</span><button disabled={working} onClick={() => void run(async () => { await api('frappe.handler.logout', {}, true); clearPrivateState() })}>{t('logout')}</button><button disabled={working} onClick={() => void run(() => refresh())}>{t('refresh')}</button></nav>
      {(patient || clinician) && <section><h2>{t('profile')} · {t(kind)}</h2><form onSubmit={e => submit(e, async () => {
        await api('save_profile', { kind, display_name: name, adult, history, share_name: defaultShareName, share_history: defaultShareHistory }, true); await refresh(true)
      })}>
        <label>{t('name')}<input required maxLength={120} value={name} onChange={e => change(() => setName(e.target.value))} /></label>
        <label className="check"><input type="checkbox" checked={adult} onChange={e => setAdult(e.target.checked)} />{t('adult')}</label>
        {patient && <><label>{t('history')}<textarea maxLength={4000} value={history} onChange={e => change(() => setHistory(e.target.value))} /></label><p>{t('defaults')}</p>
          <label className="check"><input type="checkbox" checked={defaultShareName} onChange={e => setDefaultShareName(e.target.checked)} />{t('shareName')}</label>
          <label className="check"><input type="checkbox" checked={defaultShareHistory} onChange={e => setDefaultShareHistory(e.target.checked)} />{t('shareHistory')}</label></>}{button('save')}
      </form></section>}
      {approver && <>
        <section><h2>{t('catalog')}</h2><form onSubmit={e => submit(e, async () => { await api('save_service', { service: serviceId, label: serviceLabel }, true); await refresh() })}>
          <label>{t('serviceId')}<input required pattern="[a-z0-9-]+" value={serviceId} onChange={e => setServiceId(e.target.value)} /></label>
          <label>{t('serviceLabel')}<input required value={serviceLabel} onChange={e => setServiceLabel(e.target.value)} /></label>{button('saveService')}
        </form></section>
        <section><h2>{t('approvals')}</h2><label>{t('scopeService')}<select aria-label={t('scopeService')} value={scopeService} onChange={e => setScopeService(e.target.value)}><option value="">{t('choose')}</option>{services.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}</select></label>{applications.length === 0 && <p>{t('empty')}</p>}{applications.map(a => <article key={a.user}><h3>{a.user}</h3><p>{a.statement}</p><p>{t('status')}: {t(a.status.toLowerCase() as Key)}</p>
          <button disabled={working} onClick={() => void run(async () => { await api('review', { clinician: a.user, decision: 'Approved' }, true); await refresh() })}>{t('approve')}</button>{' '}
          <button disabled={working} onClick={() => void run(async () => { await api('review', { clinician: a.user, decision: 'Rejected' }, true); await refresh() })}>{t('reject')}</button>
          <p>{t('serviceScopes')}: {scopes.filter(scope => scope.clinician === a.user).map(scope => `${scope.service}: ${scope.status === 'Approved' ? t('approved') : t('scopeRevoked')}`).join(', ') || t('empty')}</p>
          <button disabled={working || !scopeService} onClick={() => void run(async () => { await api('review_service_scope', { clinician: a.user, service: scopeService, decision: 'Approved' }, true); await refresh() })}>{t('approveScope')}</button>{' '}
          <button disabled={working || !scopeService} onClick={() => void run(async () => { await api('review_service_scope', { clinician: a.user, service: scopeService, decision: 'Revoked' }, true); await refresh() })}>{t('revokeScope')}</button>
        </article>)}</section>
      </>}
      {clinician && session.profile && <>
        <section><h2>{t('application')}</h2>{applications.map(a => <p key={a.user}>{t('status')}: {t(a.status.toLowerCase() as Key)}</p>)}
          <form onSubmit={e => submit(e, async () => { await api('apply', { statement }, true); await refresh() })}><label>{t('statement')}<textarea required maxLength={2000} value={statement} onChange={e => setStatement(e.target.value)} /></label>{button('apply')}</form>
        </section>
        <section><h2>{t('offering')}</h2><form onSubmit={e => submit(e, async () => { await api('publish', { service, price, minutes }, true); await refresh() })}>
          <label>{t('service')}<select aria-label={t('service')} required value={service} onChange={e => setService(e.target.value)}><option value="">{t('choose')}</option>{services.map(s => <option value={s.id} key={s.id}>{s.label}</option>)}</select></label>
          <label>{t('price')}<input type="number" min="1" max="100000000" step="1" required value={price} onChange={e => setPrice(e.target.value)} /></label>
          <label>{t('minutes')}<input type="number" min="5" max="240" step="1" required value={minutes} onChange={e => setMinutes(e.target.value)} /></label>{button('publish')}
        </form></section>
        <section><h2>{t('availability')}</h2><p>{t('availabilityTiming')}</p><form onSubmit={e => submit(e, async () => { await api('add_availability', { start: new Date(start).toISOString(), end: new Date(end).toISOString() }, true); await refresh() })}>
          <label>{t('start')}<input required type="datetime-local" value={start} onChange={e => change(() => setStart(e.target.value))} /></label>
          <label>{t('end')}<input required type="datetime-local" value={end} onChange={e => setEnd(e.target.value)} /></label>{button('addWindow')}
        </form></section>
      </>}
      {patient && session.profile && <>
        <section><h2>{t('wallet')}</h2><p>{t('available')}: ETB {money(balance.available)} · {t('reserved')}: ETB {money(balance.reserved)}</p>
          {session.simulation && <button disabled={working} onClick={() => void run(async () => { await api('simulated_deposit', { amount: 10000, retry_key: depositKey }, true); setDepositKey(crypto.randomUUID()); await refresh() })}>{t('deposit')}</button>}
        </section>
        <section><h2>{t('discovery')}</h2><label>{t('service')}<select aria-label={t('service')} value={filter} onChange={e => { const next = e.target.value; setFilter(next); setOffer(null); void run(async () => { setOffers(await api('discover', next ? { service: next } : {})) }) }}><option value="">{t('all')}</option>{services.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}</select></label>
          {offers.length === 0 && <p>{t('noOffer')}</p>}{offers.map(o => <article key={o.id}><h3>{o.display_name} · {o.label}</h3><p>ETB {money(o.price)} · {o.minutes} {t('duration')}</p><button disabled={working} onClick={() => void run(async () => { change(() => { setOffer(o); setShareName(Boolean(session.profile?.share_name)); setShareHistory(Boolean(session.profile?.share_history)) }); setWindows(await api('windows', { offering: o.id })) })}>{t('choose')}</button></article>)}
        </section>
        {offer && <section><h2>{offer.display_name} · {offer.label}</h2><p>ETB {money(offer.price)} · {offer.minutes} {t('duration')}</p><p>{t('timezone')}: {timezone}</p><h3>{t('windows')}</h3>{windows.windows.map(w => <p key={w.start}>{date(w.start)} – {date(w.end)}</p>)}<h3>{t('busy')}</h3>{windows.busy.map(w => <p key={w.start}>{date(w.start)} – {date(w.end)}</p>)}
          <label>{t('start')}<input type="datetime-local" required value={start} onChange={e => change(() => setStart(e.target.value))} /></label>
          <label>{t('request')}<textarea required maxLength={2000} value={request} onChange={e => change(() => setRequest(e.target.value))} /></label><h3>{t('sharing')}</h3>
          <label className="check"><input type="checkbox" checked={shareName} onChange={e => change(() => setShareName(e.target.checked))} />{t('shareName')}</label>
          <label className="check"><input type="checkbox" checked={shareHistory} onChange={e => change(() => setShareHistory(e.target.checked))} />{t('shareHistory')}</label>
          <p>{t('previewNote')}</p><button disabled={working || !request || !start} onClick={() => void run(async () => { const result = await api<{ disclosure: Disclosure }>('preview', { request_text: request, sharing: { name: shareName, history: shareHistory } }, true); setPreview(result.disclosure) })}>{t('preview')}</button>
          {preview && <><h3>{t('previewTitle')}</h3>{disclosureView(preview)}<button disabled={working} onClick={() => void run(async () => {
            await api('book', { offering: offer.id, start: new Date(start).toISOString(), request_text: request, sharing: { name: shareName, history: shareHistory }, retry_key: retryKey,
              expected_price: offer.price, expected_minutes: offer.minutes, expected_disclosure: preview }, true)
            await refresh(); setWindows(await api('windows', { offering: offer.id }))
          })}>{t('book')}</button></>}
        </section>}
      </>}
      {(patient || clinician) && !session.profile && <p>{t('noProfile')}</p>}
      {session.profile && <section><h2>{t('appointments')}</h2>{appointments.length === 0 && <p>{t('empty')}</p>}{appointments.map(a => <article key={a.id} data-appointment-id={a.id}><h3>{a.service_label} · {t('booked')}</h3><p>{date(a.start)} – {date(a.end)} · ETB {money(a.price)} · {a.minutes} {t('duration')}</p>{disclosureView(a.disclosure)}<Consultation appointment={a} t={t} /></article>)}</section>}
    </>}
  </main>
}

type ConsultationInfo = { state: 'Not started' | 'Open' | 'Ended'; role: 'patient' | 'clinician'; can_join: boolean; can_end: boolean; room_close_pending: boolean }
function Consultation({ appointment, t }: { appointment: Appointment; t: (key: Key) => string }) {
  const [info, setInfo] = useState<ConsultationInfo | null>(null)
  const [lifecycleStatus, setLifecycleStatus] = useState<Key>('callNotStarted')
  const [mediaStatus, setMediaStatus] = useState<Key>('callNotConnected')
  const [checked, setChecked] = useState(false)
  const [audioOnly, setAudioOnly] = useState(false)
  const [muted, setMuted] = useState(false)
  const [cameraOn, setCameraOn] = useState(true)
  const [busy, setBusy] = useState(false)
  const mounted = useRef(false)
  const generation = useRef(0)
  const joining = useRef(false)
  const preview = useRef<HTMLVideoElement>(null)
  const remote = useRef<HTMLDivElement>(null)
  const roomRef = useRef<LiveKitRoom | null>(null)
  const previewStream = useRef<MediaStream | null>(null)

  const refresh = useCallback(async () => {
    try {
      const next = await api<ConsultationInfo>('tele_tena.api.consultations.consultation', { appointment: appointment.id })
      if (!mounted.current) return
      setInfo(next)
      setLifecycleStatus(next.state === 'Ended' ? next.room_close_pending ? 'callClosePending' : 'callEnded' : !next.can_join ? 'callOutsideWindow' : next.state === 'Open' ? 'callReady' : 'callNotStarted')
    } catch { if (mounted.current) setLifecycleStatus('callUnavailable') }
  }, [appointment.id])
  useEffect(() => {
    mounted.current = true
    void Promise.resolve().then(refresh)
    const timer = window.setInterval(() => void refresh(), 5000)
    return () => {
      mounted.current = false
      window.clearInterval(timer)
      void leave(false)
    }
  }, [appointment.id, refresh])
  function stopPreview() {
    previewStream.current?.getTracks().forEach(track => track.stop())
    previewStream.current = null
    if (preview.current) preview.current.srcObject = null
    if (mounted.current) setChecked(false)
  }
  function detachRemote(room?: LiveKitRoom) {
    if (room) {
      for (const participant of room.remoteParticipants.values()) {
        for (const publication of participant.trackPublications.values()) publication.track?.detach().forEach(element => element.remove())
      }
    }
    remote.current?.replaceChildren()
  }
  async function disposeRoom(room: LiveKitRoom) {
    try { await room.disconnect() } catch { /* cleanup continues even if signaling failed */ }
    for (const publication of room.localParticipant.trackPublications.values()) publication.track?.stop()
    detachRemote(room)
  }
  async function checkDevices() {
    stopPreview()
    const attempt = generation.current
    let stream: MediaStream | null = null
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: !audioOnly })
      if (!mounted.current || attempt !== generation.current) { stream.getTracks().forEach(track => track.stop()); return }
      previewStream.current = stream
      if (preview.current && !audioOnly) { preview.current.srcObject = stream; await preview.current.play().catch(() => undefined) }
      setChecked(true); setMediaStatus('callReady')
    } catch {
      stream?.getTracks().forEach(track => track.stop())
      if (mounted.current && attempt === generation.current) setMediaStatus('callDeviceError')
    }
  }
  async function join() {
    if (joining.current || !mounted.current) return
    joining.current = true
    const attempt = ++generation.current
    let room: LiveKitRoom | null = null
    setBusy(true); setMediaStatus('callConnecting')
    try {
      const issued = await api<{ url: string; token: string; audio_only: boolean }>('tele_tena.api.consultations.join',
        { appointment: appointment.id, audio_only: audioOnly ? 1 : 0 }, true)
      if (!mounted.current || attempt !== generation.current) return
      const { Room, RoomEvent } = await import('livekit-client')
      if (!mounted.current || attempt !== generation.current) return
      const connectedRoom = new Room({ adaptiveStream: true, dynacast: true })
      room = connectedRoom
      roomRef.current = connectedRoom
      const current = () => mounted.current && generation.current === attempt && roomRef.current === connectedRoom
      connectedRoom.on(RoomEvent.Reconnecting, () => { if (current()) setMediaStatus('callReconnecting') })
      connectedRoom.on(RoomEvent.Reconnected, () => { if (current()) setMediaStatus('callConnected') })
      connectedRoom.on(RoomEvent.Disconnected, () => {
        if (current()) { roomRef.current = null; void disposeRoom(connectedRoom); setMediaStatus('callDisconnected') }
      })
      connectedRoom.on(RoomEvent.TrackSubscribed, (track) => {
        const element = track.attach()
        if (!current() || !remote.current) { track.detach(element); element.remove(); return }
        remote.current.appendChild(element)
      })
      connectedRoom.on(RoomEvent.TrackUnsubscribed, (track) => track.detach().forEach(element => element.remove()))
      await connectedRoom.connect(issued.url, issued.token)
      if (!current()) { await disposeRoom(connectedRoom); return }
      stopPreview()
      await connectedRoom.localParticipant.setMicrophoneEnabled(true)
      if (!audioOnly) await connectedRoom.localParticipant.setCameraEnabled(true)
      if (!current()) { await disposeRoom(connectedRoom); return }
      setMuted(false); setCameraOn(!audioOnly); setMediaStatus('callConnected')
    } catch {
      if (room) {
        if (roomRef.current === room) roomRef.current = null
        await disposeRoom(room)
      }
      stopPreview()
      if (mounted.current && attempt === generation.current) setMediaStatus('callConnectError')
    } finally {
      if (attempt === generation.current) joining.current = false
      if (mounted.current && attempt === generation.current) setBusy(false)
    }
  }
  async function leave(showStatus = true) {
    generation.current++
    joining.current = false
    const room = roomRef.current
    roomRef.current = null
    if (room) await disposeRoom(room)
    stopPreview()
    if (showStatus && mounted.current) setMediaStatus('callDisconnected')
  }
  async function end() {
    setBusy(true)
    try {
      await api('tele_tena.api.consultations.end', { appointment: appointment.id }, true)
      await leave(false); if (mounted.current) setMediaStatus('callDisconnected'); await refresh()
    } catch { if (mounted.current) setLifecycleStatus('callClosePending') }
    finally { if (mounted.current) setBusy(false) }
  }
  async function toggleMute() {
    setBusy(true)
    try { const next = !muted; await roomRef.current?.localParticipant.setMicrophoneEnabled(!next); if (mounted.current) setMuted(next) }
    catch { if (mounted.current) setMediaStatus('callToggleError') }
    finally { if (mounted.current) setBusy(false) }
  }
  async function toggleCamera() {
    setBusy(true)
    try { const next = !cameraOn; await roomRef.current?.localParticipant.setCameraEnabled(next); if (mounted.current) setCameraOn(next) }
    catch { if (mounted.current) setMediaStatus('callToggleError') }
    finally { if (mounted.current) setBusy(false) }
  }
  const connected = Boolean(roomRef.current)
  return <section className="consultation" aria-label={t('consultation')}>
    <h4>{t('consultation')}</h4><p>{t('sessionLifecycle')}: {t(lifecycleStatus)}</p><p role="status">{t('mediaStatus')}: {t(mediaStatus)}</p>
    {!connected && info?.state !== 'Ended' && <>
      <label className="check"><input type="checkbox" checked={audioOnly} disabled={busy} onChange={e => { generation.current++; stopPreview(); setMediaStatus('callNotConnected'); setAudioOnly(e.target.checked) }} />{t('audioOnly')}</label>
      <button disabled={busy || !info?.can_join} onClick={() => void checkDevices()}>{t(audioOnly ? 'checkMicrophone' : 'checkDevices')}</button>
      {!audioOnly && <video ref={preview} autoPlay muted playsInline className="call-video" aria-label={t('localPreview')} />}
      <button disabled={busy || !checked || !info?.can_join} onClick={() => void join()}>{t('joinCall')}</button>
      <button type="button" disabled={busy} onClick={() => void refresh()}>{t('refreshCall')}</button>
    </>}
    <div ref={remote} className="call-remote" aria-label={t('remoteMedia')} />
    {connected && <div className="call-controls">
      <button type="button" disabled={busy} onClick={() => void toggleMute()}>{t(muted ? 'unmute' : 'mute')}</button>
      {!audioOnly && <button type="button" disabled={busy} onClick={() => void toggleCamera()}>{t(cameraOn ? 'cameraOff' : 'cameraOn')}</button>}
      <button type="button" disabled={busy} onClick={() => void leave()}>{t('leaveCall')}</button>
      {info?.can_end && <button type="button" disabled={busy} onClick={() => void end()}>{t('endConsultation')}</button>}
    </div>}
    {info?.can_end && !connected && <button type="button" disabled={busy} onClick={() => void end()}>{t('endConsultation')}</button>}
  </section>
}
