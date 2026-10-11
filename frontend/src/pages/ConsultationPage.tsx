import {BookingCalendar} from "../components/BookingCalendar";
import { SharedCarePrivacy, ConversationFacts, DisclosureSnapshot, PreparationPanel, RecordedCallTiming } from "../components/ConsultationDetails";
import { appointmentStatus } from "../appointment-status";
import { Link, useParams, useLocation, useNavigate } from "react-router-dom";
import { useCallback, useEffect, useState } from "react";
import { useResource } from "../hooks/useResource";
import { useSession } from "../hooks/useSession";
import { journeyApi } from "../journey-api";
import { api } from "../api";
import { date, PageTitle } from "../components/Domain";
import { Button, Card, Checkbox, Dialog, InlineNotice, Select, Skeleton } from "../components/ui";
import { useAction } from "../hooks/useAction";
import Consultation from "../features/consultations/Consultation";
import { useLocale } from "../hooks/useLocale";

export default function ConsultationPage() {
  const { id = "" } = useParams();
  // Never carry a clinical draft, disclosure, modal or late resource result
  // into a different appointment when the router reuses this route.
  return <ConsultationDetail key={id} appointmentId={id}/>;
}

function ConsultationDetail({appointmentId:id}:{appointmentId:string}) {
  const { session } = useSession();
  const location=useLocation();
  const navigate=useNavigate();
  const returnView=location.state?.appointmentView;
  const appointmentQuery=["all","upcoming","attention","completed","cancelled"].includes(returnView)?"?view="+returnView:"";
  const { t, w } = useLocale();
  const base = session?.profile?.kind === "clinician" ? "/clinician" : "/patient";
  const loadDetail = useCallback(() => journeyApi.appointmentDetail(id), [id]);
  const detail = useResource(loadDetail);
  useEffect(()=>{
    if(detail.data?.status!=='Booked')return;
    const timer=window.setInterval(()=>void detail.refresh(),15000);
    return()=>window.clearInterval(timer);
  },[detail.data?.status,detail.data?.call_state,detail.refresh]);
  const [privateNote, setPrivateNote] = useState<string|null>(null);
  const [summary, setSummary] = useState<string|null>(null);
  const [followup,setFollowup]=useState<string|null>(null);
  const [followupRecipient,setFollowupRecipient]=useState<string|null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [finalizeOpen,setFinalizeOpen]=useState(false);
  const [amending,setAmending]=useState(false);
  const [recipients,setRecipients]=useState<string[]|null>(null);
  const [shareNote,setShareNote]=useState<boolean|null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [disputeReason, setDisputeReason] = useState("");
  const [feedbackRating, setFeedbackRating] = useState<number|null>(null);
  const action = useAction();
  if (detail.error) return <InlineNotice tone="danger">{w("This appointment could not be loaded. Check your access and try again.")} <Button variant="secondary" onClick={()=>void detail.refresh()}>{w("Retry")}</Button></InlineNotice>;
  if (!detail.data) return <Skeleton />;
  const item = detail.data;
  const clinician = session?.profile?.kind === "clinician";
  const callEnded = item.call_state === "Ended";
  const presentation=appointmentStatus(item,clinician);
  const displayStatus=w(presentation.label);
  const canOpenRoom = item.status === "Booked" && item.can_join === true;
  const noteSharingSelected=shareNote??item.private_note?.note_share_selected??false;
  const followupText=followup??item.private_note?.individual_followup?.text??'';
  const selectedFollowupRecipient=followupRecipient??item.private_note?.individual_followup?.recipient??'';
  const sharedCompleted=item.is_couple&&!clinician&&item.status==="Completed";
  const documenting=clinician&&callEnded&&(item.documentation_state!=="Finalized"||amending);
  if(location.pathname.endsWith('/reschedule')) return <section className="reschedule-workspace">
    <PageTitle title={w('Choose a new time')} description={w(item.is_couple?'A new time takes effect only when both adults and the clinician agree.':'A new time takes effect only when both sides agree.')}/>
    <ReschedulePanel appointment={item} refresh={detail.refresh} focused onClose={()=>navigate(base+'/consultations/'+id,{state:location.state})}/>
  </section>;
  const documentationActions=<div className="actions"><Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{const savedPrivate=privateNote??item.private_note?.text??"";const savedSummary=summary??item.private_note?.patient_summary??"";await journeyApi.saveNoteDraft(id,savedPrivate,savedSummary,noteSharingSelected,recipients??item.private_note?.summary_recipients??[],item.is_couple?followupText:undefined,item.is_couple?selectedFollowupRecipient:undefined);setPrivateNote(current=>current===savedPrivate?null:current);setSummary(current=>current===savedSummary?null:current);setShareNote(current=>current===noteSharingSelected?null:current);setFollowup(current=>current===followupText?null:current);setFollowupRecipient(current=>current===selectedFollowupRecipient?null:current);setAmending(false);await detail.refresh();},"Draft saved.")}>{w("Save draft")}</Button><Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{const result=await journeyApi.previewSummary(id,summary??item.private_note?.patient_summary??"");setPreview(result.summary);},"")}>{w("Preview patient summary")}</Button><Button loading={action.busy} disabled={item.call_room_close_pending} onClick={()=>setFinalizeOpen(true)}>{w("Finalize consultation")}</Button></div>;
  const conversationPanel=<Card className="conversation-overview"><h2>{w("Your conversation")}</h2><ConversationFacts item={item} clinician={clinician} status={displayStatus}/>
      {item.status === "PendingConfirmation"&&<InlineNotice>Waiting for the clinician to respond. Request expires {item.expires_at?date(item.expires_at):"at the time shown in the request"}.</InlineNotice>}
      {item.status==="Booked"&&!callEnded&&!item.can_join&&<InlineNotice>The room is not open yet. Join becomes available within the appointment window.</InlineNotice>}
      {callEnded&&item.status!=="Completed"&&<InlineNotice tone="info"><strong>Call ended.</strong>{clinician&&item.documentation_state!=="Finalized"?" Finish the consultation note below.":" The call ended; session completion is recorded separately."}</InlineNotice>}
      {!clinician&&callEnded&&item.documentation_state!=="Finalized"&&<InlineNotice>Summary being prepared. You’ll see it here if your clinician chooses to share one.</InlineNotice>}
      {canOpenRoom&&!callEnded&&<Card className="join-card"><h2>{item.call_state==="Open"?"Your consultation is ready":"Join your consultation"}</h2><p>Use the pre-call device check before joining. Booked duration is {item.booked_minutes} minutes.</p><Link className="button primary" to={`/consultation/${item.id}/room`}>Join consultation</Link></Card>}
      {clinician&&item.can_respond&&<div className="actions"><Button loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.respondToRequest(id,"confirm");await detail.refresh();},"Appointment confirmed.")}>Confirm request</Button><Button variant="danger" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.respondToRequest(id,"decline");await detail.refresh();},"Request declined and reservation released.")}>Decline request</Button></div>}
      {item.can_cancel&&<><Button variant="secondary" onClick={() => setCancelOpen(true)}>{w("Cancel appointment")}</Button><Dialog open={cancelOpen} onOpenChange={setCancelOpen} title={w("Cancel this appointment?")} description={w("Review your decision before cancelling. The saved booking policy determines the financial outcome.")}><label className="field">{w("Reason for cancellation (optional)")}<textarea rows={3} maxLength={1000} value={cancelReason} onChange={event => setCancelReason(event.target.value)} /></label>{action.error && <InlineNotice tone="danger">{action.error}</InlineNotice>}<div className="actions"><Button variant="secondary" disabled={action.busy} onClick={() => setCancelOpen(false)}>{w("Keep appointment")}</Button><Button variant="danger" loading={action.busy} onClick={() => void action.run(async () => { await journeyApi.cancelAppointment(id, cancelReason); setCancelOpen(false); setCancelReason(""); await detail.refresh(); }, w("Appointment cancelled. Reservation release recorded."))}>{w("Confirm cancellation")}</Button></div></Dialog></>}
      {item.status === "Booked" && !callEnded && <ReschedulePanel appointment={item} refresh={detail.refresh} />}
      </Card>;
  return <div data-appointment-id={item.id} className={`consultation-page${sharedCompleted?" shared-care-record":""}${documenting?" consultation-documenting":""}`}>
    <header className="consultation-summary"><div><h1>{w(documenting?(item.is_couple?"Notes & recipients":"Finish the consultation"):sharedCompleted?"Your shared care record":item.status==="Completed"?"Consultation record":"Appointment details")}</h1><p>{documenting?w(item.is_couple?"Choose recipients explicitly for each note.":"The call has ended. Review your notes and finalize the encounter."):`${displayStatus} · ${date(item.start,item.timezone)}`}</p></div><span className={`status-pill status-${String(displayStatus).toLowerCase().replaceAll(" ","-")}`}>{displayStatus}</span></header>
    <div className="consultation-detail-grid"><main>{!documenting&&!sharedCompleted&&conversationPanel}
      {item.status==="Cancelled"&&<Card><h2>Cancellation</h2><p>Cancelled by {item.cancellation.actor} · {item.cancellation.at?date(item.cancellation.at):"time unavailable"}</p>{item.cancellation.reason&&<p>Reason: {item.cancellation.reason}</p>}<p>Reserved balance released under the accepted demonstration policy.</p></Card>}
      {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}{action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
      {documenting&&<section className="note-editor" data-tour-unsaved={privateNote!==null||summary!==null||shareNote!==null||followup!==null||followupRecipient!==null?"true":"false"}>{amending&&<InlineNotice>{w("This creates a new revision. Previously shared content remains in the sharing history.")}</InlineNotice>}<section className="note-document-panel"><h2>{w(item.is_couple?"Private clinical note":"Consultation note")}</h2><label className="field">{w("Private consultation note")} <span className="visibility-label">{w("Only you can see this")}</span><textarea rows={4} maxLength={12000} value={privateNote??item.private_note?.text??""} onChange={e=>setPrivateNote(e.target.value)} /></label><Checkbox label={w("Share this note with the patient")} checked={noteSharingSelected} onChange={event=>setShareNote(event.target.checked)}/><p className="supporting">{w(noteSharingSelected?"This note will be included in the patient-visible preview and published when you finalize.":"Private to the treating clinician unless you choose to share.")}</p></section><section className="note-document-panel"><h2>{w(item.is_couple?"Shared session summary":"Patient summary")}</h2><label className="field">{w("Patient summary / next steps")} <span className="visibility-label">{w("For patient sharing, with your approval")}</span><textarea rows={4} maxLength={6000} value={summary??item.private_note?.patient_summary??""} onChange={e=>setSummary(e.target.value)} /></label>{item.is_couple&&<fieldset className="note-recipient-choices"><legend>{w("Choose recipients for this revision")}</legend>{item.couple_participants?.filter((person:any)=>person.state==='Consented').map((person:any)=><Checkbox key={person.id} label={person.label} variant="card" description={w("Include in summary recipients.")} checked={(recipients??item.private_note?.summary_recipients??[]).includes(person.id)} onChange={event=>{const selected=recipients??item.private_note?.summary_recipients??[];setRecipients(event.target.checked?[...selected,person.id]:selected.filter((value:string)=>value!==person.id));}}/>)}<p className="supporting">{w("Only selected adults receive the summary and any note you explicitly share.")}</p></fieldset>}<InlineNotice>{w(item.is_couple?"Only selected adults receive this summary after finalization.":"This summary is visible to the patient. Keep private clinical material in the separate note.")}</InlineNotice></section>{item.is_couple&&<section className="note-document-panel"><h2>{w('Individual follow-up')}</h2><Select label={w('Recipient')} value={selectedFollowupRecipient} onChange={event=>setFollowupRecipient(event.target.value)}><option value="">{w('Choose a recipient')}</option>{item.couple_participants?.filter((person:any)=>person.state==='Consented').map((person:any)=><option value={person.id} key={person.id}>{person.label}</option>)}</Select><label className="field">{w('Private follow-up message')}<span className="visibility-label">{w('Only the selected adult receives this message')}</span><textarea rows={4} maxLength={6000} value={followupText} onChange={event=>setFollowup(event.target.value)}/></label><p className="supporting">{w('Do not include another participant’s private intake. Published revisions remain in the recipient’s sharing history.')}</p></section>}<Dialog open={preview!==null} onOpenChange={open=>{if(!open)setPreview(null);}} title={w("Patient-visible preview")} description={w("This is a preview. Nothing is published until you finalize and choose to share.")}><h3>{w("Patient summary")}</h3><p className="prewrap">{preview||w("No patient summary has been entered.")}</p>{noteSharingSelected&&<><h3>{w("Consultation note")}</h3><p className="prewrap">{privateNote??item.private_note?.text??""}</p></>}{item.is_couple&&followupText&&<><h3>{w('Individual follow-up')}</h3><p>{w('Recipient')}: {item.couple_participants?.find((person:any)=>person.id===selectedFollowupRecipient)?.label||w('None selected')}</p><p className="prewrap">{followupText}</p></>}<p className="supporting">{w("Previously shared content may already have been seen.")}</p><Button variant="secondary" onClick={()=>setPreview(null)}>{w("Back to notes")}</Button></Dialog></section>}
      <Dialog open={finalizeOpen} onOpenChange={open=>{if(!action.busy)setFinalizeOpen(open);}} title={w("Finalize consultation")} description={w("Review what the patient will receive before you finalize.")}>{item.is_couple&&<p><strong>{w("Recipients")}: </strong>{item.couple_participants?.filter((person:any)=>(recipients??item.private_note?.summary_recipients??[]).includes(person.id)).map((person:any)=>person.label).join(" · ")||w("None selected")}</p>}{item.is_couple&&followupText&&<><h3>{w('Individual follow-up')}</h3><p>{w('Recipient')}: {item.couple_participants?.find((person:any)=>person.id===selectedFollowupRecipient)?.label||w('None selected')}</p><p className="prewrap">{followupText}</p></>}<h3>{w("Patient-visible summary")}</h3><p className="prewrap">{summary??item.private_note?.patient_summary??w("No patient summary has been entered.")}</p>{noteSharingSelected&&<><h3>{w("Consultation note shared with the patient")}</h3><p className="prewrap">{privateNote??item.private_note?.text??""}</p></>}<InlineNotice>{w(noteSharingSelected?"Only the note and summary shown here will be shared. Finalization records pending earnings; it does not release an external payment.":"Your private consultation note stays private. Finalization records completion and pending earnings; it does not release earnings or send an external payment.")}</InlineNotice>{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}<div className="actions"><Button variant="secondary" disabled={action.busy} onClick={()=>setFinalizeOpen(false)}>{w("Back to notes")}</Button><Button loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.saveNoteDraft(id,privateNote??item.private_note?.text??"",summary??item.private_note?.patient_summary??"",noteSharingSelected,recipients??item.private_note?.summary_recipients??[],item.is_couple?followupText:undefined,item.is_couple?selectedFollowupRecipient:undefined);await journeyApi.finalizeConsultation(id,!!(summary??item.private_note?.patient_summary),noteSharingSelected);setFinalizeOpen(false);await detail.refresh();},w("Consultation finalized."))}>{w("Finalize and publish")}</Button></div></Dialog>
      {clinician&&item.documentation_state==="Finalized"&&!amending&&<Card className="finalized-note-document"><h2>{w("Consultation notes")}</h2><p className="visibility-label">{w(item.private_note?.note_published?"Shared with the patient":"Only you can see this")}</p><p className="prewrap">{item.private_note?.text||w("No consultation note was entered.")}</p><p className="supporting">{w("Revision")} {item.private_note?.revision} · {w(item.private_note?.author||"Treating clinician")}</p>{item.private_note?.individual_followup&&<><h3>{w('Individual follow-up')}</h3><p>{w('Recipient')}: {item.couple_participants?.find((person:any)=>person.id===item.private_note.individual_followup.recipient)?.label}</p><p className="prewrap">{item.private_note.individual_followup.text}</p></>}<h3>{w("Patient summary")}</h3><p className="prewrap">{item.private_note?.patient_summary||w("No patient summary has been entered.")}</p><p className="supporting">{w(item.private_note?.summary_published?"Shared with the patient":"Not shared")}</p>{item.individual_followup_history?.length>0&&<details><summary>{w('Follow-up sharing history')}</summary>{item.individual_followup_history.map((revision:any)=><section key={revision.revision}><p>{w('Revision')} {revision.revision} · {item.couple_participants?.find((person:any)=>person.id===revision.recipient)?.label} · {date(revision.published_at,item.timezone)}</p><p className="prewrap">{revision.text}</p></section>)}</details>}{item.prior_shared_revisions?.length>0&&<details><summary>{w("Sharing history")}</summary><ul>{item.prior_shared_revisions.map((revision:any)=><li key={revision.revision}>{w("Revision")} {revision.revision} · {date(revision.published_at,item.timezone)} · {[revision.note_published?w("Consultation note"):null,revision.summary_published?w("Patient summary"):null].filter(Boolean).join(" · ")}</li>)}</ul><p className="supporting">{w("Previously shared content may already have been seen.")}</p></details>}<Button variant="secondary" onClick={()=>{setPrivateNote(null);setSummary(null);setShareNote(false);setFollowup(null);setFollowupRecipient(null);setAmending(true);}}>{w("Amend consultation notes")}</Button></Card>}
      {!clinician&&item.individual_followup_revisions?.map((revision:any)=><Card className="shared-summary-document" key={'followup-'+revision.revision}><h2>{w('Your individual follow-up')}</h2><p className="visibility-label">{w('Shared only with you')}</p><p className="prewrap">{revision.text}</p><p className="supporting">{w('Revision')} {revision.revision} · {date(revision.published_at,item.timezone)}</p></Card>)}
      {!clinician&&item.shared_consultation_notes?.map((revision:any)=><Card className="shared-summary-document" key={"note-"+revision.revision}><h2>{w("Shared consultation note")}</h2><p className="supporting">{w("Revision")} {revision.revision} · {date(revision.published_at,item.timezone)}</p><p className="prewrap">{revision.text}</p></Card>)}
      {!clinician&&item.patient_summary_revisions?.map((revision:any)=><Card className="shared-summary-document" key={revision.revision}><h2>{w("Shared summary")}</h2><p className="supporting">{w("Revision")} {revision.revision}</p><p className="prewrap">{revision.summary}</p><p className="supporting">Shared {date(revision.published_at)}</p>{sharedCompleted&&<><dl className="encounter-facts"><dt>{w("Clinician")}</dt><dd>{item.clinician}</dd><dt>{w("Booked duration")}</dt><dd>{item.booked_minutes} {w("minutes")}</dd></dl><Link className="button primary" to={`/patient/book/${item.offering}`}>{w("Book a follow-up")}</Link></>}</Card>)}
      {sharedCompleted&&<>{!item.patient_summary_revisions?.length&&<Link className="button primary" to={`/patient/book/${item.offering}`}>{w("Book a follow-up")}</Link>}<details className="consultation-secondary-action"><summary>{w("Session details")}</summary>{conversationPanel}</details><details className="consultation-secondary-action"><summary>{w("Disclosure used at booking")}</summary><DisclosureSnapshot disclosure={item.disclosure}/></details></>}{!documenting&&!sharedCompleted&&<DisclosureSnapshot disclosure={item.disclosure}/>}
      {!clinician&&item.status==="Booked"&&!callEnded&&<details className="consultation-secondary-action"><summary>{t("shareScheduleTitle")}</summary><PatientClinicScheduleSharing appointment={id}/></details>}
      {!clinician&&item.can_submit_feedback&&<Card className="session-feedback"><h2>{t("sessionExperience")}</h2><p>{t("sessionExperienceExplainer")}</p><fieldset><legend>{t("sessionExperienceScale")}</legend><div className="feedback-rating" role="radiogroup" aria-label={t("sessionExperience")}>
        {[1,2,3,4,5].map(value=><label key={value}><input type="radio" name="session-experience" value={value} aria-label={`${value} / 5`} checked={feedbackRating===value} onChange={()=>setFeedbackRating(value)}/><span>{value}</span></label>)}
      </div></fieldset><Button loading={action.busy} disabled={feedbackRating===null} onClick={()=>void action.run(async()=>{await journeyApi.submitSessionFeedback(id,feedbackRating!);setFeedbackRating(null);await detail.refresh();},t("feedbackSubmitted"))}>{t("submitSessionFeedback")}</Button></Card>}
      {!clinician&&item.session_feedback?.submitted&&<Card className="session-feedback"><h2>{t("sessionExperience")}</h2><p>{item.session_feedback.rating} / 5 · {t("feedbackSubmitted")}</p></Card>}
      {!clinician&&item.can_open_financial_dispute&&<Card><h2>Ask for a payment review</h2><p>Use this for a payment concern. Do not include private clinical details.</p><label className="field">Reason<textarea rows={3} maxLength={500} value={disputeReason} onChange={e=>setDisputeReason(e.target.value)} /></label><Button loading={action.busy} disabled={action.busy||!disputeReason.trim()} onClick={()=>void action.run(async()=>{await api("tele_tena.accounting.open_earning_dispute",{appointment:id,reason:disputeReason},true);setDisputeReason("");await detail.refresh();},"Payment review requested. The related simulated earnings are on hold.")}>Request payment review</Button></Card>}
      {!clinician&&item.financial_state==="Disputed"&&<InlineNotice>A payment review is open. Related simulated earnings remain on hold.</InlineNotice>}
      {!clinician&&item.supports_clinic_sharing!==false&&item.status==="Completed"&&item.patient_summary_revisions?.length>0&&<PatientClinicSummarySharing appointment={id}/>}
      {documenting&&<details className="consultation-secondary-action"><summary>{w("Disclosure used at booking")}</summary>{item.is_couple?item.couple_participants?.map((person:any)=><section key={person.id}><h3>{person.label}</h3><DisclosureSnapshot disclosure={person.disclosure}/></section>):<DisclosureSnapshot disclosure={item.disclosure}/>}</details>}
    </main><aside>{sharedCompleted&&<SharedCarePrivacy/>}{!clinician&&!sharedCompleted&&item.status==="Completed"&&<Card><h2>{w("Continue your care")}</h2><Link className="button primary" to={`/patient/book/${item.offering}`}>{w("Book a follow-up")}</Link></Card>}{documenting&&<Card className="documentation-actions"><h2>{w(item.is_couple?"Before finalizing":"Finalize encounter")}</h2><p>{w("Review the private note and patient summary before finalizing.")}</p>{item.call_room_close_pending&&<InlineNotice tone="info">{t("callClosePending")} <Link to={`/consultation/${id}/room`}>{w("View consultation")}</Link></InlineNotice>}<dl className="encounter-facts"><dt>{w(item.is_couple?"Participants":"Patient")}</dt><dd>{item.is_couple?item.couple_participants?.map((person:any)=>person.label).join(" · "):item.patient_identity}</dd><dt>{w("Booked duration")}</dt><dd>{item.booked_minutes} {w("minutes")}</dd><dt>{w("Call state")}</dt><dd>{w("Call ended")}</dd><dt>{w("Documentation")}</dt><dd>{w(amending?"Amendment draft":"Notes pending")}</dd><dt>{w("Earnings")}</dt><dd>{w(item.status==="Completed"?"Previously recorded":"Pending release after finalization")}</dd></dl>{item.is_couple&&<InlineNotice>{w("Recipient selection applies to this revision, not every record in the shared care relationship.")}</InlineNotice>}{documentationActions}</Card>}{documenting&&<details className="consultation-secondary-action"><summary>{w("Appointment details")}</summary>{conversationPanel}</details>}{item.status!=="Cancelled"&&item.status!=="Expired"&&item.status!=="Declined"&&item.status!=="Completed"&&!callEnded&&<PreparationPanel/>}<RecordedCallTiming item={item}/><details className="consultation-secondary-action" open={!sharedCompleted&&!documenting}><summary>{w("Timeline")}</summary><ol className="consultation-timeline">{item.timeline.map((event:any,index:number)=><li key={index}><strong>{w(event.event)}</strong><span>{date(event.at,item.timezone)} · {event.actor}</span>{event.reason&&<p>{event.reason}</p>}</li>)}</ol></details></aside></div>
    {item.is_couple&&!clinician&&<Link className="text-link" to="/patient/couples">{w("Consent and shared session details")}</Link>}
    <footer className="consultation-detail-footer"><Link className="text-link" to={base+"/appointments"+appointmentQuery}>{w("Back to appointments")}</Link></footer>
  </div>;
}

function PatientClinicSummarySharing({appointment}:{appointment:string}) {
  const {t}=useLocale();
  const eligible=useResource(useCallback(()=>journeyApi.eligibleClinicsForSummary(appointment),[appointment]));
  const grants=useResource(useCallback(()=>journeyApi.myClinicScheduleAccess(appointment),[appointment]));
  const action=useAction();
  const [clinic,setClinic]=useState('');
  const [consented,setConsented]=useState(false);
  const choices=eligible.data||[];
  const summaryGrants=(grants.data||[]).filter((grant:any)=>grant.purpose==='Patient-shared summary');
  const active=summaryGrants.filter((grant:any)=>grant.status==='Active');
  const past=summaryGrants.filter((grant:any)=>grant.status!=='Active');
  const refresh=async()=>{await Promise.all([eligible.refresh(),grants.refresh()]);};
  return <Card className="clinic-schedule-sharing"><h2>{t('shareSummaryTitle')}</h2><p>{t('shareSummaryExplainer')}</p>
    {eligible.error||grants.error?<InlineNotice tone="danger">{t('clinicShareLoadError')} <Button variant="secondary" onClick={()=>void refresh()}>{t('tryAgain')}</Button></InlineNotice>:null}
    {!eligible.error&&!grants.error&&(!eligible.data||!grants.data)&&<Skeleton/>}
    {active.map((grant:any)=><div className="clinic-shared-row" key={grant.grant}><p><strong>{grant.clinic_name}</strong> · {t('sharedSummary')}</p><Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.revokeClinicScheduleAccess(grant.grant);await refresh();})}>{t('stopSharing')}</Button></div>)}
    {past.map((grant:any)=><p className="supporting" key={grant.grant}>{grant.clinic_name} · {t('summaryPreviouslyShared')} {grant.revoked_at?date(grant.revoked_at):''}</p>)}
    {choices.filter(item=>!item.already_shared).length>0&&<><Select label={t('chooseClinic')} value={clinic} onChange={event=>{setClinic(event.target.value);setConsented(false);}}><option value="">{t('chooseClinic')}</option>{choices.filter(item=>!item.already_shared).map(item=><option key={item.clinic} value={item.clinic}>{item.clinic_name} · {item.jurisdiction}</option>)}</Select>
      {clinic&&<><Checkbox label={t('clinicSummaryConsent')} checked={consented} onChange={event=>setConsented(event.target.checked)}/><Button disabled={!consented||action.busy} loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.grantClinicSummaryAccess(appointment,clinic);setClinic('');setConsented(false);await refresh();},t('sharedSummary'))}>{t('shareSummary')}</Button></>}
    </>}
    {eligible.data&&!choices.length&&!active.length&&<p className="supporting">{t('noEligibleClinic')}</p>}
    {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}{action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
  </Card>;
}

function ReschedulePanel({appointment,refresh,focused=false,onClose}:{appointment:any;refresh:()=>Promise<void>;focused?:boolean;onClose?:()=>void}) {
  const {w}=useLocale();
  const navigate=useNavigate();
  const location=useLocation();
  const {session}=useSession();
  const base=session?.profile?.kind==="clinician"?"/clinician":"/patient";
  const [selected,setSelected]=useState("");
  const [retryKey,setRetryKey]=useState("");
  const [outcome,setOutcome]=useState("");
  const action=useAction();
  const today=new Intl.DateTimeFormat('en-CA',{timeZone:appointment.timezone||'UTC',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const [fromDate,setFromDate]=useState(today);
  const [selectedDate,setSelectedDate]=useState('');
  const load=useCallback(()=>journeyApi.calendar(appointment.offering,fromDate,appointment.timezone||'UTC'),[appointment.offering,appointment.timezone,fromDate]);
  const calendar=useResource(load);
  const hasSlots=(calendar.data?.days||[]).some(day=>day.slots.length>0);
  const current=appointment.reschedule;
  const propose=async()=>{
    if(!selected||!retryKey)return;
    await action.run(async()=>{await journeyApi.proposeReschedule(appointment.id,selected,retryKey);setSelected("");setRetryKey("");await refresh();onClose?.();},"");
  };
  if(!current&&!focused) return appointment.can_propose_reschedule
    ? <Button variant="secondary" onClick={()=>navigate(base+'/consultations/'+appointment.id+'/reschedule',{state:location.state})}>{w('Request a new time')}</Button>
    : null;
  return <>
    <Card className={`reschedule-panel${focused?' reschedule-calendar-panel':''}`}>
      <h2>{w(current?'Review the proposed time':'Choose a proposed time')}</h2>
      {current&&appointment.is_couple&&<p role="status">{current.accepted_count} / {current.required_count} {w('participants have agreed')}. {w(current.your_response==='accept'?'Your agreement is recorded.':'Review the new time before agreeing.')}</p>}
      {current&&<><p><strong>{w('A new time is waiting for your response.')}</strong></p><p>{w('Your proposed time')}: {date(current.start,current.timezone)}</p>
        {current.proposed_by_you?<Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.withdrawReschedule(appointment.id,current.id);await refresh();},w('Withdraw request'))}>{w('Withdraw request')}</Button>:<div className="actions"><Button disabled={appointment.is_couple&&current.your_response==='accept'} loading={action.busy} onClick={()=>void action.run(async()=>{const result=await journeyApi.respondToReschedule(appointment.id,current.id,'accept');if(result.state==='Unavailable')setOutcome(result.message);await refresh();},w('Accept new time'))}>{w('Accept new time')}</Button><Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.respondToReschedule(appointment.id,current.id,'decline');await refresh();},w('Decline new time'))}>{w('Decline new time')}</Button></div>}
      </>}
      {!current&&appointment.can_propose_reschedule&&<>
        {calendar.error&&<InlineNotice tone="danger">{w('Available times could not be loaded.')} <Button variant="secondary" onClick={()=>void calendar.refresh()}>{w('Try again')}</Button></InlineNotice>}
        {!calendar.error&&!calendar.data&&<Skeleton/>}
        {calendar.data&&<><p className="supporting">{w('Timezone')}: {appointment.timezone}</p><BookingCalendar days={calendar.data.days} fromDate={fromDate} selectedDate={selectedDate} selectedStart={selected} duration={appointment.booked_minutes} onMonth={value=>{setFromDate(value);setSelectedDate('');setSelected('');setRetryKey('');}} onDate={value=>{setSelectedDate(value);setSelected('');setRetryKey('');}} onStart={value=>{setSelected(value);setRetryKey(crypto.randomUUID());}}/></>}
        {calendar.data&&!hasSlots&&<InlineNotice>{w('No available times to propose in the current booking window.')}</InlineNotice>}
      </>}
      {!current&&!appointment.can_propose_reschedule&&<InlineNotice>{w('This appointment is not eligible for a time change.')}</InlineNotice>}
    </Card>
    {focused&&<InlineNotice>{w(appointment.is_couple?'The original appointment stays reserved until both adults and the clinician agree.':'The original appointment stays reserved until both of you agree.')}</InlineNotice>}
    {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
    {outcome&&<InlineNotice tone="info">{outcome}</InlineNotice>}
    {action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
    {focused&&<div className="actions">{!current&&appointment.can_propose_reschedule&&<Button loading={action.busy} disabled={!selected||!retryKey} onClick={()=>void propose()}>{w('Send reschedule request')}</Button>}<Button variant="secondary" disabled={action.busy} onClick={onClose}>{w(current?'Back to appointment':'Keep current time')}</Button></div>}
  </>;
}

function PatientClinicScheduleSharing({appointment}:{appointment:string}) {
  const {t}=useLocale();
  const eligible=useResource(useCallback(()=>journeyApi.eligibleClinicsForAppointment(appointment),[appointment]));
  const grants=useResource(useCallback(()=>journeyApi.myClinicScheduleAccess(appointment),[appointment]));
  const action=useAction();
  const [clinic,setClinic]=useState('');
  const [consented,setConsented]=useState(false);
  const choices=eligible.data||[];
  const active=(grants.data||[]).filter((grant:any)=>grant.status==='Active');
  const visible=choices.length>0||(grants.data||[]).length>0||eligible.error||grants.error;
  if(!visible)return null;
  const refresh=async()=>{await Promise.all([eligible.refresh(),grants.refresh()]);};
  return <Card className="clinic-schedule-sharing"><h2>{t('shareScheduleTitle')}</h2><p>{t('shareScheduleExplainer')}</p>
    {eligible.error||grants.error?<InlineNotice tone="danger">{t('clinicShareLoadError')} <Button variant="secondary" onClick={()=>void refresh()}>{t('tryAgain')}</Button></InlineNotice>:null}
    {active.map((grant:any)=><div className="clinic-shared-row" key={grant.grant}><p><strong>{grant.clinic_name}</strong> · {t('sharedSchedule')}</p><Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.revokeClinicScheduleAccess(grant.grant);await refresh();})}>{t('stopSharing')}</Button></div>)}
    {choices.filter(item=>!item.already_shared).length>0&&<><Select label={t('chooseClinic')} value={clinic} onChange={event=>{setClinic(event.target.value);setConsented(false);}}><option value="">{t('chooseClinic')}</option>{choices.filter(item=>!item.already_shared).map(item=><option key={item.clinic} value={item.clinic}>{item.clinic_name} · {item.jurisdiction}</option>)}</Select>
      {clinic&&<><Checkbox label={t('clinicScheduleConsent')} checked={consented} onChange={event=>setConsented(event.target.checked)}/><Button disabled={!consented||action.busy} loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.grantClinicScheduleAccess(appointment,clinic);setClinic('');setConsented(false);await refresh();},t('sharedSchedule'))}>{t('shareAppointment')}</Button></>}
    </>}
    {!choices.length&&!active.length&&!eligible.error&&<p className="supporting">{t('noEligibleClinic')}</p>}
    {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}{action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
  </Card>;
}

export function ConsultationRoomPage() {
  const { id = "" } = useParams();
  const { t } = useLocale();
  const loadAppointments = useCallback(() => journeyApi.appointments(), []);
  const { data, error } = useResource(loadAppointments);
  if (error) return <InlineNotice tone="danger">The consultation could not be loaded.</InlineNotice>;
  if (!data) return <Skeleton />;
  const appointment = data.find(item => item.id === id);
  if (!appointment) return <InlineNotice tone="danger">This consultation is unavailable to your account.</InlineNotice>;
  return <main className="focused-call" data-appointment-id={id}><Consultation key={id} appointment={{...appointment,display_identity:appointment.display_identity||"Private participant"}} t={t}/></main>;
}
