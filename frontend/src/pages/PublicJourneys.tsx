import {Link} from 'react-router-dom';
import ClinicianApplicationGuide from '../components/ClinicianApplicationGuide';
import InteractiveProductTour from '../components/InteractiveProductTour';
import PublicExperience,{PublicSteps} from '../components/PublicExperience';
import {useLocale} from '../hooks/useLocale';
export default function PublicJourney({clinician=false}:{clinician?:boolean}){
 const{w}=useLocale();
 if(clinician)return <PublicExperience initialMode="clinician"/>;
 return <main className="public-info-page"><p className="eyebrow">{w('How TeleTena works')}</p><h1>{w('From Finding Care to a Real Conversation.')}</h1><p>{w('Browse mental-health and counseling services, choose a clinician and book a time—or request an available expert.')}</p><div className="public-hero-actions"><Link className="button" to="/care">{w('Find Care')}</Link><Link className="button secondary" to="/request">{w('Request a Consultation')}</Link></div><InteractiveProductTour/><ClinicianApplicationGuide/><PublicSteps/>
 <section className="public-faq" id="public-faq"><div><p className="eyebrow">{w('Help & FAQ')}</p><h2>{w('Before You Begin.')}</h2><p>{w('Adults 18+ · Not an emergency service.')}</p></div><div>{[
 ['Can I browse before creating an account?','Yes. Explore public profiles and services first. Sign in when you choose a service to book or publish a request.'],
 ['What will my clinician see?','Your sharing choices are visible and editable. History files are selected individually for the treating clinician, not broadcast with an open request.'],
 ['What happens after the consultation?','Find deliberately shared summaries in your account. Private clinician notes remain separate.']
 ].map(([q,a])=><details key={q}><summary>{w(q)}<span aria-hidden="true">+</span></summary><p>{w(a)}</p></details>)}</div></section><Link className="text-link" to="/policies">{w('Terms & Privacy')}</Link></main>;
}
