import type { AppointmentView } from "../appointment-groups";
import { appointmentStatus } from "../appointment-status";
import { useRef, useState } from "react";
import { ClinicianPreview } from "./ClinicianPreview";
import { useLocale } from "../hooks/useLocale";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Video,
  Headphones,
  FileText,
  ShieldCheck,
  Languages,
} from "lucide-react";
import { Button, Card, StatusBadge } from "./ui";
import type { Appointment, Disclosure, Offer } from "../journey-api";
export const money = (minor: number) =>
  `${Math.floor(minor / 100)}.${String(minor % 100).padStart(2, "0")}`;
export const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
export const date = (value: string, timeZone?: string | null) =>
  new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    ...(timeZone?{timeZone}:{}),
  });
export function PageTitle({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-title">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action}
    </div>
  );
}
export function ClinicianCard({ offer }: { offer: Offer }) {
  const { w } = useLocale();
  const [preview, setPreview] = useState(false);
  const trigger = useRef<HTMLButtonElement | null>(null);
  return <>
    <Card className="clinician-card reference-clinician-card">
      <div className="clinician-body"><div className="avatar" aria-hidden="true">{offer.display_name.slice(0, 1).toUpperCase()}</div><div className="clinician-card-copy">
        <h3>{offer.display_name}</h3><p>{offer.label}</p>
        <span className="verified"><ShieldCheck size={16} />{w("Approved for this service")}</span>
        {offer.description && <p className="clinician-description">{offer.description}</p>}
        <div className="clinician-facts"><span><Languages size={16} aria-hidden="true" />{offer.care_languages?.map(language => ({ en: 'English', am: 'አማርኛ', om: 'Afaan Oromo' })[language]).join(', ') || w("Care language not listed")}</span><span>{offer.consultation_format === 'audio' ? <Headphones size={16} aria-hidden="true" /> : <Video size={16} aria-hidden="true" />}{w(offer.consultation_format === 'audio' ? 'Audio' : 'Video')}</span></div>
      </div></div>
      <div className="card-actions"><div><strong>ETB {money(offer.price)}</strong><small>{offer.minutes} {w("minutes")} · {w("per session")}</small></div><div className="actions"><Button variant="quiet" onClick={event => { trigger.current = event.currentTarget; setPreview(true); }}>{w("View profile")}</Button><Link className="button" to={"/patient/book/" + offer.id}>{w("Choose a time")}</Link></div></div>
    </Card>
    {preview && <ClinicianPreview offer={offer} close={() => { setPreview(false); requestAnimationFrame(() => trigger.current?.focus()); }} />}
  </>;
}
/** Compact C01 upcoming-session row; status remains server-derived. */
export function HomeAppointmentPreview({ appointment }: { appointment: Appointment }) {
  const { w } = useLocale();
  const status = appointmentStatus(appointment, false);
  const href = "/patient/consultations/" + appointment.id;
  return <div className="home-appointment-preview">
    <div className="home-appointment-row"><span className="appointment-icon" aria-hidden="true">{appointment.consultation_format === "audio" ? <Headphones size={22}/> : <Video size={22}/>}</span><div><h3><Link to={href}>{appointment.display_identity || appointment.service_label}</Link></h3><p>{date(appointment.start, appointment.timezone)} · {w(appointment.consultation_format === "audio" ? "Audio" : "Video")}</p></div><StatusBadge tone={status.tone}>{w(status.label)}</StatusBadge></div>
    <div className="home-appointment-actions"><Link className="button primary" to={href}>{w("View appointment")}</Link><Link className="button secondary" to="/patient/appointments">{w("All appointments")}</Link></div>
  </div>;
}
/** F01 compact schedule row, using the same authorized snapshot/status as details. */
export function ScheduleAppointmentRow({ appointment }: { appointment: Appointment }) {
  const { w, locale } = useLocale();
  const status = appointmentStatus(appointment, true);
  const instant = new Date(appointment.start);
  const time = new Intl.DateTimeFormat(locale, {
    hour: "2-digit", minute: "2-digit", timeZone: appointment.timezone || timezone,
  }).format(instant);
  return <div className="schedule-appointment-row">
    <span className="schedule-appointment-icon" aria-hidden="true">{appointment.call_state === "Ended" ? <FileText size={20}/> : appointment.consultation_format === "audio" ? <Headphones size={20}/> : <Video size={20}/>}</span>
    <div className="schedule-appointment-copy">
      <Link to={"/clinician/consultations/" + appointment.id}>{time} · {appointment.display_identity || w("Private patient")}</Link>
      <p>{appointment.service_label} · {w(appointment.consultation_format === "audio" ? "Audio" : "Video")}</p>
      <p><time dateTime={appointment.start}>{new Intl.DateTimeFormat(locale, {month:"short",day:"numeric",timeZone:appointment.timezone || timezone}).format(instant)}</time> · {appointment.timezone || timezone}</p>
      {status.detail && <p>{w(status.detail)}</p>}
    </div>
    <StatusBadge tone={status.tone}>{w(status.label)}</StatusBadge>
  </div>;
}
export function AppointmentCard({
  appointment,
  base,
  view,
}: {
  appointment: Appointment;
  base: string;
  view?: AppointmentView;
}) {
  const {w}=useLocale();
  const presentation=appointmentStatus(appointment,base.startsWith("/clinician"));
  return <Card className="appointment-card">
    <div className="appointment-icon" aria-hidden="true">{appointment.state === "Completed" ? <FileText size={22}/> : appointment.consultation_format === "audio" ? <Headphones size={22}/> : <Video size={22}/>}</div>
    <div className="appointment-details"><h3>{appointment.display_identity || appointment.service_label}</h3><p>{appointment.service_label} · {w(appointment.consultation_format === "audio" ? "Audio" : "Video")}</p><p className="supporting">{date(appointment.start,appointment.timezone)} · {appointment.minutes} {w("booked minutes")}</p><p className="supporting">{appointment.timezone || timezone} · ETB {money(appointment.price)}</p></div>
    <div className="appointment-status-actions"><StatusBadge tone={presentation.tone}>{w(presentation.label)}</StatusBadge>{presentation.detail && <p className="supporting">{w(presentation.detail)}</p>}<Link className="button secondary" to={`${base}/consultations/${appointment.id}`} state={view?{appointmentView:view}:undefined}>{w("View consultation")}<ArrowRight size={18}/></Link></div>
  </Card>;
}
export function DisclosurePreview({ disclosure }: { disclosure: Disclosure }) {
  return (
    <section className="disclosure-preview">
      <h3>
        <ShieldCheck size={20} />
        What you’ll share
      </h3>
      <p>
        Your clinician will receive only the information shown below for this
        booking.
      </p>
      <dl className="summary-list">
        <dt>Your request</dt>
        <dd>{disclosure.request}</dd>
        <dt>Preferred name</dt>
        <dd>{disclosure.name ?? "Not shared"}</dd>
        <dt>Saved history</dt>
        <dd>{disclosure.history ?? "Not shared"}</dd>
      </dl>
    </section>
  );
}

export function BookingSummary({
  offer,
  start,
  displayTimezone,
}: {
  offer: Offer;
  start?: string;
  displayTimezone?: string;
}) {
  return (
    <aside className="booking-summary">
      <p className="eyebrow">YOUR SESSION</p>
      <h2>{offer.label}</h2>
      <p>{offer.display_name}</p>
      <dl className="summary-list">
        <dt>Duration</dt>
        <dd>{offer.minutes} minutes</dd>
        <dt>Price</dt>
        <dd>ETB {money(offer.price)}</dd>
        <dt>Payment</dt>
        <dd>Balance</dd>
        {start && (
          <>
            <dt>Time</dt>
            <dd>
              {date(new Date(start).toISOString(), displayTimezone || offer.schedule_timezone || timezone)}
              <br />
              {displayTimezone || offer.schedule_timezone || timezone}
            </dd>
          </>
        )}
      </dl>
      <Link to="/patient/payments">View balance</Link>
    </aside>
  );
}
