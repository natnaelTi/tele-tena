import {ProfessionalEditor,ProfessionalReview} from '../components/ProfessionalReview';
import {FileUpload} from "../components/FileUpload";
import { useEffect, useRef, useState } from 'react';
import './Vetting.css';
import { journeyApi } from '../journey-api';
import { Button, Checkbox, EmptyState, InlineNotice, Select, Skeleton, TextField, RequiredFieldsNotice } from '../components/ui';
import { PageTitle } from '../components/Domain';
import { useAction } from '../hooks/useAction';
import { useResource } from '../hooks/useResource';
import { useLocale } from '../hooks/useLocale';
import { api,ApiError } from '../api';

const loadOperationalScopeReviews = () => journeyApi.scopeAppointmentReviews('All');

function encodeFile(file:File):Promise<string>{
  return new Promise((resolve,reject)=>{
    const reader=new FileReader();
    reader.onerror=()=>reject(new Error('The selected file could not be read.'));
    reader.onload=()=>resolve(String(reader.result).split(',')[1]||'');
    reader.readAsDataURL(file);
  });
}

async function openScopeEvidence(item:any,w:(value:string)=>string){
  try{
    const response=await fetch(`/api/method/tele_tena.api.vetting.download_scope_evidence?evidence=${encodeURIComponent(item.id)}`,{credentials:'same-origin',cache:'no-store'});
    if(!response.ok)throw new Error();
    const url=URL.createObjectURL(await response.blob());
    const link=document.createElement('a');link.href=url;link.download=item.filename;link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch{window.alert(w('Private service evidence could not be opened. Check your access and try again.'));}
}

function VettingRubricManager(){
  const {w}=useLocale();const current=useResource(journeyApi.vettingRubric);
  const versions=useResource(journeyApi.vettingRubricVersions);const action=useAction();
  const [version,setVersion]=useState('proposed-1.1');const [title,setTitle]=useState('Human-led scope vetting rubric');
  const [approvalNote,setApprovalNote]=useState('Proposed for medical-lead review; not an approved credentialing standard.');
  const [decisionRule,setDecisionRule]=useState('Scores organize evidence only. Human reviewers apply mandatory gates and record each scope decision.');
  const [criteria,setCriteria]=useState([
    {key:'scope_education',label:'Scope-relevant education'},
    {key:'supervised_experience',label:'Supervised clinical experience'},
    {key:'approach_training',label:'Training in selected approach'},
    {key:'adult_population',label:'Adult population experience'},
    {key:'ethics_safeguarding',label:'Ethics, privacy and safeguarding understanding'},
    {key:'assessment_interview',label:'Consultation or assessment interview'},
  ]);
  const [reasons,setReasons]=useState<Record<string,string>>({});
  const useCurrent=()=>{if(!current.data)return;setTitle(current.data.title);setApprovalNote(current.data.approval_note);setDecisionRule(current.data.decision_rule);setCriteria(current.data.scored_criteria.map((item:any)=>({key:item.key,label:item.label})));};
  return <details className="vetting-rubric-manager"><summary>{w('Rubric Versions and Approval')}</summary>
    <p className="supporting">{w('The current rubric is proposed. Scores organize evidence only; a designated medical lead must approve a version before it is described as an approved standard.')}</p>
    {action.error&&<InlineNotice tone="danger">{w(action.error)}</InlineNotice>}
    {(versions.error||current.error)&&<InlineNotice tone="danger">{w('Rubric versions could not be loaded.')} <Button variant="secondary" onClick={()=>void Promise.all([versions.refresh(),current.refresh()])}>{w('Retry')}</Button></InlineNotice>}
    {!versions.data?<Skeleton/>:<div className="vetting-rubric-version-list">{versions.data.items.map((item:any)=><article className="vetting-rubric-version" key={item.version}>
      <div><strong>{item.version}</strong><span className={`status-pill status-${String(item.status).toLowerCase()}`}>{w(item.status)}</span><p className="supporting">{item.created_at?new Date(item.created_at).toLocaleString():w('Date unavailable')}</p>{item.approval_reason&&<p>{item.approval_reason}</p>}
        <details className="rubric-version-definition"><summary>{w('Inspect This Rubric Definition')}</summary><h3>{item.definition.title}</h3><p>{item.definition.approval_note}</p><h4>{w('Scored Dimensions')}</h4><ul>{item.definition.scored_criteria.map((criterion:any)=><li key={criterion.key}>{criterion.label} <span className="supporting">({criterion.key})</span></li>)}</ul><p><strong>{w('Score range')}:</strong> {item.definition.score_min}–{item.definition.score_max}</p><p><strong>{w('How scores are used')}:</strong> {item.definition.decision_rule}</p><p className="supporting">{w('Definition digest')}: <code>{item.definition.definition_sha256}</code></p></details>
      </div>
      {versions.data.can_approve&&item.status==='Proposed'&&<div className="vetting-rubric-approve"><TextField label={w('Medical-lead approval rationale')} value={reasons[item.version]||''} onChange={event=>setReasons({...reasons,[item.version]:event.target.value})}/><Button disabled={!reasons[item.version]?.trim()||action.busy} loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.approveVettingRubric(item.version,reasons[item.version]);await Promise.all([versions.refresh(),current.refresh()]);})}>{w('Approve rubric version')}</Button></div>}
    </article>)}</div>}
    <details className="vetting-rubric-propose"><summary>{w('Propose a New Rubric Version')}</summary>
      <p className="supporting">{w('This creates a new immutable proposal. It does not change applications already in review or current booking eligibility.')}</p>
      <div className="vetting-rubric-propose-grid"><TextField label={w('Version')} value={version} onChange={event=>setVersion(event.target.value)} maxLength={40}/><TextField label={w('Rubric title')} value={title} onChange={event=>setTitle(event.target.value)} maxLength={120}/></div>
      <TextField label={w('Medical-lead review note')} value={approvalNote} onChange={event=>setApprovalNote(event.target.value)} maxLength={500}/>
      <TextField label={w('How scores are used')} value={decisionRule} onChange={event=>setDecisionRule(event.target.value)} maxLength={1000}/>
      <Button variant="quiet" onClick={useCurrent} disabled={!current.data}>{w('Copy current rubric into this proposal')}</Button>
      <div className="vetting-rubric-propose-grid">{criteria.map((item,index)=><TextField key={item.key} label={`${item.key} · ${w('English label')}`} value={item.label} onChange={event=>setCriteria(current=>current.map((criterion,i)=>i===index?{...criterion,label:event.target.value}:criterion))} maxLength={180}/>)}</div>
      <p className="supporting">{w('Scores use the fixed 0–3 scale. Mandatory reviewer gates remain separate and cannot be offset by a score.')}</p>
      <Button loading={action.busy} disabled={action.busy||!version.trim()} onClick={()=>void action.run(async()=>{await journeyApi.proposeVettingRubric(version,{title,approval_note:approvalNote,decision_rule:decisionRule,score_min:0,score_max:3,scored_criteria:criteria});await versions.refresh();})}>{w('Save proposed version')}</Button>
    </details>
  </details>;
}

export function VettingRubricManagementPage(){
  const {w}=useLocale();
  return <><PageTitle title={w('Clinical Vetting Rubric')} description={w('Versioned review criteria remain separate from human decisions on each clinician service scope.')}/><VettingRubricManager/></>;
}

function ScopeEvidencePanel({item,canUpload,refresh}:{item:any;canUpload:boolean;refresh:()=>Promise<unknown>}){
  const {w}=useLocale();const action=useAction();const [evidenceType,setEvidenceType]=useState('Qualification');
  const [profileLicenses,setProfileLicenses]=useState<{id:string;filename:string}[]>([]);
  useEffect(()=>{let active=true;if(canUpload)void api<any>('tele_tena.api.professional.application').then(state=>{if(active)setProfileLicenses(state.evidence.filter((file:any)=>file.purpose==='License'&&file.mime==='application/pdf'&&(state.payload.license_files||[]).includes(file.id)));}).catch(()=>{});return()=>{active=false;};},[canUpload]);

  return <section className="scope-evidence-panel" aria-label={w('Evidence for this service')}>
    <h3>{w('Evidence for This Service')}</h3>
    <p className="supporting">{w('PDF only, up to 5 MB. New uploads create a revision; earlier evidence remains in the review history.')}</p>
    {item.scope_evidence?.length?<ul className="scope-evidence-list">{item.scope_evidence.map((evidence:any)=><li key={evidence.id}><span>{w(evidence.evidence_type)} · {evidence.filename} · v{evidence.revision}</span><Button variant="quiet" onClick={()=>void openScopeEvidence(evidence,w)}>{w('Open private evidence')}</Button></li>)}</ul>:<p className="supporting">{w('No service-specific evidence uploaded yet.')}</p>}
    {canUpload&&profileLicenses.length>0&&<section><h4>{w('Use a License From Your Professional Profile')}</h4><p className="supporting">{w('Attach the applicable PDF to this service. This shares evidence for review; it does not verify the license or approve the scope.')}</p>{profileLicenses.map(file=><Button key={file.id} variant="secondary" disabled={action.busy} onClick={()=>void action.run(async()=>{await api('tele_tena.api.professional.attach_scope_license',{application:item.name,id:file.id},true);await refresh();})}>{w('Attach License')}: {file.filename}</Button>)}</section>}
    {canUpload&&<div className="scope-evidence-upload"><Select label={w('Evidence type')} value={evidenceType} onChange={e=>setEvidenceType(e.target.value)}>
      {['Qualification','License or registration','Scope training','Approach experience','Other supporting evidence'].map(value=><option key={value} value={value}>{w(value)}</option>)}
    </Select><div className="field"><FileUpload label={w(evidenceType==='License or registration'?'Professional License':evidenceType==='CV'?'CV':'Credential Document')} description={w('PDF only. Up to 5 MB. Choose the evidence type before uploading.')} actionLabel={w(evidenceType==='CV'?'Select CV PDF':evidenceType==='License or registration'?'Select Professional License PDF':'Select Credential PDF')} maxBytes={5*1024*1024} accept="application/pdf,.pdf" disabled={action.busy} onFiles={files=>{
      const file=files[0];if(!file)return;
      void action.run(async()=>{if(file.size>5*1024*1024)throw new Error('The PDF must be 5 MB or smaller.');await journeyApi.uploadScopeEvidence(item.name,evidenceType,file.name,await encodeFile(file));await refresh();});
    }}/></div>
    {action.error&&<InlineNotice tone="danger">{w(action.error)}</InlineNotice>}</div>}
  </section>;
}

export function ClinicianScopeApplications() {
  const { w, locale } = useLocale();
  const services = useResource(journeyApi.vettingServices);
  const context = useResource(journeyApi.scopeApplicationContext);
  const contextApplied=useRef(false);
  const [initialized,setInitialized]=useState(false);
  const applications = useResource(journeyApi.myScopeApplications);
  const action = useAction();
  const [service, setService] = useState('');
  const [selectedServices,setSelectedServices]=useState<string[]>([]);
  const [serviceSearch,setServiceSearch]=useState('');
  const [competencies,setCompetencies]=useState('');const [certifications,setCertifications]=useState('');const [validFrom,setValidFrom]=useState('');
  const [dirty, setDirty] = useState(false);
  const [step, setStep] = useState(0);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const changeStep = (next:number) => { setStep(next); requestAnimationFrame(()=>headingRef.current?.focus()); };
  const [category, setCategory] = useState('');
  const [qualification, setQualification] = useState('');
  const [institution, setInstitution] = useState('');
  const [license, setLicense] = useState('');
  const [authority, setAuthority] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [expiry, setExpiry] = useState('');
  const [experience, setExperience] = useState('');
  const [approaches, setApproaches] = useState('');
  const [training, setTraining] = useState('');
  const [statement, setStatement] = useState('');
  const [adults, setAdults] = useState(false);
  const [independent, setIndependent] = useState(false);
  const [appealStatements,setAppealStatements]=useState<Record<string,string>>({});
  const [reverificationOf,setReverificationOf]=useState<string|null>(null);
  const approachOptions=context.data?.treatment_approaches||[];
  const selectedApproaches=approaches.split('\n').map(value=>value.trim()).filter(Boolean);
  const unlistedApproaches=selectedApproaches.filter(key=>!approachOptions.some((item:any)=>item.id===key));

  useEffect(()=>{
    if(!context.data||!applications.data||contextApplied.current||dirty)return;
    contextApplied.current=true;
    const resumable=applications.data.find((item:any)=>['Draft','Clarification'].includes(item.status));
    const claims=resumable||context.data.professional||{};
    setCategory(claims.professional_category||'');setQualification(claims.qualification||'');
    setInstitution(claims.issuing_institution||'');setLicense(claims.registration_number||'');
    setAuthority(claims.issuing_authority||'');setJurisdiction(claims.jurisdiction||'');
    setValidFrom(claims.credential_valid_from||'');setExpiry(claims.credential_expiry||'');
    setCompetencies(claims.competencies||'');setCertifications(claims.certifications||'');
    setExperience(String(claims.experience_years??''));
    setSelectedServices(resumable?[resumable.service]:(context.data.requested_services||[]).filter((key:string)=>!applications.data?.some((item:any)=>item.service===key&&!['Draft','Clarification'].includes(item.status))));setService(resumable?.service||(context.data.requested_services||[]).find((key:string)=>!applications.data?.some((item:any)=>item.service===key&&!['Draft','Clarification'].includes(item.status)))||'');
    if(resumable){
      setReverificationOf(resumable.reverification_of||null);setStep(1);
      setApproaches(resumable.approach_keys||'');setTraining(resumable.relevant_training||'');
      setStatement(resumable.applicant_statement||'');setAdults(!!resumable.population_adults);
      setIndependent(!!resumable.independent_practice);
    }
    setInitialized(true);
  },[context.data,applications.data,dirty]);

  const save = (submit:boolean) => void action.run(async()=>{
    if(!service) throw new ApiError('scope_selection_invalid');
    if(submit&&(!category.trim()||!qualification.trim()||!institution.trim()))throw new ApiError('scope_qualification_required');
    if(submit&&!adults)throw new ApiError('scope_adult_required');
    if(unlistedApproaches.length)throw new ApiError('scope_approach_invalid');
    const values={professional_category:category,qualification,issuing_institution:institution,competencies,certifications,credential_valid_from:validFrom,
      registration_number:license,issuing_authority:authority,jurisdiction,credential_expiry:expiry,
      experience_years:experience||'0',approach_keys:approaches,population_adults:adults,
      independent_practice:independent,clinic_affiliations:'',relevant_training:training,
      applicant_statement:statement};
    if(!reverificationOf&&selectedServices.length>1)await journeyApi.saveScopeApplications(selectedServices,values,submit);
    else await journeyApi.saveScopeApplication(service,values,submit,reverificationOf);
    await applications.refresh();
    setDirty(false);
  });
  const continueApplication=(item:any)=>{
    contextApplied.current=true;
    setDirty(false);setStep(1);setService(item.service);setSelectedServices([item.service]);setCompetencies(item.competencies||'');setCertifications(item.certifications||'');setValidFrom(item.credential_valid_from||'');setCategory(item.professional_category||'');
    setReverificationOf(item.reverification_of||null);
    setQualification(item.qualification||'');setInstitution(item.issuing_institution||'');
    setLicense(item.registration_number||'');setAuthority(item.issuing_authority||'');
    setJurisdiction(item.jurisdiction||'');setExpiry(item.credential_expiry||'');
    setExperience(String(item.experience_years??''));setApproaches(item.approach_keys||'');
    setTraining(item.relevant_training||'');setStatement(item.applicant_statement||'');
    setAdults(!!item.population_adults);setIndependent(!!item.independent_practice);
    document.querySelector('.scope-application-form')?.scrollIntoView({behavior:'smooth',block:'start'});
  };
  const beginReverification=(item:any)=>continueApplication({...item,reverification_of:item.name});
  return <><ProfessionalEditor/><RequiredFieldsNotice/>
    {applications.error&&<InlineNotice tone="danger">{w("Your scope applications could not be loaded.")} <Button onClick={()=>void applications.refresh()}>{w("Retry")}</Button></InlineNotice>}
    <section className="scope-application-workspace">
      <div className="scope-application-form" data-tour-unsaved={dirty ? 'true' : 'false'} onChange={()=>{contextApplied.current=true;setDirty(true)}}>
        <p className="eyebrow">{w("STEP")} {step+1} {w("OF")} 4</p>
        <div className="step-progress" aria-hidden="true">{[0,1,2,3].map(index=><span key={index} data-complete={index<=step}/>)}</div>
        <h2 ref={headingRef} tabIndex={-1}>{w(step===0?"Choose Your Service Scopes":step===1?"Scope Qualifications":step===2?"Relevant Experience":"Review Your Application")}</h2>
        <p className="supporting">{w(step===0?"Select each service you are qualified to provide. Each is reviewed separately.":"Documents are private to authorized reviewers.")}</p>
        {reverificationOf&&<InlineNotice>{w("A renewal request does not extend an expired approval. If the credential has expired, this service remains unavailable until a reviewer records a new approval.")}</InlineNotice>}
        {!services.data||!initialized?<Skeleton/>:services.data.length===0?<EmptyState title={w("No Service Applications Are Open Yet.")}>{w("The service catalog is present in draft and remains non-bookable until the medical lead approves its terminology and local credential requirements.")}</EmptyState>:<>
          {step===0&&<><TextField label={w("Search service scopes")} value={serviceSearch} onChange={e=>setServiceSearch(e.target.value)}/><fieldset className="scope-selection"><legend className="sr-only">{w("Services you want to provide")}</legend>{services.data.filter((item:any)=>item.label.toLocaleLowerCase().includes(serviceSearch.toLocaleLowerCase())).map((item:any)=><div key={item.id}><Checkbox variant="card" description={w("Evidence and approved scope are required.")} label={item.label} checked={selectedServices.includes(item.id)} disabled={!!reverificationOf||applications.data?.some((application:any)=>application.service===item.id&&!['Draft','Clarification'].includes(application.status))} onChange={event=>{const next=event.target.checked?[...selectedServices,item.id]:selectedServices.filter(id=>id!==item.id);setSelectedServices(next);setService(next[0]||'');}}/>{selectedServices.includes(item.id)&&<p className="supporting">{item.clinical_review_status!=='Approved'&&w("Clinical definition review pending. Applying does not authorize bookings.")} {item.credential_requirements}</p>}</div>)}</fieldset><p className="supporting">{w("Selected services")}: {selectedServices.length}</p></>}
          {step===1&&<>
          <TextField label={w("Professional category")} value={category} onChange={e=>setCategory(e.target.value)} required />
          <TextField label={w("Relevant qualification")} value={qualification} onChange={e=>setQualification(e.target.value)} required />
          <TextField label={w("Issuing institution")} value={institution} onChange={e=>setInstitution(e.target.value)} required />
          <TextField label={w("Registration or license number")} value={license} onChange={e=>setLicense(e.target.value)} />
          <TextField label={w("Issuing authority")} value={authority} onChange={e=>setAuthority(e.target.value)} />
          <TextField label={w("Jurisdiction")} value={jurisdiction} onChange={e=>setJurisdiction(e.target.value)} />
          <TextField label={w("Valid From")} type="date" value={validFrom} onChange={e=>setValidFrom(e.target.value)} />
          <p className="supporting">{w("Manage certification records and competency self-assessments in Professional Profile and Credentials above. Historical scope text remains in earlier submissions.")}</p>
          <TextField label={w("Valid Until")} type="date" value={expiry} onChange={e=>setExpiry(e.target.value)} />
          </>}
          {step===2&&<>
          <TextField label={w("Years of relevant experience")} type="number" min="0" max="60" value={experience} onChange={e=>setExperience(e.target.value)} />
          <fieldset className="scope-selection"><legend>{w("Treatment approaches (optional)")}</legend>
            <p className="supporting">{w("Select only approaches you are trained to use. Your evidence is reviewed separately.")}</p>
            {approachOptions.length?approachOptions.map((item:any)=><Checkbox key={item.id} variant="card" label={locale==='am'?item.label_am||item.label_en:locale==='om'?item.label_om||item.label_en:item.label_en} description={item.definition} checked={selectedApproaches.includes(item.id)} onChange={event=>setApproaches((event.target.checked?[...selectedApproaches,item.id]:selectedApproaches.filter(key=>key!==item.id)).join('\n'))}/>):<p>{w("No reviewed approaches are available to select yet. You can still submit your service application.")}</p>}
            <p className="supporting">{w("If an approach is not listed, describe your training below. Selecting an approach does not grant approval.")}</p>
          </fieldset>
          {unlistedApproaches.length>0&&<InlineNotice tone="info"><p>{w("These previous entries are not selectable catalog approaches. Move them to your training description or remove them before saving.")}</p><ul>{unlistedApproaches.map(key=><li key={key}>{key}</li>)}</ul><Button variant="secondary" onClick={()=>{setTraining([training,...unlistedApproaches].filter(Boolean).join('\n'));setApproaches(selectedApproaches.filter(key=>!unlistedApproaches.includes(key)).join('\n'));setDirty(true);}}>{w("Move to training description")}</Button></InlineNotice>}
          <label className="field">{w("Relevant training")}<textarea rows={3} value={training} onChange={e=>setTraining(e.target.value)} /></label>
          <label className="field">{w("Why are you prepared to provide this service?")}<textarea rows={4} value={statement} onChange={e=>setStatement(e.target.value)} /></label>
          <Checkbox label={w("My application is limited to adult care.")} checked={adults} onChange={e=>setAdults(e.target.checked)} />
          <Checkbox label={w("I practice independently (optional).")} checked={independent} onChange={e=>setIndependent(e.target.checked)} />
          </>}
          {step===2&&<section className="guided-evidence"><h3>{w("Documents for Each Requested Service")}</h3><p>{w("Your CV is shared with the reviewer. Attach a License or registration PDF to each scope for credential verification. Additional qualification or training evidence supports the individual review.")}</p><Button variant="secondary" loading={action.busy} onClick={()=>save(false)}>{w("Save draft to attach documents")}</Button>{selectedServices.map(key=>{const item=applications.data?.find((value:any)=>value.service===key);return item?<details key={key}><summary>{item.service_label} · {w((item.scope_evidence||[]).some((e:any)=>e.evidence_type==='License or registration')?"License evidence uploaded":"License evidence missing")}</summary><ScopeEvidencePanel item={item} canUpload={['Draft','Clarification'].includes(item.status)} refresh={applications.refresh}/></details>:null})}</section>}
          {step===3&&<dl className="scope-application-preview"><div><dt>{w('Services you want to provide')}</dt><dd>{services.data.filter((item:any)=>selectedServices.includes(item.id)).map((item:any)=>item.label).join(', ')}</dd></div>
            {[['Professional competencies',competencies],['Credentials',certifications],['Credential valid from, if applicable',validFrom],['Professional category',category],['Relevant qualification',qualification],['Issuing institution',institution],['Registration or license number',license],['Issuing authority',authority],['Jurisdiction',jurisdiction],['Credential expiry, if applicable',expiry],['Years of relevant experience',experience],['Relevant training',training],['Why are you prepared to provide this service?',statement]].map(([label,value])=><div key={label}><dt>{w(label)}</dt><dd>{value||w('Not provided')}</dd></div>)}
            <div><dt>{w('My application is limited to adult care.')}</dt><dd>{w(adults?'Yes':'No')}</dd></div>
          </dl>}
          <div className="scope-form-actions">
            {step>0&&<Button variant="quiet" disabled={action.busy} onClick={()=>changeStep(step-1)}>{w('Back')}</Button>}
            <Button variant="secondary" disabled={!service||action.busy} loading={action.busy} onClick={()=>save(false)}>{w('Save draft')}</Button>
            {step<3?<Button disabled={action.busy||(step===0&&!selectedServices.length)} onClick={()=>changeStep(step+1)}>{w('Continue')}</Button>:<Button disabled={action.busy} loading={action.busy} onClick={()=>save(true)}>{w('Submit for review')}</Button>}
          </div>
        </>}
        {action.error&&<InlineNotice tone="danger">{w(action.error)}</InlineNotice>}
        {action.success&&!dirty&&<InlineNotice tone="success">{w(action.success)}</InlineNotice>}
      </div>
      <section className="scope-application-list"><h2>{w("Your Applications")}</h2>{!applications.data?<Skeleton/>:applications.data.length?applications.data.map((item:any)=><article className="scope-application-row" key={item.name}><strong>{item.service_label}</strong><span>{w(item.status)}</span>{item.reverification_of&&<InlineNotice>{w('Credential re-verification for an existing scope. A reviewer must approve it before expired credentials can be used.')}</InlineNotice>}{['Approved','Expired'].includes(item.status)&&(item.credential_expired||item.status==='Expired')&&!item.scope_eligible&&<InlineNotice tone="danger">{w('This credential has expired. The service is paused until a reviewer approves updated credentials.')}</InlineNotice>}{item.clarification_request&&<InlineNotice>{item.clarification_request}</InlineNotice>}{item.decision_reason&&<p>{item.decision_reason}</p>}{item.restrictions&&<p>{w("Restrictions:")} {item.restrictions}</p>}{item.appeals?.map((appeal:any)=><InlineNotice key={appeal.name}>{w('Reconsideration')}: {w(appeal.status)}{appeal.reviewer_reason?` — ${appeal.reviewer_reason}`:''}</InlineNotice>)}{['Rejected','Suspended','Expired'].includes(item.status)&&!item.appeals?.some((appeal:any)=>appeal.basis_assessment===item.latest_assessment)&&<div className="scope-appeal-form"><label className="field">{w('Request reconsideration')}<textarea rows={3} maxLength={1600} value={appealStatements[item.name]||''} onChange={e=>setAppealStatements({...appealStatements,[item.name]:e.target.value})} /></label><Button loading={action.busy} onClick={()=>void action.run(async()=>{const statement=(appealStatements[item.name]||'').trim();if(!statement)throw new Error(w('Explain why this decision should be reconsidered.'));await journeyApi.submitScopeAppeal(item.name,statement);await applications.refresh();})}>{w('Submit reconsideration')}</Button></div>}{['Draft','Clarification'].includes(item.status)&&<Button variant="secondary" onClick={()=>continueApplication(item)}>{w('Continue this application')}</Button>}{['Approved','Expired'].includes(item.status)&&['Approved','Revoked'].includes(item.service_scope_status)&&!applications.data?.some((other:any)=>other.reverification_of===item.name)&&<Button variant="secondary" onClick={()=>beginReverification(item)}>{w('Update credential details')}</Button>}<ScopeEvidencePanel item={item} canUpload={['Draft','Clarification'].includes(item.status)} refresh={applications.refresh}/>{item.status==='Approved'&&<p>{w("This specific scope is approved. Offerings still require the matching service configuration and published availability.")}</p>}</article>):<EmptyState title={w("No Scope Applications Yet.")} />}</section>
    </section>
    <details className="scope-review-policy"><summary>{w("Review Rubric and Policies")}</summary><p>{w("Apply for each service separately. Clinic affiliations do not establish competence, and approval is always decided by a human reviewer.")}</p><p>{w("TeleTena’s proposed vetting rubric is versioned for medical-lead review. Credential verification is manual. Upload your PDF CV in Account and attach supporting evidence to each service application.")}</p></details>
  </>;
}

const checks=[['identity_reviewed','Identity evidence reviewed'],['credential_verified','Required credential independently verified'],['qualification_relevant','Qualification relevant to this service'],['experience_adequate','Scope-relevant experience assessed'],['approach_evidence_reviewed','Approach evidence reviewed'],['adult_scope_appropriate','Adult population scope appropriate'],['interview_completed','Structured interview or assessment completed']] as const;
export function VettingQueue() {
  const { w } = useLocale();
  const queue=useResource(journeyApi.myScopeApplications);const action=useAction();
  const appeals=useResource(journeyApi.scopeAppeals);
  const operational=useResource(loadOperationalScopeReviews);
  const [appealDecisions,setAppealDecisions]=useState<Record<string,string>>({});
  const [appealReasons,setAppealReasons]=useState<Record<string,string>>({});
  const [values,setValues]=useState<Record<string,Record<string,boolean>>>({});
  const [findings,setFindings]=useState<Record<string,string>>({});
  const [restrictions,setRestrictions]=useState<Record<string,string>>({});
  const [decision,setDecision]=useState<Record<string,string>>({});
  const [selectedReview,setSelectedReview]=useState<string|null>(null);
  const [reviewStep,setReviewStep]=useState(0);
  const reviewSteps=["Application & documents","Verify credentials","Assess this scope","Decision & next steps"];
  const reviewHeading=useRef<HTMLHeadingElement>(null);
  useEffect(()=>{if(selectedReview){reviewHeading.current?.focus({preventScroll:true});reviewHeading.current?.scrollIntoView({block:'start'});}},[selectedReview,reviewStep]);
  const [scoredCriteria,setScoredCriteria]=useState<Record<string,Record<string,{score:string;rationale:string;evidence:string}>>>({});
  const [credentialVerification,setCredentialVerification]=useState<Record<string,{source:string;checked_on:string;evidence:string;reference:string}>>({});
  const updateCredential=(application:string,field:'source'|'checked_on'|'evidence'|'reference',value:string)=>setCredentialVerification(current=>{
    const previous=current[application]||{source:'',checked_on:'',evidence:'',reference:''};
    return {...current,[application]:{...previous,[field]:value}};
  });
  const updateScored=(application:string,key:string,field:'score'|'rationale'|'evidence',value:string)=>setScoredCriteria(current=>{
    const previous=current[application]?.[key]||{score:'',rationale:'',evidence:''};
    return {...current,[application]:{...current[application],[key]:{...previous,[field]:value}}};
  });
  return <><PageTitle title={w("Service-scope Vetting")} description={w("Review each professional scope separately. A missing mandatory criterion cannot be offset by other evidence.")} /><RequiredFieldsNotice/>
    <details className="review-policy-details" hidden={!!selectedReview}><summary>{w("Review Rubric and Policies")}</summary><VettingRubricManager /></details>
    <details className="scope-review-appeals" hidden={!!selectedReview}><summary>{w('Booked Appointments Needing Scope Review')}</summary><p className="supporting">{w('This queue contains scheduling references only. It does not grant access to patient records or private notes.')}</p>{operational.error&&<InlineNotice tone="danger">{w('Operational review items could not be loaded.')} <Button onClick={()=>void operational.refresh()}>{w('Retry')}</Button></InlineNotice>}{!operational.data?<Skeleton/>:operational.data.filter((item:any)=>item.status!=='Cleared').length?operational.data.filter((item:any)=>item.status!=='Cleared').map((item:any)=><article className="scope-review-card" key={item.name}><header><div><h3>{item.clinician_name||w('Clinician unavailable')}</h3><p className="supporting">{item.service_label} · {w(item.reason_code)} · {w(item.status)}</p></div><span>{item.scheduled_start?new Date(item.scheduled_start).toLocaleString():w('date unavailable')}</span></header><p className="supporting">{w('Appointment reference')}: {item.appointment}</p><TextField label={w('Reviewer rationale')} value={appealReasons[item.name]||''} onChange={e=>setAppealReasons({...appealReasons,[item.name]:e.target.value})}/><div className="actions">{item.status==='Open'&&<Button variant="secondary" loading={action.busy} onClick={()=>void action.run(async()=>{const rationale=(appealReasons[item.name]||'').trim();if(!rationale)throw new Error(w('Record a rationale for this operational action.'));await journeyApi.resolveScopeAppointmentReview(item.name,'Acknowledge',rationale);await operational.refresh()})}>{w('Acknowledge')}</Button>}<Button loading={action.busy} onClick={()=>void action.run(async()=>{const rationale=(appealReasons[item.name]||'').trim();if(!rationale)throw new Error(w('Record a rationale for this operational action.'));await journeyApi.resolveScopeAppointmentReview(item.name,'Clear',rationale);await operational.refresh()})}>{w('Clear after scope is current')}</Button></div>{action.error&&<InlineNotice tone="danger">{w(action.error)}</InlineNotice>}</article>):<EmptyState title={w('No Booked Appointments Need Scope Review.')} />}</details>
    <details className="scope-review-appeals" hidden={!!selectedReview}><summary>{w('Reconsideration Requests')}</summary>{appeals.error&&<InlineNotice tone="danger">{w('Reconsideration requests could not be loaded.')} <Button onClick={()=>void appeals.refresh()}>{w('Retry')}</Button></InlineNotice>}{!appeals.data?<Skeleton/>:appeals.data.length?appeals.data.map((item:any)=><article className="scope-review-card" key={item.name}><header><div><h3>{item.display_name||w('Clinician application')}</h3><p className="supporting">{item.service_label} · {w('Previously')} {w(item.basis_decision)}</p></div><span>{item.submitted_at?new Date(item.submitted_at).toLocaleDateString():w('date unavailable')}</span></header><p><strong>{w('Applicant statement')}</strong></p><p>{item.applicant_statement}</p><details><summary>{w('Prior Reviewer Rationale')}</summary><p>{item.basis_reason}</p></details><TextField label={w('Reviewer rationale')} value={appealReasons[item.name]||''} onChange={e=>setAppealReasons({...appealReasons,[item.name]:e.target.value})} /><Select label={w('Reconsideration outcome')} value={appealDecisions[item.name]||''} onChange={e=>setAppealDecisions({...appealDecisions,[item.name]:e.target.value})}><option value="">{w('Choose decision')}</option><option value="Upheld">{w('Uphold previous decision')}</option><option value="Reopen">{w('Reopen for new evidence and full review')}</option></Select><Button loading={action.busy} onClick={()=>void action.run(async()=>{const reason=(appealReasons[item.name]||'').trim();if(!reason||!appealDecisions[item.name])throw new Error(w('Choose an outcome and record the reviewer rationale.'));await journeyApi.reviewScopeAppeal(item.name,appealDecisions[item.name] as 'Upheld'|'Reopen',reason);await Promise.all([appeals.refresh(),queue.refresh()]);})}>{w('Record reconsideration outcome')}</Button></article>):<EmptyState title={w('No Reconsideration Requests Are Waiting.')} />}</details>
    {queue.error&&<InlineNotice tone="danger">{w("The vetting queue could not be loaded.")} <Button onClick={()=>void queue.refresh()}>{w("Retry")}</Button></InlineNotice>}
    {!selectedReview&&queue.data&&<section className="vetting-queue" data-tour="reviewer-vetting"><h2>{w("Choose an Application to Review")}</h2><p>{w("Review one clinician and one service at a time. General approval and service approval are separate.")}</p>{queue.data.map((item:any)=><div className="vetting-queue-row" key={item.name}><div><strong>{item.display_name||w('Clinician application')}</strong><p>{item.service_label} · {w(item.status)}</p><small>{w("License evidence")}: {(item.scope_evidence||[]).some((e:any)=>e.evidence_type==='License or registration')?w("Uploaded"):w("Missing")}</small></div><Button variant="secondary" disabled={!['Submitted','Resubmitted','Clarification','Approved'].includes(item.status)} onClick={()=>{setSelectedReview(item.name);setReviewStep(0);}}>{w("Review application")}</Button></div>)}</section>}
    {selectedReview&&<Button variant="quiet" onClick={()=>setSelectedReview(null)}>{w("Back to review queue")}</Button>}
    {!queue.data?<Skeleton/>:queue.data.length?queue.data.filter((item:any)=>item.name===selectedReview).map((item:any)=><article className="scope-review-card guided-review" key={item.name} data-tour="reviewer-vetting" data-tour-unsaved="true">
      <header><div><h2>{item.display_name||w('Clinician application')}</h2><p className="supporting">{item.service_label} · {w(item.status)} · {w('Submitted')} {item.submitted_at?new Date(item.submitted_at).toLocaleDateString():w('date unavailable')}</p></div><span>{w('Rubric')} {item.rubric_version}</span></header>
      <nav className="guided-step-nav" aria-label={w("Review progress")}>{reviewSteps.map((label,index)=><button key={label} type="button" aria-current={reviewStep===index?"step":undefined} onClick={()=>setReviewStep(index)}><span>{index+1}</span>{w(label)}</button>)}</nav>
      <h3 ref={reviewHeading} tabIndex={-1}>{w(reviewSteps[reviewStep])}</h3>
      <div hidden={reviewStep!==0}>
      {item.reverification_of&&<InlineNotice>{w('Credential renewal for a previously approved scope. Check the new credential evidence and validity dates; do not treat the earlier approval as renewed.')}</InlineNotice>}
      <dl className="scope-review-facts"><dt>{w('Professional category')}</dt><dd>{item.professional_category}</dd><dt>{w('Qualification')}</dt><dd>{item.qualification} · {item.issuing_institution}</dd><dt>{w("Professional competencies")}</dt><dd>{item.competencies||w("Not provided")}</dd><dt>{w("Credentials")}</dt><dd>{item.certifications||w("Not provided")}</dd><dt>{w("License valid from")}</dt><dd>{item.credential_valid_from||w("Not provided")}</dd><dt>{w('Registration')}</dt><dd>{item.registration_number||w('Not provided')} · {item.issuing_authority||w('Authority not provided')}</dd><dt>{w('Jurisdiction and expiry')}</dt><dd>{item.jurisdiction||w('Not provided')} · {item.credential_expiry||w('No expiry recorded')}</dd><dt>{w('Relevant experience')}</dt><dd>{item.experience_years} {w('years')} · {w('adult scope')} {item.population_adults?w('confirmed'):w('not confirmed')}</dd><dt>{w('Approaches and training')}</dt><dd>{item.approach_keys||w('None listed')} · {item.relevant_training||w('No training summary')}</dd><dt>{w('Affiliations')}</dt><dd>{item.clinic_affiliations||w('Independent or not provided; affiliation is not competence evidence')}</dd><dt>{w('Application evidence')}</dt><dd>{item.resume_uploaded?w('Private CV uploaded'):w('CV missing')}</dd></dl>
      <ProfessionalReview clinician={item.clinician} submission={item.professional_submission}/>{item.resume_uploaded&&<Button variant="secondary" onClick={async()=>{try{const response=await fetch(`/api/method/tele_tena.api.presentation.download_resume?clinician=${encodeURIComponent(item.clinician)}`,{credentials:'same-origin',cache:'no-store'});if(!response.ok)throw new Error();const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='clinician-cv.pdf';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch{window.alert(w('Private evidence could not be opened. Check reviewer authorization and retry.'))}}}>{w('Open private CV')}</Button>}
      {!!item.scope_evidence?.length&&<ScopeEvidencePanel item={item} canUpload={false} refresh={()=>Promise.resolve()}/>}
      {!(item.scope_evidence||[]).some((evidence:any)=>evidence.evidence_type==='License or registration')&&<InlineNotice><p>{w("License evidence is missing for this scope. A CV is not license evidence. Choose Request information so the applicant can upload a License or registration PDF and resubmit.")}</p><p>{w("Evidence references beside assessment scores are optional. License evidence for credential verification is required before approval.")}</p></InlineNotice>}
      </div><div hidden={reviewStep!==1}>
      {item.credential_verification&&<details className="credential-verification-history"><summary>{w('Previous Credential Verification Source')}</summary><p><strong>{w('Verification source')}:</strong> {item.credential_verification.source}</p><p><strong>{w('Checked on')}:</strong> {item.credential_verification.checked_on}</p><p><strong>{w('Source reference')}:</strong> {item.credential_verification.source_reference}</p><p><strong>{w('Evidence revision')}:</strong> v{item.credential_verification.evidence.revision} · {item.credential_verification.evidence.sha256}</p></details>}
      <fieldset className="credential-verification-inputs"><legend>{w('Credential source verification')}</legend><p className="supporting">{w('Mark verified only after you checked the issuing authority. Approval requires a source, date, reference, and license evidence from this scope.')}</p>
        <Button variant="quiet" disabled={action.busy} onClick={()=>{setCredentialVerification(current=>({...current,[item.name]:{source:'',checked_on:'',evidence:'',reference:''}}));setValues(current=>({...current,[item.name]:{...current[item.name],credential_verified:false}}));}}>{w("Clear unfinished credential check")}</Button>
        <TextField label={w('Verification source')} required={decision[item.name]==='Approved'||!!values[item.name]?.credential_verified} value={credentialVerification[item.name]?.source||''} maxLength={180} onChange={event=>updateCredential(item.name,'source',event.target.value)}/>
        <TextField label={w('Checked on')} required={decision[item.name]==='Approved'||!!values[item.name]?.credential_verified} type="date" value={credentialVerification[item.name]?.checked_on||''} onChange={event=>updateCredential(item.name,'checked_on',event.target.value)}/>
        <TextField label={w('Source reference')} required={decision[item.name]==='Approved'||!!values[item.name]?.credential_verified} value={credentialVerification[item.name]?.reference||''} maxLength={180} hint={w('Use a registry record or reviewer reference; do not enter a password or access token.')} onChange={event=>updateCredential(item.name,'reference',event.target.value)}/>
        <Select disabled={!(item.scope_evidence||[]).some((e:any)=>e.evidence_type==='License or registration')} label={w('License evidence reviewed')} required={decision[item.name]==='Approved'||!!values[item.name]?.credential_verified} value={credentialVerification[item.name]?.evidence||''} onChange={event=>updateCredential(item.name,'evidence',event.target.value)}><option value="">{w((item.scope_evidence||[]).some((e:any)=>e.evidence_type==='License or registration')?'Choose license evidence':'No license document attached')}</option>{(item.scope_evidence||[]).filter((evidence:any)=>evidence.evidence_type==='License or registration').map((evidence:any)=><option key={evidence.id} value={evidence.id}>{w(evidence.evidence_type)} · v{evidence.revision}</option>)}</Select>
      </fieldset>
      </div><div hidden={reviewStep!==2}>
      <Button variant="quiet" disabled={action.busy} onClick={()=>setScoredCriteria(current=>({...current,[item.name]:Object.fromEntries(Object.entries(current[item.name]||{}).filter(([,value])=>['0','1','2','3'].includes(value.score)&&value.rationale.trim()))}))}>{w("Clear unfinished assessment")}</Button>
      {item.rubric_definition&&<details className="vetting-scored-rubric" open><summary>{w('Structured Evidence Assessment')} · {item.rubric_definition.version} ({w(item.rubric_definition.status)})</summary>
        <InlineNotice>{w(item.rubric_definition.approval_note)} {w('Scores organize reviewer evidence only. They do not make or replace a human scope decision.')}</InlineNotice>
        {(item.rubric_definition.scored_criteria||[]).map((criterion:any,index:number)=><details className="assessment-dimension" key={criterion.key} open={index===0}><summary>{w(criterion.label)} · {w(scoredCriteria[item.name]?.[criterion.key]?.score&&scoredCriteria[item.name]?.[criterion.key]?.rationale?.trim()?"Complete":"Not assessed")}</summary><fieldset className="vetting-rubric-dimension"><legend className="sr-only">{w(criterion.label)}</legend>
          <Select label={w('Evidence score (0–3)')} required={decision[item.name]==='Approved'||!!scoredCriteria[item.name]?.[criterion.key]?.rationale||!!scoredCriteria[item.name]?.[criterion.key]?.evidence} value={scoredCriteria[item.name]?.[criterion.key]?.score||''} onChange={event=>updateScored(item.name,criterion.key,'score',event.target.value)}>
            <option value="">{w('Choose a score')}</option>{[0,1,2,3].map(score=><option key={score} value={score}>{score}</option>)}
          </Select>
          <TextField label={w('Reviewer rationale for this dimension')} required={decision[item.name]==='Approved'||!!scoredCriteria[item.name]?.[criterion.key]?.score||!!scoredCriteria[item.name]?.[criterion.key]?.evidence} value={scoredCriteria[item.name]?.[criterion.key]?.rationale||''} onChange={event=>updateScored(item.name,criterion.key,'rationale',event.target.value)} maxLength={800}/>
          <Select label={w('Private evidence reference (optional)')} value={scoredCriteria[item.name]?.[criterion.key]?.evidence||''} onChange={event=>updateScored(item.name,criterion.key,'evidence',event.target.value)}>
            <option value="">{w(item.scope_evidence?.length?'No reference selected (optional)':'No documents attached to this scope')}</option>{(item.scope_evidence||[]).map((evidence:any)=><option key={evidence.id} value={evidence.id}>{w(evidence.evidence_type)} · v{evidence.revision}</option>)}
          </Select>
        </fieldset></details>)}
      </details>}
      <fieldset><legend>{w('Mandatory and supporting assessment')}</legend>{checks.map(([key,label])=><Checkbox key={key} label={w(label)} required={decision[item.name]==='Approved'&&key!=='approach_evidence_reviewed'} checked={!!values[item.name]?.[key]} onChange={e=>setValues({...values,[item.name]:{...values[item.name],[key]:e.target.checked}})} />)}</fieldset>
      </div><div hidden={reviewStep!==3}>
      <ul className="review-readiness" aria-label={w("Approval readiness")}>{[
        ["License evidence attached",(item.scope_evidence||[]).some((e:any)=>e.evidence_type==='License or registration')],
        ["Credential check recorded",!!values[item.name]?.credential_verified&&!!credentialVerification[item.name]?.source&&!!credentialVerification[item.name]?.checked_on&&!!credentialVerification[item.name]?.reference&&!!credentialVerification[item.name]?.evidence],
        ["Mandatory checks passed",['identity_reviewed','credential_verified','qualification_relevant','experience_adequate','adult_scope_appropriate','interview_completed'].every(key=>values[item.name]?.[key])],
        ["Assessment scores and reasons complete",(item.rubric_definition?.scored_criteria||[]).every((criterion:any)=>{const value=scoredCriteria[item.name]?.[criterion.key];return value&&['0','1','2','3'].includes(value.score)&&value.rationale.trim();})],
        ["Service definition approved",item.definition_review_status==='Approved'&&!!item.definition_active],
      ].map(([label,ready])=><li key={String(label)}><span>{w(String(label))}</span><strong>{w(ready?"Ready":"Needs attention")}</strong></li>)}</ul>
      <p className="supporting">{w("Approve only when all required checks and evidence pass. Request information to let the applicant correct missing documents; decline when requirements are not met.")}</p>
      <label className="field">{w('Structured Findings and Decision Reason')}<span className="required-marker" aria-hidden="true"> *</span><textarea aria-label={w('Structured Findings and Decision Reason')} required maxLength={2000} rows={3} value={findings[item.name]||''} onChange={e=>setFindings({...findings,[item.name]:e.target.value})}/></label><label className="field">{w('Restrictions')}<textarea maxLength={1000} rows={2} value={restrictions[item.name]||''} onChange={e=>setRestrictions({...restrictions,[item.name]:e.target.value})}/></label>
      <div className="actions"><Select required label={w('Decision')} value={decision[item.name]||''} onChange={e=>setDecision({...decision,[item.name]:e.target.value})}><option value="">{w('Choose decision')}</option><option value="Clarification">{w('Request information')}</option><option value="Approved">{w('Approve this scope')}</option><option value="Rejected">{w('Reject this scope')}</option><option value="Suspended">{w('Suspend this scope')}</option><option value="Expired">{w('Mark expired')}</option></Select><Button loading={action.busy} disabled={!item.rubric_definition||action.busy} onClick={()=>void action.run(async()=>{if(!decision[item.name])throw new ApiError('review_decision_required');const scored_criteria=Object.fromEntries(Object.entries(scoredCriteria[item.name]||{}).map(([key,value])=>[key,{score:value.score,rationale:value.rationale,evidence:value.evidence?[value.evidence]:[]}]));await journeyApi.reviewScopeApplication({application:item.name,decision:decision[item.name],...values[item.name],findings:findings[item.name],restrictions:restrictions[item.name],credential_source:credentialVerification[item.name]?.source,credential_checked_on:credentialVerification[item.name]?.checked_on,credential_evidence:credentialVerification[item.name]?.evidence,credential_source_reference:credentialVerification[item.name]?.reference,scored_criteria});await queue.refresh()})}>{w('Record human decision')}</Button></div>
      </div><div className="guided-review-footer"><Button variant="quiet" disabled={reviewStep===0} onClick={()=>setReviewStep(reviewStep-1)}>{w("Back")}</Button>{reviewStep<3&&<Button onClick={()=>setReviewStep(reviewStep+1)}>{w("Continue")}</Button>}<span>{w("Your entries stay while you move between steps. A decision is recorded only when you confirm it.")}</span></div>
      {action.error&&<InlineNotice tone="danger">{w(action.error)}</InlineNotice>}
    </article>):<EmptyState title={w("No Scope Applications Are Waiting for Review.")} />}</>;
}
