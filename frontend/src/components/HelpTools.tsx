import { useRef, useState } from 'react';
import { CircleHelp, BookOpen, Route } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useSession } from '../hooks/useSession';
import { useLocale } from '../hooks/useLocale';
import { Button, Dialog } from './ui';
import WorkspaceTour from './WorkspaceTour';
import './HelpTools.css';

const reviewerGuide = [
  ['1. General application', 'Review professional identity, qualifications and the private resume. General approval creates clinician access; it does not approve any service scope.'],
  ['2. Service definition', 'The medical lead reviews the service definition, credential requirements and supported workflows. A draft service can accept applications but cannot authorize practice.'],
  ['3. Scope documents', 'Open one service application. Review its qualifications and private evidence. A resume describes experience; a License or registration document supports the credential check. Documents must be attached to this particular scope.'],
  ['4. Credential verification', 'Check the issuing authority yourself. Record the source, actual check date, source reference and uploaded license document. A source reference identifies the registry record or your documented check; it is not a password. Do not mark a credential verified merely because a file was uploaded.'],
  ['5. Assessment', 'Complete every score and explain its rationale. Document references beside scores are optional. Mandatory identity, credential, qualification, adult-care, experience and interview checks must pass; high scores cannot compensate for missing requirements.'],
  ['6. Decision', 'Approve only when the evidence and requirements pass. Request information when evidence is missing: clear unfinished verification, choose Request information and state what is needed. The applicant can then edit, upload documents and resubmit. Reject with a meaningful reason when requirements are not met.'],
  ['7. After approval', 'Each approved scope permits matching offerings. The clinician publishes an offering and availability before discovery or requests. Expired or revoked approval blocks new bookings; existing appointments remain preserved for operational review. Vetting permissions never grant private patient-record access.'],
];
export default function HelpTools() {
  const {session}=useSession();const {w}=useLocale();const location=useLocation();
  const [open,setOpen]=useState(false);const [guide,setGuide]=useState(false);
  const opener=useRef<HTMLButtonElement>(null);
  const reviewer=!!session?.roles.includes('Tele Tena Approver');
  const role=reviewer?'admin':session?.profile?.kind==='clinician'?'clinician':session?.profile?.kind==='patient'?'patient':'applicant';
  const protectedWork=/consultation|sign-in|onboarding|payments/.test(location.pathname);
  return <>
    <button ref={opener} className="help-island" type="button" aria-label={w('Help & tours')} title={w('Help & tours')} aria-haspopup="dialog" onClick={()=>{setGuide(false);setOpen(true);}}><CircleHelp size={24}/></button>
    {session&&<WorkspaceTour role={role}/>}
    <Dialog open={open} onOpenChange={setOpen} title={w('Help & tours')} description={w('Guidance for this workspace. Help never submits a form or records a decision.')} focusReturnTarget={opener.current} size={guide?'wide':'default'}>
      {guide&&reviewer?<div className="help-guide" tabIndex={0} aria-label={w('Reviewer guide')}><Button variant="quiet" onClick={()=>setGuide(false)}>{w('Back to help')}</Button><h3>{w('Reviewer guide')}</h3><p>{w('Use this guide while reviewing. All final decisions remain human decisions.')}</p>{reviewerGuide.map(([title,body])=><section key={title}><h4>{w(title)}</h4><p>{w(body)}</p></section>)}</div>:<div className="help-menu">
        {session&&<section><Route size={24}/><h3>{w('Guided workspace tour')}</h3><p>{w('Learn the main controls without changing any records.')}</p><Button disabled={protectedWork} onClick={()=>{setOpen(false);window.setTimeout(()=>window.dispatchEvent(new Event('teletena-start-tour')),100);}}>{w('Start guided tour')}</Button>{protectedWork&&<p className="supporting">{w('Finish the current protected step before starting a tour. You can still read help here.')}</p>}</section>}
        {reviewer&&<section><BookOpen size={24}/><h3>{w('Reviewer guide')}</h3><p>{w('Application review, private evidence, credential checks, scope decisions and correction workflows.')}</p><Button variant="secondary" onClick={()=>setGuide(true)}>{w('Open reviewer guide')}</Button></section>}
        {!reviewer&&<section><h3>{w('Applications and access')}</h3><p>{w('Clinicians apply for each service separately. Upload private documents in Professional review, save the draft, then submit. If information is requested, open the application, correct it and resubmit. Approval is always manual.')}</p><p>{w('For sign-in, use an enabled code-delivery method or choose password access. A code proves contact possession, not professional approval.')}</p></section>}
      </div>}
    </Dialog>
  </>;
}
