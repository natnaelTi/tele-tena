import { appointmentStatus } from "../appointment-status";
import { useRef, useState } from "react";
import { ClinicianPreview } from "./ClinicianPreview";
import { useLocale } from "../hooks/useLocale";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CalendarDays,
  ShieldCheck,
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
        <div className="clinician-facts"><span>{offer.care_languages?.map(language => ({ en: 'English', am: 'አማርኛ', om: 'Afaan Oromo' })[language]).join(', ') || w("Care language not listed")}</span><span>{w(offer.consultation_format === 'audio' ? 'Audio' : 'Video')}</span></div>
      </div></div>
      <div className="card-actions"><div><strong>ETB {money(offer.price)}</strong><small>{offer.minutes} {w("minutes")} · {w("per session")}</small></div><div className="actions"><Button variant="quiet" onClick={event => { trigger.current = event.currentTarget; setPreview(true); }}>{w("View profile")}</Button><Link className="button" to={"/patient/book/" + offer.id}>{w("Choose a time")}</Link></div></div>
    </Card>
    {preview && <ClinicianPreview offer={offer} close={() => { setPreview(false); requestAnimationFrame(() => trigger.current?.focus()); }} />}
  </>;
}
export function AppointmentCard({
  appointment,
  base,
}: {
  appointment: Appointment;
  base: string;
}) {
  const {w}=useLocale();
  const presentation=appointmentStatus(appointment,base.startsWith("/clinician"));
  return (
    <Card className="appointment-card">
      <div className="appointment-icon">
        <CalendarDays size={24} />
      </div>
      <div className="appointment-details">
        <StatusBadge tone={presentation.tone}>{w(presentation.label)}</StatusBadge>
        {presentation.detail&&<p className="supporting">{w(presentation.detail)}</p>}
        <h3>{appointment.service_label}</h3>
        <p>
          {date(appointment.start,appointment.timezone)} · {appointment.minutes} booked minutes
        </p>
        <p className="supporting">
          {(appointment.timezone || timezone)} · ETB {money(appointment.price)}
        </p>
      </div>
      <Link
        className="button secondary"
        to={`${base}/consultations/${appointment.id}`}
      >
        {w("View consultation")}
        <ArrowRight size={18} />
      </Link>
    </Card>
  );
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
