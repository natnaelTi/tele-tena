import {AvailabilityStatus} from '../components/AvailabilityStatus';
import {Avatar} from '../components/ProfilePhoto';
import {useCallback,useEffect} from 'react';
import {Link,useLocation,useParams,useSearchParams} from 'react-router-dom';
import {journeyApi} from '../journey-api';
import {PageTitle,money} from '../components/Domain';
import {Button,EmptyState,InlineNotice,Select,Skeleton} from '../components/ui';
import {useLocale} from '../hooks/useLocale';
import {useSession} from '../hooks/useSession';
import {useResource} from '../hooks/useResource';
export {PatientRequestsWorkspace as PatientOpenRequests,PatientRequestsWorkspace as PatientRequestDetail,PatientRequestsWorkspace as PatientRequestOfferDetail,ClinicianRequestsWorkspace as ClinicianRequestInbox} from './RequestWorkspaces';
function usePolling<T>(loader:()=>Promise<T>,delay=30000){const resource=useResource(loader);useEffect(()=>{const timer=setInterval(()=>void resource.refresh(),delay);return()=>clearInterval(timer);},[delay,resource.refresh]);return resource;}

export function PublicClinicianProfile(){
  const {t,w}=useLocale();
  const {session}=useSession();
  const canBook=session?.profile?.kind==='patient'&&session.roles.includes('Tele Tena Patient');
  const {clinicianId=''}=useParams();
  const load=useCallback(()=>journeyApi.publicClinician(clinicianId),[clinicianId]);
  const resource=usePolling(load,30000);
  const location=useLocation();
  const [serviceParams,setServiceParams]=useSearchParams();
  const initialOffering=typeof location.state?.selectedOffering==='string'?location.state.selectedOffering:'';
  const selectedService=serviceParams.get('service')||initialOffering;
  // A public offering identifier preserves booking context after refresh. No care
  // query, disclosure or patient information belongs in this URL.
  useEffect(()=>{
    if(initialOffering&&!serviceParams.has('service')){
      const next=new URLSearchParams(serviceParams);next.set('service',initialOffering);
      setServiceParams(next,{replace:true});
    }
  },[initialOffering,serviceParams,setServiceParams]);
  const selectService=(offering:string)=>{
    const next=new URLSearchParams(serviceParams);next.set('service',offering);
    setServiceParams(next,{replace:true});
  };
  const bookingService=resource.data?.services.find((item:any)=>item.offering===selectedService)||resource.data?.services[0];
  if(resource.error)return <InlineNotice tone="danger">{w("This clinician profile is unavailable or no longer approved.")} <Button variant="secondary" onClick={()=>void resource.refresh()}>{w("Retry")}</Button></InlineNotice>;
  if(!resource.data)return <Skeleton/>;
  return <section className="public-clinician-page">
    <PageTitle title={w("Meet Your Clinician")} />
    <div className="public-profile-layout"><section className="public-profile-main"><section className="public-profile-identity"><Avatar className="large" url={resource.data.photo_url} name={resource.data.display_name}/><div><h2>{resource.data.display_name}</h2><p>{resource.data.approval_meaning}</p></div></section>
    {resource.data.introduction&&<section className="patient-dashboard-panel"><h2>{w("Introduction")}</h2><p className="public-profile-introduction">{resource.data.introduction}</p></section>}<section className="patient-dashboard-panel public-profile-services"><h2>{w("Approved Services")}</h2><div className="public-profile-scopes" aria-label={w("Approved services")}>{[...new Set<string>(resource.data.services.map((service:any)=>service.service_category||service.label))].map(label=><span className="scope-chip" key={label}>{label}</span>)}</div>{resource.data.services.length?resource.data.services.map((service:any)=><article className="public-profile-service" key={service.offering}><div><h3>{service.label}</h3><p className="supporting">{service.minutes} {w("minutes")} · {w(service.consultation_format==='audio'?'Audio':'Video')} · ETB {money(service.price)}</p></div><Link className="button secondary" to={'/care/select/'+service.offering}>{w(canBook?'Choose a time':'Sign in to Book')}</Link></article>):<EmptyState title={w("No Published Service Times Are Available Yet.")} />}</section><section className="patient-dashboard-panel"><h2>{t("sessionExperienceMetric")}</h2><p>{resource.data.trust_indicators.session_experience.average===null?t(resource.data.trust_indicators.session_experience.status==="new"?"sessionExperienceNew":"sessionExperienceMore"):resource.data.trust_indicators.session_experience.average+' / 5'} · {resource.data.trust_indicators.session_experience.sample_count} {t("evidenceCount")}</p><p className="supporting">{t("sessionExperienceExplainer")}</p></section></section><aside className="public-profile-aside">
    {bookingService&&<section className="public-profile-booking"><h2>{w("Book a Conversation")}</h2>{resource.data.services.length>1?<Select label={w("Choose a service")} value={bookingService.offering} onChange={event=>selectService(event.target.value)}>{resource.data.services.map((service:any)=><option key={service.offering} value={service.offering}>{service.label}</option>)}</Select>:<p>{bookingService.label}</p>}<AvailabilityStatus value={bookingService.availability}/><p>{bookingService.description}</p><p className="public-profile-price">ETB {money(bookingService.price)}<span> / {bookingService.minutes} {w("minutes")}</span></p><dl className="summary-list"><dt>{w("Format")}</dt><dd>{w(bookingService.consultation_format==='audio'?'Audio':'Video')}</dd><dt>{w("Timezone")}</dt><dd>{bookingService.availability?.timezone||w("Not listed")}</dd></dl><Link className="button primary" to={'/care/select/'+bookingService.offering}>{w(canBook?"Choose a time":"Sign in to Book")}</Link></section>}
    <section className="trust-indicators" aria-labelledby="trust-indicators-title"><h2 id="trust-indicators-title">{t("trustIndicators")}</h2><dl>
      <div><dt>{t("professionalReview")}</dt><dd>{t("manuallyReviewedScopes")}</dd></div>
      <div><dt>{t("responseBehavior")}</dt><dd>{resource.data.trust_indicators.responsiveness.rate_percent===null
        ? resource.data.trust_indicators.responsiveness.status==="new"?t("noRequestHistory"): <>{t("trustInsufficientData")} · {resource.data.trust_indicators.responsiveness.sample_count} {t("immediateRequestsPresented")}</>
        : <>{resource.data.trust_indicators.responsiveness.rate_percent}% {t("offerResponseRate")} · {resource.data.trust_indicators.responsiveness.response_count}/{resource.data.trust_indicators.responsiveness.sample_count} {t("immediateRequestsPresented")}</>}</dd></div>
      {resource.data.trust_indicators.confirmation_responsiveness&&<div><dt>{w('Booking Confirmation Response')}</dt><dd>{resource.data.trust_indicators.confirmation_responsiveness.rate_percent===null?w('More response history is needed'):resource.data.trust_indicators.confirmation_responsiveness.rate_percent+'% '+w('responded within three minutes')} · {resource.data.trust_indicators.confirmation_responsiveness.sample_count} {w('presented booking prompts')}</dd></div>}
      <div><dt>{t("reliability")}</dt><dd>{resource.data.trust_indicators.reliability.rate_percent===null
        ? resource.data.trust_indicators.reliability.status==="new"?t("noAppointmentHistory"): <>{t("trustInsufficientData")} · {resource.data.trust_indicators.reliability.sample_count} {t("completedAndCancelledSessions")}</>
        : <>{resource.data.trust_indicators.reliability.rate_percent}% {t("clinicianCancellations")} · {resource.data.trust_indicators.reliability.clinician_cancelled_count}/{resource.data.trust_indicators.reliability.sample_count} {t("completedAndCancelledSessions")}</>}</dd></div>
    </dl></section>
    </aside></div>
  </section>;
}
