import { Link, useParams } from "react-router-dom";
import { useResource } from "../hooks/useResource";
import { useSession } from "../hooks/useSession";
import { useLocale } from "../hooks/useLocale";
import { journeyApi } from "../journey-api";
import { date, timezone } from "../components/Domain";
import { Button, InlineNotice, Skeleton } from "../components/ui";
import Consultation from "../features/consultations/Consultation";
export default function ConsultationPage() {
  const { id } = useParams();
  const resource = useResource(journeyApi.appointments);
  const { session } = useSession();
  const { t } = useLocale();
  const base =
    session?.profile?.kind === "clinician" ? "/clinician" : "/patient";
  if (resource.error)
    return (
      <InlineNotice tone="danger">
        The consultation could not be loaded.{" "}
        <Button onClick={() => void resource.refresh()}>Retry</Button>
      </InlineNotice>
    );
  if (!resource.data) return <Skeleton />;
  const appointment = resource.data.find((a) => a.id === id);
  if (!appointment)
    return (
      <InlineNotice tone="danger">
        This consultation is unavailable to your account.
      </InlineNotice>
    );
  return (
    <div data-appointment-id={appointment.id} className="consultation-page">
      <Link className="text-link" to={base + "/appointments"}>
        Back to appointments
      </Link>
      <div className="page-title">
        <div>
          <p className="eyebrow">YOUR CONSULTATION</p>
          <h1>{appointment.service_label}</h1>
          <p>
            {date(appointment.start)} · {timezone} · {appointment.minutes}{" "}
            minutes
          </p>
        </div>
      </div>
      <Consultation key={appointment.id} appointment={appointment} t={t} />
      <p className="supporting">
        No recording or transcription. Leaving does not end the session for
        everyone. No automatic charges are based on connection time.
      </p>
    </div>
  );
}
