import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { journeyApi } from "../journey-api";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";
import { Button, Card, InlineNotice, Skeleton } from "../components/ui";
import { money, PageTitle } from "../components/Domain";
export default function ServiceDetails() {
  const { offering = '' } = useParams();
  const resource = useResource(journeyApi.discover);
  const { w } = useLocale();
  if (resource.error) return <InlineNotice tone="danger">{w("Care options could not be loaded.")} <Button onClick={() => void resource.refresh()}>{w("Try again")}</Button></InlineNotice>;
  if (!resource.data) return <Skeleton />;
  const offer = resource.data.find(item => item.id === offering);
  if (!offer) return <InlineNotice>{w("This service is no longer available.")} <Link to="/patient/discovery">{w("Find care")}</Link></InlineNotice>;
  return <><Link className="text-link" to={'/patient/clinicians/' + offer.clinician_id}><ArrowLeft size={16} />{w("View full profile")}</Link><PageTitle title={offer.label} description={w("Understand the service before choosing a time.")} /><div className="service-details-layout"><Card><div className="profile-preview-identity"><div className="avatar" aria-hidden="true">{offer.display_name.slice(0,1)}</div><div><h2>{offer.display_name}</h2><span className="verified"><ShieldCheck size={18} />{w("Approved for this service")}</span></div></div>{offer.description && <p>{offer.description}</p>}<dl className="profile-preview-facts"><div><dt>{w("Approved service")}</dt><dd>{offer.service_category}</dd></div><div><dt>{w("Duration")}</dt><dd>{offer.minutes} {w("minutes")}</dd></div><div><dt>{w("Published fee")}</dt><dd>ETB {money(offer.price)}</dd></div><div><dt>{w("Session format")}</dt><dd>{w(offer.consultation_format === 'audio' ? 'Audio' : 'Video')}</dd></div><div><dt>{w("Care language")}</dt><dd>{offer.care_languages?.map(language => ({ en: 'English', am: 'አማርኛ', om: 'Afaan Oromo' })[language]).join(', ') || w("Not listed")}</dd></div><div><dt>{w("Age group")}</dt><dd>{w("Adults 18+")}</dd></div></dl></Card><Card><h2>{w("Before you book")}</h2><InlineNotice>{w("This service is not an emergency response service.")}</InlineNotice><p>{w("Review what you share, the final price and the booking policy before confirming.")}</p><Link className="button full" to={'/patient/book/' + offer.id}>{w("Choose a time")}</Link></Card></div></>;
}
