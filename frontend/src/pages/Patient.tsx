import { useCallback, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
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
import { useLocale } from "../hooks/useLocale";
export function PatientHome() {
  const { w } = useLocale();
  const [now] = useState(() => Date.now());
  const { session } = useSession();
  const appointments = useResource(journeyApi.appointments);
  const wallet = useResource(journeyApi.wallet);
  const requests = useResource(journeyApi.myRequests);
  const previousClinicians = useResource(journeyApi.previousClinicians);
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
      <section className="request-entry"><div><h2>{w("Let clinicians respond to you")}</h2><p>{w("Share what support you’re looking for and compare private offers from eligible clinicians.")}</p></div><Link className="button secondary" to="/patient/requests" state={{requestDraft:{request_text:query}}}>{w("Post a request")}</Link></section>
      {!!requests.data?.some((item:any)=>item.state==='Open')&&<section className="active-request-summary"><div className="section-line"><h2>Active care requests</h2><Link to="/patient/requests">Review requests and offers <ArrowRight size={16}/></Link></div>{requests.data.filter((item:any)=>item.state==='Open').slice(0,3).map((item:any)=><Link className="active-request-row" key={item.id} to={'/patient/requests/'+encodeURIComponent(item.id)}><span>{item.urgency==='immediate'?'As soon as possible':'Schedule for later'} · {item.category}</span><strong>{item.offers.filter((offer:any)=>offer.state==='Active').length} new offers</strong></Link>)}</section>}
      {wallet.data&&<Link to="/patient/payments" className="balance-summary"><span>Balance</span><strong>ETB {money(wallet.data.available)}</strong><small>Available · ETB {money(wallet.data.reserved)} reserved</small></Link>}
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
      ) : appointments.data.filter((a) => a.state==="Booked" && a.call_state!=="Ended" && new Date(a.end).getTime() > now)
          .length ? (
        <AppointmentCard
          appointment={
            appointments.data.filter((a) => a.state==="Booked" && a.call_state!=="Ended" && new Date(a.end).getTime() > now)[0]
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
        <h2>{w("People you’ve spoken with")}</h2>
        <Link to="/patient/appointments">{w("Appointments")} <ArrowRight size={16} /></Link>
      </div>
      {previousClinicians.error ? (
        <InlineNotice tone="danger">{w("Your previous clinicians could not be loaded.")} <Button onClick={() => void previousClinicians.refresh()}>{w("Try again")}</Button></InlineNotice>
      ) : !previousClinicians.data ? (
        <Skeleton />
      ) : previousClinicians.data.length ? (
        <div className="previous-clinician-list">
          {previousClinicians.data.map((clinician) => (
            <article className="previous-clinician-row" key={clinician.clinician_id}>
              <div className="avatar" aria-hidden="true">{clinician.display_name.slice(0, 1).toUpperCase()}</div>
              <div className="previous-clinician-copy">
                <h3>{clinician.display_name}</h3>
                <p className="supporting">{w("Last session")} {date(clinician.last_consultation)} · {clinician.completed_sessions} {w(clinician.completed_sessions === 1 ? "completed session" : "completed sessions")}</p>
              </div>
              <Link className="button secondary" to={`/patient/clinicians/${encodeURIComponent(clinician.clinician_id)}`}>{w("View profile")} <ArrowRight size={16} /></Link>
            </article>
          ))}
        </div>
      ) : (
        <p className="supporting">{w("Clinicians you have completed a consultation with will appear here when they have current approved services available.")}</p>
      )}
    </>
  );
}
export function Discovery() {
  const routeLocation=useLocation();
  const { w } = useLocale();
  const offers = useResource(journeyApi.discover);
  const services = useResource(journeyApi.services);
  const [category, setCategory] = useState("");
  const [query, setQuery] = useState(
    (routeLocation.state as {careQuery?:string}|null)?.careQuery || new URLSearchParams(location.search).get("q") || "",
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
      <section className="request-entry"><div><h2>{w("Let clinicians respond to you")}</h2><p>{w("Post for free and compare private offers without changing your filters.")}</p></div><Link to="/patient/requests" state={{requestDraft:{request_text:query,service_label:category}}}>{w("Post a request")}</Link></section>
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
          available. <Link to="/patient/requests" state={{requestDraft:{request_text:query,service_label:category}}}>Post a private request</Link> without relaxing your preferences.
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
  const clinician=base==="/clinician";
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
        <div className="appointment-groups">{([
          ["Needs action", resource.data.filter(a=>a.state==="PendingConfirmation" || (clinician && a.call_state==="Ended" && a.documentation_state!=="Finalized"))],
          ["In progress", resource.data.filter(a=>a.call_state==="Open")],
          ["Upcoming", resource.data.filter(a=>a.state==="Booked" && a.call_state!=="Open" && a.call_state!=="Ended" && new Date(a.start).getTime()>=Date.now())],
          ["Past", resource.data.filter(a=>["Completed","Cancelled","Expired","NoShow"].includes(a.state) || a.call_state==="Ended" || (a.state==="Booked" && new Date(a.end).getTime()<Date.now()))],
        ] as [string,typeof resource.data][]).filter(([,rows])=>rows.length).map(([title,rows])=><section key={title}><h2>{title}</h2><div className="stack">{rows.map(a=><AppointmentCard key={a.id} appointment={a} base={base} />)}</div></section>)}</div>
      ) : (
        <EmptyState title="No appointments yet.">
          Booked sessions will appear here.
        </EmptyState>
      )}
    </>
  );
}
export function BookingLink() {
  const { token = "" } = useParams();
  const load = useCallback(() => journeyApi.resolveBookingLink(token), [token]);
  const resource = useResource(load);
  if (resource.error) return <InlineNotice tone="danger">This booking link is unavailable or no longer active. Find care to choose another clinician.</InlineNotice>;
  if (!resource.data) return <Skeleton />;
  return <Booking offeringOverride={resource.data.offering} />;
}

export function Booking({ offeringOverride }: { offeringOverride?: string }) {
  const route = useParams();
  const offering = offeringOverride || route.offering;
  const { session } = useSession();
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState("");
  const [displayZone, setDisplayZone] = useState("Africa/Addis_Ababa");
  const load = useCallback(async () => {
    const all = await journeyApi.discover();
    const today = new Intl.DateTimeFormat("en-CA", { timeZone: displayZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    return {
      offer: all.find((o) => o.id === offering),
      calendar: await journeyApi.calendar(offering || "", selectedDate || today, displayZone),
    };
  }, [offering, selectedDate, displayZone]);
  const { data, error, refresh } = useResource(load);
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
            {action.error} If this time is no longer open, refresh availability and choose another. <Button variant="secondary" onClick={()=>{setStart("");setStep(0);void refresh();}}>Refresh availability</Button>
          </InlineNotice>
        )}
        {step === 0 && (
          <>
            <p>Choose an open appointment time. Session length: <strong>{data.calendar.duration} minutes</strong>. Times use your selected timezone.</p>
            <Select label="Show times in timezone" value={displayZone} onChange={e=>{setDisplayZone(e.target.value);setStart("");setSelectedDate("");}}><option value="Africa/Addis_Ababa">Addis Ababa (EAT)</option><option value="UTC">UTC</option><option value="Africa/Nairobi">Nairobi (EAT)</option></Select>
            <div className="booking-dates" aria-label="Available dates">
              {data.calendar.days.filter(d=>d.slots.length).map(d=><button type="button" key={d.date} className={selectedDate===d.date?"date-chip selected":"date-chip"} onClick={()=>{setSelectedDate(d.date);setStart("");}}><strong>{new Date(d.date+"T12:00:00").toLocaleDateString(undefined,{weekday:"short",timeZone:displayZone})}</strong><span>{d.date}</span></button>)}
            </div>
            {data.calendar.days.filter(d=>d.slots.length).length===0&&<InlineNotice>No open times are available in this booking window.</InlineNotice>}
            <div className="booking-times" role="group" aria-label="Available times">
              {(data.calendar.days.find(d=>d.date===(selectedDate||data.calendar.days.find(x=>x.slots.length)?.date))?.slots||[]).map(slot=><Button key={slot.start} variant={start===slot.start?"primary":"secondary"} onClick={()=>setStart(slot.start)}>{slot.local_time}</Button>)}
            </div>
            {start&&<p className="supporting">Selected: {new Date(start).toLocaleString(undefined,{dateStyle:"full",timeStyle:"short",timeZone:displayZone})} · {displayZone}</p>}
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
              ETB {money(offer.price)} will be reserved from your balance. Under this demonstration policy, cancelling before the session starts releases the full reservation.
            </p>
            <Button
              loading={action.busy}
              onClick={() =>
                void action.run(async () => {
                  const payload = {
                    offering: offer.id,
                    start,
                    booked_timezone: displayZone,
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
  const wallet = useResource(journeyApi.walletActivity);
  const action = useAction();
  const [retryKey, setRetryKey] = useState(() => crypto.randomUUID());
  return (
    <>
      <PageTitle
        title="Payments"
        description="Your available balance, reservations and payment activity."
      />
      {wallet.data && (
        <div className="balance-grid">
          <Card>
            <p>Available balance</p>
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
          }, "ETB 100 added to your balance.")
        }
      >
        Add funds · ETB 100
      </Button>
      {action.success && (
        <InlineNotice tone="success">{action.success}</InlineNotice>
      )}
      <p className="supporting">
        This review environment records demonstration funds and reservations. No external payment or refund is processed.
      </p>
      {wallet.data?.activity?.length ? <section><h2>Payment activity</h2><ul className="payment-activity">{wallet.data.activity.map((item,i)=><li key={i}><span>{item.kind}</span><strong>ETB {money(item.amount)}</strong><time>{date(item.created)}</time></li>)}</ul></section>:<EmptyState title="No payment activity yet." />}
    </>
  );
}
