import {Link} from 'react-router-dom';
import {ArrowRight,ChevronDown,FileCheck2,GraduationCap,ShieldCheck,UserRound} from 'lucide-react';
import {useLocale} from '../hooks/useLocale';
import './ClinicianApplicationGuide.css';

// A public explanation of existing steps; never collects evidence or grants a role.
const stages=[
 {title:'Your Professional Profile',summary:'Tell us who you are and how you practice.',questions:['Your professional category, competencies and care languages.','Your qualifications, issuing institutions and relevant experience.','A short public introduction, separate from your private application.'],note:'Save your progress and return to it. Your application details are not a public clinician profile.'},
 {title:'Credentials and Supporting Documents',summary:'Prepare the information a human reviewer needs.',questions:['Registration or license number, issuing authority and practice jurisdiction, where applicable.','Validity start and expiry dates, certifications and relevant training.','Your résumé and documents supporting the services you want to provide.'],note:'Upload readable PDF evidence within the displayed file limits. Documents stay private to you and authorized reviewers. Uploading a document does not verify a credential.'},
 {title:'Services You Want to Provide',summary:'Choose the scopes that match your actual qualifications.',questions:['Select one or several services from the reviewed application catalog.','Explain your preparation, supervised experience and adult-population competence for each service.','Select treatment approaches from the controlled list and attach the relevant evidence to each scope.'],note:'A general application approval does not approve every scope. A catalog draft may accept an application without being available for bookings.'},
 {title:'Independent or Clinic-Based Practice',summary:'Describe your practice without granting access to records.',questions:['You may practice independently or list more than one clinic affiliation.','Keep affiliation details accurate and distinguish a requested link from a verified affiliation.'],note:'Clinic affiliation is reviewed separately. It is not evidence of clinical competence and does not grant access to patient records.'},
 {title:'Human Review and Individual Decisions',summary:'Understand what happens after submission.',questions:['Reviewers assess your general application and each service-scope application separately.','They may ask for clarification, additional evidence or an interview/structured assessment.','Each scope can be pending, approved or declined, with reasons and any restrictions.'],note:'Correct and resubmit when information is requested. If a scope is declined, use the supported reconsideration route; do not create duplicate accounts. Approval does not imply regulatory accreditation.'},
 {title:'From Approval to Your First Consultation',summary:'Publish only what your current approvals permit.',questions:['Create an offering within an approved scope: service description, duration, price, language and format.','Publish recurring hours or date exceptions; saving a draft alone does not publish availability.','For immediate requests, enable request availability with a connected workspace and a feasible free opening.'],note:'Manual pause takes priority. Expired or suspended approval prevents new bookings. Existing appointments, privacy choices and consent remain protected.'},
];
export default function ClinicianApplicationGuide(){
 const{w}=useLocale();
 return <section className="clinician-application-guide" id="clinician-application" aria-labelledby="application-guide-title">
  <header><p className="eyebrow">{w('For Clinicians')}</p><h2 id="application-guide-title">{w('Your Application, Step by Step')}</h2><p>{w('Prepare once, save your progress and follow each decision. Here is what we ask and why, without a long form to read upfront.')}</p></header>
  <ol className="application-guide-path" aria-label={w('Application Journey')}>
   {[['Profile',UserRound],['Evidence',GraduationCap],['Scope Review',ShieldCheck],['Publish',FileCheck2]].map(([label,Icon])=>{const Mark=Icon as typeof UserRound;return <li key={String(label)}><Mark size={22}/><span>{w(String(label))}</span></li>;})}
  </ol>
  <div className="application-guide-questions">{stages.map((stage,index)=><details key={stage.title} open={index===0}>
   <summary><span className="application-guide-number">{String(index+1).padStart(2,'0')}</span><span><strong>{w(stage.title)}</strong><small>{w(stage.summary)}</small></span><ChevronDown size={22} aria-hidden="true"/></summary>
   <div className="application-guide-answer"><ul>{stage.questions.map(question=><li key={question}>{w(question)}</li>)}</ul><p>{w(stage.note)}</p></div>
  </details>)}</div>
  <footer><p>{w('Ready to Apply?')} <span>{w('Contact verification starts your application; it never grants clinical approval.')}</span></p><Link className="button" to="/sign-in?intent=clinician&mode=register">{w('Apply as a Clinician')}<ArrowRight size={18}/></Link></footer>
 </section>;
}
