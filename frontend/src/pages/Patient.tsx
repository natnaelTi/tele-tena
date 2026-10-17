import {discoveryFilters} from '../care-intent';
import {clearReturn,returnIntent} from '../guest-intent';
import {FileSharingChoice} from '../components/EncounterFiles';
import PublicDirectory from './PublicDirectory';
import {Avatar} from "../components/ProfilePhoto";
import { PatientCareLinks } from "../components/PatientCareLinks";
import PaymentActivity from "../components/PaymentActivity";
import { AddFundsDialog } from "../components/AddFundsDialog";
import { BookingReview } from "../components/BookingReview";
import { appointmentDisplayGroups, appointmentsForView, type AppointmentView } from "../appointment-groups";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowRight, Sparkles } from "lucide-react";
import "./PatientJourney.css";
import { WalletSummary } from "../components/WalletSummary";
import { BookingCalendar } from "../components/BookingCalendar";
import { journeyApi } from "../journey-api";
import type { Disclosure, Offer } from "../journey-api";
import {
  AppointmentCard,
  HomeAppointmentPreview,
  DisclosurePreview,
  PageTitle,
  date,
  money,
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
  const query = "";
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
      <Link className="button" to="/patient/discovery">{w("Find care")} <ArrowRight size={18}/></Link></section>
      <section className="request-entry"><Sparkles size={20} aria-hidden="true" /><div><h2>{w("Let clinicians respond to you")}</h2><p>{w("Post for free and compare private offers.")}</p></div><Link className="text-link" to="/patient/requests" state={{requestDraft:{request_text:query}}}>{w("Post a request")}</Link></section>
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
        <HomeAppointmentPreview appointment={upcoming[0]} />
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
              <Avatar url={clinician.photo_url} name={clinician.display_name}/>
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
      </section></section><aside className="patient-dashboard-aside">{wallet.data ? <WalletSummary available={wallet.data.available} reserved={wallet.data.reserved} /> : wallet.error ? <InlineNotice tone="danger">{w("Balance unavailable.")} <Button variant="secondary" onClick={() => void wallet.refresh()}>{w("Try again")}</Button></InlineNotice> : <Skeleton />}<PatientCareLinks appointments={appointments.data} /></aside></div>
    </>
  );
}
export function Discovery(){return <PublicDirectory/>;}
export function Appointments({ base = "/patient" }: { base?: string }) {
  const {w,locale} = useLocale();
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
  const viewStrip = useRef<HTMLElement>(null);
  useEffect(()=>{
    const strip=viewStrip.current;
    if(!strip)return;
    const revealSelected=()=>{
      const selected=strip.querySelector<HTMLElement>('[aria-pressed="true"]');
      if(!selected)return;
      const bounds=strip.getBoundingClientRect(),target=selected.getBoundingClientRect();
      if(target.left<bounds.left||target.right>bounds.right){
        strip.scrollLeft+=target.left-bounds.left-(bounds.width-target.width)/2;
      }
    };
    revealSelected();
    const observer=new ResizeObserver(revealSelected);
    observer.observe(strip);
    return()=>observer.disconnect();
  },[view,resource.data,locale]);
  return <><PageTitle title={w(clinician?"Appointments":"Your appointments")} description={w("Upcoming care and past conversations, clearly separated.")} />
    {resource.error ? <InlineNotice tone="danger">{w("Appointments couldn’t be loaded.")} <Button onClick={()=>void resource.refresh()}>{w("Retry")}</Button></InlineNotice> : !resource.data ? <Skeleton/> : <>
      <nav ref={viewStrip} className="appointment-view-switch" aria-label={w("Appointment views")}>{views.map(([value,label])=><button type="button" key={value} aria-pressed={view===value} onClick={()=>setView(value)}>{w(label)} <span>{appointmentsForView(resource.data!,value,clinician,now).length}</span></button>)}</nav>
      {visible.length ? <div className="appointment-groups">{appointmentDisplayGroups(visible,view,clinician,now,locale).map(([title,rows])=><section key={title}><h2>{w(!clinician&&title==="Needs action"?"Awaiting confirmation":title)}</h2><div className="stack">{rows.map(a=><AppointmentCard key={a.id} appointment={a} base={base} view={view}/>)}</div></section>)}</div> : <EmptyState title={w(resource.data.length?"No appointments in this view.":"No appointments yet.")}><p>{w(resource.data.length?"Choose another view to find your conversations.":"Booked sessions will appear here.")}</p>{view!=="all"&&resource.data.length>0&&<Button variant="secondary" onClick={()=>setView("all")}>{w("View all appointments")}</Button>}{!clinician&&resource.data.length===0&&<Link className="button secondary" to="/patient/discovery">{w("Find care")}</Link>}</EmptyState>}
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
  const selectedIntent=returnIntent();
  const [careLanguage,setCareLanguage]=useState(selectedIntent?.kind==='offering'?selectedIntent.language||discoveryFilters().language:discoveryFilters().language);
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
  const [adultConsent,setAdultConsent]=useState(false);
  const [step, setStep] = useState(0);
  const [start, setStart] = useState("");
  const [request, setRequest] = useState("");
  const [sharing, setSharing] = useState({
    name: !!session?.profile?.share_name,
    history: !!session?.profile?.share_history,
    files: [] as string[],
    alias: session?.profile?.care_alias||"",
  });
  const [preview, setPreview] = useState<Disclosure | null>(null);
  const [previewError,setPreviewError]=useState(false);
  const wallet=useResource(journeyApi.wallet);
  useEffect(()=>{
    if(step!==1) return;
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
  const requiredFormat=selectedIntent?.kind==='offering'?selectedIntent.format:undefined;
  if(requiredFormat&&requiredFormat!==data.calendar.format)return <InlineNotice tone="danger">{w('Your selected consultation format is no longer available. Review your filters before continuing.')} <Link to="/care">{w('Find care')}</Link></InlineNotice>;
  const offer: Offer = data.offer;
  const selectedLanguage=careLanguage||(offer.care_languages?.length===1?offer.care_languages[0]:'');
  return (
    <div className={step === 1 ? "booking-sharing-flow" : "reference-booking"} data-tour-unsaved={Boolean(start||request)||undefined}>
      <section className="guided-content"><Select label={w("Care language")} value={selectedLanguage} onChange={event=>setCareLanguage(event.target.value)}><option value="">{w("Choose a language")}</option>{offer.care_languages?.map(value=><option key={value} value={value}>{({en:'English',am:'አማርኛ',om:'Afaan Oromo'})[value]}</option>)}</Select>
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
            <section className="booking-selection-panel"><div className="booking-selection-heading"><Avatar url={offer.photo_url} name={offer.display_name}/><div><span className="verified">{w("Approved for this service")}</span><h2>{offer.display_name}</h2><p>{offer.label} · {offer.minutes} {w("minutes")} · ETB {money(offer.price)}</p></div></div>
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
              Anything you would like your clinician to know? (optional)
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
            <TextField label={w('Alias for this appointment')} value={sharing.alias} disabled={sharing.name} onChange={event=>{setSharing({...sharing,alias:event.target.value});setPreview(null);}}/>
            <FileSharingChoice selected={sharing.files} onChange={files=>{setSharing({...sharing,files});setPreview(null);}}/>
            <p className="supporting">
              These choices apply to this booking. Your profile defaults stay
              the same.
            </p>
            {(previewError?<InlineNotice tone="danger">{w("The disclosure preview could not be loaded. Try Preview and continue again.")}</InlineNotice>:preview?<DisclosurePreview disclosure={preview}/>:<Skeleton/>)}
            <Button
              loading={action.busy}
              disabled={false}
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
        {step === 2 && preview && offer.participant_structure === 'couple' && <Card>
          <h2>{w("Invite the other adult")}</h2><p>{w("Each adult chooses what to share. One participant pays the total session price after both consent.")}</p>
          <DisclosurePreview disclosure={preview}/>
          <Checkbox label={w("I am 18 or older and freely consent to this shared consultation.")} checked={adultConsent} onChange={event=>setAdultConsent(event.target.checked)}/>
          <Button disabled={!adultConsent||action.busy} loading={action.busy} onClick={()=>void action.run(async()=>{
            const payload={offering:offer.id,start,request_text:request,sharing,expected_disclosure:preview,adult_confirmed:adultConsent,booked_timezone:displayZone};
            const fingerprint=JSON.stringify(payload);const key=submission?.fingerprint===fingerprint?submission.key:crypto.randomUUID();setSubmission({key,fingerprint});
            const result=await journeyApi.coupleInvite({...payload,retry_key:key});
            navigate('/patient/couples/'+result.id,{state:{coupleToken:result.token}});
          },'')}>{w("Create invitation link")}</Button>
          <p className="supporting">{w("The invitation does not reserve a time or charge either wallet.")}</p>
        </Card>}
        {step === 2 && preview && offer.participant_structure !== 'couple' && (
          <BookingReview offer={offer} start={start} zone={displayZone} format={data.calendar.format} disclosure={preview} balance={wallet.data} balanceError={Boolean(wallet.error)} onRetry={()=>void wallet.refresh()} busy={action.busy}
              onConfirm={() =>
                void action.run(async () => {
                  const payload = {
                    offering: offer.id,
                    start,
                    booked_timezone: displayZone,
                    care_language:selectedLanguage||undefined,expected_format:data.calendar.format,
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
                  clearReturn();navigate("/patient/booked/"+booked.id);
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
        title={w("Your balance")}
        description={w("Your funds, clearly separated.")}
      />
      <div className="patient-payments-layout"><section>
      {wallet.data && <section className="reference-wallet"><span>{w("Available to spend")}</span><strong>ETB {money(wallet.data.available)}</strong><Button variant="secondary" onClick={() => setFundsOpen(true)}>{w("Add funds")}</Button><p className="wallet-reserved-total">{w("Reserved for appointments")} · ETB {money(wallet.data.reserved)}</p></section>}
      {wallet.error && (
        <InlineNotice tone="danger">
          Balance unavailable.{" "}
          <Button onClick={() => void wallet.refresh()}>Retry</Button>
        </InlineNotice>
      )}
      <AddFundsDialog open={fundsOpen} close={() => setFundsOpen(false)} refresh={wallet.refresh} />
      </section><section className="patient-dashboard-panel">
      {wallet.data?.activity?.length ? <section><h2>{w("Recent activity")}</h2><PaymentActivity items={wallet.data.activity}/></section>:<EmptyState title="No payment activity yet." />}
      </section></div>
    </>
  );
}
