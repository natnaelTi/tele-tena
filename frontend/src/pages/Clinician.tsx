import { appointmentStatus } from "../appointment-status";
import { appointmentGroups } from "../appointment-groups";
import { useSession } from "../hooks/useSession";
import "./ClinicianWorkspace.css";
import { useState, useEffect, useCallback, useRef } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { journeyApi } from "../journey-api";
import {
  ScheduleAppointmentRow,
  DisclosurePreview,
  PageTitle,
  date,
  money,
  timezone,
} from "../components/Domain";
import {
  Button,
  Card,
  Dialog,
  EmptyState,
  InlineNotice,
  Select,
  Skeleton,
  StatusBadge,
  TextField,
} from "../components/ui";
import { useAction } from "../hooks/useAction";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";
type Practice = {
  application: { status: string; statement: string } | null;
  offerings: { id: string; service:string; label: string; title?:string; description?:string; price: number; minutes: number }[];
  availability: { start: string; end: string }[];
  schedules?: import("../journey-api").Schedule[];
};
const practice = () => api<Practice>("practice");
export function ClinicianToday() {
  const {w}=useLocale();
  const {session}=useSession();
  const approved=!!session?.roles.includes("Tele Tena Clinician");
  const [now,setNow]=useState(()=>Date.now());
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),60000);return()=>clearInterval(timer);},[]);
  const appointments=useResource(useCallback(()=>approved?journeyApi.appointments():Promise.resolve([]),[approved]));
  const current=useResource(practice);
  const earnings=useResource(useCallback(()=>approved?api<EarningsView>("tele_tena.accounting.clinician_earnings"):Promise.resolve(null),[approved]));
  const inbox=useResource(useCallback(()=>approved?journeyApi.clinicianRequests():Promise.resolve(null),[approved]));
  const groups=appointmentGroups(appointments.data||[],true,now).filter(([label])=>label!=="Past");
  const day=new Date(now).toLocaleDateString(undefined,{timeZone:timezone});
  const today=appointments.data?.filter(item=>new Date(item.start).toLocaleDateString(undefined,{timeZone:timezone})===day);
  if (!approved) return <>
    <PageTitle title={w("Your application")} description={w("Complete your professional profile and upload evidence for review. Approval is manual.")}/>
    <div className="clinician-today-layout"><section className="practice-panel"><h2>{w("Review progress")}</h2>
      {current.error?<InlineNotice tone="danger">{w("Practice details unavailable.")} <Button variant="secondary" onClick={()=>void current.refresh()}>{w("Retry")}</Button></InlineNotice>:!current.data?<Skeleton/>:<><p>{w("Current status")}</p><StatusBadge tone={current.data.application?.status === "Rejected" ? "danger" : "warning"}>{w(current.data.application?.status || "Not submitted")}</StatusBadge><p>{w("Approval and each service scope are reviewed by an administrator. Resume files are private application evidence; upload does not verify credentials.")}</p><Link className="button primary" to="/clinician/vetting">{w("Professional review")}</Link></>}
    </section><aside className="practice-panel"><h2>{w("Professional profile")}</h2><p>{w("Complete your professional profile and upload evidence for review. Approval is manual.")}</p><Link className="button secondary" to="/clinician/account">{w("Your account")}</Link></aside></div>
  </>;
  return <>
    <PageTitle title={w("Your day at a glance")} description={`${new Date(now).toLocaleDateString(undefined,{dateStyle:"full"})} · ${timezone}`} action={<Link className="button secondary" to="/clinician/availability">{w("Manage availability")}</Link>}/>
    <div className="practice-metrics">
      <section><span>{w("Today’s sessions")}</span><strong>{appointments.error?w("Unavailable"):today?.length??"—"}</strong><p>{w("Appointments on your calendar")}</p></section>
      <section><span>{w("Open requests")}</span><strong>{inbox.error?w("Unavailable"):inbox.data?.length??"—"}</strong><Link to="/clinician/requests">{w("View eligible requests")}</Link></section>
      <section><span>{w("Available earnings")}</span><strong>{earnings.data?`ETB ${money(earnings.data.balances.earnings_available)}`:earnings.error?w("Unavailable"):"—"}</strong><Link to="/clinician/earnings">{w("View earnings")}</Link></section>
    </div>
    <div className="clinician-today-layout"><section>
      {appointments.error?<InlineNotice tone="danger">{w("Appointments couldn’t be loaded.")} <Button onClick={()=>void appointments.refresh()}>{w("Retry")}</Button></InlineNotice>:!appointments.data?<Skeleton/>:groups.length?<div className="appointment-groups">{groups.map(([label,items])=><section key={label}><h2>{w(label === "Upcoming" ? "Up next" : label)}</h2><div>{items.slice(0,5).map(item=><ScheduleAppointmentRow key={item.id} appointment={item}/>)}</div>{items.length>5&&<Link className="text-link" to="/clinician/appointments">{w("View all appointments")}</Link>}</section>)}</div>:<EmptyState title={w("Your next conversation will appear here.")}>{w("Review your services and availability so patients can find a suitable time.")}</EmptyState>}
      <section className="practice-panel"><h2>{w("Quick actions")}</h2><div className="actions"><Link className="button" to="/clinician/requests">{w("View open requests")}</Link><Link className="button secondary" to="/clinician/availability">{w("Edit availability")}</Link><Link className="button secondary" to="/clinician/care">{w("Care records")}</Link></div></section>
    </section><aside className="practice-panel"><h2>{w("Practice readiness")}</h2>{current.error?<InlineNotice tone="danger">{w("Practice details unavailable.")}</InlineNotice>:!current.data?<Skeleton/>:<dl className="practice-readiness"><div><dt>{w("Application")}</dt><dd>{w(current.data.application?.status||"Not submitted")}</dd><Link to="/clinician/vetting">{w("Professional review")}</Link></div><div><dt>{w("Services & pricing")}</dt><dd>{current.data.offerings.length} {w("saved offerings")}</dd><Link to="/clinician/services">{w("Manage services")}</Link></div><div><dt>{w("Availability")}</dt><dd>{current.data.schedules?.filter(item=>item.status==='Published').length??0} {w("published schedules")}</dd><Link to="/clinician/availability">{w("Manage availability")}</Link></div></dl>}</aside></div>
  </>;
}
export function Availability() {
  const {w,locale}=useLocale();
  const current = useResource(journeyApi.schedules);
  const offerings = useResource(practice);
  const appointments = useResource(journeyApi.appointments);
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
  const [editingException,setEditingException]=useState<number|null>(null);
  const [copyDays, setCopyDays] = useState<number[]>([]);
  const [copySourceDay,setCopySourceDay]=useState(0);
  const [exceptionDate, setExceptionDate] = useState("");
  const [exceptionKind, setExceptionKind] = useState<"unavailable"|"replace"|"break">("unavailable");
  const [exceptionStart, setExceptionStart] = useState("09:00");
  const [exceptionEnd, setExceptionEnd] = useState("17:00");
  const [dirty,setDirty]=useState(false);
  const [mobileDay,setMobileDay]=useState((new Date().getDay()+6)%7);
  const [weekShift,setWeekShift]=useState(0);
  const [calendarEditMode,setCalendarEditMode]=useState<"weekly"|"date">("weekly");
  const [selectedInterval,setSelectedInterval]=useState<number|null>(null);
  const [timeEditorOpen,setTimeEditorOpen]=useState(()=>window.matchMedia("(max-width: 800px)").matches);
  const [timeErrors,setTimeErrors]=useState<Record<number,{start?:string;end?:string}>>({});
  const [serviceError,setServiceError]=useState("");
  const [nameError,setNameError]=useState("");
  const [availabilityError,setAvailabilityError]=useState("");
  const [bookingUrl,setBookingUrl]=useState("");
  const [bookingLinkStatus,setBookingLinkStatus]=useState("");
  const calendarScrollRef=useRef<HTMLDivElement>(null);
  useEffect(()=>{const query=window.matchMedia("(max-width: 800px)");const update=()=>setTimeEditorOpen(query.matches);query.addEventListener("change",update);return()=>query.removeEventListener("change",update);},[]);
  useEffect(() => {
    const s = current.data?.find(item=>item.offering===offering) || (!offering?current.data?.[0]:undefined);
    if (s) { setName(s.schedule_name); if(s.offering!==offering)setOffering(s.offering); setZone(s.timezone); setFormat(s.consultation_format); setConfirmation(s.confirmation_mode); setNotice(String(s.minimum_notice_minutes)); setHorizon(String(s.horizon_days)); setBefore(String(s.buffer_before)); setAfter(String(s.buffer_after)); setStatus(s.status); setIntervals(s.intervals); setExceptions(s.exceptions); }
    else if (!offering && offerings.data?.offerings[0]) setOffering(offerings.data.offerings[0].id);
    else if(offering){setName("Weekly schedule");setStatus("Draft");setIntervals([]);setExceptions([]);}
  }, [current.data, offerings.data, offering]);
  const dateLocale=locale==="am"?"am-ET":locale==="om"?"om-ET":"en-ET";
  const dayNames = Array.from({length:7},(_,weekday)=>new Intl.DateTimeFormat(dateLocale,{weekday:"long",timeZone:"UTC"}).format(new Date(Date.UTC(2024,0,1+weekday,12))));
  const addInterval = (weekday:number, start="09:00") => {const [hour,minute]=start.split(":").map(Number);const endMinutes=Math.min(23*60+59,hour*60+minute+60);const end=`${String(Math.floor(endMinutes/60)).padStart(2,"0")}:${String(endMinutes%60).padStart(2,"0")}`;setIntervals([...intervals, {weekday, start_local:start, end_local:end}]);setSelectedInterval(intervals.length);setMobileDay(weekday);setDirty(true);};
  const inspectInterval=(index:number,weekday:number)=>{setSelectedInterval(index);setMobileDay(weekday);setTimeEditorOpen(true);window.setTimeout(()=>document.querySelector<HTMLElement>(`[data-selected="true"] input[type="time"]`)?.focus(),0);};
  const editInterval = (i:number, field:"start_local"|"end_local", value:string) => {setIntervals(intervals.map((x,n)=>n===i?{...x,[field]:value}:x));setTimeErrors(errors=>({...errors,[i]:{...errors[i],[field==="start_local"?"start":"end"]:undefined}}));};
  const selectedSchedule = offerings.data?.offerings.find(x=>x.id===offering);
  function validateIntervals() {
    const errors:Record<number,{start?:string;end?:string}>={};
    const minutes=(value:string)=>/^([01]\d|2[0-3]):[0-5]\d$/.test(value)?Number(value.slice(0,2))*60+Number(value.slice(3)):null;
    intervals.forEach((item,index)=>{
      const start=minutes(item.start_local),end=minutes(item.end_local);
      if(start===null)errors[index]={...errors[index],start:"Enter a valid start time (HH:MM)."};
      if(end===null)errors[index]={...errors[index],end:"Enter a valid end time (HH:MM)."};
      if(start!==null&&end!==null&&end<=start)errors[index]={...errors[index],end:"End time must be after start time."};
    });
    for(let weekday=0;weekday<7;weekday++){
      const day=intervals.map((item,index)=>({item,index,start:minutes(item.start_local),end:minutes(item.end_local)})).filter(x=>x.item.weekday===weekday&&x.start!==null&&x.end!==null).sort((a,b)=>(a.start as number)-(b.start as number));
      day.slice(1).forEach((current,index)=>{const previous=day[index];if((current.start as number)<(previous.end as number)){errors[previous.index]={...errors[previous.index],end:"This time overlaps another interval."};errors[current.index]={...errors[current.index],start:"This time overlaps another interval."};}});
    }
    setTimeErrors(errors);
    return Object.keys(errors).length===0;
  }
  function saveSchedule() {
    setServiceError("");setNameError("");setAvailabilityError("");
    const validTimes=validateIntervals();
    if(!offering){setServiceError("Choose an approved service before saving.");return;}
    if(!name.trim()){setNameError("Enter a name for this schedule.");return;}
    if(status==="Published"&&!intervals.length&&!exceptions.some(x=>x.kind==="replace")){setAvailabilityError("Add at least one available time before publishing.");return;}
    if(!validTimes)return;
    void action.run(async()=>{await journeyApi.saveSchedule({offering,schedule_name:name,timezone_name:zone,consultation_format:format,confirmation_mode:confirmation,minimum_notice_minutes:Number(notice),horizon_days:Number(horizon),buffer_before:Number(before),buffer_after:Number(after),status,intervals,exceptions});setDirty(false);await current.refresh();},"Schedule saved.");
  }
  async function createBookingLink() {
    setBookingLinkStatus("");
    await action.run(async()=>{
      const result=await journeyApi.bookingLink(offering);
      const url=`${window.location.origin}${import.meta.env.PROD?"/teletena":""}/patient/book-link/${result.token}`;
      setBookingUrl(url);
      try { await navigator.clipboard.writeText(url); setBookingLinkStatus(w("Booking link copied.")); }
      catch { setBookingLinkStatus(w("Copy the link from the field below.")); }
    },"");
  }
  const localTodayParts = new Intl.DateTimeFormat("en-CA",{timeZone:zone,year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date());
  const localTodayValues = Object.fromEntries(localTodayParts.map(x=>[x.type,x.value]));
  const localToday = new Date(Date.UTC(Number(localTodayValues.year),Number(localTodayValues.month)-1,Number(localTodayValues.day),12));
  const weekMonday = new Date(localToday);
  weekMonday.setUTCDate(weekMonday.getUTCDate()-((weekMonday.getUTCDay()+6)%7)+weekShift*7);
  const weekDays = Array.from({length:7},(_,i)=>{const day=new Date(weekMonday);day.setUTCDate(day.getUTCDate()+i);return day;});
  const dateKey = (day:Date) => day.toISOString().slice(0,10);
  const displayDay = (day:Date) => new Intl.DateTimeFormat(dateLocale,{weekday:"short",month:"short",day:"numeric",timeZone:"UTC"}).format(day);
  const minutePosition = (value:string) => {const [h,m]=value.slice(0,5).split(":").map(Number);return h*60+m;};
  const readableZone = (()=>{try{return new Intl.DateTimeFormat(dateLocale,{timeZone:zone,timeZoneName:"long"}).formatToParts(new Date()).find(item=>item.type==="timeZoneName")?.value||zone;}catch{return zone;}})();
  useEffect(()=>{
    if(!current.data)return;
    const saved=current.data.find(item=>item.offering===offering)||current.data[0];
    const first=saved?.intervals.length?Math.min(...saved.intervals.map(item=>minutePosition(item.start_local))):8*60;
    const startHour=Math.max(0,Math.floor(first/60)-1);
    calendarScrollRef.current?.scrollTo({top:startHour*40,behavior:"instant"});
  },[current.data,offering,weekShift]);
  const visibleException = (date:string) => exceptions.map((item,index)=>({...item,index})).filter(item=>item.date===date);
  const visibleBookings = (date:string) => (appointments.data||[]).filter(item=>["Booked","PendingConfirmation"].includes(item.state)).flatMap(item=>{try{const parts=new Intl.DateTimeFormat("en-CA",{timeZone:zone,year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(new Date(item.start));const values=Object.fromEntries(parts.map(x=>[x.type,x.value]));const localDate=`${values.year}-${values.month}-${values.day}`;if(localDate!==date)return[];const startMinute=Number(values.hour)*60+Number(values.minute);const endMinute=startMinute+Number(item.minutes);return endMinute<=0||startMinute>=1440?[]:[{...item,startMinute:Math.max(0,startMinute),endMinute:Math.min(1440,endMinute)}];}catch{return[];}});
  return (
    <>
      <PageTitle
        title="Availability"
        description="Set a weekly schedule and date exceptions. Existing appointments stay unchanged."
      />
      <div className="schedule-editor" data-tour-unsaved={dirty?"true":"false"} onChange={()=>setDirty(true)}>
        <aside className="schedule-config">
          <TextField label="Schedule name" value={name} error={nameError} onChange={e=>{setName(e.target.value);setNameError("");}} required />
          <Select label="Service" value={offering} error={serviceError} onChange={e=>{e.stopPropagation();if(dirty&&!window.confirm(w("Discard unsaved schedule changes?")))return;setDirty(false);setOffering(e.target.value);setServiceError("");}} required>
            <option value="">Choose a published service</option>{offerings.data?.offerings.map(o=><option key={o.id} value={o.id}>{o.label} · {o.minutes} min</option>)}
          </Select>
          <TextField label="Timezone" value={zone} onChange={e=>setZone(e.target.value)} required placeholder="Africa/Addis_Ababa" />
          <details className="schedule-advanced"><summary>Format, confirmation and booking rules</summary>
            <Select label="Consultation format" value={format} onChange={e=>setFormat(e.target.value as "video"|"audio")}><option value="video">Video</option><option value="audio">Audio</option></Select>
            <Select label="Booking confirmation" value={confirmation} onChange={e=>setConfirmation(e.target.value as "automatic"|"manual")}><option value="automatic">Confirm automatically</option><option value="manual">Review each request</option></Select>
            <div className="schedule-number-grid"><TextField label="Notice (minutes)" type="number" min="0" value={notice} onChange={e=>setNotice(e.target.value)} /><TextField label="Book ahead (days)" type="number" min="1" value={horizon} onChange={e=>setHorizon(e.target.value)} /><TextField label="Buffer before (min)" type="number" min="0" value={before} onChange={e=>setBefore(e.target.value)} /><TextField label="Buffer after (min)" type="number" min="0" value={after} onChange={e=>setAfter(e.target.value)} /></div>
            <Select label="Patient visibility" value={status} onChange={e=>setStatus(e.target.value as "Draft"|"Published"|"Paused")}><option>Draft</option><option>Published</option><option>Paused</option></Select>
          </details>
          {selectedSchedule && <p className="supporting">Preview: ETB {money(selectedSchedule.price)} · {selectedSchedule.minutes} minutes · {format}</p>}
          {availabilityError&&<InlineNotice tone="danger">{availabilityError}</InlineNotice>}
          <Button className="schedule-config-save" loading={action.busy} disabled={action.busy||current.error||offerings.error} onClick={saveSchedule}>{w(action.busy?"Saving schedule…":"Save schedule")}</Button>
          <p className="supporting" role="status">{w(action.busy?"Saving changes…":action.success?"Schedule saved.":dirty?"Unsaved changes":current.data?.some(item=>item.offering===offering)?"Saved schedule":"Not saved yet")}</p>
          {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}{action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
          <div className="schedule-share-link"><Button variant="secondary" disabled={action.busy||dirty||status!=="Published"||!offering} onClick={()=>void createBookingLink()}>{w("Copy patient booking link")}</Button>{bookingLinkStatus&&<p className="supporting" role="status">{bookingLinkStatus}</p>}{bookingUrl&&<TextField label={w("Patient booking link")} value={bookingUrl} readOnly />}</div>
        </aside>
        <section className="schedule-week" aria-label="Weekly availability editor">
          <div className="availability-toolbar"><div className="availability-period-actions"><Button variant="secondary" onClick={()=>setWeekShift(0)}>Today</Button><Button variant="quiet" aria-label="Previous week" onClick={()=>setWeekShift(weekShift-1)}>‹</Button><Button variant="quiet" aria-label="Next week" onClick={()=>setWeekShift(weekShift+1)}>›</Button><strong>{displayDay(weekDays[0])} – {displayDay(weekDays[6])}</strong></div><span className="timezone-label">{readableZone} · {zone}</span></div>
          <div className="schedule-week-heading"><h2>{w("Weekly availability")}</h2><Select label={w("Calendar edit mode")} value={calendarEditMode} onChange={e=>setCalendarEditMode(e.target.value as "weekly"|"date")}><option value="weekly">{w("Recurring weekly")}</option><option value="date">{w("This date only")}</option></Select></div>
          <p className="supporting">{calendarEditMode==="weekly"?w("Choose a time to add a weekly interval."):w("Choose a time to prepare a date-specific replacement. Confirm it in Date exceptions before saving. Existing appointments remain unchanged.")}</p>
          <p className="supporting">Daylight-saving gaps are not offered. Existing appointments remain at their saved times.</p>
          <div className="availability-workspace">
          <div className="availability-calendar-scroll" aria-label="Weekly appointment calendar" ref={calendarScrollRef}>
            <div className={`availability-calendar-grid${calendarEditMode==="date"?" date-edit-mode":""}`} style={{gridTemplateColumns:"56px repeat(7,minmax(90px,1fr))"}}>
              <div className="calendar-corner">Local time</div>{weekDays.map((day,weekday)=><div className="calendar-day-heading" key={dateKey(day)} aria-current={dateKey(day)===dateKey(localToday)?"date":undefined}><strong>{dayNames[weekday]}</strong><span>{displayDay(day)}</span></div>)}
              <div className="calendar-ruler">{Array.from({length:24},(_,i)=><span key={i} style={{top:i*40-8}}>{String(i).padStart(2,"0")}:00</span>)}</div>
              {weekDays.map((day,weekday)=>{const key=dateKey(day);const rules=intervals.map((item,index)=>({...item,index})).filter(item=>item.weekday===weekday);return <div className="calendar-day-track" key={key} aria-label={`${dayNames[weekday]} ${key}`}>
                {Array.from({length:24},(_,hour)=><button type="button" key={hour} className="calendar-add-slot" style={{top:hour*40}} aria-label={`${calendarEditMode==="weekly"?"Add weekly availability":"Set date-specific availability"} ${dayNames[weekday]} ${key} at ${String(hour).padStart(2,"0")}:00`} title={`Add at ${String(hour).padStart(2,"0")}:00`} onClick={()=>{const start=`${String(hour).padStart(2,"0")}:00`;if(calendarEditMode==="weekly")addInterval(weekday,start);else{const endMinutes=Math.min(23*60+59,hour*60+60);setExceptionDate(key);setExceptionKind("replace");setExceptionStart(start);setExceptionEnd(`${String(Math.floor(endMinutes/60)).padStart(2,"0")}:${String(endMinutes%60).padStart(2,"0")}`);setDirty(true);}}}><span aria-hidden="true">+</span></button>)}
                {rules.map(item=>{const top=minutePosition(item.start_local)/60*40;const height=(minutePosition(item.end_local)-minutePosition(item.start_local))/60*40;return <button type="button" key={`rule-${item.index}`} className="calendar-block availability-block" style={{top,height:Math.max(24,height)}} aria-pressed={selectedInterval===item.index} aria-label={`Edit ${dayNames[weekday]} availability ${item.start_local} to ${item.end_local}`} onClick={()=>inspectInterval(item.index,weekday)}>{item.start_local}–{item.end_local}</button>;})}
                {visibleException(key).map(item=>{const start=minutePosition(item.start_local||"00:00"),end=minutePosition(item.end_local||"24:00");const top=item.kind==="unavailable"?0:Math.max(0,start/60*40);const height=item.kind==="unavailable"?960:Math.max(24,(Math.min(1440,end)-Math.max(0,start))/60*40);return <button type="button" key={`exception-${item.index}`} className={`calendar-block calendar-exception ${item.kind}`} style={{top,height}} aria-label={`Edit ${item.kind} exception on ${key}`} onClick={()=>{setExceptionDate(key);setExceptionKind(item.kind);setExceptionStart(item.start_local||"09:00");setExceptionEnd(item.end_local||"17:00");setEditingException(item.index);}}>{item.kind==="unavailable"?"Unavailable":item.kind}</button>;})}
                {visibleBookings(key).map(item=>{const blockHeight=Math.max(26,(item.endMinute-item.startMinute)/60*40);const appointmentTime=new Date(item.start).toLocaleTimeString(undefined,{hour:"2-digit",minute:"2-digit",timeZone:zone});return <div key={`booking-${item.id}`} className="calendar-block calendar-booking" style={{top:item.startMinute/60*40,height:blockHeight}} aria-label={`${item.display_identity||"Appointment"}, ${item.service_label}, ${appointmentTime}`} title={`${item.service_label} · ${appointmentTime}`}><strong>{item.display_identity||"Appointment"}</strong>{blockHeight>=36&&<span>{item.service_label} · {appointmentTime}</span>}</div>;})}
              </div>;})}
            </div>
          </div>
          {selectedInterval!==null&&intervals[selectedInterval]&&<aside className="availability-interval-editor" aria-label="Edit weekly availability interval">
            <div className="availability-editor-heading"><h3>{w("Edit weekly interval")}</h3><Button variant="quiet" aria-label={w("Close interval editor")} onClick={()=>setSelectedInterval(null)}>×</Button></div>
            <p className="supporting">{dayNames[intervals[selectedInterval].weekday]} · {w("Repeats every week")}</p>
            <TextField label={w("Interval starts")} type="time" value={intervals[selectedInterval].start_local} error={timeErrors[selectedInterval]?.start} onChange={e=>editInterval(selectedInterval,"start_local",e.target.value)} />
            <TextField label={w("Interval ends")} type="time" value={intervals[selectedInterval].end_local} error={timeErrors[selectedInterval]?.end} onChange={e=>editInterval(selectedInterval,"end_local",e.target.value)} />
            <Button variant="quiet" onClick={()=>{setIntervals(intervals.filter((_,n)=>n!==selectedInterval));setTimeErrors({});setSelectedInterval(null);setDirty(true);}}>{w("Remove interval")}</Button>
          </aside>}
          </div>
          <div className="schedule-mobile-save"><Button loading={action.busy} disabled={action.busy||current.error||offerings.error} onClick={saveSchedule}>{w(action.busy?"Saving schedule…":"Save schedule")}</Button><span role="status">{w(action.busy?"Saving changes…":action.success?"Schedule saved.":dirty?"Unsaved changes":current.data?.some(item=>item.offering===offering)?"Saved schedule":"Not saved yet")}</span></div>
          <p className="supporting">Teal blocks repeat weekly. Striped blocks are date exceptions. Dark blocks are already reserved appointments.</p>
          {appointments.error&&<InlineNotice>Existing appointments are temporarily unavailable in this calendar; they remain protected by server-side conflict checks.</InlineNotice>}
          <details className="schedule-accessible-times" open={timeEditorOpen} onToggle={e=>setTimeEditorOpen(e.currentTarget.open)}><summary>{w("Time-field editor and keyboard alternative")}</summary>
          <nav className="schedule-day-picker" aria-label="Choose day to edit">{dayNames.map((day,weekday)=><button type="button" key={day} aria-pressed={mobileDay===weekday} onClick={()=>setMobileDay(weekday)}>{day.slice(0,3)}</button>)}</nav>
          {dayNames.map((day,weekday)=>{const items=intervals.map((x,index)=>({...x,index})).filter(x=>x.weekday===weekday);return <div className={`schedule-day${mobileDay===weekday?" mobile-selected":""}`} key={day}><h3>{day}</h3><div className="schedule-intervals">{items.map(x=><div className="schedule-interval" key={x.index} data-selected={selectedInterval===x.index}><TextField label={`${day} starts`} type="time" value={x.start_local} error={timeErrors[x.index]?.start} onChange={e=>editInterval(x.index,"start_local",e.target.value)} /><span>to</span><TextField label={`${day} ends`} type="time" value={x.end_local} error={timeErrors[x.index]?.end} onChange={e=>editInterval(x.index,"end_local",e.target.value)} /><Button variant="quiet" onClick={()=>{setIntervals(intervals.filter((_,n)=>n!==x.index));setTimeErrors({});setSelectedInterval(null);setDirty(true);}}>Remove</Button></div>)}<Button variant="secondary" onClick={()=>addInterval(weekday)}>Add time</Button></div></div>})}
          </details>
          <details className="schedule-copy-controls"><summary>{w("Copy availability to other days")}</summary><div className="copy-day"><Select label="Copy intervals from" value={String(copySourceDay)} onChange={e=>{setCopySourceDay(Number(e.target.value));setCopyDays(copyDays.filter(day=>day!==Number(e.target.value)));}}>{dayNames.map((day,index)=><option key={day} value={index}>{day}</option>)}</Select><Select label="Copy to days" multiple value={copyDays.map(String)} onChange={e=>{setCopyDays(Array.from(e.target.selectedOptions).map(o=>Number(o.value)));setDirty(true);}}>{dayNames.map((day,index)=>index!==copySourceDay&&<option key={day} value={index}>{day}</option>)}</Select><Button variant="secondary" disabled={!copyDays.length} onClick={()=>{const source=intervals.filter(x=>x.weekday===copySourceDay); setIntervals([...intervals.filter(x=>!copyDays.includes(x.weekday)),...copyDays.flatMap(day=>source.map(x=>({...x,weekday:day})))]);setDirty(true);}}>Copy {dayNames[copySourceDay]} times</Button></div></details>
          <details className="schedule-exceptions" open={Boolean(exceptionDate)}><summary>{w("Date exceptions and breaks")}</summary><div className="exception-form"><TextField label="Date" type="date" value={exceptionDate} onChange={e=>setExceptionDate(e.target.value)} /><Select label="Change" value={exceptionKind} onChange={e=>setExceptionKind(e.target.value as typeof exceptionKind)}><option value="unavailable">Unavailable all day</option><option value="replace">Replace that day</option><option value="break">Break</option></Select>{exceptionKind!=="unavailable"&&<><TextField label="Starts" type="time" value={exceptionStart} onChange={e=>setExceptionStart(e.target.value)} /><TextField label="Ends" type="time" value={exceptionEnd} onChange={e=>setExceptionEnd(e.target.value)} /></>}<Button variant="secondary" disabled={!exceptionDate} onClick={()=>{const next={date:exceptionDate,kind:exceptionKind,start_local:exceptionKind==="unavailable"?null:exceptionStart,end_local:exceptionKind==="unavailable"?null:exceptionEnd};setExceptions(editingException===null?[...exceptions,next]:exceptions.map((item,index)=>index===editingException?next:item));setExceptionDate("");setEditingException(null);setDirty(true);}}>{editingException===null?"Add exception":"Update exception"}</Button>{editingException!==null&&<Button variant="quiet" onClick={()=>{setExceptionDate("");setEditingException(null);}}>Cancel edit</Button>}</div>{exceptions.map((x,i)=><p key={i}>{x.date} · {x.kind} {x.start_local&&`${x.start_local}–${x.end_local}`} <Button variant="quiet" onClick={()=>{setExceptions(exceptions.filter((_,n)=>n!==i));setDirty(true);}}>Remove</Button></p>)}</details>
        </section>
      </div>
    </>
  );
}
export { default as Services } from "./ServiceOfferings";
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

type EarningsView = {
  balances: { pending: number; earnings_available: number; payout_reserved: number };
  activity: { event_ref: string; event_type: string; kind: string; amount: number; created: string }[];
  earnings: { id: string; gross_minor: number; fee_minor: number; net_minor: number; state: string; completed_at: string | null; release_at: string | null }[];
  payouts: { id: string; amount_minor: number; state: string; created: string; cancelled_at: string | null }[];
  external_settlement: false;
};

export function ClinicianEarnings() {
  const completedSessions=useResource(journeyApi.appointments);
  const [activityFilter,setActivityFilter]=useState<"All activity"|"Pending"|"Payouts">("All activity");
  const { w } = useLocale();
  const load = useCallback(() => api<EarningsView>("tele_tena.accounting.clinician_earnings"), []);
  const resource = useResource(load);
  const action = useAction();
  const [amount, setAmount] = useState("");
  const [payoutOpen,setPayoutOpen]=useState(false);
  const [amountError,setAmountError]=useState("");
  const [retryKey, setRetryKey] = useState(() => crypto.randomUUID());
  const cancelReason = "Changed plans";
  async function request() {
    if (!/^\d+(\.\d{1,2})?$/.test(amount)) throw new Error("Enter an amount in ETB with up to two decimal places.");
    const [whole, fraction = ""] = amount.split(".");
    const minor = (BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"))).toString();
    await api("tele_tena.accounting.request_payout", { amount_minor: minor, idempotency_key: retryKey }, true);
    setAmount("");
    setPayoutOpen(false);
    setRetryKey(crypto.randomUUID());
    await resource.refresh();
  }
  const history = resource.data ? [
    ...resource.data.earnings.map(item => ({ kind: "Consultation earnings", id: `earning-${item.id}`, at: item.completed_at, amount: item.net_minor, state: item.state, item })),
    ...resource.data.payouts.map(item => ({ kind: "Payout request", id: `payout-${item.id}`, at: item.created, amount: item.amount_minor, state: item.state, item })),
  ].sort((a,b) => String(b.at||"").localeCompare(String(a.at||""))) : [];
  const shownHistory=history.filter(entry=>activityFilter==="All activity"||(activityFilter==="Payouts"?entry.kind==="Payout request":["Pending","Disputed","LegacyHold"].includes(entry.state)));
  return <>
    <PageTitle title={w("Earnings")} description={w("See what is pending, available, and reserved for payout requests.")} />
    {resource.error ? <InlineNotice tone="danger">Earnings could not be loaded. <Button onClick={() => void resource.refresh()}>Try again</Button></InlineNotice> : !resource.data ? <Skeleton /> : <>
      <div className="earnings-overview">
        <Card className="earnings-available"><p>{w("Available earnings")}</p><h2>ETB {money(resource.data.balances.earnings_available)}</h2><p className="supporting">{w("Available to request")}</p><Button variant="secondary" disabled={resource.data.balances.earnings_available<=0} onClick={()=>setPayoutOpen(true)}>{w("Request payout")}</Button></Card>
        <dl className="earnings-supporting">
          <div><dt>{w("Pending")}</dt><dd>ETB {money(resource.data.balances.pending)}</dd><p className="supporting">{w("Held until the saved review window ends or a dispute is resolved.")}</p></div>
          <div><dt>{w("Payout requested")}</dt><dd>ETB {money(resource.data.balances.payout_reserved)}</dd><p className="supporting">{w("Reserved for open requests")}</p></div>
          <div><dt>{w("Open payout requests")}</dt><dd>{resource.data.payouts.filter(item=>item.state==='Requested').length}</dd><p className="supporting">{w("Awaiting a recorded processing decision")}</p></div>
          <div><dt>{w("Completed sessions")}</dt><dd>{completedSessions.data?.filter(item=>item.state==='Completed').length??"—"}</dd><p className="supporting">{w(completedSessions.error?"Unavailable":"Explicitly finalized · all time")}</p></div>
        </dl>
      </div>
      <Dialog open={payoutOpen} onOpenChange={open=>{if(!action.busy)setPayoutOpen(open);}} title={w("Request a payout")} description={w("Reserve part of your available earnings.")}>
        <p>{w("Available earnings")}: ETB {money(resource.data.balances.earnings_available)}</p><p>{w("This request reserves the amount. It does not send money outside this demonstration.")}</p>
        <TextField label={w("Amount (ETB)")} inputMode="decimal" value={amount} error={amountError} onChange={event=>{setAmount(event.target.value);setAmountError("");setRetryKey(crypto.randomUUID());}} placeholder="0.00" />
        <div className="actions"><Button variant="secondary" disabled={action.busy} onClick={()=>setPayoutOpen(false)}>{w("Cancel")}</Button><Button loading={action.busy} onClick={()=>{if(!/^\d{1,7}(\.\d{1,2})?$/.test(amount)){setAmountError(w("Enter a positive amount with at most two decimal places."));return;}const [whole,fraction=""]=amount.split(".");const minor=BigInt(whole)*100n+BigInt(fraction.padEnd(2,"0"));if(minor<1n||minor>BigInt(resource.data!.balances.earnings_available)){setAmountError(w("Choose an amount within your available earnings."));return;}void action.run(request,w("Payout request saved. No external transfer was made."));}}>{w("Request payout")}</Button></div>
        {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
      </Dialog>
      {action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
      <ol className="earnings-stages" aria-label={w("Earnings lifecycle")}>{[["Reserved","At booking"],["Pending","After finalization"],["Available","After the review window"],["Payout requested","Reserved for your request"]].map(([label,description],index)=><li key={label}><span aria-hidden="true">{index+1}</span><strong>{w(label)}</strong><p>{w(description)}</p></li>)}</ol>
      <section className="earnings-history-section"><h2>{w("Recent activity")}</h2><div className="earnings-activity-tabs" role="group" aria-label={w("Activity filter")}>{(["All activity","Pending","Payouts"] as const).map(filter=><Button key={filter} variant="quiet" aria-pressed={activityFilter===filter} onClick={()=>setActivityFilter(filter)}>{w(filter)}</Button>)}</div>{shownHistory.length ? <><div className="table-scroll earnings-activity-table"><table><thead><tr>{["Activity","Status","Expected availability","Amount"].map(label=><th key={label}>{w(label)}</th>)}</tr></thead><tbody>{shownHistory.map(entry=><tr key={entry.id}><td><Link to={`/clinician/earnings/transactions/${encodeURIComponent(entry.id)}`}>{w(entry.kind)}</Link><p className="supporting">{entry.at?date(entry.at):w("Date unavailable")}</p></td><td><StatusBadge>{w(entry.state==='Disputed'?'On hold':entry.state==='Released'?'Available':entry.state)}</StatusBadge></td><td>{"release_at" in entry.item&&entry.state==='Pending'&&entry.item.release_at?date(entry.item.release_at):w(entry.state==='Disputed'?'On hold':entry.state==='LegacyHold'?'Review required':'Not applicable')}{"amount_minor" in entry.item&&entry.state==='Requested'&&<Button variant="quiet" loading={action.busy} onClick={()=>void action.run(async()=>{await api("tele_tena.accounting.cancel_payout",{payout:entry.item.id,reason:cancelReason},true);await resource.refresh();},w("Payout request cancelled; the reservation was released."))}>{w("Cancel request")}</Button>}</td><td><strong>ETB {money(entry.amount)}</strong></td></tr>)}</tbody></table></div><ul className="earnings-history earnings-activity-cards">{shownHistory.map(entry=><li key={entry.id}><div><strong>{w(entry.kind)}</strong><span className="supporting">{entry.at ? date(entry.at) : w("Date unavailable")}</span></div><div className="earnings-history-value"><strong>ETB {money(entry.amount)}</strong><StatusBadge>{w(entry.state === "Disputed" ? "On hold" : entry.state)}</StatusBadge></div>
          <Link className="text-link" to={`/clinician/earnings/transactions/${encodeURIComponent(entry.id)}`}>{w("Transaction details")}</Link>
          {"gross_minor" in entry.item && <p className="supporting">{w("Gross")}: ETB {money(entry.item.gross_minor)} · {w("Fee")}: ETB {money(entry.item.fee_minor)} · {w("Net")}: ETB {money(entry.item.net_minor)}{entry.item.release_at&&entry.state==="Pending"?` · ${w("Expected release")}: ${date(entry.item.release_at)}`:""}</p>}
          {entry.state==="Disputed"&&<p className="supporting">{w("Release is paused while an authorized reviewer resolves the dispute.")}</p>}
          {entry.state==="LegacyHold"&&<p className="supporting">{w("Historical balance is preserved for authorized review.")}</p>}
          {"amount_minor" in entry.item&&entry.state==="Requested"&&<Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await api("tele_tena.accounting.cancel_payout",{payout:entry.item.id,reason:cancelReason},true);await resource.refresh();},w("Payout request cancelled; the reservation was released."))}>{w("Cancel request")}</Button>}
        </li>)}</ul></> : <EmptyState title={w(history.length?"No activity in this view.":"No earnings or payout activity yet.")} />}</section>
    </>}
  </>;
}

export function CareRecords() {
  const {w}=useLocale();
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
      <div className="care-filters"><TextField label="Search visible patient name or alias" value={search} onChange={e=>{setSearch(e.target.value);setPage(1);}} /><Select label="Service" value={service} onChange={e=>setService(e.target.value)}><option value="">All services</option>{services.data?.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}</Select><Select label="Status" value={status} onChange={e=>setStatus(e.target.value)}><option value="">All statuses</option>{["Booked","PendingConfirmation","Completed","Cancelled","Expired","NoShow"].map(s=><option key={s} value={s}>{w(({Booked:"Confirmed",PendingConfirmation:"Needs confirmation",NoShow:"No-show recorded"} as Record<string,string>)[s]||s)}</option>)}</Select><div className="view-toggle"><Button variant={view==="table"?"primary":"secondary"} onClick={()=>setView("table")}>Table</Button><Button variant={view==="cards"?"primary":"secondary"} onClick={()=>setView("cards")}>Cards</Button></div></div>
      {appointments.error ? (
        <InlineNotice tone="danger">
          Records could not be loaded.{" "}
          <Button onClick={() => void appointments.refresh()}>Retry</Button>
        </InlineNotice>
      ) : !appointments.data ? (
        <Skeleton />
      ) : appointments.data?.rows.length ? (
        <>{view==="table"?<div className="table-scroll care-directory-table"><table><thead><tr><th>Patient</th><th>Last consultation</th><th>Next appointment</th><th>Care status</th><th>Action</th></tr></thead><tbody>{appointments.data.rows.map((item:any)=><tr key={item.id}><td>{item.patient_label}</td><td>{item.last_consultation?date(item.last_consultation):"No completed consultation"}</td><td>{item.next_appointment?date(item.next_appointment):"None scheduled"}</td><td><StatusBadge>{w(appointmentStatus(item,true).label)}</StatusBadge></td><td><Link className="text-link" to={`/clinician/care/${item.id}`}>View record</Link></td></tr>)}</tbody></table></div>:<div className="offering-grid">{appointments.data.rows.map((item:any)=><Card key={item.id}><h2>{item.patient_label}</h2><p>Last consultation: {item.last_consultation?date(item.last_consultation):"None yet"}</p><p>Next appointment: {item.next_appointment?date(item.next_appointment):"None scheduled"}</p><StatusBadge>{w(appointmentStatus(item,true).label)}</StatusBadge><Link className="button secondary" to={`/clinician/care/${item.id}`}>View record</Link></Card>)}</div>}<div className="actions"><Button variant="secondary" disabled={page<=1} onClick={()=>setPage(page-1)}>Previous</Button><span>Page {page} of {appointments.data.pages||1} · {appointments.data.total} patients/encounters</span><Button variant="secondary" disabled={page>=(appointments.data.pages||1)} onClick={()=>setPage(page+1)}>Next</Button></div></>
      ) : (
        <EmptyState title="No matching care records." />
      )}
    </>
  );
}

export function CareRecordDetail() {
  const {w}=useLocale();
  const {id=""}=useParams();
  const load=useCallback(()=>journeyApi.carePatientRecord(id),[id]);
  const record=useResource(load);
  if(record.error)return <InlineNotice tone="danger">{w("This care record is unavailable to your account.")}</InlineNotice>;
  if(!record.data)return <Skeleton/>;
  return <><PageTitle title={record.data.patient_label} description={w("Authorized encounters only")} action={<Link className="button secondary" to="/clinician/care">{w("Back to care records")}</Link>}/>
    <div className="care-record-layout"><section className="practice-panel"><h2>{w("Care timeline")}</h2>
      {record.data.encounters.map((item:any)=>{const status=appointmentStatus(item,true);return <article className="care-encounter" key={item.id}>
        <header><div><time>{date(item.start,item.timezone)}</time><h3>{item.service}</h3></div><StatusBadge tone={status.tone}>{w(status.label)}</StatusBadge></header>
        {status.detail&&<p className="supporting">{w(status.detail)}</p>}
        <p className="supporting">{item.booked_minutes} {w("booked minutes")} · {item.timezone||w("Timezone unavailable")}</p>
        <details><summary>{w("Disclosure at this encounter")}</summary><DisclosurePreview disclosure={item.disclosure}/></details>
        {item.private_note&&<details className="care-private-note"><summary>{w("Private clinician note · only you")}</summary><p className="prewrap">{item.private_note.text}</p>{item.private_note.patient_summary&&<><h4>{w("Patient summary draft")}</h4><p className="prewrap">{item.private_note.patient_summary}</p></>}</details>}
        <Link className="button secondary" to={`/clinician/consultations/${item.id}`}>{w("Open consultation")}</Link>
      </article>;})}
    </section><aside className="practice-panel"><h2>{w("Sharing boundaries")}</h2><p>{w("Each consultation keeps its original disclosure. Private encounters stay separate; later profile changes do not reveal earlier information.")}</p><p>{w("Clinic affiliation does not grant access to this record.")}</p></aside></div>
  </>;
}
