import type { CSSProperties } from "react";
import { useLocale } from "../../hooks/useLocale";

/** E08: activity comes from the existing LiveKit remote audio, never a second mic. */
export default function AudioStage({identity, service, minutes, status, activity, waiting, muted, participants}: {
  identity: string; service?: string; minutes?: number; status: string;
  activity: number; waiting: boolean; muted: boolean;
  participants?:{identity:string;label:string;activity:number;muted:boolean}[];
}) {
  const { t, w } = useLocale();
  const level = waiting || muted ? 0 : activity;
  if(participants?.length)return <div className="reference-audio-stage shared-audio-stage">
    <span className="audio-connection-badge" role="status">{w("Audio only")} · {status}</span>
    <div className="shared-audio-participants">{participants.map(person=>{const active=person.muted?0:person.activity;return <section key={person.identity}>
      <div className="reference-audio-orb" style={{"--audio-level":active} as CSSProperties} aria-label={w(active>0?"Participant speaking":"Participant is quiet")}><div className="room-audio-wave" aria-hidden="true">{Array.from({length:7},(_,index)=><i key={index}/>)}</div></div>
      <h2>{person.label}</h2><p>{person.muted?t("callRemoteMuted"):w(active>0?"Participant speaking":"Participant is quiet")}</p>
    </section>;})}</div><p>{service} · {w("Booked duration")}: {minutes} {w("minutes")}</p>
  </div>;
  return <div className="reference-audio-stage">
    <span className="audio-connection-badge" role="status">{w("Audio only")} · {status}</span>
    <div className="reference-audio-orb" style={{"--audio-level":level} as CSSProperties} aria-label={w(level > 0 ? "Participant speaking" : "Participant is quiet")}>
      <div className="room-audio-wave" aria-hidden="true">{Array.from({length:7},(_,index)=><i key={index}/>)}</div>
    </div>
    <h2>{identity}</h2><p>{service} · {w("Booked duration")}: {minutes} {w("minutes")}</p>
    <p className="audio-activity-caption">{waiting ? t("callWaiting") : muted ? t("callRemoteMuted") : w(level > 0 ? "Participant speaking" : "Participant is quiet")}</p>
  </div>;
}
