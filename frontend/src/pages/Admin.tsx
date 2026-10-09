import "./AdminWorkspace.css";
import { useCallback, useState } from "react";
import { api } from "../api";
import { journeyApi } from "../journey-api";
import { PageTitle, date, money } from "../components/Domain";
import {
  Button,
  Card,
  Dialog,
  Checkbox,
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
import { Link } from "react-router-dom";
import { ClipboardCheck, Layers, ShieldCheck, Building2, ArrowRight } from "lucide-react";
export function AdminOverview() {
  const {w}=useLocale();
  const applications=useResource(journeyApi.applications);
  const pending=applications.data?.filter(item=>item.status==='Pending');
  return <>
    <PageTitle title={w("Review workspace")} description={w("Focus on the decisions that need a person.")}/>
    {applications.error?<InlineNotice tone="danger">{w("The queue could not be loaded.")} <Button onClick={()=>void applications.refresh()}>{w("Retry")}</Button></InlineNotice>:!applications.data?<Skeleton/>:<>
      <div className="review-overview-metrics">{[
        [w("Applications"),applications.data.length,w("Submitted professional applications")],
        [w("Awaiting decision"),pending?.length??0,w("Manual application review")],
        [w("Evidence ready"),pending?.filter(item=>item.evidence_complete).length??0,w("Received evidence still requires verification")],
      ].map(([label,count,detail])=><section key={label}><span>{label}</span><strong>{count}</strong><p>{detail}</p></section>)}</div>
      <div className="review-overview-layout"><section className="review-overview-panel"><h2>{w("Needs your review")}</h2>
        {pending?.length?pending.slice(0,5).map(item=><Link className="review-overview-row" key={item.user} to="/admin/applications"><ClipboardCheck size={24}/><div><strong>{item.display_name||w("Clinician application")}</strong><p>{item.requested_service_labels?.join(", ")||w("No requested scopes recorded")}</p></div><StatusBadge>{w(item.evidence_complete?"Ready for review":"Needs evidence")}</StatusBadge></Link>):<EmptyState title={w("No applications awaiting a decision.")}/>}
        <Link className="text-link" to="/admin/applications">{w("View all applications")} <ArrowRight size={16}/></Link>
      </section><section className="review-overview-panel"><h2>{w("Operations")}</h2>{[
        ["/admin/scopes",w("Service scopes"),w("Review each service authorization separately"),ShieldCheck],
        ["/admin/services",w("Service catalog"),w("Review definitions and operational requirements"),Layers],
        ["/admin/clinics",w("Clinic affiliations"),w("Affiliation is separate from clinical approval"),Building2],
      ].map(([route,title,detail,Icon])=>{const RowIcon=Icon as typeof ShieldCheck;return <Link className="review-overview-row" to={route as string} key={route as string}><RowIcon size={24}/><div><strong>{title as string}</strong><p>{detail as string}</p></div></Link>;})}</section></div>
    </>}
  </>;
}
export function Applications() {
  const {w}=useLocale();
  const resource=useResource(journeyApi.applications);
  const action=useAction();
  const [query,setQuery]=useState("");
  const [status,setStatus]=useState("");
  const [selectedUser,setSelectedUser]=useState<string|null>(null);
  const [resumeError,setResumeError]=useState("");
  const selected=resource.data?.find(item=>item.user===selectedUser);
  const shown=resource.data?.filter(item=>(!status||item.status===status)&&(!query||item.display_name?.toLocaleLowerCase().includes(query.toLocaleLowerCase())));
  const review=(user:string)=>{setResumeError("");setSelectedUser(user);};
  return <>
    <PageTitle title={w("Application review")} description={w("Review professional evidence before granting approval. Approval does not grant access to patient records.")}/>
    <div className="review-queue-filters"><TextField label={w("Search clinician name")} value={query} onChange={event=>setQuery(event.target.value)}/><Select label={w("Application status")} value={status} onChange={event=>setStatus(event.target.value)}><option value="">{w("All statuses")}</option>{["Pending","Approved","Rejected"].map(value=><option key={value} value={value}>{w(value)}</option>)}</Select></div>
    {resource.error?<InlineNotice tone="danger">{w("The queue could not be loaded.")} <Button onClick={()=>void resource.refresh()}>{w("Retry")}</Button></InlineNotice>:!resource.data?<Skeleton/>:shown?.length?<>
      <div className="table-scroll review-queue-table"><table><thead><tr>{["Clinician","Application status","Requested services","Submitted","Evidence","Action"].map(label=><th key={label}>{w(label)}</th>)}</tr></thead><tbody>{shown.map(item=><tr key={item.user}><td><strong>{item.display_name||w("Clinician application")}</strong></td><td><StatusBadge>{w(item.status)}</StatusBadge></td><td>{item.requested_service_labels?.join(", ")||w("Not recorded")}</td><td>{item.submitted_at?new Date(item.submitted_at).toLocaleDateString():w("Date unavailable")}</td><td>{w(item.evidence_complete?"Complete":"Incomplete")}</td><td><Button variant="secondary" onClick={()=>review(item.user)}>{w("Review")}</Button></td></tr>)}</tbody></table></div>
      <div className="review-queue-cards">{shown.map(item=><Card key={item.user}><header><h2>{item.display_name||w("Clinician application")}</h2><StatusBadge>{w(item.status)}</StatusBadge></header><p>{item.requested_service_labels?.join(", ")||w("No requested scopes recorded")}</p><p className="supporting">{w("Evidence")}: {w(item.evidence_complete?"Complete":"Incomplete")}</p><Button variant="secondary" onClick={()=>review(item.user)}>{w("Review")}</Button></Card>)}</div>
    </>:<EmptyState title={w("No applications to review.")}>{w("Submitted applications will appear here.")}</EmptyState>}
    {selected&&<Dialog open onOpenChange={open=>{if(!open&&!action.busy)setSelectedUser(null);}} title={selected.display_name||w("Clinician application")} description={w("Review the application and private evidence. Decide service scopes separately.")} className="application-review-dialog"><StatusBadge>{w(selected.status)}</StatusBadge><p className="supporting">{w("Contact / account reference")}: {selected.user}</p><h3>{w("Professional statement")}</h3><p className="prewrap">{selected.statement}</p><h3>{w("Requested service scopes")}</h3><p>{selected.requested_service_labels?.join(", ")||w("No requested scopes recorded")}</p><p>{w("Evidence")}: {w(selected.evidence_complete?"Complete":"Incomplete")} · {w("Resume")}: {w(selected.resume_uploaded?"Uploaded":"Not uploaded")}</p>
      {selected.resume_uploaded&&<Button variant="secondary" onClick={async()=>{setResumeError("");try{const response=await fetch(`/api/method/tele_tena.api.presentation.download_resume?clinician=${encodeURIComponent(selected.user)}`,{credentials:"same-origin",cache:"no-store"});if(!response.ok)throw new Error();const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download="clinician-resume.pdf";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch{setResumeError(w("Resume could not be opened. Check your reviewer access and try again."));}}}>{w("Open resume")}</Button>}
      {resumeError&&<InlineNotice tone="danger">{resumeError}</InlineNotice>}
      <InlineNotice>{w("Application approval does not approve every requested service. Review each scope and its evidence separately.")}</InlineNotice><div className="actions"><Button loading={action.busy} disabled={selected.status==='Approved'} onClick={()=>void action.run(async()=>{await journeyApi.reviewApplication(selected.user,'Approved');await resource.refresh();})}>{w("Approve application")}</Button><Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.reviewApplication(selected.user,'Rejected');await resource.refresh();})}>{w("Reject application")}</Button></div>{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
    </Dialog>}
  </>;
}
export function Scopes() {
  const applications = useResource(journeyApi.applications);
  const services = useResource(journeyApi.services);
  const scopes = useResource(journeyApi.serviceScopes);
  const immediateServices = useResource(journeyApi.immediateServices);
  const [clinician, setClinician] = useState("");
  const [service, setService] = useState("");
  const action = useAction();
  const { w } = useLocale();
  const [policyService, setPolicyService] = useState("");
  const [policySearch, setPolicySearch] = useState("");
  const [policyReason, setPolicyReason] = useState("");
  const policy = immediateServices.data?.find((item) => item.id === policyService);
  const loadPolicyHistory = useCallback(() => policyService ? journeyApi.immediatePolicyHistory(policyService) : Promise.resolve([]), [policyService]);
  const policyHistory = useResource(loadPolicyHistory);
  return (
    <>
      <PageTitle
        title="Service scopes"
        description="Approve each service separately. General clinician approval does not authorize an unapproved scope."
      />
      <div className="two-column">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void action.run(async () => {
              await journeyApi.reviewServiceScope(
                clinician,
                service,
                "Approved",
              );
              await scopes.refresh();
            });
          }}
        >
          <Select
            label="Clinician"
            required
            value={clinician}
            onChange={(e) => setClinician(e.target.value)}
          >
            <option value="">Choose clinician</option>
            {applications.data
              ?.filter((a) => a.status === "Approved")
              .map((a) => (
                <option key={a.user} value={a.user}>{a.display_name || "Clinician"} · {a.requested_service_labels?.length ? a.requested_service_labels.join(", ") : "No requested scopes"}</option>
              ))}
          </Select>
          <Select
            label="Service"
            required
            value={service}
            onChange={(e) => setService(e.target.value)}
          >
            <option value="">Choose service</option>
            {services.data?.map((s) => (
              <option value={s.id} key={s.id}>
                {s.label}
              </option>
            ))}
          </Select>
          <Button type="submit" loading={action.busy}>
            Approve service scope
          </Button>
        </form>
      </div>
      {action.error && (
        <InlineNotice tone="danger">{action.error}</InlineNotice>
      )}
      <Card className="immediate-policy-review">
        <h2>{w("Immediate requests")}</h2>
        <p>{w("A reviewer controls this service setting. It does not replace clinician approval, approved scope, language, presence, or available time.")}</p>
        {immediateServices.error ? <InlineNotice tone="danger">{w("Service policies could not be loaded.")}</InlineNotice> : !immediateServices.data ? <Skeleton /> : <>
          <TextField label={w("Find a service")} value={policySearch} onChange={(e)=>{setPolicySearch(e.target.value);setPolicyService("");setPolicyReason("");}} />
          <Select label={w("Service") } value={policyService} onChange={(e)=>{setPolicyService(e.target.value);setPolicyReason("");}}>
            <option value="">{w("Choose a service")}</option>
            {immediateServices.data.filter(item=>`${item.label} ${item.catalog_status} ${item.id}`.toLocaleLowerCase().includes(policySearch.trim().toLocaleLowerCase())).map(item=><option value={item.id} key={item.id}>{item.label} · {item.catalog_status} · {item.id}</option>)}
          </Select>
          {policy && <>
            <p className="supporting">{policy.immediate_care_enabled ? w("Immediate requests enabled") : w("Immediate requests paused")} · {w("Definition")}: {policy.definition_version || "—"}</p>
            <TextField label={w("Review reason") } value={policyReason} onChange={e=>setPolicyReason(e.target.value)} maxLength={1000} hint={w("At least 20 characters. Record service-level reasoning; do not include patient data. This is retained in the review history.")} />
            <div className="actions">
              <Button disabled={action.busy || !policyReason.trim() || !!policy.immediate_care_enabled} loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.setImmediatePolicy(policy.id,true,policyReason,crypto.randomUUID());setPolicyReason("");await immediateServices.refresh();},w("Immediate requests enabled for this service."))}>{w("Enable immediate requests")}</Button>
              <Button variant="secondary" disabled={action.busy || !policyReason.trim() || !policy.immediate_care_enabled} loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.setImmediatePolicy(policy.id,false,policyReason,crypto.randomUUID());setPolicyReason("");await immediateServices.refresh();},w("Immediate requests paused for this service."))}>{w("Pause immediate requests")}</Button>
            </div>
            <h3>{w("Recent policy decisions")}</h3>
            {policyHistory.error ? <InlineNotice tone="danger">{w("Policy history could not be loaded.")}</InlineNotice> : policyHistory.data?.length ? <ul className="policy-history">{policyHistory.data.map((event:any)=><li key={event.id}><strong>{event.enabled ? w("Immediate requests enabled") : w("Immediate requests paused")}</strong><span className="supporting"> · {date(event.created)} · {event.reviewer}</span><p>{event.reason}</p></li>)}</ul> : <p className="supporting">{w("No policy decisions recorded yet.")}</p>}
          </>}
        </>}
      </Card>
      {action.success && <InlineNotice tone="success">{action.success}</InlineNotice>}
      <h2>Current scopes</h2>
      {scopes.data?.map((scope) => (
        <Card key={scope.clinician + scope.service}>
          <h3>{applications.data?.find(a=>a.user===scope.clinician)?.display_name || "Clinician"}</h3>
          <p>
            {scope.service} · {scope.status} <span className="supporting">· {scope.clinician}</span>
          </p>
          <Button
            variant="secondary"
            disabled={action.busy || scope.status === "Revoked"}
            onClick={() =>
              void action.run(async () => {
                await journeyApi.reviewServiceScope(
                  scope.clinician,
                  scope.service,
                  "Revoked",
                );
                await scopes.refresh();
              })
            }
          >
            Revoke scope
          </Button>
        </Card>
      ))}
    </>
  );
}

type ServiceDraft = {
  id?: string; service_key: string; service_label: string; category: string;
  description: string; service_label_am: string; service_label_om: string;
  synonyms: string; professional_categories: string; credential_requirements: string;
  population_restriction: string; participant_structure: string; supported_formats: string;
  booking_rules: string; required_consent_schema: string; location_jurisdiction_policy: string;
  required_workflows: string; definition_version: string; catalog_source: string;
  effective_from: string; effective_until: string; min_duration_minutes: string;
  max_duration_minutes: string;
};
const emptyServiceDraft = ():ServiceDraft => ({service_key:"",service_label:"",category:"",description:"",
  service_label_am:"",service_label_om:"",synonyms:"",professional_categories:"",credential_requirements:"",
  population_restriction:"Adults only",participant_structure:"individual",supported_formats:"audio\nvideo",
  booking_rules:"direct-booking\nscheduled",required_consent_schema:"",location_jurisdiction_policy:"",
  required_workflows:"individual-consultation\nprivate-notes\npatient-summary",definition_version:"tele-tena-adult-catalog-1",
  catalog_source:"",effective_from:"",effective_until:"",min_duration_minutes:"20",max_duration_minutes:"90"});
const emptyAttribute = () => ({field_key:"",label_en:"",label_am:"",label_om:"",data_type:"Text",allowed_values:"",
  required:false,minimum_value:"",maximum_value:"",visibility:"Reviewer only",sensitivity:"Sensitive",
  applicability:"always",filterable:false,matching_field:false,active:true});

export function ServiceCatalog() {
  const {w}=useLocale();
  const catalog=useResource(journeyApi.serviceCatalog);
  const action=useAction();
  const [form,setForm]=useState<ServiceDraft>(emptyServiceDraft);
  const [selected,setSelected]=useState("");
  const [attribute,setAttribute]=useState(emptyAttribute);
  const [saved,setSaved]=useState("");
  const definitions=catalog.data?.definitions||[];
  const chosen=definitions.find((item:any)=>item.id===selected);
  const editable=!chosen||(chosen.catalog_status==="Draft"&&chosen.clinical_review_status==="Not reviewed"&&!chosen.active);
  const set=(key:keyof ServiceDraft,value:string)=>setForm(previous=>({...previous,[key]:value}));
  const startNew=()=>{setSelected("");setForm(emptyServiceDraft());setAttribute(emptyAttribute());setSaved("");};
  const choose=(id:string)=>{
    setSelected(id);setSaved("");setAttribute(emptyAttribute());
    const item=definitions.find((value:any)=>value.id===id);
    if(!item){setForm(emptyServiceDraft());return;}
    setForm({id:item.id,service_key:item.service_key,service_label:item.service_label,category:item.category||"",
      description:item.description||"",service_label_am:item.service_label_am||"",service_label_om:item.service_label_om||"",
      synonyms:item.synonyms||"",professional_categories:item.professional_categories||"",
      credential_requirements:item.credential_requirements||"",population_restriction:item.population_restriction||"Adults only",
      participant_structure:item.participant_structure||"individual",supported_formats:item.supported_formats||"",
      booking_rules:item.booking_rules||"",required_consent_schema:item.required_consent_schema||"",
      location_jurisdiction_policy:item.location_jurisdiction_policy||"",required_workflows:item.required_workflows||"",
      definition_version:item.definition_version||"tele-tena-adult-catalog-1",catalog_source:item.catalog_source||"",
      effective_from:item.effective_from||"",effective_until:item.effective_until||"",
      min_duration_minutes:String(item.min_duration_minutes||""),max_duration_minutes:String(item.max_duration_minutes||"")});
  };
  const save=()=>void action.run(async()=>{
    const result=await journeyApi.saveServiceDraft(form as unknown as Record<string,unknown>);
    setSelected(result.id);setSaved(result.id);await catalog.refresh();
  },w("Draft definition saved. It is not bookable."));
  const saveAttribute=()=>void action.run(async()=>{
    if(!selected)throw new Error(w("Save the service draft before adding attributes."));
    await journeyApi.saveServiceAttribute(selected,attribute as unknown as Record<string,unknown>);
    setAttribute(emptyAttribute());await catalog.refresh();setSaved(selected);
  },w("Versioned attribute saved."));
  const submit=()=>void action.run(async()=>{
    if(!selected)throw new Error(w("Save the service draft before requesting review."));
    await journeyApi.submitServiceForReview(selected);await catalog.refresh();
  },w("Sent for clinical terminology review. This does not activate bookings."));
  return <>
    <PageTitle eyebrow={w("REVIEW WORKSPACE")} title={w("Service catalog")} description={w("Maintain typed service definitions and versioned attributes. Patient concerns remain navigation terms, not diagnoses.")} />
    <InlineNotice tone="info">{w("Definitions remain drafts until separate clinical terminology review. This workspace cannot approve clinician scopes or make a service bookable.")}</InlineNotice>
    {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
    {action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
    {catalog.error&&<InlineNotice tone="danger">{w("Service catalog could not be loaded.")} <Button variant="secondary" onClick={()=>void catalog.refresh()}>{w("Try again")}</Button></InlineNotice>}
    {!catalog.data&&!catalog.error?<Skeleton/>:<div className="service-catalog-workspace">
      <aside className="service-catalog-list">
        <div className="service-catalog-list-header"><h2>{w("Definitions")}</h2><Button variant="secondary" onClick={startNew}>{w("New draft")}</Button></div>
        {definitions.map((item:any)=><button type="button" key={item.id} aria-current={selected===item.id?"true":undefined}
          className={`service-definition-choice${selected===item.id?" selected":""}`} onClick={()=>choose(item.id)}>
          <strong>{item.service_label||item.service_key}</strong><span>{item.service_key}</span><span>{w(item.catalog_status)} · {item.definition_version||w("Version unavailable")}</span>
          <span>{w(item.clinical_review_status||"Not reviewed")}</span>
        </button>)}
        {!definitions.length&&<EmptyState title={w("No service definitions yet.")}/>}
      </aside>
      <section className="service-catalog-editor">
        <header><h2>{selected?form.service_label||form.service_key:w("New service definition")}</h2>
          {chosen&&<StatusBadge>{w(chosen.clinical_review_status||chosen.catalog_status)}</StatusBadge>}</header>
        {!editable&&<InlineNotice tone="info">{w("This definition is locked after terminology review begins. Create a new version for future changes; existing definitions and records are preserved.")}</InlineNotice>}
        <fieldset disabled={!editable||action.busy}>
          <div className="form-grid two-column">
            <TextField label={w("Stable service code")} value={form.service_key} onChange={e=>set("service_key",e.target.value)} required maxLength={80} hint={w("Lowercase letters, numbers, and hyphens; stable after creation.")}/>
            <TextField label={w("Definition version")} value={form.definition_version} onChange={e=>set("definition_version",e.target.value)} required maxLength={80}/>
            <TextField label={w("Patient-facing name (English)")} value={form.service_label} onChange={e=>set("service_label",e.target.value)} required maxLength={120}/>
            <Select label={w("Service category")} value={form.category} onChange={e=>set("category",e.target.value)} required>
              <option value="">{w("Choose a category")}</option>{catalog.data?.categories.map((item:any)=><option key={item.id} value={item.id}>{item.label} · {w(item.status)}</option>)}
            </Select>
            <TextField label={w("Amharic name (provisional)")} value={form.service_label_am} onChange={e=>set("service_label_am",e.target.value)} maxLength={120}/>
            <TextField label={w("Afaan Oromo name (provisional)")} value={form.service_label_om} onChange={e=>set("service_label_om",e.target.value)} maxLength={120}/>
          </div>
          <label className="field">{w("Professional description")}<textarea rows={4} maxLength={2000} value={form.description} onChange={e=>set("description",e.target.value)}/></label>
          <label className="field">{w("Search names and synonyms (one per line)")}<textarea rows={2} maxLength={1000} value={form.synonyms} onChange={e=>set("synonyms",e.target.value)}/></label>
          <Select label={w("Participant structure")} value={form.participant_structure} onChange={e=>set("participant_structure",e.target.value)}>
            {catalog.data?.participant_formats.map((item:any)=><option key={item.id} value={item.id}>{item.label} · {w(item.status)}</option>)}
          </Select>
          <Select label={w("Population restriction")} value={form.population_restriction} onChange={e=>set("population_restriction",e.target.value)}>
            <option>Adults only</option><option>All ages</option><option>Not specified</option>
          </Select>
          <label className="field">{w("Allowed delivery formats")}<textarea rows={2} value={form.supported_formats} onChange={e=>set("supported_formats",e.target.value)}/><span className="field-hint">{w("Use one of these keys per line: audio, video, in_person.")}</span></label>
          <details className="service-catalog-advanced"><summary>{w("Professional eligibility and workflow rules")}</summary>
            <label className="field">{w("Eligible professional categories")}<textarea rows={3} value={form.professional_categories} onChange={e=>set("professional_categories",e.target.value)}/></label>
            <label className="field">{w("Credential requirements")}<textarea rows={3} value={form.credential_requirements} onChange={e=>set("credential_requirements",e.target.value)}/></label>
            <label className="field">{w("Booking rules")}<textarea rows={2} value={form.booking_rules} onChange={e=>set("booking_rules",e.target.value)}/><span className="field-hint">{w("Controlled keys: direct-booking, scheduled, immediate-request.")}</span></label>
            <label className="field">{w("Required platform workflows")}<textarea rows={3} value={form.required_workflows} onChange={e=>set("required_workflows",e.target.value)}/><span className="field-hint">{w("Only known workflow keys are accepted; this does not implement new workflows.")}</span></label>
            <TextField label={w("Consent schema version")} value={form.required_consent_schema} onChange={e=>set("required_consent_schema",e.target.value)}/>
            <TextField label={w("Location/jurisdiction policy key")} value={form.location_jurisdiction_policy} onChange={e=>set("location_jurisdiction_policy",e.target.value)}/>
            <TextField label={w("Minimum session length (minutes)")} type="number" value={form.min_duration_minutes} onChange={e=>set("min_duration_minutes",e.target.value)}/>
            <TextField label={w("Maximum session length (minutes)")} type="number" value={form.max_duration_minutes} onChange={e=>set("max_duration_minutes",e.target.value)}/>
            <TextField label={w("Effective from")} type="date" value={form.effective_from} onChange={e=>set("effective_from",e.target.value)}/>
            <TextField label={w("Effective until")} type="date" value={form.effective_until} onChange={e=>set("effective_until",e.target.value)}/>
            <TextField label={w("Clinical/source references")} value={form.catalog_source} onChange={e=>set("catalog_source",e.target.value)} maxLength={2000}/>
          </details>
          {editable&&<div className="actions"><Button loading={action.busy} onClick={save}>{w("Save draft definition")}</Button>
            {selected&&chosen?.clinical_review_status!=="In review"&&<Button variant="secondary" loading={action.busy} onClick={submit}>{w("Request clinical review")}</Button>}</div>}
        </fieldset>
        {saved&&<InlineNotice tone="success">{w("Draft definition saved. It is not bookable.")}</InlineNotice>}
        {selected&&<section className="service-attribute-editor"><h3>{w("Versioned attributes")}</h3>
          <p className="supporting">{w("These definitions are metadata only. Runtime intake collection and validation are not implemented yet.")}</p>
          {(chosen?.attributes||[]).map((item:any)=><article className="service-attribute-row" key={item.id}><strong>{item.label_en} · {item.field_key}</strong><span>{item.data_type} · {item.visibility} · {item.sensitivity} · v{item.definition_version}</span>{item.allowed_values&&<span className="supporting">{item.allowed_values.split("\n").join(" · ")}</span>}</article>)}
          {editable&&<details className="service-catalog-advanced"><summary>{w("Add or edit an attribute")}</summary><fieldset disabled={action.busy}>
            <div className="form-grid two-column"><TextField label={w("Stable field key")} value={attribute.field_key} onChange={e=>setAttribute({...attribute,field_key:e.target.value})}/>
              <TextField label={w("English field label")} value={attribute.label_en} onChange={e=>setAttribute({...attribute,label_en:e.target.value})}/>
              <TextField label={w("Amharic field label (provisional)")} value={attribute.label_am} onChange={e=>setAttribute({...attribute,label_am:e.target.value})}/>
              <TextField label={w("Afaan Oromo field label (provisional)")} value={attribute.label_om} onChange={e=>setAttribute({...attribute,label_om:e.target.value})}/>
              <Select label={w("Data type")} value={attribute.data_type} onChange={e=>setAttribute({...attribute,data_type:e.target.value})}>{["Text","Integer","Date","Boolean","Choice"].map(value=><option key={value}>{value}</option>)}</Select>
              <Select label={w("Visibility")} value={attribute.visibility} onChange={e=>setAttribute({...attribute,visibility:e.target.value})}>{["Public metadata","Clinician only","Patient private","Reviewer only"].map(value=><option key={value}>{value}</option>)}</Select>
              <Select label={w("Sensitivity")} value={attribute.sensitivity} onChange={e=>setAttribute({...attribute,sensitivity:e.target.value})}>{["Ordinary","Sensitive","Clinical"].map(value=><option key={value}>{value}</option>)}</Select>
              <Select label={w("Applicability")} value={attribute.applicability} onChange={e=>setAttribute({...attribute,applicability:e.target.value})}>{[["always","Always"],["scheduled-booking","Scheduled booking"],["open-request","Open request"]].map(([value,label])=><option key={value} value={value}>{w(label)}</option>)}</Select>
            </div>
            <label className="field">{w("Allowed values (one per line)")}<textarea rows={3} value={attribute.allowed_values} onChange={e=>setAttribute({...attribute,allowed_values:e.target.value})}/></label>
            <div className="form-grid two-column"><TextField label={w("Minimum integer value")} type="number" value={attribute.minimum_value} onChange={e=>setAttribute({...attribute,minimum_value:e.target.value})}/><TextField label={w("Maximum integer value")} type="number" value={attribute.maximum_value} onChange={e=>setAttribute({...attribute,maximum_value:e.target.value})}/></div>
            <Checkbox label={w("Required field")} checked={attribute.required} onChange={e=>setAttribute({...attribute,required:e.target.checked})}/>
            <Checkbox label={w("Usable as a discovery filter")} checked={attribute.filterable} onChange={e=>setAttribute({...attribute,filterable:e.target.checked})}/>
            <Checkbox label={w("Usable for matching")} checked={attribute.matching_field} onChange={e=>setAttribute({...attribute,matching_field:e.target.checked})}/>
            <Button loading={action.busy} disabled={!editable} onClick={saveAttribute}>{w("Save versioned attribute")}</Button>
          </fieldset></details>}
        </section>}
      </section>
    </div>}
  </>;
}

type OpenDispute = { earning_id: string; appointment: string; net_minor: number; state: string; reason: string; opened_at: string };
type ReconciliationCase = {
  case_ref: string; legacy_available: number; legacy_reserved: number;
  wallet_available: number; wallet_reserved: number; subledger_available: number;
  subledger_reserved: number; event_count: number; unknown_event_count: number;
  boundary_event_count: number; status: string; created: string;
};
export function FinancialDisputes() {
  const { w } = useLocale();
  const resource = useResource(() => api<OpenDispute[]>("tele_tena.accounting.open_disputes"));
  const reconciliation = useResource(() => api<ReconciliationCase[]>("tele_tena.accounting.financial_reconciliation_queue"));
  const action = useAction();
  const [resolutionReason, setResolutionReason] = useState("");
  const [snapshotReasons, setSnapshotReasons] = useState<Record<string, string>>({});
  const reviewCases = reconciliation.data?.filter((item) => item.status === "ReviewRequired") || [];
  return <>
    <PageTitle title={w("Financial disputes")} description={w("Financial disputes review only payment concerns. No clinical note access is included.")} />
    {action.error && <InlineNotice tone="danger">{action.error}</InlineNotice>}
    {resource.error ? <InlineNotice tone="danger">Disputes could not be loaded. <Button onClick={() => void resource.refresh()}>Try again</Button></InlineNotice> : !resource.data ? <Skeleton /> : resource.data.length ? <div className="stack">{resource.data.map(item => <Card key={item.earning_id}>
      <div className="row-between"><h2>ETB {money(item.net_minor)} {w("On hold")}</h2><StatusBadge tone="warning">{w("Disputed")}</StatusBadge></div>
      <p className="supporting">{w("Opened")} {date(item.opened_at)} · {w("Payment concern")}</p>
      <h3>Patient’s dispute reason</h3><p className="prewrap">{item.reason}</p>
      <TextField label={w("Resolution record")} value={resolutionReason} onChange={e => setResolutionReason(e.target.value)} maxLength={500} hint={w("Record a short reason. This does not add or change clinical documentation.")} />
      <div className="actions"><Button loading={action.busy} disabled={action.busy || !resolutionReason.trim()} onClick={() => void action.run(async () => { await api("tele_tena.accounting.resolve_earning_dispute", { appointment: item.appointment, resolution: "release", reason: resolutionReason }, true); setResolutionReason(""); await resource.refresh(); }, w("Hold resolved. Eligible release will run through the scheduled process."))}>{w("Release after review")}</Button><Button variant="secondary" loading={action.busy} disabled={action.busy || !resolutionReason.trim()} onClick={() => void action.run(async () => { await api("tele_tena.accounting.resolve_earning_dispute", { appointment: item.appointment, resolution: "refund", reason: resolutionReason }, true); setResolutionReason(""); await resource.refresh(); }, w("Refund recorded in the demonstration ledger."))}>{w("Refund patient")}</Button></div>
    </Card>)}</div> : <EmptyState title={w("No open financial disputes.")} />}
    <section className="stack" aria-labelledby="wallet-reconciliation-title">
      <div><h2 id="wallet-reconciliation-title">{w("Wallet reconciliation")}</h2><p className="supporting">{w("Review existing balance differences. Accepting a snapshot does not change balances or erase history.")}</p></div>
      {reconciliation.error ? <InlineNotice tone="danger">{w("Reconciliation cases could not be loaded.")} <Button onClick={() => void reconciliation.refresh()}>{w("Try again")}</Button></InlineNotice>
        : !reconciliation.data ? <Skeleton />
        : reviewCases.length ? reviewCases.map(item => <Card key={item.case_ref}>
          <div className="row-between"><h3>{w("Balance review required")}</h3><StatusBadge tone="warning">{w("Review required")}</StatusBadge></div>
          <p className="supporting">{w("Case reference")}: {item.case_ref.slice(0, 15)} · {w("Recorded")}: {date(item.created)}</p>
          <div className="form-grid two-column reconciliation-balances">
            <p>{w("Activity record")}: ETB {money(item.legacy_available)} {w("available")}; ETB {money(item.legacy_reserved)} {w("reserved")}</p>
            <p>{w("Current balance")}: ETB {money(item.wallet_available)} {w("available")}; ETB {money(item.wallet_reserved)} {w("reserved")}</p>
            <p>{w("Subledger")}: ETB {money(item.subledger_available)} {w("available")}; ETB {money(item.subledger_reserved)} {w("reserved")}</p>
            <p>{w("Evidence")}: {item.event_count} {w("events")}; {item.unknown_event_count} {w("unknown")}; {item.boundary_event_count} {w("at snapshot boundary")}</p>
          </div>
          <p className="supporting">{w("Historical activity remains unchanged. Review the account’s source records through the authorized financial operations process before deciding.")}</p>
          <TextField label={w("Reviewer decision reason")} value={snapshotReasons[item.case_ref] || ""} onChange={e => setSnapshotReasons(previous => ({...previous, [item.case_ref]: e.target.value}))} maxLength={500} hint={w("Required. This records authorization to continue from the unchanged wallet and subledger snapshot; it does not resolve the historical difference.")} />
          <Button variant="secondary" disabled={action.busy || !(snapshotReasons[item.case_ref] || "").trim()} loading={action.busy} onClick={() => void action.run(async () => {
            await api("tele_tena.accounting.accept_reconciliation_case", {case_ref: item.case_ref, reason: snapshotReasons[item.case_ref]}, true);
            setSnapshotReasons(previous => ({...previous, [item.case_ref]: ""}));
            await reconciliation.refresh();
          }, w("Decision recorded. The historical difference remains preserved."))}>{w("Accept unchanged snapshot")}</Button>
        </Card>) : <EmptyState title={w("No wallet reconciliation cases need review.")} />}
    </section>
    {action.success && <InlineNotice tone="success">{action.success}</InlineNotice>}
  </>;
}
