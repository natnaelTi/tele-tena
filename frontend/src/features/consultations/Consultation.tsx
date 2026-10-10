import { Brand } from "../../components/Brand";
import { Dialog, Button } from "../../components/ui";
import { Mic, MicOff, Video, VideoOff, PhoneOff, Maximize2, Headphones, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import type { Room as LiveKitRoom } from "livekit-client";
import { Link } from "react-router-dom";
import { useLocale } from "../../hooks/useLocale";
import "./consultation-room.css";
import { ApiError, api } from "../../api";
import type { Key } from "../../i18n";
import AudioStage from "./AudioStage";
import ExtensionPanel from "./ExtensionPanel";
type Appointment = { id: string; display_identity?:string; call_state?:string; timezone?:string | null; service_label?:string; minutes?:number; consultation_format?:string };
type ConsultationInfo = {
  appointment_state: string;
  documentation_state: string;
  state: "Not started" | "Open" | "Ended";
  role: "patient" | "clinician";
  can_join: boolean;
  can_end: boolean;
  room_close_pending: boolean;
  join_opens_at: string;
  join_closes_at: string;
};
export default function Consultation({
  appointment,
  t,
}: {
  appointment: Appointment;
  t: (key: Key) => string;
}) {
  const { w } = useLocale();
  const [confirmEnd, setConfirmEnd] = useState(false);
  const selfPreview = useRef<HTMLVideoElement>(null);
  const [info, setInfo] = useState<ConsultationInfo | null>(null);
  const [lifecycleStatus, setLifecycleStatus] = useState<Key>("callNotStarted");
  const [controlError, setControlError] = useState<Key | null>(null);
  const [mediaStatus, setMediaStatus] = useState<Key>("callNotConnected");
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [microphone, setMicrophone] = useState("");
  const [camera, setCamera] = useState("");
  const [checked, setChecked] = useState(false);
  const [audioOnly, setAudioOnly] = useState(false);
  const [muted, setMuted] = useState(false);
  const [cameraOn, setCameraOn] = useState(true);
  const [remotePresent, setRemotePresent] = useState(false);
  const [remoteVideo, setRemoteVideo] = useState(false);
  const [remoteMuted, setRemoteMuted] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [level, setLevel] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);
  const root = useRef<HTMLElement>(null);
  const [expanded, setExpanded] = useState(false);
  const [busy, setBusy] = useState(false);
  const mounted = useRef(false);
  const generation = useRef(0);
  const joining = useRef(false);
  const endedObserved = useRef(false);
  const preview = useRef<HTMLVideoElement>(null);
  const remote = useRef<HTMLDivElement>(null);
  const roomRef = useRef<LiveKitRoom | null>(null);
  const previewStream = useRef<MediaStream | null>(null);

  const refresh = useCallback(async () => {
    try {
      const next = await api<ConsultationInfo>(
        "tele_tena.api.consultations.consultation",
        { appointment: appointment.id },
      );
      if (!mounted.current || (endedObserved.current && next.state !== "Ended")) return;
      if (next.state === "Ended") endedObserved.current = true;
      setInfo(next);
      if (next.state === "Ended") {
        if (roomRef.current || previewStream.current) await leave(false);
        if (mounted.current) setMediaStatus("callEndedDisconnected");
      }
      if (!mounted.current) return;
      setLifecycleStatus(
        next.state === "Ended"
          ? next.room_close_pending
            ? "callClosePending"
            : "callEnded"
          : !next.can_join
            ? "callOutsideWindow"
            : next.state === "Open"
              ? "callReady"
              : "callNotStarted",
      );
    } catch {
      if (mounted.current) setLifecycleStatus("callUnavailable");
    }
  }, [appointment.id]);
  useEffect(() => {
    mounted.current = true;
    void Promise.resolve().then(refresh);
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => {
      mounted.current = false;
      window.clearInterval(timer);
      void leave(false);
    };
  }, [appointment.id, refresh]);
  useEffect(() => {
    // Use LiveKit's existing received-audio measurements; no extra capture,
    // audio recording or Web Audio microphone stream is created.
    const timer = window.setInterval(() => {
      const room = roomRef.current;
      if (!room || !mounted.current) return;
      const activity = Math.max(0, ...[...room.remoteParticipants.values()]
        .filter(participant => participant.isMicrophoneEnabled)
        .map(participant => participant.audioLevel));
      setSpeaking(activity > 0.08);
      setLevel(activity > 0.08 ? Math.min(1, activity) : 0);
    }, 150);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    const changed = () => setFullscreen(document.fullscreenElement === root.current);
    document.addEventListener("fullscreenchange", changed);
    return () => document.removeEventListener("fullscreenchange", changed);
  }, []);
  useEffect(() => {
    const node = root.current;
    if (!expanded || !node) return;
    const previous = document.activeElement;
    const keys = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setExpanded(false); return; }
      if (event.key !== "Tab") return;
      const controls = [...node.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), select:not([disabled])')]
        .filter(element => element.offsetParent !== null);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    node.addEventListener("keydown", keys);
    node.querySelector<HTMLElement>('.fullscreen-control')?.focus();
    return () => { node.removeEventListener("keydown", keys); if (previous instanceof HTMLElement && previous.isConnected) previous.focus(); };
  }, [expanded]);
  function stopPreview() {
    previewStream.current?.getTracks().forEach((track) => track.stop());
    previewStream.current = null;
    if (preview.current) preview.current.srcObject = null;
    if (mounted.current) setChecked(false);
  }
  function detachRemote(room?: LiveKitRoom) {
    if (room) {
      for (const participant of room.remoteParticipants.values()) {
        for (const publication of participant.trackPublications.values())
          publication.track?.detach().forEach((element) => element.remove());
      }
    }
    if (!room || !roomRef.current || roomRef.current === room) remote.current?.replaceChildren();
  }
  async function disposeRoom(room: LiveKitRoom) {
    const tracks = [...room.localParticipant.trackPublications.values()].map(
      (publication) => publication.track,
    );
    for (const track of tracks) {
      track?.stop();
      track?.detach().forEach((element) => {
        if (element !== selfPreview.current) element.remove();
      });
    }
    if (selfPreview.current && (!roomRef.current || roomRef.current === room)) selfPreview.current.srcObject = null;
    try {
      await room.disconnect();
    } catch {
      /* cleanup continues even if signaling failed */
    }
    for (const publication of room.localParticipant.trackPublications.values())
      publication.track?.stop();
    detachRemote(room);
    room.removeAllListeners();
  }
  async function checkDevices() {
    stopPreview();
    if (busy || joining.current) return;
    const attempt = ++generation.current;
    setBusy(true);
    let stream: MediaStream | null = null;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: microphone ? { deviceId: { exact: microphone } } : true,
        video: audioOnly ? false : camera ? { deviceId: { exact: camera } } : true,
      });
      if (!mounted.current || attempt !== generation.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      previewStream.current = stream;
      if (preview.current && !audioOnly) {
        preview.current.srcObject = stream;
        await preview.current.play().catch(() => undefined);
      }
      const availableDevices = await navigator.mediaDevices.enumerateDevices();
      if (!mounted.current || attempt !== generation.current) { stream.getTracks().forEach(track => track.stop()); return; }
      setDevices(availableDevices);
      setChecked(true);
      setMediaStatus("callReady");
    } catch {
      stream?.getTracks().forEach((track) => track.stop());
      if (mounted.current && attempt === generation.current)
        setMediaStatus("callDeviceError");
    } finally {
      if (mounted.current && attempt === generation.current) setBusy(false);
    }
  }
  async function join() {
    if (joining.current || !mounted.current) return;
    joining.current = true;
    const attempt = ++generation.current;
    let room: LiveKitRoom | null = null;
    setBusy(true);
    setMediaStatus("callConnecting");
    try {
      const issued = await api<{
        url: string;
        token: string;
        audio_only: boolean;
      }>(
        "tele_tena.api.consultations.join",
        { appointment: appointment.id, audio_only: audioOnly ? 1 : 0 },
        true,
      );
      if (!mounted.current || attempt !== generation.current) return;
      const { Room, RoomEvent } = await import("livekit-client");
      if (!mounted.current || attempt !== generation.current) return;
      const connectedRoom = new Room({ adaptiveStream: true, dynacast: true, audioCaptureDefaults: { deviceId: microphone || undefined }, videoCaptureDefaults: { deviceId: camera || undefined } });
      room = connectedRoom;
      roomRef.current = connectedRoom;
      const current = () =>
        mounted.current &&
        generation.current === attempt &&
        roomRef.current === connectedRoom;
      connectedRoom.on(RoomEvent.Reconnecting, () => {
        if (current()) setMediaStatus("callReconnecting");
      });
      connectedRoom.on(RoomEvent.SignalReconnecting, () => {
        if (current()) setMediaStatus("callReconnecting");
      });
      connectedRoom.on(RoomEvent.Reconnected, () => {
        if (current()) setMediaStatus("callConnected");
      });
      connectedRoom.on(RoomEvent.ActiveSpeakersChanged, speakers => {
        if (!current()) return;
        const remoteSpeaker = speakers.find(participant => participant.identity !== connectedRoom.localParticipant.identity && participant.audioLevel > 0.08 && participant.isMicrophoneEnabled);
        const active = Boolean(remoteSpeaker);
        setSpeaking(active); setLevel(active ? Math.min(1, remoteSpeaker?.audioLevel || 0) : 0);
      });
      connectedRoom.on(RoomEvent.ParticipantConnected, () => {
        if (current()) setRemotePresent(connectedRoom.remoteParticipants.size > 0);
      });
      connectedRoom.on(RoomEvent.ParticipantDisconnected, () => {
        if (current()) {
          setRemotePresent(connectedRoom.remoteParticipants.size > 0);
          if (!connectedRoom.remoteParticipants.size) { setRemoteVideo(false); setSpeaking(false); setLevel(0); }
        }
      });
      connectedRoom.on(RoomEvent.TrackMuted, (publication, participant) => {
        if (current() && participant !== connectedRoom.localParticipant && publication.kind === "video") setRemoteVideo(false);
        if (current() && participant !== connectedRoom.localParticipant && publication.kind === "audio") {
          setRemoteMuted(true); setSpeaking(false); setLevel(0);
        }
      });
      connectedRoom.on(RoomEvent.TrackUnmuted, (publication, participant) => {
        if (current() && participant !== connectedRoom.localParticipant && publication.kind === "audio") setRemoteMuted(false);
        if (current() && participant !== connectedRoom.localParticipant && publication.kind === "video") setRemoteVideo(true);
      });
      connectedRoom.on(RoomEvent.Disconnected, () => {
        if (current()) {
          roomRef.current = null;
          void disposeRoom(connectedRoom);
          setMediaStatus("callConnectionLost");
          void refresh();
        }
      });
      connectedRoom.on(RoomEvent.LocalTrackPublished, (publication) => {
        if (
          current() &&
          publication.track?.kind === "video" &&
          selfPreview.current
        )
          publication.track.attach(selfPreview.current);
      });
      connectedRoom.on(RoomEvent.TrackSubscribed, (track) => {
        // Subscriptions can arrive before React mounts the connected stage.
        // Attach from publications, also on stage mount, rather than discarding them.
        if (current()) { if (track.kind === "video") setRemoteVideo(!track.isMuted); attachMedia(); }
      });
      connectedRoom.on(RoomEvent.TrackUnsubscribed, (track) => {
        track.detach().forEach((element) => element.remove());
        if (current() && track.kind === "video") setRemoteVideo(false);
      });
      await connectedRoom.connect(issued.url, issued.token);
      if (!current()) {
        await disposeRoom(connectedRoom);
        return;
      }
      setRemotePresent(connectedRoom.remoteParticipants.size > 0);
      stopPreview();
      await connectedRoom.localParticipant.setMicrophoneEnabled(true);
      if (!audioOnly)
        await connectedRoom.localParticipant.setCameraEnabled(true);
      if (!current()) {
        await disposeRoom(connectedRoom);
        return;
      }
      setMuted(false);
      setCameraOn(!audioOnly);
      setMediaStatus("callConnected");
    } catch (error) {
      if (room) {
        if (roomRef.current === room) roomRef.current = null;
        await disposeRoom(room);
      }
      if (mounted.current && attempt === generation.current) {
        stopPreview();
        if (error instanceof ApiError && error.code === "outside_join_window") {
          setMediaStatus("callNotConnected"); setControlError("callOutsideWindow"); await refresh();
        } else if (error instanceof ApiError && ["consultation_ended", "appointment_inactive"].includes(error.code)) {
          setMediaStatus("callNotConnected"); await refresh();
        } else if (error instanceof ApiError && ["permission_denied", "session_required"].includes(error.code)) {
          setMediaStatus("callUnavailable"); setInfo(null);
        } else setMediaStatus(error instanceof ApiError && error.code === "consultation_service_unconfigured" ? "callServiceUnavailable" : "callConnectError");
      }
    } finally {
      if (attempt === generation.current) joining.current = false;
      if (mounted.current && attempt === generation.current) setBusy(false);
    }
  }
  async function leave(showStatus = true) {
    generation.current++;
    joining.current = false;
    const room = roomRef.current;
    roomRef.current = null;
    stopPreview();
    if (mounted.current) { setSpeaking(false); setLevel(0); setRemoteMuted(false); setRemotePresent(false); setRemoteVideo(false); setControlError(null); setBusy(false); }
    if (room) await disposeRoom(room);
    if (showStatus && mounted.current) setMediaStatus("callDisconnected");
  }
  async function end() {
    setConfirmEnd(false);
    setBusy(true);
    try {
      await api(
        "tele_tena.api.consultations.end",
        { appointment: appointment.id },
        true,
      );
      await leave(false);
      await refresh();
    } catch {
      // End may have committed even when Cloud closure failed. Read the
      // authoritative lifecycle rather than guessing that it ended.
      await refresh();
      if (mounted.current) setControlError("callEndError");
    } finally {
      if (mounted.current) setBusy(false);
    }
  }
  async function toggleMedia(kind: "microphone" | "camera") {
    const room = roomRef.current;
    const attempt = generation.current;
    if (!room || busy) return;
    setBusy(true); setControlError(null);
    try {
      if (kind === "microphone") await room.localParticipant.setMicrophoneEnabled(muted);
      else await room.localParticipant.setCameraEnabled(!cameraOn);
    } catch {
      if (mounted.current && attempt === generation.current) setControlError("callToggleError");
    } finally {
      if (!mounted.current || attempt !== generation.current || roomRef.current !== room) {
        await disposeRoom(room);
      } else {
        setMuted(!room.localParticipant.isMicrophoneEnabled);
        setCameraOn(room.localParticipant.isCameraEnabled);
        setBusy(false);
      }
    }
  }
  async function toggleAudioOnly() {
    const room = roomRef.current;
    const attempt = generation.current;
    if (!room || busy) return;
    setBusy(true); setControlError(null);
    try {
      if (audioOnly) {
        // Obtain a camera-capable token only after leaving and a new preflight.
        await leave(false);
        if (mounted.current && generation.current === attempt + 1 && !roomRef.current) {
          setAudioOnly(false); setMediaStatus("callDisconnected");
        }
        return;
      }
      await room.localParticipant.setCameraEnabled(false);
      if (!mounted.current || attempt !== generation.current || roomRef.current !== room) {
        await disposeRoom(room);
        return;
      }
      setCameraOn(room.localParticipant.isCameraEnabled); setAudioOnly(true);
    } catch {
      if (mounted.current && attempt === generation.current) setControlError("callToggleError");
    } finally {
      if (mounted.current && attempt === generation.current) setBusy(false);
    }
  }
  async function toggleFullscreen(){
    if (expanded) { setExpanded(false); return; }
    const node=root.current;
    try{if(!document.fullscreenElement&&node?.requestFullscreen)await node.requestFullscreen();else if(document.fullscreenElement)await document.exitFullscreen();else setExpanded(current=>!current);}catch{setExpanded(current=>!current);}
  }
  async function requestEndConfirmation() {
    try {
      // Radix dialogs are portalled outside the fullscreen element. Exit first
      // so the confirmation remains visible and keyboard-accessible.
      if (document.fullscreenElement) await document.exitFullscreen();
      if (mounted.current) { setExpanded(false); setConfirmEnd(true); }
    } catch { if (mounted.current) setControlError("callToggleError"); }
  }
  function attachMedia() {
    const room = roomRef.current;
    if (!room) return;
    for (const participant of room.remoteParticipants.values()) {
      for (const publication of participant.trackPublications.values()) {
        const track = publication.track;
        if (!track || !remote.current) continue;
        // Reuse attached elements: remounting an audio/video stage must not
        // leave detached playing elements or duplicate audio playback.
        const element = track.attachedElements[0] || track.attach();
        if (element.parentElement !== remote.current) remote.current.appendChild(element);
      }
    }
    for (const publication of room.localParticipant.trackPublications.values())
      if (publication.track?.kind === "video" && selfPreview.current)
        publication.track.attach(selfPreview.current);
  }
  const connected = Boolean(roomRef.current);
  const audioSurface = audioOnly || !remoteVideo;
  const joinTime = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short", timeZone: appointment.timezone || "UTC" }).format(new Date(value));
  const detailRoute = `/${info?.role || "patient"}/consultations/${appointment.id}`;
  return (
    <section ref={root} className={`consultation ${connected ? "room-connected" : "room-preflight"} ${connected && audioOnly ? "room-audio-layout" : ""} ${expanded ? "room-expanded" : ""}`} aria-label={t("consultation")}>
      {(fullscreen || expanded) && <div className="room-demo" role="note">{w("Demonstration environment — no real payments or clinical care.")}</div>}
      {connected && !audioOnly && <header className="room-heading"><Brand/><div><strong>{appointment.service_label}</strong><span>{appointment.display_identity} · {appointment.minutes} {w("minutes")}</span></div><span className="room-private"><ShieldCheck size={18}/>{w("Private consultation")}</span></header>}
      {(!connected || audioOnly) && <header className="light-call-header"><Brand/><Link className="text-link" to={detailRoute}>{w("Back to consultation details")}</Link></header>}
      {connected && audioOnly && <div className="audio-page-title"><h1>{w("Audio consultation")}</h1><p>{w("More room to listen. Less bandwidth.")}</p></div>}
      {!connected && <><h2>{info?.state === "Ended" ? w("Call ended") : w("Check your devices")}</h2>{info?.state !== "Ended" && <p>{w("Make sure you’re comfortable before joining.")}</p>}</>}
      {!connected && info?.state === "Ended" && <p>
        {t("sessionLifecycle")}: {t(lifecycleStatus)}
      </p>}
      {((connected && !audioOnly) || info?.state === "Ended") && <p className="room-connection" role="status">
        {t("mediaStatus")}: {t(mediaStatus)}
      </p>}
      {controlError && <p className="call-control-error" role="alert">{t(controlError)}</p>}
      {info?.state === "Ended" && <div className="call-ended-panel">
        <p>{info.role === "clinician" && info.documentation_state !== "Finalized" ? w("The call has ended. Review your notes and finalize the encounter.") : w(info.appointment_state === "Completed" ? "Consultation record" : "Summary being prepared")}</p>
        <Link className="button primary" to={detailRoute}>{w(info.role === "clinician" && info.documentation_state !== "Finalized" ? "Finish the consultation" : "View consultation")}</Link>
        {info.room_close_pending && <p role="alert">{t("callClosePending")}</p>}
      </div>}
      {!connected && info?.state !== "Ended" && (
        <div className="device-check-layout"><div className="device-check-preview">
          {!audioOnly && (
            <video
              ref={preview}
              autoPlay
              muted
              playsInline
              className="call-video"
              aria-label={t("localPreview")}
            />
          )}

          <div className="device-selectors"><label className="field">{w("Microphone")}<select disabled={busy} value={microphone} onChange={event => { stopPreview(); setMediaStatus("callNotConnected"); setMicrophone(event.target.value); }}><option value="">{w("Default microphone")}</option>{devices.filter(device=>device.kind === "audioinput").map((device,index)=><option value={device.deviceId} key={device.deviceId}>{device.label || `${w("Microphone")} ${index + 1}`}</option>)}</select></label>{!audioOnly && <label className="field">{w("Camera")}<select disabled={busy} value={camera} onChange={event=>{stopPreview();setMediaStatus("callNotConnected");setCamera(event.target.value);}}><option value="">{w("Default camera")}</option>{devices.filter(device=>device.kind === "videoinput").map((device,index)=><option value={device.deviceId} key={device.deviceId}>{device.label || `${w("Camera")} ${index + 1}`}</option>)}</select></label>}</div>
          <label className="check">
            <input
              type="checkbox"
              checked={audioOnly}
              disabled={busy}
              onChange={(e) => {
                generation.current++;
                stopPreview();
                setMediaStatus("callNotConnected");
                setAudioOnly(e.target.checked);
              }}
            />
            {t("audioOnly")}
          </label>
          <button className="button"
            disabled={busy || !info?.can_join}
            onClick={() => void checkDevices()}
          >
            {t(audioOnly ? "checkMicrophone" : "checkDevices")}
          </button>
          </div><aside className="device-check-summary"><h2>{w("Ready when you are")}</h2><h3>{appointment.display_identity || w("Private participant")}</h3><p>{appointment.service_label}</p><p>{appointment.minutes} {w("minutes")} · {t(audioOnly ? "audioOnly" : "consultation")}</p><div className="preflight-state"><p role="status">{t("sessionLifecycle")}: {t(lifecycleStatus)}</p><p role="status">{t("mediaStatus")}: {t(mediaStatus)}</p></div><p>{w("Find a private space")}. {w("Use headphones if possible.")}</p>{info?.join_opens_at&&<p className="supporting">{w("Join window")}: {joinTime(info.join_opens_at)} – {joinTime(info.join_closes_at)} · {appointment.timezone || "UTC"}</p>}
          <button className="button"
            disabled={busy || !checked || !info?.can_join}
            onClick={() => void join()}
          >
            {t("joinCall")}
          </button>
          <button className="button secondary" type="button" disabled={busy} onClick={() => void refresh()}>
            {t("refreshCall")}
          </button>
        </aside></div>
      )}
      {connected&&<div className="room-workspace"><div className="room-main"><div className={`media-stage ${audioSurface?"audio-only":""} ${expanded?"expanded":""}`} data-connected={connected} data-remote-audio-muted={remoteMuted}>
        <div ref={node => { remote.current = node; attachMedia(); }} className={audioSurface?"call-audio-hidden":"call-remote"} aria-label={t("remoteMedia")}/>
        {audioOnly && <AudioStage identity={appointment.display_identity || w("Private participant")} service={appointment.service_label} minutes={appointment.minutes} status={t(mediaStatus)} activity={level} waiting={!remotePresent} muted={remoteMuted}/>}{audioSurface && !audioOnly && <div className="audio-participant"><div className={`audio-avatar ${speaking?"speaking":""}`} style={{"--audio-level":level} as CSSProperties} aria-label={w(speaking?"Participant speaking":"Participant is quiet")}><span aria-hidden="true">{(appointment.display_identity||"P").slice(0,1).toUpperCase()}</span></div><div className="room-audio-wave" style={{"--audio-level":level} as CSSProperties} aria-hidden="true">{Array.from({length:7},(_,index)=><i key={index}/>)}</div><h2>{appointment.display_identity||w("Private participant")}</h2><p>{!remotePresent ? t("callWaiting") : remoteMuted ? t("callRemoteMuted") : t(mediaStatus === "callConnected" ? "callConnected" : "callReconnecting")}</p></div>}
        {!audioOnly&&<video ref={node => { selfPreview.current = node; attachMedia(); }} autoPlay muted playsInline className="self-preview" hidden={!cameraOn} aria-label={t("localPreview")}/>}
        <button className="fullscreen-control" type="button" onClick={()=>void toggleFullscreen()} aria-label={w("Expand consultation")}><Maximize2 size={20}/></button>
      </div>
        <div className="call-controls">
          <button
            type="button"
            disabled={busy}
            onClick={() => void toggleMedia("microphone")}
            aria-label={t(muted ? "unmute" : "mute")}
            title={t(muted ? "unmute" : "mute")}
          >
            {muted ? <MicOff size={20} /> : <Mic size={20} />}
            {audioOnly ? w("Microphone") : t(muted ? "unmute" : "mute")}
          </button>
          {!audioOnly && (
            <button
              type="button"
              disabled={busy}
              onClick={() => void toggleMedia("camera")}
            >
              {cameraOn ? <Video size={20} /> : <VideoOff size={20} />}
              {t(cameraOn ? "cameraOff" : "cameraOn")}
            </button>
          )}
          <button type="button" disabled={busy} onClick={()=>void toggleAudioOnly()} aria-pressed={audioOnly} aria-label={w(audioOnly?"Turn video on":"Audio only")} title={w(audioOnly?"Turn video on":"Audio only")}>{audioOnly ? <Video size={20}/> : <Headphones size={20}/>} {w(audioOnly?"Video":"Audio only")}</button>
          <button
            className="leave-call"
            type="button"
            disabled={busy}
            onClick={() => void leave()}
          >
            <PhoneOff size={20} />
            {t("leaveCall")}
          </button>
          {info?.can_end && (
            <button
              className="end-call"
              type="button"
              disabled={busy}
              onClick={() => void requestEndConfirmation()}
            >
              {t("endConsultation")}
            </button>
          )}
        </div></div><aside className="room-session-details" hidden={audioOnly}><h3>{appointment.display_identity || w("Private participant")}</h3><dl><dt>{w("Service")}</dt><dd>{appointment.service_label}</dd><dt>{w("Booked duration")}</dt><dd>{appointment.minutes} {w("minutes")}</dd></dl><p>{w("Booked duration is not measured connected time.")}</p><Link to={detailRoute}>{w("Back to consultation details")}</Link><div className="room-privacy-note"><ShieldCheck size={20}/><h4>{w("Your privacy stays with you.")}</h4><p>{w("Your clinician sees only the information you chose to share for this session.")}</p></div>{info?.state === "Open" && !audioOnly && <ExtensionPanel appointment={appointment.id} role={info.role} open={true} t={t}/>}</aside></div>}
      {connected && audioOnly && <details className="audio-session-more"><summary>{w("Session details and extra time")}</summary><p>{appointment.service_label} · {appointment.minutes} {w("minutes")}</p><Link to={detailRoute}>{w("Back to consultation details")}</Link>{info?.state === "Open" && <ExtensionPanel appointment={appointment.id} role={info.role} open={true} t={t}/>}</details>}
      {info?.can_end && !connected && (
        <button
          className="end-call"
          type="button"
          disabled={busy}
          onClick={() => void requestEndConfirmation()}
        >
          {t("endConsultation")}
        </button>
      )}

      <Dialog
        open={confirmEnd}
        onOpenChange={setConfirmEnd}
        title={w("End for everyone?")}
        description={w("Ends the consultation for everyone. Room closure must be confirmed before finalizing notes.")}
      >
        <div className="actions">
          <Button variant="secondary" onClick={() => setConfirmEnd(false)}>
            {w("Keep consultation open")}
          </Button>
          <Button variant="danger" onClick={() => void end()}>
            {t("endConsultation")}
          </Button>
        </div>
      </Dialog>
    </section>
  );
}
