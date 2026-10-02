import { Link, useParams } from "react-router-dom";
import { useCallback, useState } from "react";
import { useResource } from "../hooks/useResource";
import { useSession } from "../hooks/useSession";
import { journeyApi } from "../journey-api";
import { api } from "../api";
import { date, money } from "../components/Domain";
import { Button, Card, InlineNotice, Skeleton } from "../components/ui";
import { useAction } from "../hooks/useAction";
import Consultation from "../features/consultations/Consultation";
import { useLocale } from "../hooks/useLocale";

export default function ConsultationPage() {
  const { id = "" } = useParams();
  const { session } = useSession();
  const base = session?.profile?.kind === "clinician" ? "/clinician" : "/patient";
  const loadDetail = useCallback(() => journeyApi.appointmentDetail(id), [id]);
  const detail = useResource(loadDetail);
  const [privateNote, setPrivateNote] = useState<string|null>(null);
  const [summary, setSummary] = useState<string|null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [disputeReason, setDisputeReason] = useState("");
  const action = useAction();
  if (detail.error) return <InlineNotice tone="danger">This consultation could not be loaded. Check your access and try again.</InlineNotice>;
  if (!detail.data) return <Skeleton />;
  const item = detail.data;
  const clinician = session?.profile?.kind === "clinician";
  const callEnded = item.call_state === "Ended";
  const displayStatus = item.status === "Completed" ? "Completed" : callEnded ? "Call ended" : item.status === "PendingConfirmation" ? "Needs confirmation" : item.status;
  const canOpenRoom = item.status === "Booked" && item.can_join === true;
  return <div data-appointment-id={item.id} className="consultation-page">
    <Link className="text-link" to={base+"/appointments"}>Back to appointments</Link>
    <header className="consultation-summary"><div><p className="eyebrow">CONSULTATION DETAILS</p><h1>{item.service}</h1><p>{clinician ? item.patient_identity : item.clinician} · {date(item.start,item.timezone)} · {item.timezone || "Timezone unavailable"}</p></div><span className={`status-pill status-${String(displayStatus).toLowerCase().replaceAll(" ","-")}`}>{displayStatus}</span></header>
    <div className="consultation-detail-grid"><main>
      {item.status === "PendingConfirmation"&&<InlineNotice>Waiting for the clinician to respond. Request expires {item.expires_at?date(item.expires_at):"at the time shown in the request"}.</InlineNotice>}
      {item.status==="Booked"&&!callEnded&&!item.can_join&&<InlineNotice>The room is not open yet. Join becomes available within the appointment window.</InlineNotice>}
      {callEnded&&<InlineNotice tone="info"><strong>Call ended.</strong>{clinician&&item.documentation_state!=="Finalized"?" Finish the consultation note below.":" The call ended; session completion is recorded separately."}</InlineNotice>}
      {!clinician&&callEnded&&item.documentation_state!=="Finalized"&&<InlineNotice>Summary being prepared. You’ll see it here if your clinician chooses to share one.</InlineNotice>}
      {canOpenRoom&&!callEnded&&<Card className="join-card"><h2>{item.call_state==="Open"?"Your consultation is ready":"Join your consultation"}</h2><p>Use the pre-call device check before joining. Booked duration is {item.booked_minutes} minutes.</p><Link className="button primary" to={`/consultation/${item.id}/room`}>Join consultation</Link></Card>}
      {clinician&&item.can_respond&&<div className="actions"><Button loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.respondToRequest(id,"confirm");await detail.refresh();},"Appointment confirmed.")}>Confirm request</Button><Button variant="danger" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.respondToRequest(id,"decline");await detail.refresh();},"Request declined and reservation released.")}>Decline request</Button></div>}
      {item.can_cancel&&<Button variant="secondary" onClick={()=>{const reason=window.prompt("Reason for cancellation (optional)");if(reason!==null)void action.run(async()=>{await journeyApi.cancelAppointment(id,reason);await detail.refresh();},"Appointment cancelled. Reservation release recorded.");}}>Cancel appointment</Button>}
      {item.status==="Cancelled"&&<Card><h2>Cancellation</h2><p>Cancelled by {item.cancellation.actor} · {item.cancellation.at?date(item.cancellation.at):"time unavailable"}</p>{item.cancellation.reason&&<p>Reason: {item.cancellation.reason}</p>}<p>Reserved balance released under the accepted demonstration policy.</p></Card>}
      {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}{action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
      {clinician&&callEnded&&item.documentation_state!=="Finalized"&&<section className="note-editor" data-tour-unsaved={privateNote!==null||summary!==null?"true":"false"}><h2>Consultation notes</h2><label className="field">Private consultation note <span className="visibility-label">Only you can see this</span><textarea rows={7} maxLength={12000} value={privateNote??item.private_note?.text??""} onChange={e=>setPrivateNote(e.target.value)} /></label><label className="field">Patient summary / next steps <span className="visibility-label">For patient sharing, with your approval</span><textarea rows={5} maxLength={6000} value={summary??item.private_note?.patient_summary??""} onChange={e=>setSummary(e.target.value)} /></label><div className="actions"><Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.saveNoteDraft(id,privateNote??item.private_note?.text??"",summary??item.private_note?.patient_summary??"");await detail.refresh();},"Draft saved.")}>Save draft</Button><Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{const result=await journeyApi.previewSummary(id,summary??item.private_note?.patient_summary??"");setPreview(result.summary);},"")}>Preview patient summary</Button><Button loading={action.busy} onClick={()=>{if(window.confirm("Finalize this consultation and publish the current patient summary?"))void action.run(async()=>{await journeyApi.saveNoteDraft(id,privateNote??item.private_note?.text??"",summary??item.private_note?.patient_summary??"");await journeyApi.finalizeConsultation(id,!!(summary??item.private_note?.patient_summary));await detail.refresh();},"Consultation finalized.");}}>Finalize consultation</Button></div>{preview!==null&&<Card><h3>Patient-visible preview</h3><p className="prewrap">{preview||"No patient summary has been entered."}</p><p className="supporting">Previously shared material may already have been seen and cannot be recalled.</p></Card>}</section>}
      {!clinician&&item.patient_summary_revisions?.map((revision:any)=><Card key={revision.revision}><h2>Shared summary · revision {revision.revision}</h2><p className="prewrap">{revision.summary}</p><p className="supporting">Shared {date(revision.published_at)}</p></Card>)}
      {!clinician&&item.status==="Completed"&&<Link className="button secondary" to={`/patient/book/${item.offering}`}>Book a follow-up</Link>}
      {!clinician&&item.can_open_financial_dispute&&<Card><h2>Ask for a payment review</h2><p>Use this for a payment concern. Do not include private clinical details.</p><label className="field">Reason<textarea rows={3} maxLength={500} value={disputeReason} onChange={e=>setDisputeReason(e.target.value)} /></label><Button loading={action.busy} disabled={action.busy||!disputeReason.trim()} onClick={()=>void action.run(async()=>{await api("tele_tena.accounting.open_earning_dispute",{appointment:id,reason:disputeReason},true);setDisputeReason("");await detail.refresh();},"Payment review requested. The related simulated earnings are on hold.")}>Request payment review</Button></Card>}
      {!clinician&&item.financial_state==="Disputed"&&<InlineNotice>A payment review is open. Related simulated earnings remain on hold.</InlineNotice>}
    </main><aside><Card><h2>Session details</h2><dl className="summary-list"><dt>Appointment state</dt><dd>{item.status}</dd><dt>Service</dt><dd>{item.service}</dd><dt>Scheduled</dt><dd>{date(item.start,item.timezone)}<br/>{item.timezone||"Timezone unavailable"}</dd><dt>Format</dt><dd>{item.format}</dd><dt>Booked duration</dt><dd>{item.booked_minutes} minutes</dd><dt>Call state</dt><dd>{item.call_state==="Ended"?"Call ended":item.call_state}</dd><dt>Call ended</dt><dd>{item.call_ended_at?date(item.call_ended_at,item.timezone):"Unavailable"}</dd><dt>Connected time</dt><dd>{item.actual_connected_time_available?"Available":"Unavailable"}</dd><dt>Price</dt><dd>ETB {money(item.price)}</dd><dt>Reservation</dt><dd>{item.status==="Cancelled"||item.status==="Expired"?"Released":item.financial_state==="Pending"||item.financial_state==="Released"?"Consumed":item.status==="Completed"?"Consumed":"Reserved"}</dd></dl></Card><Card><h2>What you’ll share</h2><p>{item.disclosure.request}</p><dl className="summary-list"><dt>Preferred name</dt><dd>{item.disclosure.name||"Not shared"}</dd><dt>Saved history</dt><dd>{item.disclosure.history||"Not shared"}</dd></dl></Card><Card><h2>Timeline</h2><ol className="consultation-timeline">{item.timeline.map((event:any,index:number)=><li key={index}><strong>{event.event}</strong><span>{date(event.at,item.timezone)} · {event.actor}</span>{event.reason&&<p>{event.reason}</p>}</li>)}</ol></Card></aside></div>
  </div>;
}

export function ConsultationRoomPage() {
  const { id = "" } = useParams();
  const { session } = useSession();
  const { t } = useLocale();
  const loadAppointments = useCallback(() => journeyApi.appointments(), []);
  const { data, error } = useResource(loadAppointments);
  if (error) return <InlineNotice tone="danger">The consultation could not be loaded.</InlineNotice>;
  if (!data) return <Skeleton />;
  const appointment = data.find(item => item.id === id);
  if (!appointment) return <InlineNotice tone="danger">This consultation is unavailable to your account.</InlineNotice>;
  return <main className="focused-call" data-appointment-id={id}><Link to={`/${session?.profile?.kind||"patient"}/consultations/${id}`} className="text-link">Back to consultation details</Link><Consultation key={id} appointment={{id,display_identity:appointment.display_identity||"Private participant",call_state:appointment.call_state}} t={t}/></main>;
}
