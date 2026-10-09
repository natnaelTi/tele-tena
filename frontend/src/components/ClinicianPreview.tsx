import { useCallback } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { journeyApi } from "../journey-api";
import type { Offer } from "../journey-api";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";
import { Dialog, InlineNotice, Skeleton, Button } from "./ui";
import { money } from "./Domain";
/** Patient-facing, approved backend facts only. No credentials inferred from a title. */
export function ClinicianPreview({ offer, close }: { offer: Offer; close: () => void }) {
  const { w, t } = useLocale();
  const load = useCallback(() => journeyApi.publicClinician(offer.clinician_id), [offer.clinician_id]);
  const resource = useResource(load);
  const experience = resource.data?.trust_indicators?.session_experience;
  const currentOffering = resource.data?.services?.some((service: any) => service.offering === offer.id);
  return <Dialog open onOpenChange={value => { if (!value) close(); }} title={offer.display_name} description={w("Review approved services and sharing choices before booking.")} className="clinician-preview-dialog">
    <div className="profile-preview-identity"><div className="avatar large" aria-hidden="true">{offer.display_name.slice(0, 1)}</div><div><h3>{offer.service_category || offer.label}</h3><span className="verified"><ShieldCheck size={18} />{w("Approved for this service")}</span></div></div>
    {resource.error ? <InlineNotice tone="danger">{w("This clinician profile is unavailable or no longer approved.")} <Button variant="secondary" onClick={() => void resource.refresh()}>{w("Try again")}</Button></InlineNotice> : !resource.data ? <Skeleton /> : <>
      <dl className="profile-preview-facts"><div><dt>{w("Approved service")}</dt><dd>{offer.label}</dd></div><div><dt>{w("Care language")}</dt><dd>{offer.care_languages?.map(language => ({ en: 'English', am: 'አማርኛ', om: 'Afaan Oromo' })[language]).join(', ') || w("Not listed")}</dd></div><div><dt>{w("Consultation")}</dt><dd>{w(offer.consultation_format === 'audio' ? 'Audio' : 'Video')} · {offer.minutes} {w("minutes")}</dd></div><div><dt>{w("Published fee")}</dt><dd>ETB {money(offer.price)}</dd></div><div><dt>{t("sessionExperienceMetric")}</dt><dd>{experience?.average == null ? t("sessionExperienceNew") : `${experience.average} / 5`} · {experience?.sample_count ?? 0} {t("evidenceCount")}</dd></div></dl>
      <p className="supporting">{w("Credential review and patient feedback are separate signals. Neither guarantees a clinical outcome.")}</p>
      <div className="actions"><Link className="button secondary" to={'/patient/clinicians/' + offer.clinician_id}>{w("View full profile")}</Link>{currentOffering && <Link className="button" to={'/patient/book/' + offer.id}>{w("Choose a time")}</Link>}</div>
      {!currentOffering && <InlineNotice>{w("This offering is no longer available. Close this preview and choose another service.")}</InlineNotice>}
    </>}
  </Dialog>;
}
