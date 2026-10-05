import { useState } from 'react';
import { journeyApi } from '../journey-api';
import { Button, Checkbox, EmptyState, InlineNotice, Select, Skeleton, TextField } from '../components/ui';
import { PageTitle } from '../components/Domain';
import { useAction } from '../hooks/useAction';
import { useResource } from '../hooks/useResource';
import { useLocale } from '../hooks/useLocale';

export function ClinicianScopeApplications() {
  const { w } = useLocale();
  const services = useResource(journeyApi.vettingServices);
  const applications = useResource(journeyApi.myScopeApplications);
  const action = useAction();
  const [service, setService] = useState('');
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

  const save = (submit:boolean) => void action.run(async()=>{
    if(!service) throw new Error('Choose an active reviewed service scope.');
    const values={professional_category:category,qualification,issuing_institution:institution,
      registration_number:license,issuing_authority:authority,jurisdiction,credential_expiry:expiry,
      experience_years:experience||'0',approach_keys:approaches,population_adults:adults,
      independent_practice:independent,clinic_affiliations:'',relevant_training:training,
      applicant_statement:statement};
    await journeyApi.saveScopeApplication(service,values,submit);
    await applications.refresh();
  });
  return <>
    <PageTitle title={w("Professional profile and scope review")} description={w("Apply for each service separately. Clinic affiliations do not establish competence, and approval is always decided by a human reviewer.")} />
    <InlineNotice>{w("TeleTena’s proposed vetting rubric is versioned for medical-lead review. Credential verification is manual. Upload your PDF CV in Account; the current release does not provide per-scope evidence attachments.")}</InlineNotice>
    {applications.error&&<InlineNotice tone="danger">{w("Your scope applications could not be loaded.")} <Button onClick={()=>void applications.refresh()}>{w("Retry")}</Button></InlineNotice>}
    <section className="scope-application-workspace">
      <div className="scope-application-form">
        <h2>{w("Apply for a service scope")}</h2>
        {!services.data?<Skeleton/>:services.data.length===0?<EmptyState title={w("No reviewed service scopes are open yet.")}>{w("The service catalog is present in draft and remains non-bookable until the medical lead approves its terminology and local credential requirements.")}</EmptyState>:<>
          <Select label={w("Service scope")} value={service} onChange={e=>setService(e.target.value)}><option value="">{w("Choose a service")}</option>{services.data.map((item:any)=><option key={item.id} value={item.id}>{item.label}</option>)}</Select>
          <TextField label={w("Professional category")} value={category} onChange={e=>setCategory(e.target.value)} required />
          <TextField label={w("Relevant qualification")} value={qualification} onChange={e=>setQualification(e.target.value)} required />
          <TextField label={w("Issuing institution")} value={institution} onChange={e=>setInstitution(e.target.value)} required />
          <TextField label={w("Registration or license number")} value={license} onChange={e=>setLicense(e.target.value)} />
          <TextField label={w("Issuing authority")} value={authority} onChange={e=>setAuthority(e.target.value)} />
          <TextField label={w("Jurisdiction")} value={jurisdiction} onChange={e=>setJurisdiction(e.target.value)} />
          <TextField label={w("Credential expiry, if applicable")} type="date" value={expiry} onChange={e=>setExpiry(e.target.value)} />
          <TextField label={w("Years of relevant experience")} type="number" min="0" max="60" value={experience} onChange={e=>setExperience(e.target.value)} />
          <label className="field">{w("Treatment approaches (one per line)")}<textarea rows={3} value={approaches} onChange={e=>setApproaches(e.target.value)} /></label>
          <label className="field">{w("Relevant training")}<textarea rows={3} value={training} onChange={e=>setTraining(e.target.value)} /></label>
          <label className="field">{w("Why are you prepared to provide this service?")}<textarea rows={4} value={statement} onChange={e=>setStatement(e.target.value)} /></label>
          <Checkbox label={w("My application is limited to adult care.")} checked={adults} onChange={e=>setAdults(e.target.checked)} />
          <Checkbox label={w("I practice independently (optional).")} checked={independent} onChange={e=>setIndependent(e.target.checked)} />
          <div className="actions"><Button variant="secondary" loading={action.busy} onClick={()=>save(false)}>{w("Save draft")}</Button><Button loading={action.busy} onClick={()=>save(true)}>{w("Submit for review")}</Button></div>
        </>}
        {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
      </div>
      <section className="scope-application-list"><h2>{w("Your applications")}</h2>{!applications.data?<Skeleton/>:applications.data.length?applications.data.map((item:any)=><article className="scope-application-row" key={item.name}><strong>{item.service_label}</strong><span>{w(item.status)}</span>{item.clarification_request&&<InlineNotice>{item.clarification_request}</InlineNotice>}{item.decision_reason&&<p>{item.decision_reason}</p>}{item.restrictions&&<p>{w("Restrictions:")} {item.restrictions}</p>}{item.status==='Approved'&&<p>{w("This specific scope is approved. Offerings still require the matching service configuration and published availability.")}</p>}</article>):<EmptyState title={w("No scope applications yet.")} />}</section>
    </section>
  </>;
}

const checks=[['identity_reviewed','Identity evidence reviewed'],['credential_verified','Required credential independently verified'],['qualification_relevant','Qualification relevant to this service'],['experience_adequate','Scope-relevant experience assessed'],['approach_evidence_reviewed','Approach evidence reviewed'],['adult_scope_appropriate','Adult population scope appropriate'],['interview_completed','Structured interview or assessment completed']] as const;
export function VettingQueue() {
  const { w } = useLocale();
  const queue=useResource(journeyApi.myScopeApplications);const action=useAction();
  const [values,setValues]=useState<Record<string,Record<string,boolean>>>({});
  const [findings,setFindings]=useState<Record<string,string>>({});
  const [restrictions,setRestrictions]=useState<Record<string,string>>({});
  const [decision,setDecision]=useState<Record<string,string>>({});
  return <><PageTitle title={w("Service-scope vetting")} description={w("Review each professional scope separately. A missing mandatory criterion cannot be offset by other evidence.")} />
    {queue.error&&<InlineNotice tone="danger">{w("The vetting queue could not be loaded.")} <Button onClick={()=>void queue.refresh()}>{w("Retry")}</Button></InlineNotice>}
    {!queue.data?<Skeleton/>:queue.data.length?queue.data.map((item:any)=><article className="scope-review-card" key={item.name}>
      <header><div><h2>{item.display_name||w('Clinician application')}</h2><p className="supporting">{item.service_label} · {w(item.status)} · {w('Submitted')} {item.submitted_at?new Date(item.submitted_at).toLocaleDateString():w('date unavailable')}</p></div><span>{w('Rubric proposed-1.0')}</span></header>
      <dl className="scope-review-facts"><dt>{w('Professional category')}</dt><dd>{item.professional_category}</dd><dt>{w('Qualification')}</dt><dd>{item.qualification} · {item.issuing_institution}</dd><dt>{w('Registration')}</dt><dd>{item.registration_number||w('Not provided')} · {item.issuing_authority||w('Authority not provided')}</dd><dt>{w('Jurisdiction and expiry')}</dt><dd>{item.jurisdiction||w('Not provided')} · {item.credential_expiry||w('No expiry recorded')}</dd><dt>{w('Relevant experience')}</dt><dd>{item.experience_years} {w('years')} · {w('adult scope')} {item.population_adults?w('confirmed'):w('not confirmed')}</dd><dt>{w('Approaches and training')}</dt><dd>{item.approach_keys||w('None listed')} · {item.relevant_training||w('No training summary')}</dd><dt>{w('Affiliations')}</dt><dd>{item.clinic_affiliations||w('Independent or not provided; affiliation is not competence evidence')}</dd><dt>{w('Application evidence')}</dt><dd>{item.resume_uploaded?w('Private CV uploaded'):w('CV missing')}</dd></dl>
      {item.resume_uploaded&&<Button variant="secondary" onClick={async()=>{try{const response=await fetch(`/api/method/tele_tena.api.presentation.download_resume?clinician=${encodeURIComponent(item.clinician)}`,{credentials:'same-origin',cache:'no-store'});if(!response.ok)throw new Error();const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='clinician-cv.pdf';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch{window.alert(w('Private evidence could not be opened. Check reviewer authorization and retry.'))}}}>{w('Open private CV')}</Button>}
      <fieldset><legend>{w('Mandatory and supporting assessment')}</legend>{checks.map(([key,label])=><Checkbox key={key} label={w(label)} checked={!!values[item.name]?.[key]} onChange={e=>setValues({...values,[item.name]:{...values[item.name],[key]:e.target.checked}})} />)}</fieldset>
      <label className="field">{w('Structured findings and decision reason')}<textarea rows={3} value={findings[item.name]||''} onChange={e=>setFindings({...findings,[item.name]:e.target.value})}/></label><label className="field">{w('Restrictions')}<textarea rows={2} value={restrictions[item.name]||''} onChange={e=>setRestrictions({...restrictions,[item.name]:e.target.value})}/></label>
      <div className="actions"><Select label={w('Decision')} value={decision[item.name]||''} onChange={e=>setDecision({...decision,[item.name]:e.target.value})}><option value="">{w('Choose decision')}</option><option value="Clarification">{w('Request information')}</option><option value="Approved">{w('Approve this scope')}</option><option value="Rejected">{w('Reject this scope')}</option><option value="Suspended">{w('Suspend this scope')}</option><option value="Expired">{w('Mark expired')}</option></Select><Button loading={action.busy} onClick={()=>void action.run(async()=>{if(!decision[item.name])throw new Error('Choose a decision.');await journeyApi.reviewScopeApplication({application:item.name,decision:decision[item.name],...values[item.name],findings:findings[item.name],restrictions:restrictions[item.name]});await queue.refresh()})}>{w('Record human decision')}</Button></div>
      {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}
    </article>):<EmptyState title={w("No scope applications are waiting for review.")} />}</>;
}
