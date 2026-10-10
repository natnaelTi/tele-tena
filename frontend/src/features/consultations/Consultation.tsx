import { Dialog, Button } from "../../components/ui";
import { Mic, MicOff, Video, VideoOff, PhoneOff, Maximize2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import type { Room as LiveKitRoom } from "livekit-client";
import { Link } from "react-router-dom";
import { useLocale } from "../../hooks/useLocale";
import "./consultation-room.css";
import { ApiError, api } from "../../api";
import type { Key } from "../../i18n";
import ExtensionPanel from "./ExtensionPanel";
type Appointment = { id: string; display_identity?:string; call_state?:string };
type ConsultationInfo = {
  state: "Not started" | "Open" | "Ended";
  role: "patient" | "clinician";
  can_join: boolean;
  can_end: boolean;
  room_close_pending: boolean;
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
  const [mediaStatus, setMediaStatus] = useState<Key>("callNotConnected");
  const [checked, setChecked] = useState(false);
  const [audioOnly, setAudioOnly] = useState(false);
  const [muted, setMuted] = useState(false);
  const [cameraOn, setCameraOn] = useState(true);
  const [speaking, setSpeaking] = useState(false);
  const [level, setLevel] = useState(0);
  const [expanded, setExpanded] = useState(false);
  const [busy, setBusy] = useState(false);
  const mounted = useRef(false);
  const generation = useRef(0);
  const joining = useRef(false);
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
      if (!mounted.current) return;
      setInfo(next);
      if (next.state === "Ended" && (roomRef.current || previewStream.current)) {
        await leave(false);
        if (mounted.current) setMediaStatus("callDisconnected");
      }
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
    remote.current?.replaceChildren();
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
    if (selfPreview.current) selfPreview.current.srcObject = null;
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
        audio: true,
        video: !audioOnly,
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
      const connectedRoom = new Room({ adaptiveStream: true, dynacast: true });
      room = connectedRoom;
      roomRef.current = connectedRoom;
      const current = () =>
        mounted.current &&
        generation.current === attempt &&
        roomRef.current === connectedRoom;
      connectedRoom.on(RoomEvent.Reconnecting, () => {
        if (current()) setMediaStatus("callReconnecting");
      });
      connectedRoom.on(RoomEvent.Reconnected, () => {
        if (current()) setMediaStatus("callConnected");
      });
      connectedRoom.on(RoomEvent.ActiveSpeakersChanged, speakers => {
        if (!current()) return;
        const remoteSpeaker = speakers.find(participant => participant.identity !== connectedRoom.localParticipant.identity && participant.audioLevel > 0.08);
        const active = Boolean(remoteSpeaker);
        setSpeaking(active); setLevel(active ? Math.min(1, remoteSpeaker?.audioLevel || 0) : 0);
      });
      connectedRoom.on(RoomEvent.Disconnected, () => {
        if (current()) {
          roomRef.current = null;
          void disposeRoom(connectedRoom);
          setMediaStatus("callDisconnected");
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
      connectedRoom.on(RoomEvent.TrackSubscribed, () => {
        // Subscriptions can arrive before React mounts the connected stage.
        // Attach from publications, also on stage mount, rather than discarding them.
        if (current()) attachMedia();
      });
      connectedRoom.on(RoomEvent.TrackUnsubscribed, (track) =>
        track.detach().forEach((element) => element.remove()),
      );
      await connectedRoom.connect(issued.url, issued.token);
      if (!current()) {
        await disposeRoom(connectedRoom);
        return;
      }
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
      stopPreview();
      if (mounted.current && attempt === generation.current)
        setMediaStatus(error instanceof ApiError && error.code === "consultation_unavailable" ? "callServiceUnavailable" : "callConnectError");
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
    if (mounted.current) { setSpeaking(false); setLevel(0); setBusy(false); }
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
      if (mounted.current) setMediaStatus("callDisconnected");
      await refresh();
    } catch {
      // End may have committed even when Cloud closure failed. Read the
      // authoritative lifecycle rather than guessing that it ended.
      await refresh();
      if (mounted.current) setMediaStatus("callEndError");
    } finally {
      if (mounted.current) setBusy(false);
    }
  }
  async function toggleMute() {
    setBusy(true);
    try {
      const next = !muted;
      await roomRef.current?.localParticipant.setMicrophoneEnabled(!next);
      if (mounted.current) setMuted(next);
    } catch {
      if (mounted.current) setMediaStatus("callToggleError");
    } finally {
      if (mounted.current) setBusy(false);
    }
  }
  async function toggleCamera() {
    setBusy(true);
    try {
      const next = !cameraOn;
      await roomRef.current?.localParticipant.setCameraEnabled(next);
      if (mounted.current) setCameraOn(next);
    } catch {
      if (mounted.current) setMediaStatus("callToggleError");
    } finally {
      if (mounted.current) setBusy(false);
    }
  }
  async function toggleAudioOnly(){
    if(!roomRef.current)return;
    setBusy(true);
    try{
      const next=!audioOnly;
      if(!next&&audioOnly){
        // Audio-only tokens deliberately cannot publish camera tracks. Leave
        // cleanly, then return to preflight to request a camera-capable token.
        await leave(false);
        if(mounted.current){setAudioOnly(false);setMediaStatus("callDisconnected");}
        return;
      }
      if(next){await roomRef.current.localParticipant.setCameraEnabled(false);setCameraOn(false);}
      else {await roomRef.current.localParticipant.setCameraEnabled(true);setCameraOn(true);}
      if(mounted.current)setAudioOnly(next);
    }catch{if(mounted.current)setMediaStatus("callToggleError");}
    finally{if(mounted.current)setBusy(false);}
  }
  async function toggleFullscreen(){
    const node=remote.current?.closest(".consultation");
    try{if(!document.fullscreenElement&&node?.requestFullscreen)await node.requestFullscreen();else if(document.fullscreenElement)await document.exitFullscreen();else setExpanded(!expanded);}catch{setExpanded(!expanded);}
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
  const detailRoute = `/${info?.role || "patient"}/consultations/${appointment.id}`;
  return (
    <section className="consultation" aria-label={t("consultation")}>
      <h2>{info?.state === "Ended" ? t("callEnded") : connected ? t("consultation") : w("Before you join")}</h2>
      <p>
        {t("sessionLifecycle")}: {t(lifecycleStatus)}
      </p>
      <p role="status">
        {t("mediaStatus")}: {t(mediaStatus)}
      </p>
      {info?.state === "Ended" && <div className="call-ended-panel">
        <p>{info.role === "clinician" ? w("The call has ended. Review your notes and finalize the encounter.") : w("Summary being prepared")}</p>
        <Link className="button primary" to={detailRoute}>{w(info.role === "clinician" ? "Finish the consultation" : "View consultation")}</Link>
        {info.room_close_pending && <p role="alert">{t("callClosePending")}</p>}
      </div>}
      {!connected && info?.state !== "Ended" && (
        <>
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
          <button className="button"
            disabled={busy || !checked || !info?.can_join}
            onClick={() => void join()}
          >
            {t("joinCall")}
          </button>
          <button className="button secondary" type="button" disabled={busy} onClick={() => void refresh()}>
            {t("refreshCall")}
          </button>
        </>
      )}
      {connected&&<div className={`media-stage ${audioOnly?"audio-only":""} ${expanded?"expanded":""}`} data-connected={connected}>
        <div ref={node => { remote.current = node; attachMedia(); }} className={audioOnly?"call-audio-hidden":"call-remote"} aria-label={t("remoteMedia")}/>
        {audioOnly&&<div className="audio-participant"><div className={`audio-avatar ${speaking?"speaking":""}`} style={{"--audio-level":level} as CSSProperties} aria-label={w(speaking?"Participant speaking":"Participant is quiet")}><span aria-hidden="true">{(appointment.display_identity||"P").slice(0,1).toUpperCase()}</span></div><h2>{appointment.display_identity||"Private participant"}</h2><p>{mediaStatus==="callConnected"?"Connected":"Reconnecting"}</p></div>}
        {!audioOnly&&<video ref={node => { selfPreview.current = node; attachMedia(); }} autoPlay muted playsInline className="self-preview" hidden={!cameraOn} aria-label="Your camera"/>}
        <button className="fullscreen-control" type="button" onClick={()=>void toggleFullscreen()} aria-label="Expand consultation"><Maximize2 size={20}/></button>
      </div>}
      {connected && (
        <div className="call-controls">
          <button
            type="button"
            disabled={busy}
            onClick={() => void toggleMute()}
          >
            {muted ? <MicOff size={20} /> : <Mic size={20} />}
            {t(muted ? "unmute" : "mute")}
          </button>
          {!audioOnly && (
            <button
              type="button"
              disabled={busy}
              onClick={() => void toggleCamera()}
            >
              {cameraOn ? <Video size={20} /> : <VideoOff size={20} />}
              {t(cameraOn ? "cameraOff" : "cameraOn")}
            </button>
          )}
          <button type="button" disabled={busy} onClick={()=>void toggleAudioOnly()} aria-pressed={audioOnly}>{audioOnly?"Turn video on":"Audio only"}</button>
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
              onClick={() => setConfirmEnd(true)}
            >
              {t("endConsultation")}
            </button>
          )}
        </div>
      )}
      {info?.can_end && !connected && (
        <button
          className="end-call"
          type="button"
          disabled={busy}
          onClick={() => setConfirmEnd(true)}
        >
          {t("endConsultation")}
        </button>
      )}
      {info?.state === "Open" && (
        <ExtensionPanel appointment={appointment.id} role={info.role} open={true} t={t} />
      )}
      <Dialog
        open={confirmEnd}
        onOpenChange={setConfirmEnd}
        title="End for everyone?"
        description="This closes the consultation for both participants. Neither participant can rejoin after it ends."
      >
        <div className="actions">
          <Button variant="secondary" onClick={() => setConfirmEnd(false)}>
            Keep consultation open
          </Button>
          <Button variant="danger" onClick={() => void end()}>
            End for everyone
          </Button>
        </div>
      </Dialog>
    </section>
  );
}
