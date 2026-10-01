import { useCallback, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowRight, Search } from "lucide-react";
import { api } from "../api";
import { journeyApi } from "../journey-api";
import type { Disclosure, Offer } from "../journey-api";
import {
  AppointmentCard,
  BookingSummary,
  ClinicianCard,
  DisclosurePreview,
  PageTitle,
  date,
  money,
  timezone,
} from "../components/Domain";
import {
  Button,
  Card,
  Checkbox,
  EmptyState,
  InlineNotice,
  Select,
  Skeleton,
  TextField,
} from "../components/ui";
import { useResource } from "../hooks/useResource";
import { useSession } from "../hooks/useSession";
import { useAction } from "../hooks/useAction";
export function PatientHome() {
  const [now] = useState(() => Date.now());
  const { session } = useSession();
  const appointments = useResource(journeyApi.appointments);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  return (
    <>
      <PageTitle
        eyebrow="YOUR SPACE FOR CARE"
        title={`Welcome, ${session?.profile?.display_name || "there"}.`}
        description="You don’t have to figure everything out at once."
      />
      <section className="care-search">
        <h2>What would you like help with?</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            navigate("/patient/discovery?q=" + encodeURIComponent(query));
          }}
        >
          <TextField
            label="Search available support"
            placeholder="Try a service or clinician’s name"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Button type="submit">
            <Search size={20} />
            Find care
          </Button>
        </form>
      </section>
      <div className="section-line">
        <h2>Your next appointment</h2>
        <Link to="/patient/appointments">
          View all <ArrowRight size={16} />
        </Link>
      </div>
      {appointments.error ? (
        <InlineNotice tone="danger">
          Appointments could not be loaded.{" "}
          <Button onClick={() => void appointments.refresh()}>Retry</Button>
        </InlineNotice>
      ) : !appointments.data ? (
        <Skeleton />
      ) : appointments.data.filter((a) => new Date(a.end).getTime() > now)
          .length ? (
        <AppointmentCard
          appointment={
            appointments.data.filter((a) => new Date(a.end).getTime() > now)[0]
          }
          base="/patient"
        />
      ) : (
        <EmptyState
          title="A conversation starts with a choice."
          action={
            <Link className="button secondary" to="/patient/discovery">
              Explore available clinicians
            </Link>
          }
        >
          When you book a session, its details will appear here.
        </EmptyState>
      )}
      <div className="section-line">
        <h2>People you’ve spoken with</h2>
      </div>
      <p className="supporting">
        Your past appointments are available in Appointments. A dedicated
        previous-clinician view is planned.
      </p>
    </>
  );
}
export function Discovery() {
  const offers = useResource(journeyApi.discover);
  const services = useResource(journeyApi.services);
  const [category, setCategory] = useState("");
  const [query, setQuery] = useState(
    new URLSearchParams(location.search).get("q") || "",
  );
  const shown = offers.data?.filter(
    (offer) =>
      (!category || offer.label === category) &&
      `${offer.display_name} ${offer.label}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <>
      <PageTitle
        eyebrow="FIND CARE"
        title="Find the right conversation for you."
        description="Choose an approved service, a clear price and a time that works."
      />
      <div className="filter-row">
        <TextField
          label="Clinician or service"
          placeholder="Search available care"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Select
          label="Service"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All services</option>
          {services.data?.map((service) => (
            <option key={service.id}>{service.label}</option>
          ))}
        </Select>
      </div>
      <p className="supporting">
        Online sessions · Times shown in {timezone}. Language and format filters
        will appear when verified clinician details are available.
      </p>
      {offers.error ? (
        <InlineNotice tone="danger">
          Care options could not be loaded.{" "}
          <Button onClick={() => void offers.refresh()}>Try again</Button>
        </InlineNotice>
      ) : !offers.data ? (
        <Skeleton />
      ) : shown?.length ? (
        <div className="offering-grid">
          {shown.map((offer) => (
            <ClinicianCard key={offer.id} offer={offer} />
          ))}
        </div>
      ) : (
        <EmptyState title="No matching services yet.">
          Try another search or return when more approved offerings are
          available.
        </EmptyState>
      )}
      <p className="verification-note">
        “Approved for this service” means the application and service scope have
        been manually approved. This demo uses synthetic clinician details.
      </p>
    </>
  );
}
export function Appointments({ base = "/patient" }: { base?: string }) {
  const resource = useResource(journeyApi.appointments);
  return (
    <>
      <PageTitle
        title="Appointments"
        description={`Your booked conversations, in ${timezone}.`}
      />
      {resource.error ? (
        <InlineNotice tone="danger">
          Appointments couldn’t be loaded.{" "}
          <Button onClick={() => void resource.refresh()}>Retry</Button>
        </InlineNotice>
      ) : !resource.data ? (
        <Skeleton />
      ) : resource.data.length ? (
        <div className="stack">
          {resource.data.map((a) => (
            <AppointmentCard key={a.id} appointment={a} base={base} />
          ))}
        </div>
      ) : (
        <EmptyState title="No appointments yet.">
          Booked sessions will appear here.
        </EmptyState>
      )}
    </>
  );
}
export function Booking() {
  const { offering } = useParams();
  const { session } = useSession();
  const navigate = useNavigate();
  const load = useCallback(async () => {
    const all = await journeyApi.discover();
    return {
      offer: all.find((o) => o.id === offering),
      times: await journeyApi.windows(offering || ""),
    };
  }, [offering]);
  const { data, error } = useResource(load);
  const action = useAction();
  const [step, setStep] = useState(0);
  const [start, setStart] = useState("");
  const [request, setRequest] = useState("");
  const [sharing, setSharing] = useState({
    name: !!session?.profile?.share_name,
    history: !!session?.profile?.share_history,
  });
  const [preview, setPreview] = useState<Disclosure | null>(null);
  const [submission, setSubmission] = useState<{
    key: string;
    fingerprint: string;
  } | null>(null);
  if (error)
    return (
      <InlineNotice tone="danger">
        This offering is unavailable. Return to Find care and choose another.
      </InlineNotice>
    );
  if (!data) return <Skeleton />;
  if (!data.offer)
    return <EmptyState title="This service is no longer available." />;
  const offer: Offer = data.offer;
  return (
    <div className="booking-layout">
      <section className="guided-content">
        <Link className="text-link" to="/patient/discovery">
          Back to Find care
        </Link>
        <PageTitle
          eyebrow={`BOOK A SESSION · STEP ${step + 1} OF 3`}
          title={
            ["Choose a time", "What you’ll share", "Review your session"][step]
          }
        />
        {action.error && (
          <InlineNotice tone="danger">
            {action.error} Retry with the same details after a connection
            failure.
          </InlineNotice>
        )}
        {step === 0 && (
          <>
            <p>
              Available windows in <strong>{timezone}</strong>. Allow{" "}
              {offer.minutes} minutes for your session.
            </p>
            {data.times.windows.length ? (
              <ul className="availability-list">
                {data.times.windows.map((window, i) => (
                  <li key={i}>
                    {date(window.start)} — {date(window.end)}
                  </li>
                ))}
              </ul>
            ) : (
              <InlineNotice>
                No available times have been published.
              </InlineNotice>
            )}
            {data.times.busy.length > 0 && (
              <details>
                <summary>Already booked times</summary>
                {data.times.busy.map((window, i) => (
                  <p key={i}>
                    {date(window.start)} — {date(window.end)}
                  </p>
                ))}
              </details>
            )}
            <TextField
              label="Session starts"
              type="datetime-local"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              required
            />
            <Button disabled={!start} onClick={() => setStep(1)}>
              Continue
            </Button>
          </>
        )}
        {step === 1 && (
          <>
            <label className="field">
              What would you like to talk about?
              <textarea
                rows={4}
                maxLength={2000}
                value={request}
                onChange={(e) => {
                  setRequest(e.target.value);
                  setPreview(null);
                }}
              />
            </label>
            <p className="supporting">
              Include only what helps this conversation. Use synthetic
              information in this demo.
            </p>
            <Checkbox
              label="Share my preferred name"
              checked={sharing.name}
              onChange={(e) => {
                setSharing({ ...sharing, name: e.target.checked });
                setPreview(null);
              }}
            />
            <Checkbox
              label="Share my saved history"
              checked={sharing.history}
              onChange={(e) => {
                setSharing({ ...sharing, history: e.target.checked });
                setPreview(null);
              }}
            />
            <p className="supporting">
              These choices apply to this booking. Your profile defaults stay
              the same.
            </p>
            <Button
              loading={action.busy}
              disabled={!request.trim()}
              onClick={() =>
                void action.run(async () => {
                  const result = await journeyApi.preview(request, sharing);
                  setPreview(result.disclosure);
                  setStep(2);
                }, "")
              }
            >
              Preview and continue
            </Button>
          </>
        )}
        {step === 2 && preview && (
          <>
            <DisclosurePreview disclosure={preview} />
            <p>
              ETB {money(offer.price)} will be reserved from your simulated
              balance. No real payment is taken. Cancellation and refund
              workflows are not yet available.
            </p>
            <Button
              loading={action.busy}
              onClick={() =>
                void action.run(async () => {
                  const payload = {
                    offering: offer.id,
                    start: new Date(start).toISOString(),
                    request_text: request,
                    sharing,
                    expected_price: offer.price,
                    expected_minutes: offer.minutes,
                    expected_disclosure: preview,
                  };
                  const fingerprint = JSON.stringify(payload);
                  const key =
                    submission?.fingerprint === fingerprint
                      ? submission.key
                      : crypto.randomUUID();
                  setSubmission({ key, fingerprint });
                  await journeyApi.book({ ...payload, retry_key: key });
                  navigate("/patient/appointments");
                }, "")
              }
            >
              Confirm session · ETB {money(offer.price)}
            </Button>
          </>
        )}
        {step > 0 && (
          <Button
            variant="quiet"
            disabled={action.busy}
            onClick={() => setStep(step - 1)}
          >
            Back
          </Button>
        )}
      </section>
      <BookingSummary offer={offer} start={start} />
    </div>
  );
}
export function Payments() {
  const wallet = useResource(journeyApi.wallet);
  const action = useAction();
  const [retryKey, setRetryKey] = useState(() => crypto.randomUUID());
  return (
    <>
      <PageTitle
        title="Payments"
        description="A clear view of your simulated balance."
      />
      <InlineNotice>
        This is a demonstration. You cannot add or withdraw real money.
      </InlineNotice>
      {wallet.data && (
        <div className="balance-grid">
          <Card>
            <p>Simulated balance · available</p>
            <h2>ETB {money(wallet.data.available)}</h2>
          </Card>
          <Card>
            <p>Reserved for appointments</p>
            <h2>ETB {money(wallet.data.reserved)}</h2>
          </Card>
        </div>
      )}
      {wallet.error && (
        <InlineNotice tone="danger">
          Balance unavailable.{" "}
          <Button onClick={() => void wallet.refresh()}>Retry</Button>
        </InlineNotice>
      )}
      {action.error && (
        <InlineNotice tone="danger">{action.error}</InlineNotice>
      )}
      <Button
        loading={action.busy}
        onClick={() =>
          void action.run(async () => {
            await api(
              "simulated_deposit",
              { amount: 10000, retry_key: retryKey },
              true,
            );
            setRetryKey(crypto.randomUUID());
            await wallet.refresh();
          }, "ETB 100 added to your simulated balance.")
        }
      >
        Add simulated ETB 100
      </Button>
      {action.success && (
        <InlineNotice tone="success">{action.success}</InlineNotice>
      )}
      <p className="supporting">
        This simulation transaction log is not the planned double-entry
        accounting subledger or ERPNext integration.
      </p>
    </>
  );
}
