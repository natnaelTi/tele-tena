import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { pendingCareQuery } from "../care-intent";
import { api } from "../api";
import {
  Button,
  Checkbox,
  InlineNotice,
  Select,
  Skeleton,
  TextField,
} from "../components/ui";
import { destination, useSession } from "../hooks/useSession";
import { useLocale } from "../hooks/useLocale";
import { journeyApi } from "../journey-api";
import WorkspaceTour from "../components/WorkspaceTour";
type Answers = {
  name?: string;
  adult?: boolean;
  consent?: boolean;
  language?: string;
  share_name?: boolean;
  share_history?: boolean;
  statement?: string;
  affiliations?: string;
  requested_services?: string[];
};
export default function Onboarding() {
  const { session, refresh } = useSession();
  const { w } = useLocale();
  const navigate = useNavigate();
  const routeLocation = useLocation();
  const [params] = useSearchParams();
  const [step, setStep] = useState(0);
  const [kind, setKind] = useState("patient");
  const [answers, setAnswers] = useState<Answers>({});
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [catalog, setCatalog] = useState<{id:string;label:string}[]>([]);
  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [resumeBusy, setResumeBusy] = useState(false);
  useEffect(() => {
    api<{ kind: string; step: number; answers: Answers }>(
      "tele_tena.api.contact_auth.onboarding",
    )
      .then((draft) => {
        setKind(
          params.get("intent") === "clinician" ? "clinician" : draft.kind,
        );
        setStep(draft.step);
        setAnswers(draft.answers);
        setReady(true);
      })
      .catch(() =>
        setError(
          "Your saved progress could not be loaded. Reload to try again.",
        ),
      );
    void api<{id:string;label:string}[]>("services").then(setCatalog).catch(()=>undefined);
    void journeyApi.resumeStatus().then(value=>setResumeUploaded(value.uploaded)).catch(()=>undefined);
  }, [params]);
  if (session?.profile) return <Navigate to={session.profile.kind === "patient" && pendingCareQuery() ? "/patient/discovery" : destination(session)} replace />;
  const clinician = kind === "clinician";
  const titles = clinician
    ? [
        "Your professional identity",
        "Your experience and service scope",
        "A few final details",
        "Review your application",
      ]
    : [
        "What should we call you?",
        "A thoughtful start",
        "Your language. Your privacy.",
        "You’re ready to find care.",
      ];
  const update = (value: Partial<Answers>) => {
    setAnswers({ ...answers, ...value });
    setSaved(false);
  };
  async function save(next: number, complete = false) {
    if (complete && clinician && (!resumeUploaded || !(answers.requested_services||[]).length)) {
      setError("Upload a resume and select at least one service to request before submitting.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api(
        "tele_tena.api.contact_auth.save_onboarding",
        { kind, step: next, answers, complete: complete ? 1 : 0 },
        true,
      );
      setStep(next);
      setSaved(true);
      if (complete) {
        const current = await refresh();
        const invitationToken=(routeLocation.state as {relationshipInvitationToken?:string}|null)?.relationshipInvitationToken;
        navigate(invitationToken && current?.profile?.kind==='patient' ? '/relationship-invitation' : current?.profile?.kind === 'patient' && pendingCareQuery() ? '/patient/discovery' : destination(current),
          { replace:true, state: invitationToken ? {relationshipInvitationToken:invitationToken} : undefined });
      }
    } catch {
      setError(
        "Please check this step and try again. Adult eligibility and consent are required to finish.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
    <section className="guided-panel">
      <p className="eyebrow">
        {clinician ? "CLINICIAN APPLICATION" : "YOUR SPACE FOR CARE"} · STEP{" "}
        {step + 1} OF 4
      </p>
      <div className="step-progress" aria-label={`Step ${step + 1} of 4`}>
        {[0, 1, 2, 3].map((value) => (
          <span key={value} data-complete={value <= step} />
        ))}
      </div>
      <h1>{titles[step]}</h1>
      {error && <InlineNotice tone="danger">{error}</InlineNotice>}
      {!ready ? (
        <Skeleton />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void save(Math.min(step + 1, 3), step === 3);
          }}
        >
          {step === 0 && (
            <>
              <p>
                {clinician
                  ? "Use the professional name your credentials are issued under."
                  : "A preferred name or alias is enough. You choose whether to share it when you book."}
              </p>
              <div data-tour={clinician?"applicant-profile":undefined}><TextField
                label={
                  clinician ? "Professional name" : "Preferred name or alias"
                }
                value={answers.name || ""}
                maxLength={120}
                required
                onChange={(e) => update({ name: e.target.value })}
              /></div>
            </>
          )}
          {step === 1 &&
            (clinician ? (
              <>
                <label className="field">
                  Credentials and requested services
                  <textarea
                    required
                    maxLength={2000}
                    rows={6}
                    value={answers.statement || ""}
                    onChange={(e) => update({ statement: e.target.value })}
                  />
                </label>
                <p className="supporting">
                  Describe your qualification, registration and the services you
                  would like reviewed. This demonstration accepts synthetic
                  information only. Upload a PDF resume (up to 5 MB); receipt
                  does not mean your credentials are verified.
                </p>
                <fieldset className="scope-picker" data-tour="applicant-scopes"><legend>Services requested for approval</legend>{catalog.map(service=><Checkbox key={service.id} label={service.label} checked={(answers.requested_services||[]).includes(service.id)} onChange={e=>update({requested_services:e.target.checked?[...(answers.requested_services||[]),service.id]:(answers.requested_services||[]).filter(x=>x!==service.id)})}/>)}</fieldset>
                <label className="field" data-tour="applicant-resume">Resume (PDF, up to 5 MB)<input type="file" accept="application/pdf,.pdf" disabled={resumeBusy} onChange={async e=>{const file=e.target.files?.[0];if(!file)return;if(file.size>5*1024*1024){setError("Choose a PDF no larger than 5 MB.");return;}setResumeBusy(true);setError("");try{const base64=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(",")[1]||"");reader.onerror=()=>reject(new Error("Read failed"));reader.readAsDataURL(file);});await journeyApi.uploadResume(file.name,base64);setResumeUploaded(true);}catch{setError("The resume could not be uploaded. Choose a valid PDF and try again.");}finally{setResumeBusy(false);e.target.value="";}}}/>{resumeUploaded&&<span role="status">Resume uploaded for authorized review. <button type="button" className="text-button" onClick={()=>void journeyApi.removeResume().then(()=>setResumeUploaded(false)).catch(()=>setError("Resume could not be removed."))}>Remove</button></span>}</label>
              </>
            ) : (
              <>
                <p>
                  This service is for adults. Please review these choices before
                  continuing.
                </p>
                <Checkbox
                  label="I am 18 or older."
                  checked={!!answers.adult}
                  required
                  onChange={(e) => update({ adult: e.target.checked })}
                />
                <Checkbox
                  label="I consent to storing my profile and the information I choose to share for this care journey."
                  checked={!!answers.consent}
                  required
                  onChange={(e) => update({ consent: e.target.checked })}
                />
              </>
            ))}
          {step === 2 &&
            (clinician ? (
              <>
                <TextField
                  label="Clinic affiliations (optional)"
                  value={answers.affiliations || ""}
                  onChange={(e) => update({ affiliations: e.target.value })}
                  hint="Affiliation does not grant access to patient records."
                />
                <Checkbox
                  label="I am 18 or older."
                  checked={!!answers.adult}
                  required
                  onChange={(e) => update({ adult: e.target.checked })}
                />
                <Checkbox
                  label="I consent to storing these details for manual application review."
                  checked={!!answers.consent}
                  required
                  onChange={(e) => update({ consent: e.target.checked })}
                />
              </>
            ) : (
              <>
                <Select
                  label="Preferred language"
                  value={answers.language || "en"}
                  onChange={(e) => update({ language: e.target.value })}
                >
                  <option value="en">English</option>
                  <option value="am">አማርኛ</option>
                  <option value="om">Afaan Oromo</option>
                </Select>
                <p>
                  Start with private defaults. You can change these for each
                  booking.
                </p>
                <Checkbox
                  label="Share my preferred name by default"
                  checked={!!answers.share_name}
                  onChange={(e) => update({ share_name: e.target.checked })}
                />
                <Checkbox
                  label="Share my saved history by default"
                  checked={!!answers.share_history}
                  onChange={(e) => update({ share_history: e.target.checked })}
                />
              </>
            ))}
          {step === 3 && (
            <>
              <p>
                {clinician
                  ? "Your application will be submitted for manual review. You cannot accept bookings until your professional status and service scopes are approved."
                  : "You can explore available clinicians and choose what to share before each appointment."}
              </p>
              <dl className="summary-list">
                <dt>Name</dt>
                <dd>{answers.name}</dd>
                <dt>{clinician ? "Credentials & scope" : "Default sharing"}</dt>
                <dd>
                  {clinician
                    ? answers.statement
                    : answers.share_name
                      ? "Preferred name"
                      : "Preferred name stays private"}
                </dd>
              </dl>
            </>
          )}
          <div className="form-actions" data-tour={step===3&&clinician?"applicant-submit":undefined}>
            {step > 0 && (
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() => void save(step - 1)}
              >
                {w("Back")}
              </Button>
            )}
            <Button type="submit" loading={busy}>
              {step === 3
                ? clinician
                  ? "Submit for review"
                  : w("Find care")
                : w("Continue")}
            </Button>
          </div>
          <Button
            variant="quiet"
            data-tour={clinician?"applicant-save":undefined}
            disabled={busy}
            onClick={() => void save(step)}
          >
            Save for later
          </Button>
          {saved && (
            <p role="status">Progress saved. You can return to this step.</p>
          )}
        </form>
      )}
    </section>{clinician&&saved&&<WorkspaceTour role="applicant"/>}
    </>
  );
}
