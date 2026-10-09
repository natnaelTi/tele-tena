import { careSearchScore } from "../care-search";
import { AddFundsDialog } from "../components/AddFundsDialog";
import { BookingReview } from "../components/BookingReview";
import { appointmentGroups, appointmentsForView, type AppointmentView } from "../appointment-groups";
import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowRight, Search } from "lucide-react";
import "./PatientJourney.css";
import { WalletSummary } from "../components/WalletSummary";
import { BookingCalendar } from "../components/BookingCalendar";
import { pendingCareQuery, rememberCareQuery, discoveryFilters, rememberDiscoveryFilters } from "../care-intent";
import { journeyApi } from "../journey-api";
import type { Disclosure, Offer } from "../journey-api";
import {
  AppointmentCard,
  ClinicianCard,
  DisclosurePreview,
  PageTitle,
  date,
  money,
  timezone,
} from "../components/Domain";
import {
  Button,
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
  const upcoming = appointments.data?.filter(a => a.state === "Booked" && a.call_state !== "Ended" && new Date(a.end).getTime() > now)
    .sort((a,b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  return (
    <>
      <PageTitle
        title={w("Your care, in one place.")}
        description={`${w("Welcome")}, ${session?.profile?.display_name || w("there")}.`}
      />
      <div className="patient-dashboard-layout"><section className="patient-dashboard-primary">
      <section className="patient-home-hero"><h2>{w("A little space")}<br />{w("for yourself.")}</h2><p>{w("Find the right support for today.")}</p>
      <section className="care-search patient-home-search">
        <h3 className="sr-only">{w("What would you like help with?")}</h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            rememberCareQuery(query);
            navigate("/patient/discovery");
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
      </section></section>
      <section className="request-entry"><div><h2>{w("Let clinicians respond to you")}</h2><p>{w("Share what support you’re looking for and compare private offers from eligible clinicians.")}</p></div><Link className="button secondary" to="/patient/requests" state={{requestDraft:{request_text:query}}}>{w("Post a request")}</Link></section>
      {!!requests.data?.some((item:any)=>item.state==='Open')&&<section className="active-request-summary"><div className="section-line"><h2>Active care requests</h2><Link to="/patient/requests">Review requests and offers <ArrowRight size={16}/></Link></div>{requests.data.filter((item:any)=>item.state==='Open').slice(0,3).map((item:any)=><Link className="active-request-row" key={item.id} to={'/patient/requests/'+encodeURIComponent(item.id)}><span>{item.urgency==='immediate'?'As soon as possible':'Schedule for later'} · {item.category}</span><strong>{item.offers.filter((offer:any)=>offer.state==='Active').length} new offers</strong></Link>)}</section>}
      <section className="patient-dashboard-panel">
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
      ) : upcoming?.length ? (
        <AppointmentCard
          appointment={
            upcoming[0]
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
      </section><section className="patient-dashboard-panel">
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
      </section></section><aside className="patient-dashboard-aside">{wallet.data ? <WalletSummary available={wallet.data.available} reserved={wallet.data.reserved} /> : wallet.error ? <InlineNotice tone="danger">{w("Balance unavailable.")} <Button variant="secondary" onClick={() => void wallet.refresh()}>{w("Try again")}</Button></InlineNotice> : <Skeleton />}<section className="patient-dashboard-panel"><h2>{w("Your care record")}</h2><p>{w("Shared summaries are available inside your completed consultations.")}</p><Link className="text-link" to="/patient/appointments">{w("View appointments")} <ArrowRight size={16} /></Link></section></aside></div>
    </>
  );
}
export function Discovery() {
  const routeLocation=useLocation();
  const navigate = useNavigate();
  const { w } = useLocale();
  const offers = useResource(journeyApi.discover);
  const services = useResource(journeyApi.services);
  const [category, setCategory] = useState(discoveryFilters().category);
  const [languageFilter, setLanguageFilter] = useState(discoveryFilters().language);
  const [formatFilter, setFormatFilter] = useState(discoveryFilters().format);
  const [availabilityFilter, setAvailabilityFilter] = useState(discoveryFilters().availability);
  const [availableOfferIds, setAvailableOfferIds] = useState<Set<string> | null>(null);
  const [availabilityError, setAvailabilityError] = useState(false);
  const [query, setQuery] = useState(
    pendingCareQuery(),
  );
  useEffect(() => {
    // Retire legacy care-query URLs without retaining their text in history.
    if (new URLSearchParams(routeLocation.search).has("q")) {
      navigate(routeLocation.pathname, { replace: true });
    }
  }, [routeLocation.pathname, routeLocation.search, navigate]);
  useEffect(() => {
    rememberCareQuery(query);
  }, [query]);
  useEffect(() => {
    if (availabilityFilter !== "next14" || !offers.data) return;
    let active = true;
    const checkAvailability = async () => {
      const today = new Date();
      const fromDate = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
      const zone = Intl.DateTimeFormat().resolvedOptions().timeZone || "Africa/Addis_Ababa";
      const available = new Set<string>();
      try {
        for (let offset=0; offset<offers.data!.length; offset+=5) {
          const batch = offers.data!.slice(offset, offset+5);
          const results = await Promise.all(batch.map(async offer => {
            const calendar = await journeyApi.calendar(offer.id, fromDate, zone, 14);
            return {id:offer.id, hasOpenSlot:calendar.days.some(day=>day.slots.length>0)};
          }));
          results.filter(result=>result.hasOpenSlot).forEach(result=>available.add(result.id));
        }
        if (active) setAvailableOfferIds(available);
      } catch {
        if (active) {
          setAvailabilityError(true);
        }
      }
    };
    void checkAvailability();
    return () => { active = false; };
  }, [availabilityFilter, offers.data]);
  useEffect(() => { rememberDiscoveryFilters({ category, language: languageFilter, format: formatFilter, availability: availabilityFilter }); }, [category, languageFilter, formatFilter, availabilityFilter]);
  const availabilityBusy = availabilityFilter === "next14" && !!offers.data && !availableOfferIds && !availabilityError;
  const relevance=(offer:Offer)=>{const definition=services.data?.find(item=>item.label===offer.service_category);return careSearchScore(query,[offer.display_name,offer.label,offer.service_category||"",offer.description||"",definition?.synonyms||"",definition?.service_label_am||"",definition?.service_label_om||""]);};
  const shown = offers.data?.filter(
    (offer) =>
      (!category || offer.service_category === category) &&
      (!languageFilter || offer.care_languages?.includes(languageFilter as "en"|"am"|"om")) &&
      (!formatFilter || offer.consultation_format === formatFilter) &&
      (availabilityFilter !== "next14" || !!availableOfferIds?.has(offer.id)) &&
      relevance(offer)>0,
  )?.sort((a,b)=>relevance(b)-relevance(a));
  const requestDraft={request_text:query,service_label:category,language:languageFilter||undefined,format:formatFilter||undefined};
  return (
    <>
      <PageTitle
        eyebrow="FIND CARE"
        title={w("What’s on your mind?")}
        description={w("You don’t need the right words. Start with what you’re feeling.")}
      />
      <div className="discovery-layout"><section className="discovery-primary">
      <form className="discovery-search" onSubmit={event => { event.preventDefault(); rememberCareQuery(query); }}><Search size={20} /><label className="sr-only" htmlFor="discovery-care-query">Clinician or service</label><input id="discovery-care-query" placeholder={w("Search available care")} value={query} onChange={event => setQuery(event.target.value)} /><Button type="submit">{w("Search")}</Button></form>
      <section className="request-entry"><div><h2>{w("Let clinicians respond to you")}</h2><p>{w("Post for free and compare private offers without changing your filters.")}</p></div><Link className="text-link" to="/patient/requests" state={{requestDraft}}>{w("Post a request")} <ArrowRight size={16} /></Link></section>
      <div className="discovery-filters">
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
        <Select label={w("Care language")} value={languageFilter} onChange={e=>setLanguageFilter(e.target.value)}>
          <option value="">{w("Any language")}</option><option value="en">English</option><option value="am">አማርኛ</option><option value="om">Afaan Oromo</option>
        </Select>
        <Select label={w("Session format")} value={formatFilter} onChange={e=>setFormatFilter(e.target.value)}>
          <option value="">{w("Any format")}</option><option value="video">{w("Video")}</option><option value="audio">{w("Audio")}</option>
        </Select>
        <Select label={w("Availability")} value={availabilityFilter} onChange={e=>{setAvailabilityFilter(e.target.value);setAvailableOfferIds(null);setAvailabilityError(false);}}>
          <option value="">{w("Any date")}</option><option value="next14">{w("Open times in the next 14 days")}</option>
        </Select>
      </div>

      <p className="supporting">
        {w("Filter approved services by care language, format and currently open times.")} · {w("Times shown in")} {timezone}.
      </p>
      {availabilityError&&<InlineNotice tone="danger">{w("Available times could not be checked. Clear this filter or try again.")}</InlineNotice>}
      {offers.error ? (
        <InlineNotice tone="danger">
          Care options could not be loaded.{" "}
          <Button onClick={() => void offers.refresh()}>Try again</Button>
        </InlineNotice>
      ) : !offers.data ? (
        <Skeleton />
      ) : availabilityError ? (
        <InlineNotice tone="danger">{w("Available times could not be checked. Clear this filter or try again.")} <Button variant="secondary" onClick={() => { setAvailabilityFilter(""); setAvailableOfferIds(null); setAvailabilityError(false); }}>{w("Clear availability filter")}</Button></InlineNotice>
      ) : availabilityBusy ? (
        <p role="status" className="supporting">{w("Checking open times in the next 14 days…")}</p>
      ) : shown?.length ? (
        <div className="offering-grid">
          {shown.map((offer) => (
            <ClinicianCard key={offer.id} offer={offer} />
          ))}
        </div>
        ) : (
        <EmptyState title="No matching services yet.">
          Try another search or return when more approved offerings are
          available. <Link to="/patient/requests" state={{requestDraft}}>Post a private request</Link> without relaxing your preferences.
        </EmptyState>
      )}
      <p className="supporting">{w("Matching helps you find a professional. It is not a diagnosis.")}</p>
      </section><aside className="discovery-aside"><section className="discovery-request-aside"><h2>{w("Someone to talk to. A choice that’s yours.")}</h2><p>{w("Tell us what you need. Available clinicians can respond with a session time and a clear fee.")}</p><Link className="button" to="/patient/requests" state={{requestDraft}}>{w("Post a private request")}</Link><p className="supporting">{w("Your request is only shown to eligible clinicians.")}</p></section><p className="supporting">{w("Your name and personal details stay private until you choose to share them.")}</p></aside></div>
    </>
  );
}
export function Appointments({ base = "/patient" }: { base?: string }) {
  const {w} = useLocale();
  const resource = useResource(journeyApi.appointments);
  const clinician=base==="/clinician";
  const [search,setSearch]=useSearchParams();
  const candidate=search.get("view");
  const view:AppointmentView = ["all","upcoming","attention","completed","cancelled"].includes(candidate||"") ? candidate as AppointmentView : "upcoming";
  const setView=(next:AppointmentView)=>{const params=new URLSearchParams(search);params.set("view",next);setSearch(params,{replace:true});};
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 60000); return () => clearInterval(timer); }, []);
  const views: [AppointmentView,string][] = [["upcoming","Upcoming"],["attention",clinician?"Needs action":"Awaiting confirmation"],["completed","Completed"],["cancelled","Cancelled"],["all","All appointments"]];
  const visible = resource.data ? appointmentsForView(resource.data,view,clinician,now) : [];
  return <><PageTitle title={w("Appointments")} description={w("Upcoming care and past conversations, clearly separated.")} />
    {resource.error ? <InlineNotice tone="danger">{w("Appointments couldn’t be loaded.")} <Button onClick={()=>void resource.refresh()}>{w("Retry")}</Button></InlineNotice> : !resource.data ? <Skeleton/> : <>
      <nav className="appointment-view-switch" aria-label={w("Appointment views")}>{views.map(([value,label])=><button type="button" key={value} aria-pressed={view===value} onClick={()=>setView(value)}>{w(label)} <span>{appointmentsForView(resource.data!,value,clinician,now).length}</span></button>)}</nav>
      {visible.length ? <div className="appointment-groups">{appointmentGroups(visible,clinician,now).map(([title,rows])=><section key={title}><h2>{w(!clinician&&title==="Needs action"?"Awaiting confirmation":title)}</h2><div className="stack">{rows.map(a=><AppointmentCard key={a.id} appointment={a} base={base} view={view}/>)}</div></section>)}</div> : <EmptyState title={w(resource.data.length?"No appointments in this view.":"No appointments yet.")}><p>{w(resource.data.length?"Choose another view to find your conversations.":"Booked sessions will appear here.")}</p>{view!=="all"&&resource.data.length>0&&<Button variant="secondary" onClick={()=>setView("all")}>{w("View all appointments")}</Button>}{!clinician&&resource.data.length===0&&<Link className="button secondary" to="/patient/discovery">{w("Find care")}</Link>}</EmptyState>}
    </>}
  </>;
}

export function BookingLink() {
  const { token = "" } = useParams();
  const load = useCallback(() => journeyApi.resolveBookingLink(token), [token]);
  const resource = useResource(load);
  if (resource.error) return <InlineNotice tone="danger">This booking link is unavailable or no longer active. Find care to choose another clinician.</InlineNotice>;
  if (!resource.data) return <Skeleton />;
  return <Booking offeringOverride={resource.data.offering} bookingLinkToken={token} />;
}

export function Booking({ offeringOverride, bookingLinkToken }: { offeringOverride?: string; bookingLinkToken?: string }) {
  const { w } = useLocale();
  const route = useParams();
  const offering = offeringOverride || route.offering;
  const { session } = useSession();
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState("");
  const [calendarFrom, setCalendarFrom] = useState("");
  const [displayZone, setDisplayZone] = useState("Africa/Addis_Ababa");
  const load = useCallback(async () => {
    const all = await journeyApi.discover();
    const today = new Intl.DateTimeFormat("en-CA", { timeZone: displayZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    return {
      offer: all.find((o) => o.id === offering),
      calendar: await journeyApi.calendar(offering || "", calendarFrom || today, displayZone),
    };
  }, [offering, calendarFrom, displayZone]);
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
  const [previewError,setPreviewError]=useState(false);
  const wallet=useResource(journeyApi.wallet);
  useEffect(()=>{
    if(step!==1||!request.trim()) return;
    let active=true;
    setPreviewError(false);
    const timer=setTimeout(()=>{
      void journeyApi.preview(request,sharing).then(result=>{if(active)setPreview(result.disclosure);})
        .catch(()=>{if(active)setPreviewError(true);});
    },300);
    return()=>{active=false;clearTimeout(timer);};
  },[request,sharing,step]);
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
    <div className={step === 1 ? "booking-sharing-flow" : "reference-booking"} data-tour-unsaved={Boolean(start||request)||undefined}>
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
            <section className="booking-selection-panel"><div className="booking-selection-heading"><div className="avatar" aria-hidden="true">{offer.display_name.slice(0,1)}</div><div><span className="verified">{w("Approved for this service")}</span><h2>{offer.display_name}</h2><p>{offer.label} · {offer.minutes} {w("minutes")} · ETB {money(offer.price)}</p></div></div>
            <Select label="Show times in timezone" value={displayZone} onChange={e=>{setDisplayZone(e.target.value);setStart("");setSelectedDate("");}}><option value="Africa/Addis_Ababa">Addis Ababa (EAT)</option><option value="UTC">UTC</option><option value="Africa/Nairobi">Nairobi (EAT)</option></Select>
            <BookingCalendar days={data.calendar.days} fromDate={calendarFrom || data.calendar.days[0]?.date || new Date().toISOString().slice(0,10)} selectedDate={selectedDate} selectedStart={start} duration={offer.minutes}
              onMonth={date => { setCalendarFrom(date); setSelectedDate(""); setStart(""); }}
              onDate={date => { setSelectedDate(date); setStart(""); }} onStart={setStart} />
            </section>
            {start&&<p className="supporting">Selected: {new Date(start).toLocaleString(undefined,{dateStyle:"full",timeStyle:"short",timeZone:displayZone})} · {displayZone}</p>}
            <Button disabled={!start} onClick={() => setStep(1)}>
              Continue
            </Button>
          </>
        )}
        {step === 1 && (
          <section className="booking-sharing-panel">
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
              Include only what helps this conversation. Identifying details you type will be visible to your clinician.
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
            {request.trim()&&(previewError?<InlineNotice tone="danger">{w("The disclosure preview could not be loaded. Try Preview and continue again.")}</InlineNotice>:preview?<DisclosurePreview disclosure={preview}/>:<Skeleton/>)}
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
          </section>
        )}
        {step === 2 && preview && (
          <BookingReview offer={offer} start={start} zone={displayZone} format={data.calendar.format} disclosure={preview} balance={wallet.data} balanceError={Boolean(wallet.error)} onRetry={()=>void wallet.refresh()} busy={action.busy}
              onConfirm={() =>
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
                  const booked = await journeyApi.book({
                    ...payload,
                    ...(bookingLinkToken ? { booking_link_token: bookingLinkToken } : {}),
                    retry_key: key,
                  });
                  navigate("/patient/booked/"+booked.id);
                }, "")
              }/>
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
    </div>
  );
}
export function Payments() {
  const { w } = useLocale();
  const wallet = useResource(journeyApi.walletActivity);
  const [fundsOpen, setFundsOpen] = useState(false);
  return (
    <>
      <PageTitle
        title="Payments"
        description="Your available balance, reservations and payment activity."
      />
      <div className="patient-payments-layout"><section>
      {wallet.data && <section className="reference-wallet"><span>{w("Available to spend")}</span><strong>ETB {money(wallet.data.available)}</strong><p>{w("Reserved for appointments")} · ETB {money(wallet.data.reserved)}</p><Button variant="secondary" onClick={() => setFundsOpen(true)}>{w("Add funds")}</Button></section>}
      {wallet.error && (
        <InlineNotice tone="danger">
          Balance unavailable.{" "}
          <Button onClick={() => void wallet.refresh()}>Retry</Button>
        </InlineNotice>
      )}
      <AddFundsDialog open={fundsOpen} close={() => setFundsOpen(false)} refresh={wallet.refresh} />
      </section><section className="patient-dashboard-panel">
      {wallet.data?.activity?.length ? <section><h2>Payment activity</h2><ul className="payment-activity">{wallet.data.activity.map((item,i)=><li key={item.activity_id||i}><span>{item.kind}</span><strong>ETB {money(item.amount)}</strong><time>{date(item.created)}</time>{item.activity_id&&<Link className="text-link" to={'/patient/payments/transactions/'+encodeURIComponent(item.activity_id)}>{w('Transaction details')}</Link>}</li>)}</ul></section>:<EmptyState title="No payment activity yet." />}
      </section></div>
    </>
  );
}
