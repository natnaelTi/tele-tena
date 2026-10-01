import { useCallback, useEffect, useRef, useState } from 'react'
import type { Room as LiveKitRoom } from 'livekit-client'
import { api } from '../../api'
import type { Key } from '../../i18n'
type Appointment = { id: string }
type ConsultationInfo = { state: 'Not started' | 'Open' | 'Ended'; role: 'patient' | 'clinician'; can_join: boolean; can_end: boolean; room_close_pending: boolean }
export default function Consultation({ appointment, t }: { appointment: Appointment; t: (key: Key) => string }) {
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
