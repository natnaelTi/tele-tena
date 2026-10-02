import { Link } from "react-router-dom";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  ShieldCheck,
} from "lucide-react";
import { Card, StatusBadge } from "./ui";
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
  return (
    <Card className="clinician-card">
      <div className="clinician-identity">
        <div className="avatar">
          {offer.display_name.slice(0, 1).toUpperCase()}
        </div>
        <div>
          <h3>{offer.display_name}</h3>
          <span className="verified">
            <CheckCircle2 size={16} />
            Approved for this service
          </span>
        </div>
      </div>
      <h4>{offer.label}</h4>
      <p className="supporting">
        <Clock3 size={16} />
        {offer.minutes} minutes · Online consultation
      </p>
      <div className="card-bottom">
        <div>
          <strong>ETB {money(offer.price)}</strong>
            <span className="supporting">per session</span>
        </div>
        <Link className="button secondary" to={"/patient/book/" + offer.id}>
          Choose a time
          <ArrowRight size={18} />
        </Link>
      </div>
    </Card>
  );
}
export function AppointmentCard({
  appointment,
  base,
}: {
  appointment: Appointment;
  base: string;
}) {
  const elapsed = new Date(appointment.end).getTime() < Date.now();
  const stateLabel = appointment.state === "Booked" ? elapsed ? "Past · outcome not recorded" : "Upcoming" : appointment.state === "PendingConfirmation" ? "Needs confirmation" : appointment.state;
  return (
    <Card className="appointment-card">
      <div className="appointment-icon">
        <CalendarDays size={24} />
      </div>
      <div className="appointment-details">
        <StatusBadge tone={appointment.state === "Cancelled" || appointment.state === "Expired" ? "danger" : appointment.state === "PendingConfirmation" ? "warning" : appointment.state === "Completed" ? "success" : "neutral"}>{stateLabel}</StatusBadge>
        {appointment.call_state === "Ended" && <StatusBadge tone="neutral">Call ended</StatusBadge>}
        {appointment.call_state === "Ended" && appointment.documentation_state !== "Finalized" && <StatusBadge tone="warning">Notes pending</StatusBadge>}
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
        View consultation
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
}: {
  offer: Offer;
  start?: string;
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
              {date(new Date(start).toISOString(), offer.schedule_timezone || timezone)}
              <br />
              {timezone}
            </dd>
          </>
        )}
      </dl>
      <Link to="/patient/payments">View balance</Link>
    </aside>
  );
}
