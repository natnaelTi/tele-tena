import { useState } from "react";
import { Building2, CheckCircle2 } from "lucide-react";
import { journeyApi } from "../journey-api";
import { Button, Card, EmptyState, InlineNotice, Select, Skeleton, TextField } from "../components/ui";
import { PageTitle } from "../components/Domain";
import { useAction } from "../hooks/useAction";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";

export function ClinicianAffiliations() {
  const clinics = useResource(journeyApi.myClinicApplications);
  const affiliations = useResource(journeyApi.myAffiliations);
  const verifiedClinics = useResource(journeyApi.verifiedClinics);
  const action = useAction();
  const { w } = useLocale();
  const [clinicName, setClinicName] = useState("");
  const [legalName, setLegalName] = useState("");
  const [registration, setRegistration] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [description, setDescription] = useState("");
  const [clinic, setClinic] = useState("");
  const [role, setRole] = useState("");
  const [evidence, setEvidence] = useState("");
  const refresh = async () => { await Promise.all([clinics.refresh(), affiliations.refresh(), verifiedClinics.refresh()]); };
  return <>
    <PageTitle eyebrow={w("PROFESSIONAL PRACTICE")} title={w("Clinics and affiliations")} description={w("Submit clinic details and request a separately reviewed affiliation. Neither creates clinical scope approval or patient-record access.")} />
    {action.error && <InlineNotice tone="danger">{action.error}</InlineNotice>}
    {(clinics.error || affiliations.error) && <InlineNotice tone="danger">{w("Clinic information could not be loaded.")} <Button variant="secondary" onClick={() => void refresh()}>{w("Try again")}</Button></InlineNotice>}
    <section className="clinic-settings-grid">
      <Card>
        <h2>{w("Register a clinic")}</h2>
        <p className="supporting">{w("A reviewer checks registration details. Do not include patient information.")}</p>
        <form className="clinic-form" onSubmit={e=>{e.preventDefault();void action.run(async()=>{await journeyApi.submitClinicApplication({clinic_name:clinicName,legal_name:legalName,registration_reference:registration,jurisdiction,public_description:description});setClinicName("");setLegalName("");setRegistration("");setJurisdiction("");setDescription("");await refresh();});}}>
          <TextField label={w("Clinic name")} required value={clinicName} onChange={e=>setClinicName(e.target.value)} />
          <TextField label={w("Registered legal name")} required value={legalName} onChange={e=>setLegalName(e.target.value)} />
          <TextField label={w("Registration reference")} required value={registration} onChange={e=>setRegistration(e.target.value)} />
          <TextField label={w("Jurisdiction")} required value={jurisdiction} onChange={e=>setJurisdiction(e.target.value)} />
          <TextField label={w("Public description (optional)")} value={description} onChange={e=>setDescription(e.target.value)} />
          <Button loading={action.busy}><Building2 size={18}/>{w("Submit for verification")}</Button>
        </form>
      </Card>
      <Card>
        <h2>{w("Request an affiliation")}</h2>
        <p className="supporting">{w("Verified clinic membership confirms an affiliation only; service competence is reviewed separately.")}</p>
        <form className="clinic-form" onSubmit={e=>{e.preventDefault();void action.run(async()=>{await journeyApi.submitAffiliation({clinic,professional_role:role,evidence_summary:evidence});setRole("");setEvidence("");await refresh();});}}>
          <Select label={w("Verified clinic")} required value={clinic} onChange={e=>setClinic(e.target.value)}>
            <option value="">{w("Choose a verified clinic")}</option>
            {verifiedClinics.data?.map(c=><option key={c.name} value={c.name}>{c.clinic_name} · {c.jurisdiction}</option>)}
          </Select>
          <TextField label={w("Professional role at this clinic")} required value={role} onChange={e=>setRole(e.target.value)} />
          <TextField label={w("Affiliation evidence summary")} required value={evidence} onChange={e=>setEvidence(e.target.value)} />
          <Button loading={action.busy}><CheckCircle2 size={18}/>{w("Submit affiliation")}</Button>
        </form>
      </Card>
    </section>
    <section className="clinic-record-section"><h2>{w("Clinic applications")}</h2>{!clinics.data&&!clinics.error?<Skeleton/>:clinics.data?.length?clinics.data.map(c=><article className="clinic-record-row" key={c.name}><div><strong>{c.clinic_name}</strong><p className="supporting">{c.jurisdiction} · {c.registration_reference}</p></div><span className={`status-pill status-${String(c.status).toLowerCase()}`}>{w(c.status)}</span>{c.decision_reason&&<p>{c.decision_reason}</p>}{c.status==="Rejected"&&<><p className="supporting">{w("Correct the details in the form above and submit again. The rejected application stays in your history.")}</p><Button variant="secondary" onClick={()=>{setClinicName(c.clinic_name);setLegalName(c.legal_name);setRegistration(c.registration_reference);setJurisdiction(c.jurisdiction);setDescription(c.public_description||"");document.querySelector(".clinic-settings-grid")?.scrollIntoView({block:"start"});}}>{w("Correct and resubmit")}</Button></>}</article>):<EmptyState title={w("No clinic applications yet.")}>{w("Submitted clinic details will appear here for review.")}</EmptyState>}</section>
    <section className="clinic-record-section"><h2>{w("My affiliations")}</h2>{!affiliations.data&&!affiliations.error?<Skeleton/>:affiliations.data?.length?affiliations.data.map(a=><article className="clinic-record-row" key={a.name}><div><strong>{a.clinic_name}</strong><p className="supporting">{a.professional_role} · {a.evidence_summary}</p></div><span className={`status-pill status-${String(a.status).toLowerCase()}`}>{w(a.status)}</span>{a.decision_reason&&<p>{a.decision_reason}</p>}</article>):<EmptyState title={w("No affiliations submitted yet.")}>{w("Your independently reviewed clinic affiliations will appear here.")}</EmptyState>}</section>
  </>;
}

export function ClinicReview() {
  const queue = useResource(journeyApi.clinicReviewQueue);
  const action = useAction();
  const { w } = useLocale();
  const [reasons, setReasons] = useState<Record<string,string>>({});
  const decide = (kind:"clinic"|"affiliation", id:string, decision:string) => void action.run(async()=>{if(!reasons[id]?.trim())throw new Error(w("Enter a reason for this decision."));if(kind==="clinic")await journeyApi.reviewClinic(id,decision as "Verified"|"Rejected"|"Suspended",reasons[id]);else await journeyApi.reviewAffiliation(id,decision as "Verified"|"Clarification"|"Rejected"|"Revoked",reasons[id]);await queue.refresh();});
  return <>
    <PageTitle eyebrow={w("REVIEW WORKSPACE")} title={w("Clinic verification")} description={w("Review clinic registration and affiliation separately from clinician service-scope approval. This queue grants no patient-record access.")} />
    {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
    {queue.error&&<InlineNotice tone="danger">{w("Clinic review queue could not be loaded.")} <Button variant="secondary" onClick={()=>void queue.refresh()}>{w("Try again")}</Button></InlineNotice>}
    {!queue.data&&!queue.error?<Skeleton/>:<>
      <section className="clinic-record-section"><h2>{w("Clinic registrations")}</h2>{queue.data?.clinics.length?queue.data.clinics.map(c=><Card key={c.name} className="clinic-review-card"><div className="clinic-review-heading"><div><h3>{c.clinic_name}</h3><p className="supporting">{c.legal_name} · {c.jurisdiction} · Ref {c.registration_reference}</p></div><span className={`status-pill status-${String(c.status).toLowerCase()}`}>{w(c.status)}</span></div><p className="supporting">{w("Submitted by")}: {c.submitted_by} · {c.submitted_at?new Date(c.submitted_at).toLocaleDateString():w("Date unavailable")}</p><TextField label={w("Decision reason")} required value={reasons[c.name]||""} onChange={e=>setReasons({...reasons,[c.name]:e.target.value})}/><div className="actions">{c.status==="Submitted"&&<><Button disabled={action.busy} onClick={()=>decide("clinic",c.name,"Verified")}>{w("Verify registration")}</Button><Button variant="secondary" disabled={action.busy} onClick={()=>decide("clinic",c.name,"Rejected")}>{w("Reject")}</Button></>}{c.status==="Verified"&&<Button variant="danger" disabled={action.busy} onClick={()=>decide("clinic",c.name,"Suspended")}>{w("Suspend verification")}</Button>}</div></Card>):<EmptyState title={w("No clinic registrations awaiting review.")}/>}</section>
      <section className="clinic-record-section"><h2>{w("Clinician affiliations")}</h2>{queue.data?.affiliations.length?queue.data.affiliations.map(a=><Card key={a.name} className="clinic-review-card"><div className="clinic-review-heading"><div><h3>{a.clinic_name}</h3><p className="supporting">{a.professional_role} · {a.clinician_display_name||w("Clinician profile unavailable")} · {a.clinician}</p></div><span className={`status-pill status-${String(a.status).toLowerCase()}`}>{w(a.status)}</span></div><p>{a.evidence_summary}</p><TextField label={w("Decision reason")} required value={reasons[a.name]||""} onChange={e=>setReasons({...reasons,[a.name]:e.target.value})}/><div className="actions">{a.status==="Submitted"&&<><Button disabled={action.busy} onClick={()=>decide("affiliation",a.name,"Verified")}>{w("Verify affiliation")}</Button><Button variant="secondary" disabled={action.busy} onClick={()=>decide("affiliation",a.name,"Clarification")}>{w("Request clarification")}</Button><Button variant="secondary" disabled={action.busy} onClick={()=>decide("affiliation",a.name,"Rejected")}>{w("Reject")}</Button></>}{a.status==="Verified"&&<Button variant="danger" disabled={action.busy} onClick={()=>decide("affiliation",a.name,"Revoked")}>{w("Revoke affiliation")}</Button>}</div></Card>):<EmptyState title={w("No affiliations awaiting review.")}/>}</section>
    </>}
  </>;
}
