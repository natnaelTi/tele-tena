import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "./ui";
import { journeyApi } from "../journey-api";
import { useSession } from "../hooks/useSession";
import { useLocale } from "../hooks/useLocale";

type TourStep={title:string;text:string;path:string;target:string};
const routes:Record<string,{id:string;steps:TourStep[]}>={
  patient:{id:"patient-home",steps:[
    {title:"Find care",text:"Search and filter available clinician services.",path:"/patient/discovery",target:"patient-discovery"},
    {title:"Choose a time",text:"Pick an open slot, review what you’ll share and confirm the price.",path:"/patient/discovery",target:"patient-discovery"},
    {title:"Private requests",text:"Post what you need, compare private offers and choose before funds are reserved.",path:"/patient/requests",target:"patient-private-requests"},
    {title:"Appointments",text:"Review upcoming sessions, requests and past consultations.",path:"/patient/appointments",target:"patient-appointments"},
    {title:"Consultations",text:"Join when the appointment is available and read published summaries.",path:"/patient/appointments",target:"patient-appointments"},
    {title:"Balance and privacy",text:"Review your balance, activity and sharing defaults in Account.",path:"/patient/account",target:"patient-account"},
  ]},
  clinician:{id:"clinician-today",steps:[
    {title:"Your practice",text:"Check upcoming sessions and actions for today.",path:"/clinician",target:"clinician-today"},
    {title:"Profile and resume",text:"Complete your professional profile and upload evidence for review. Approval is manual.",path:"/clinician/account",target:"clinician-account"},
    {title:"Services and schedule",text:"Publish approved services, then set a timezone-based weekly schedule.",path:"/clinician/availability",target:"clinician-availability"},
    {title:"Private offers",text:"Review your own quotes and outcomes. Accepted offers link to their consultation.",path:"/clinician/offers",target:"clinician-offers"},
    {title:"Appointments and calls",text:"Open an appointment to see its state and join the authorized room.",path:"/clinician/appointments",target:"clinician-appointments"},
    {title:"Consultation notes",text:"After ending a call, save a private note and choose whether to publish a summary.",path:"/clinician/appointments",target:"clinician-appointments"},
    {title:"Care records",text:"Open only the encounters you treated. Clinic affiliation does not grant access.",path:"/clinician/care",target:"clinician-care"},
  ]},
  approver:{id:"reviewer-applications",steps:[
    {title:"Application queue",text:"Review clinician names, application status and requested services.",path:"/admin/applications",target:"reviewer-applications"},
    {title:"Find a clinician",text:"Use the professional display name as the primary identifier.",path:"/admin/applications",target:"reviewer-applications"},
    {title:"Review evidence",text:"Open submitted resume evidence and assess it before deciding.",path:"/admin/applications",target:"reviewer-applications"},
    {title:"Make an application decision",text:"Approval is manual and does not automatically approve requested services.",path:"/admin/applications",target:"reviewer-applications"},
    {title:"Service scopes",text:"Approve each requested service separately. This does not grant access to care records.",path:"/admin/scopes",target:"reviewer-scopes"},
  ]},
  applicant:{id:"clinician-onboarding",steps:[
    {title:"Professional profile",text:"Enter the professional name that matches your credentials.",path:"/onboarding",target:"applicant-profile"},
    {title:"Request service scopes",text:"Select only the service types you want the reviewers to assess.",path:"/onboarding",target:"applicant-scopes"},
    {title:"Upload evidence",text:"Add a PDF resume. Receipt does not mean your credentials are verified.",path:"/onboarding",target:"applicant-resume"},
    {title:"Save and resume",text:"Save your progress before leaving this form.",path:"/onboarding",target:"applicant-save"},
    {title:"Manual review",text:"You cannot accept bookings until your application and each requested scope are approved.",path:"/onboarding",target:"applicant-submit"},
  ]},
};

export default function WorkspaceTour({role}:{role:"patient"|"clinician"|"admin"|"applicant"}){
  const {session}=useSession();const {w}=useLocale();const location=useLocation();const navigate=useNavigate();
  const selected=role==="admin"?"approver":role==="clinician"&&!session?.roles.includes("Tele Tena Clinician")?"pendingClinician":role;
  const config=selected==='pendingClinician'?{id:'clinician-onboarding',steps:[
    {title:"Professional profile",text:"Keep your professional profile and evidence up to date.",path:"/clinician/account",target:"clinician-account"},
    {title:"Review status",text:"See the current decision and any clarification requested by your reviewer.",path:"/clinician/vetting",target:"clinician-professional-review"},
    {title:"Requested scopes",text:"Each service needs its own human approval before publication.",path:"/clinician/vetting",target:"clinician-professional-review"},
    {title:"Private evidence",text:"Only you and authorized reviewers can access your submitted evidence.",path:"/clinician/vetting",target:"clinician-professional-review"},
    {title:"Approval first",text:"Services and patient requests become available only after the required approvals.",path:"/clinician/vetting",target:"clinician-professional-review"},
  ]}:routes[selected];
  const headingRef=useRef<HTMLHeadingElement>(null);
  const [state,setState]=useState<string|null>(null);const [ready,setReady]=useState(false);const [step,setStep]=useState(0);const [active,setActive]=useState(false);const [missing,setMissing]=useState(false);
  const load=useCallback(async()=>{try{const v=await journeyApi.tourState(config.id);setState(v.state);}catch{setState("Unavailable");}finally{setReady(true);}},[config.id]);
  useEffect(()=>{void load();},[load,session?.user]);
  const hidden=location.pathname.includes("/consultation")||location.pathname==="/sign-in"||(selected==="applicant"&&location.pathname!=="/onboarding");
  const current=config.steps[step];
  useEffect(()=>{if(!active||hidden||!current)return;let initial=true;const checkTarget=()=>{const target=Array.from(document.querySelectorAll<HTMLElement>(`[data-tour="${current.target}"]`)).find(element=>element.getClientRects().length>0&&getComputedStyle(element).visibility!="hidden"&&!element.closest('[aria-hidden="true"],[inert]'));setMissing(!target);if(target&&initial){initial=false;target.scrollIntoView({block:"center",behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"});headingRef.current?.focus({preventScroll:true});}};const timer=window.setTimeout(()=>{checkTarget();const observer=new MutationObserver(checkTarget);observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:["data-tour","aria-hidden","inert","style","class"]});cleanupObserver=()=>observer.disconnect();},180);let cleanupObserver=()=>{};return()=>{window.clearTimeout(timer);cleanupObserver();};},[active,hidden,current,location.pathname]);
  const navigateSafely=(path:string)=>{if(location.pathname===path)return;const dirty=document.querySelector('[data-tour-unsaved="true"]');if(dirty){setMissing(true);return;}navigate(path);};
  const begin=()=>{setStep(0);setActive(true);const first=config.steps[0];navigateSafely(first.path);};
  const finish=async(stateValue:"Dismissed"|"Completed")=>{setActive(false);setState(stateValue);try{await journeyApi.saveTourState(config.id,stateValue);}catch{setState("Unavailable");}};
  const next=()=>{if(step>=config.steps.length-1){void finish("Completed");return;}const nextStep=step+1;setStep(nextStep);navigateSafely(config.steps[nextStep].path);};
  const back=()=>{const previous=Math.max(0,step-1);setStep(previous);navigateSafely(config.steps[previous].path);};
  const showInvite=state!=="Dismissed"&&state!=="Completed"&&!active;
  if(hidden)return null;
  if(!ready||state==="Unavailable")return <button className="tour-replay" type="button" onClick={begin}>{w("Help & tours")}</button>;
  return <>
    {showInvite&&<aside className="tour-invite" aria-label={w("Quick tour")}> <span>{w("Want a quick tour of this workspace?")}</span><Button variant="secondary" onClick={begin}>{w("Take a quick tour")}</Button><button className="tour-dismiss" type="button" aria-label={w("Dismiss tour invitation")} onClick={()=>void finish("Dismissed")}>×</button></aside>}
    {!showInvite&&<button className="tour-replay" type="button" onClick={begin}>{w("Help & tours")}</button>}
    {active&&!hidden&&current&&<section className="tour-callout" role="dialog" aria-modal="false" aria-labelledby="tour-title"><p className="eyebrow">{w("QUICK TOUR")} · {step+1}/{config.steps.length}</p><h2 ref={headingRef} tabIndex={-1} id="tour-title">{w(current.title)}</h2><p>{w(current.text)}</p>{missing&&<p className="supporting" role="status">{w("This feature is not available in the current view. Continue to the next step.")}</p>}<div className="tour-progress" role="progressbar" aria-valuemin={1} aria-valuemax={config.steps.length} aria-valuenow={step+1}><span style={{width:`${((step+1)/config.steps.length)*100}%`}}/></div><div className="actions"><Button variant="quiet" onClick={back} disabled={step===0}>{w("Back")}</Button><Button variant="secondary" onClick={()=>void finish("Dismissed")}>{w("Skip")}</Button><Button onClick={next}>{step===config.steps.length-1?w("Finish"):w("Next")}</Button></div><button type="button" className="tour-close" onClick={()=>void finish("Dismissed")}>{w("Close tour")}</button></section>}
  </>;
}
