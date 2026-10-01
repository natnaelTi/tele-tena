import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { journeyApi } from "../journey-api";
import {
  AppointmentCard,
  DisclosurePreview,
  PageTitle,
  date,
  money,
  timezone,
} from "../components/Domain";
import {
  Button,
  Card,
  EmptyState,
  InlineNotice,
  Select,
  Skeleton,
  TextField,
} from "../components/ui";
import { useAction } from "../hooks/useAction";
import { useResource } from "../hooks/useResource";
type Practice = {
  application: { status: string; statement: string } | null;
  offerings: { id: string; label: string; price: number; minutes: number }[];
  availability: { start: string; end: string }[];
};
const practice = () => api<Practice>("practice");
export function ClinicianToday() {
  const [now] = useState(() => Date.now());
  const appointments = useResource(journeyApi.appointments);
  const current = useResource(practice);
  return (
    <>
      <PageTitle
        eyebrow="YOUR PRACTICE"
        title="Today"
        description={`Make space for the conversations ahead. Times in ${timezone}.`}
        action={
          <Link className="button secondary" to="/clinician/availability">
            Manage availability
          </Link>
        }
      />
      {current.data && current.data.application?.status !== "Approved" && (
        <InlineNotice>
          Your application status:{" "}
          {current.data?.application?.status || "Loading"}. Manual approval and
          service-scope approval are required before accepting bookings.
        </InlineNotice>
      )}
      <h2>Upcoming consultations</h2>
      {appointments.error ? (
        <InlineNotice tone="danger">
          Appointments couldn’t be loaded.{" "}
          <Button onClick={() => void appointments.refresh()}>Retry</Button>
        </InlineNotice>
      ) : !appointments.data ? (
        <Skeleton />
      ) : appointments.data.filter((a) => new Date(a.end).getTime() > now)
          .length ? (
        <div className="stack">
          {appointments.data
            .filter((a) => new Date(a.end).getTime() > now)
            .map((a) => (
              <AppointmentCard key={a.id} appointment={a} base="/clinician" />
            ))}
        </div>
      ) : (
        <EmptyState title="Your next conversation will appear here.">
          Review your services and availability so patients can find a suitable
          time.
        </EmptyState>
      )}
      <div className="quick-links">
        <Link to="/clinician/services">
          <h3>Services & pricing</h3>
          <p>Manage published sessions and clear prices.</p>
        </Link>
        <Link to="/clinician/care">
          <h3>Care records</h3>
          <p>See only the information shared for each appointment.</p>
        </Link>
      </div>
    </>
  );
}
export function Availability() {
  const current = useResource(practice);
  const action = useAction();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  return (
    <>
      <PageTitle
        title="Availability"
        description={`Choose the times you can meet. All times use ${timezone}.`}
      />
      <div className="two-column">
        <section>
          <h2>Add an available window</h2>
          <p>
            Choose a future start and an end within 24 hours. Allow at least
            five minutes before the start so you can finish saving.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void action.run(async () => {
                await journeyApi.addAvailability(
                  new Date(start).toISOString(),
                  new Date(end).toISOString(),
                );
                await current.refresh();
              }, "Availability saved.");
            }}
          >
            <TextField
              label="Starts"
              type="datetime-local"
              required
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
            <TextField
              label="Ends"
              type="datetime-local"
              required
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
            <Button type="submit" loading={action.busy}>
              Save availability
            </Button>
          </form>
          {action.error && (
            <InlineNotice tone="danger">{action.error}</InlineNotice>
          )}
          {action.success && (
            <InlineNotice tone="success">{action.success}</InlineNotice>
          )}
        </section>
        <section>
          <h2>Published availability</h2>
          {current.error ? (
            <InlineNotice tone="danger">
              Availability could not be loaded.
            </InlineNotice>
          ) : current.data?.availability.length ? (
            <ul className="availability-list">
              {current.data.availability.map((window, index) => (
                <li key={index}>
                  {date(window.start)}
                  <br />
                  to {date(window.end)}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No available windows yet.">
              Your saved times will appear here.
            </EmptyState>
          )}
        </section>
      </div>
    </>
  );
}
export function Services() {
  const current = useResource(practice);
  const services = useResource(journeyApi.services);
  const [service, setService] = useState("");
  const [price, setPrice] = useState("");
  const [duration, setDuration] = useState("30");
  const action = useAction();
  return (
    <>
      <PageTitle
        title="Services & pricing"
        description="Publish a fixed session duration and a clear price for an approved service."
      />
      <div className="two-column">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void action.run(async () => {
              if (!/^\d+(\.\d{1,2})?$/.test(price))
                throw new Error("Price invalid");
              const [whole, fraction = ""] = price.split(".");
              const minor = (
                BigInt(whole) * 100n +
                BigInt(fraction.padEnd(2, "0"))
              ).toString();
              await journeyApi.publish(service, minor, duration);
              await current.refresh();
            }, "Service published.");
          }}
        >
          <Select
            label="Service"
            required
            value={service}
            onChange={(e) => setService(e.target.value)}
          >
            <option value="">Choose an approved service</option>
            {services.data?.map((item) => (
              <option value={item.id} key={item.id}>
                {item.label}
              </option>
            ))}
          </Select>
          <TextField
            label="Session price (ETB)"
            inputMode="decimal"
            required
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
          <Select
            label="Session duration"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
          >
            {[15, 30, 45, 60, 90, 120].map((n) => (
              <option value={n} key={n}>
                {n} minutes
              </option>
            ))}
          </Select>
          <Button type="submit" loading={action.busy}>
            Publish offering
          </Button>
          {action.error && (
            <InlineNotice tone="danger">{action.error}</InlineNotice>
          )}
          {action.success && (
            <InlineNotice tone="success">{action.success}</InlineNotice>
          )}
        </form>
        <section>
          <h2>Your published services</h2>
          {current.data?.offerings.length ? (
            current.data.offerings.map((item) => (
              <Card key={item.id}>
                <h3>{item.label}</h3>
                <p>
                  ETB {money(item.price)} · {item.minutes} minutes
                </p>
              </Card>
            ))
          ) : (
            <EmptyState title="No offerings published.">
              Application approval alone does not authorize every service. Each
              scope needs manual approval.
            </EmptyState>
          )}
        </section>
      </div>
    </>
  );
}
export function PendingFeature({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <>
      <PageTitle title={title} />
      <EmptyState title="Not available in this demonstration yet.">
        {description}
      </EmptyState>
    </>
  );
}

export function CareRecords() {
  const appointments = useResource(journeyApi.appointments);
  return (
    <>
      <PageTitle
        title="Care records"
        description="Only the information authorized for each appointment appears here."
      />
      {appointments.error ? (
        <InlineNotice tone="danger">
          Records could not be loaded.{" "}
          <Button onClick={() => void appointments.refresh()}>Retry</Button>
        </InlineNotice>
      ) : !appointments.data ? (
        <Skeleton />
      ) : appointments.data.length ? (
        appointments.data.map((appointment) => (
          <section key={appointment.id}>
            <h2>{appointment.service_label}</h2>
            <p>
              {date(appointment.start)} · {timezone}
            </p>
            <DisclosurePreview disclosure={appointment.disclosure} />
          </section>
        ))
      ) : (
        <EmptyState title="No shared appointment information yet." />
      )}
      <p className="supporting">
        Notes, approved summaries and follow-ups are planned and are not
        available yet.
      </p>
    </>
  );
}
