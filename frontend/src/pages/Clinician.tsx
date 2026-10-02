import { useState, useEffect, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
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
  schedules?: import("../journey-api").Schedule[];
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
      {appointments.error ? (
        <InlineNotice tone="danger">
          Appointments couldn’t be loaded.{" "}
          <Button onClick={() => void appointments.refresh()}>Retry</Button>
        </InlineNotice>
      ) : !appointments.data ? (
        <Skeleton />
      ) : appointments.data.length ? (
        <div className="appointment-groups">{([
          ["Needs action",appointments.data.filter(a=>a.state==="PendingConfirmation"||(a.call_state==="Ended"&&a.documentation_state!=="Finalized"))],
          ["In progress",appointments.data.filter(a=>a.call_state==="Open")],
          ["Upcoming",appointments.data.filter(a=>a.state==="Booked"&&a.call_state!=="Open"&&new Date(a.start).getTime()>=now)],
          ["Past",appointments.data.filter(a=>["Completed","Cancelled","Expired","NoShow"].includes(a.state)||(a.call_state==="Ended"&&a.documentation_state==="Finalized")||(a.state==="Booked"&&a.call_state!=="Ended"&&new Date(a.end).getTime()<now))],
        ] as [string,NonNullable<typeof appointments.data>][]).filter(([,items])=>items.length).map(([label,items])=><section key={label}><h2>{label}</h2><div className="stack">{items.map(a=><AppointmentCard key={a.id} appointment={a} base="/clinician" />)}</div></section>)}</div>
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
  const current = useResource(journeyApi.schedules);
  const offerings = useResource(practice);
  const action = useAction();
  const [name, setName] = useState("Weekly schedule");
  const [offering, setOffering] = useState("");
  const [zone, setZone] = useState("Africa/Addis_Ababa");
  const [format, setFormat] = useState<"video"|"audio">("video");
  const [confirmation, setConfirmation] = useState<"automatic"|"manual">("automatic");
  const [notice, setNotice] = useState("60");
  const [horizon, setHorizon] = useState("60");
  const [before, setBefore] = useState("0");
  const [after, setAfter] = useState("0");
  const [status, setStatus] = useState<"Draft"|"Published"|"Paused">("Draft");
  const [intervals, setIntervals] = useState<import("../journey-api").ScheduleInterval[]>([]);
  const [exceptions, setExceptions] = useState<import("../journey-api").ScheduleException[]>([]);
  const [copyDays, setCopyDays] = useState<number[]>([]);
  const [exceptionDate, setExceptionDate] = useState("");
  const [exceptionKind, setExceptionKind] = useState<"unavailable"|"replace"|"break">("unavailable");
  const [exceptionStart, setExceptionStart] = useState("09:00");
  const [exceptionEnd, setExceptionEnd] = useState("17:00");
  const [dirty,setDirty]=useState(false);
  const [mobileDay,setMobileDay]=useState((new Date().getDay()+6)%7);
  useEffect(() => {
    const s = current.data?.find(item=>item.offering===offering) || (!offering?current.data?.[0]:undefined);
    if (s) { setName(s.schedule_name); if(s.offering!==offering)setOffering(s.offering); setZone(s.timezone); setFormat(s.consultation_format); setConfirmation(s.confirmation_mode); setNotice(String(s.minimum_notice_minutes)); setHorizon(String(s.horizon_days)); setBefore(String(s.buffer_before)); setAfter(String(s.buffer_after)); setStatus(s.status); setIntervals(s.intervals); setExceptions(s.exceptions); }
    else if (!offering && offerings.data?.offerings[0]) setOffering(offerings.data.offerings[0].id);
    else if(offering){setName("Weekly schedule");setStatus("Draft");setIntervals([]);setExceptions([]);}
  }, [current.data, offerings.data, offering]);
  const dayNames = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
  const addInterval = (weekday:number) => setIntervals([...intervals, {weekday, start_local:"09:00", end_local:"17:00"}]);
  const editInterval = (i:number, field:"start_local"|"end_local", value:string) => setIntervals(intervals.map((x,n)=>n===i?{...x,[field]:value}:x));
  const selectedSchedule = offerings.data?.offerings.find(x=>x.id===offering);
  return (
    <>
      <PageTitle
        title="Availability"
        description="Set a weekly schedule and date exceptions. Existing appointments stay unchanged."
      />
      <div className="schedule-editor" data-tour-unsaved={dirty?"true":"false"} onChange={()=>setDirty(true)}>
        <aside className="schedule-config">
          <TextField label="Schedule name" value={name} onChange={e=>setName(e.target.value)} required />
          <Select label="Service" value={offering} onChange={e=>setOffering(e.target.value)} required>
            <option value="">Choose a published service</option>{offerings.data?.offerings.map(o=><option key={o.id} value={o.id}>{o.label} · {o.minutes} min</option>)}
          </Select>
          <TextField label="Timezone" value={zone} onChange={e=>setZone(e.target.value)} required placeholder="Africa/Addis_Ababa" />
          <Select label="Consultation format" value={format} onChange={e=>setFormat(e.target.value as "video"|"audio")}><option value="video">Video</option><option value="audio">Audio</option></Select>
          <Select label="Booking confirmation" value={confirmation} onChange={e=>setConfirmation(e.target.value as "automatic"|"manual")}><option value="automatic">Confirm automatically</option><option value="manual">Review each request</option></Select>
          <div className="schedule-number-grid"><TextField label="Notice (minutes)" type="number" min="0" value={notice} onChange={e=>setNotice(e.target.value)} /><TextField label="Book ahead (days)" type="number" min="1" value={horizon} onChange={e=>setHorizon(e.target.value)} /><TextField label="Buffer before (min)" type="number" min="0" value={before} onChange={e=>setBefore(e.target.value)} /><TextField label="Buffer after (min)" type="number" min="0" value={after} onChange={e=>setAfter(e.target.value)} /></div>
          <Select label="Patient visibility" value={status} onChange={e=>setStatus(e.target.value as "Draft"|"Published"|"Paused")}><option>Draft</option><option>Published</option><option>Paused</option></Select>
          {selectedSchedule && <p className="supporting">Preview: ETB {money(selectedSchedule.price)} · {selectedSchedule.minutes} minutes · {format}</p>}
          <Button loading={action.busy} onClick={()=>void action.run(async()=>{if(!offering) throw new Error("Choose a published service first."); await journeyApi.saveSchedule({offering,schedule_name:name,timezone_name:zone,consultation_format:format,confirmation_mode:confirmation,minimum_notice_minutes:Number(notice),horizon_days:Number(horizon),buffer_before:Number(before),buffer_after:Number(after),status,intervals,exceptions}); setDirty(false); await current.refresh();},"Schedule saved.")}>Save schedule</Button>
          {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}{action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
        </aside>
        <section className="schedule-week" aria-label="Weekly availability editor">
          <div className="schedule-week-heading"><h2>Weekly availability</h2><span>{zone}</span></div>
          <p className="supporting">Enter local times for this timezone. Ambiguous or skipped daylight-saving times are not offered.</p>
          <nav className="schedule-day-picker" aria-label="Choose day to edit">{dayNames.map((day,weekday)=><button type="button" key={day} aria-pressed={mobileDay===weekday} onClick={()=>setMobileDay(weekday)}>{day.slice(0,3)}</button>)}</nav>
          {dayNames.map((day,weekday)=>{const items=intervals.map((x,index)=>({...x,index})).filter(x=>x.weekday===weekday);return <div className={`schedule-day${mobileDay===weekday?" mobile-selected":""}`} key={day}><h3>{day}</h3><div className="schedule-intervals">{items.map(x=><div className="schedule-interval" key={x.index}><TextField label={`${day} starts`} type="time" value={x.start_local} onChange={e=>editInterval(x.index,"start_local",e.target.value)} /><span>to</span><TextField label={`${day} ends`} type="time" value={x.end_local} onChange={e=>editInterval(x.index,"end_local",e.target.value)} /><Button variant="quiet" onClick={()=>setIntervals(intervals.filter((_,n)=>n!==x.index))}>Remove</Button></div>)}<Button variant="secondary" onClick={()=>addInterval(weekday)}>Add time</Button></div></div>})}
          <div className="copy-day"><Select label="Copy Monday intervals to" multiple value={copyDays.map(String)} onChange={e=>setCopyDays(Array.from(e.target.selectedOptions).map(o=>Number(o.value)))}>{dayNames.slice(1).map((d,i)=><option key={d} value={i+1}>{d}</option>)}</Select><Button variant="secondary" onClick={()=>{const monday=intervals.filter(x=>x.weekday===0); setIntervals([...intervals.filter(x=>!copyDays.includes(x.weekday)),...copyDays.flatMap(day=>monday.map(x=>({...x,weekday:day})))]);}}>Copy Monday times</Button></div>
          <details className="schedule-exceptions"><summary>Date exceptions and breaks</summary><div className="exception-form"><TextField label="Date" type="date" value={exceptionDate} onChange={e=>setExceptionDate(e.target.value)} /><Select label="Change" value={exceptionKind} onChange={e=>setExceptionKind(e.target.value as typeof exceptionKind)}><option value="unavailable">Unavailable all day</option><option value="replace">Replace that day</option><option value="break">Break</option></Select>{exceptionKind!=="unavailable"&&<><TextField label="Starts" type="time" value={exceptionStart} onChange={e=>setExceptionStart(e.target.value)} /><TextField label="Ends" type="time" value={exceptionEnd} onChange={e=>setExceptionEnd(e.target.value)} /></>}<Button variant="secondary" disabled={!exceptionDate} onClick={()=>{setExceptions([...exceptions,{date:exceptionDate,kind:exceptionKind,start_local:exceptionKind==="unavailable"?null:exceptionStart,end_local:exceptionKind==="unavailable"?null:exceptionEnd}]);setExceptionDate("");}}>Add exception</Button></div>{exceptions.map((x,i)=><p key={i}>{x.date} · {x.kind} {x.start_local&&`${x.start_local}–${x.end_local}`} <Button variant="quiet" onClick={()=>setExceptions(exceptions.filter((_,n)=>n!==i))}>Remove</Button></p>)}</details>
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
  const [search,setSearch]=useState(""); const [service,setService]=useState(""); const [status,setStatus]=useState(""); const [page,setPage]=useState(1); const [view,setView]=useState<"table"|"cards">("table");
  const services=useResource(journeyApi.services);
  const load=useCallback(()=>journeyApi.careDirectory({search,service,status,page,page_size:20}),[search,service,status,page]);
  const appointments = useResource(load);
  return (
    <>
      <PageTitle
        title="Care records"
        description="Encounter-based records show only information shared for each appointment."
      />
      <div className="care-filters"><TextField label="Search visible patient name or alias" value={search} onChange={e=>{setSearch(e.target.value);setPage(1);}} /><Select label="Service" value={service} onChange={e=>setService(e.target.value)}><option value="">All services</option>{services.data?.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}</Select><Select label="Status" value={status} onChange={e=>setStatus(e.target.value)}><option value="">All statuses</option>{["Booked","PendingConfirmation","Completed","Cancelled","Expired","NoShow"].map(s=><option key={s} value={s}>{s}</option>)}</Select><div className="view-toggle"><Button variant={view==="table"?"primary":"secondary"} onClick={()=>setView("table")}>Table</Button><Button variant={view==="cards"?"primary":"secondary"} onClick={()=>setView("cards")}>Cards</Button></div></div>
      {appointments.error ? (
        <InlineNotice tone="danger">
          Records could not be loaded.{" "}
          <Button onClick={() => void appointments.refresh()}>Retry</Button>
        </InlineNotice>
      ) : !appointments.data ? (
        <Skeleton />
      ) : appointments.data?.rows.length ? (
        <>{view==="table"?<div className="table-scroll"><table><thead><tr><th>Patient</th><th>Last consultation</th><th>Next appointment</th><th>Care status</th><th>Action</th></tr></thead><tbody>{appointments.data.rows.map((item:any)=><tr key={item.id}><td>{item.patient_label}</td><td>{item.last_consultation?date(item.last_consultation):"No completed consultation"}</td><td>{item.next_appointment?date(item.next_appointment):"None scheduled"}</td><td>{item.state}</td><td><Link className="text-link" to={`/clinician/care/${item.id}`}>View record</Link></td></tr>)}</tbody></table></div>:<div className="offering-grid">{appointments.data.rows.map((item:any)=><Card key={item.id}><h2>{item.patient_label}</h2><p>Last consultation: {item.last_consultation?date(item.last_consultation):"None yet"}</p><p>Next appointment: {item.next_appointment?date(item.next_appointment):"None scheduled"}</p><p>{item.state}</p><Link className="button secondary" to={`/clinician/care/${item.id}`}>View record</Link></Card>)}</div>}<div className="actions"><Button variant="secondary" disabled={page<=1} onClick={()=>setPage(page-1)}>Previous</Button><span>Page {page} of {appointments.data.pages||1} · {appointments.data.total} patients/encounters</span><Button variant="secondary" disabled={page>=(appointments.data.pages||1)} onClick={()=>setPage(page+1)}>Next</Button></div></>
      ) : (
        <EmptyState title="No matching care records." />
      )}
    </>
  );
}

export function CareRecordDetail(){const {id=""}=useParams();const load=useCallback(()=>journeyApi.carePatientRecord(id),[id]);const record=useResource(load);if(record.error)return <InlineNotice tone="danger">This care record is unavailable to your account.</InlineNotice>;if(!record.data)return <Skeleton/>;return <><PageTitle title={record.data.patient_label} description="Only appointments where this clinician participated and the patient chose to share this name are grouped. Private encounters remain separate." action={<Link className="button secondary" to="/clinician/care">Back to care records</Link>}/>{record.data.encounters.map((item:any)=><Card key={item.id}><h2>{item.service}</h2><p>{date(item.start)} · {item.timezone||"Timezone unavailable"} · {item.booked_minutes} booked minutes</p><p>Status: {item.status} · Documentation: {item.documentation_state}</p><DisclosurePreview disclosure={item.disclosure}/>{item.private_note&&<section><h3>Private clinician note · only you</h3><p className="prewrap">{item.private_note.text}</p>{item.private_note.patient_summary&&<><h3>Patient summary draft</h3><p className="prewrap">{item.private_note.patient_summary}</p></>}</section>}<Link className="button secondary" to={`/clinician/consultations/${item.id}`}>Open consultation</Link></Card>)}</>}
