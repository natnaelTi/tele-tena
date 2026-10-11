import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { pendingCareQuery } from "../care-intent";
import { api, ApiError } from "../api";
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
import { FileText, ShieldCheck } from "lucide-react";
import "./Onboarding.css";
type Answers = {
  name?: string;
  history?: string;
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
  const [scopeSearch, setScopeSearch] = useState("");
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
  // Retain stored step 3 as the ready screen for existing saved journeys.
  // Patient-only step 4 is inserted before it without reinterpreting old drafts.
  const steps = clinician ? [0, 1, 2, 3] : [0, 1, 2, 4, 3];
  const position = Math.max(0, steps.indexOf(step));
  const titles = clinician
    ? [
        "Your professional profile",
        "Qualifications & résumé",
        "Clinic affiliations",
        "Review your application",
      ]
    : [
        "A little about you",
        "Adult eligibility",
        "Your privacy defaults",
        "You’re ready",
        "Care background",
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
        const coupleToken=(routeLocation.state as {coupleInvitationToken?:string}|null)?.coupleInvitationToken;
        if(coupleToken&&kind==="patient"){navigate("/couple-invitation",{replace:true,state:{coupleInvitationToken:coupleToken}});return;}
        const invitationToken=(routeLocation.state as {relationshipInvitationToken?:string}|null)?.relationshipInvitationToken;
        navigate(invitationToken && current?.profile?.kind==='patient' ? '/relationship-invitation' : current?.profile?.kind === 'patient' && pendingCareQuery() ? '/patient/discovery' : destination(current),
          { replace:true, state: invitationToken ? {relationshipInvitationToken:invitationToken} : undefined });
      }
    } catch (failure) {
      const code = failure instanceof ApiError ? failure.code : "network_error";
      setError(code === "adult_required"
        ? "Please check this step and try again. Adult eligibility and consent are required to finish."
        : code === "resume_required"
          ? "Upload a resume and select at least one service to request before submitting."
          : code === "session_required" || code === "contact_required"
            ? "Your session has expired. Sign in again to continue your saved registration."
            : code === "registration_unavailable"
              ? "Registration is unavailable on this site. Your saved progress has not been submitted."
              : "We couldn’t save this step. Your entries are still here; check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
    <section className={`guided-panel onboarding-guided ${!clinician&&step===3?"onboarding-ready-page":""}`}>
      <p className="eyebrow">
        {w(clinician ? "CLINICIAN APPLICATION" : "YOUR SPACE FOR CARE")} · {w("STEP")}{" "}
        {position + 1} {w("of")} {steps.length}
      </p>
      <div className="step-progress" aria-label={`${w("Step")} ${position + 1} ${w("of")} ${steps.length}`}>
        {steps.map((value, index) => (
          <span key={value} data-complete={index <= position} />
        ))}
      </div>
      <h1>{w(titles[step])}</h1>
      {error && <InlineNotice tone="danger">{w(error)}</InlineNotice>}
      {!ready ? (
        <Skeleton />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void save(steps[Math.min(position + 1, steps.length - 1)], step === 3);
          }}
        >
          {step === 0 && (
            <>
              <p>
                {w(clinician
                  ? "Use the professional name your credentials are issued under."
                  : "A preferred name or alias is enough. You choose whether to share it when you book.")}
              </p>
              <div data-tour={clinician?"applicant-profile":undefined}><TextField
                label={w(clinician ? "Professional name" : "Preferred name or alias")}
                value={answers.name || ""}
                maxLength={120}
                required
                onChange={(e) => update({ name: e.target.value })}
              /></div>
            </>
          )}
          {step === 1 && !clinician && <p className="supporting">{w("For a shared session, every participating adult completes their own registration and consent.")}</p>}
          {step === 1 &&
            (clinician ? (
              <>
                <label className="field">
                  {w("Credentials and requested services")}
                  <textarea
                    required
                    maxLength={2000}
                    rows={6}
                    value={answers.statement || ""}
                    onChange={(e) => update({ statement: e.target.value })}
                  />
                </label>
                <p className="supporting">
                  {w("Describe your qualification, registration and the services you would like reviewed. Upload a PDF resume (up to 5 MB); receipt does not mean your credentials are verified.")}
                </p>
                <fieldset className="scope-picker onboarding-scope-picker" data-tour="applicant-scopes">
                  <legend>{w("Services requested for approval")}</legend>
                  <TextField label={w("Search services")} type="search" value={scopeSearch} onChange={e=>setScopeSearch(e.target.value)}/>
                  <div className="onboarding-scope-options" role="group" aria-label={w("Services requested for approval")}>
                    {catalog.filter(service=>service.label.toLocaleLowerCase().includes(scopeSearch.trim().toLocaleLowerCase())).map(service=><Checkbox key={service.id} label={service.label} checked={(answers.requested_services||[]).includes(service.id)} onChange={e=>update({requested_services:e.target.checked?[...(answers.requested_services||[]),service.id]:(answers.requested_services||[]).filter(x=>x!==service.id)})}/>)}
                    {!catalog.some(service=>service.label.toLocaleLowerCase().includes(scopeSearch.trim().toLocaleLowerCase()))&&<p role="status">{w("No services match this search. Try another term.")}</p>}
                  </div>
                  <p className="supporting" role="status">{w("Selected services")}: {(answers.requested_services||[]).length}</p>
                </fieldset>
                <label className="field" data-tour="applicant-resume">{w("Resume (PDF, up to 5 MB)")}<input type="file" accept="application/pdf,.pdf" disabled={resumeBusy} onChange={async e=>{const file=e.target.files?.[0];if(!file)return;if(file.size>5*1024*1024){setError("Choose a PDF no larger than 5 MB.");return;}setResumeBusy(true);setError("");try{const base64=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(",")[1]||"");reader.onerror=()=>reject(new Error("Read failed"));reader.readAsDataURL(file);});await journeyApi.uploadResume(file.name,base64);setResumeUploaded(true);}catch{setError("The resume could not be uploaded. Choose a valid PDF and try again.");}finally{setResumeBusy(false);e.target.value="";}}}/>{resumeUploaded&&<span role="status">{w("Resume uploaded for authorized review.")} <button type="button" className="text-button" onClick={()=>void journeyApi.removeResume().then(()=>setResumeUploaded(false)).catch(()=>setError("Resume could not be removed."))}>{w("Remove")}</button></span>}</label>
              </>
            ) : (
              <>
                <p>
                  {w("This service is for adults. Please review these choices before continuing.")}
                </p>
                <Checkbox
                  variant="card"
                  label={w("I am 18 or older.")}
                  checked={!!answers.adult}
                  required
                  onChange={(e) => update({ adult: e.target.checked })}
                />
                <Checkbox
                  variant="card"
                  label={w("I consent to storing my profile and the information I choose to share for this care journey.")}
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
                  label={w("Clinic affiliations (optional)")}
                  value={answers.affiliations || ""}
                  onChange={(e) => update({ affiliations: e.target.value })}
                  hint={w("Affiliation does not grant access to patient records.")}
                />
                <Checkbox
                  variant="card"
                  label={w("I am 18 or older.")}
                  checked={!!answers.adult}
                  required
                  onChange={(e) => update({ adult: e.target.checked })}
                />
                <Checkbox
                  variant="card"
                  label={w("I consent to storing these details for manual application review.")}
                  checked={!!answers.consent}
                  required
                  onChange={(e) => update({ consent: e.target.checked })}
                />
              </>
            ) : (
              <>
                <Select
                  label={w("Preferred language")}
                  value={answers.language || "en"}
                  onChange={(e) => update({ language: e.target.value })}
                >
                  <option value="en">English</option>
                  <option value="am">አማርኛ</option>
                  <option value="om">Afaan Oromo</option>
                </Select>
                <p>
                  {w("Start with private defaults. You can change these for each booking.")}
                </p>
                <Checkbox
                  variant="card"
                  label={w("Share my preferred name by default")}
                  checked={!!answers.share_name}
                  onChange={(e) => update({ share_name: e.target.checked })}
                />
                <Checkbox
                  variant="card"
                  label={w("Share my saved history by default")}
                  checked={!!answers.share_history}
                  onChange={(e) => update({ share_history: e.target.checked })}
                />
              </>
            ))}
          {step === 4 && !clinician && <>
            <p>{w("Only add what you’re comfortable sharing. This step is optional.")}</p>
            <label className="field" htmlFor="onboarding-background">
              {w("Anything you’d like your clinician to know?")}
              <textarea id="onboarding-background" rows={6} maxLength={4000}
                value={answers.history || ""} aria-describedby="onboarding-background-privacy"
                onChange={e => update({ history: e.target.value })} />
            </label>
            <p id="onboarding-background-privacy" className="supporting">{w("This is saved privately. Your sharing defaults apply; preview and choose what to share before every booking.")}</p>
            {!answers.history && <Button variant="quiet" disabled={busy} onClick={() => void save(3)}>{w("Skip for now")}</Button>}
          </>}
          {step === 3 && !clinician && <section className="onboarding-ready-hero"><div><h2>{w("What’s on your mind?")}</h2><p>{w("Describe what you need, browse specialists, or ask available clinicians to respond.")}</p><Button type="submit" loading={busy}>{w("Find care")}</Button></div><aside><ShieldCheck size={26}/><h2>{w("Your choices come with you.")}</h2><dl><dt>{w("Display name")}</dt><dd>{answers.name}</dd><dt>{w("Care language")}</dt><dd>{{en:"English",am:"አማርኛ",om:"Afaan Oromo"}[answers.language as "en"|"am"|"om"]||"English"}</dd><dt>{w("Sharing")}</dt><dd>{w("Preview before every booking")}</dd></dl></aside></section>}
          {step === 3 && clinician && (
            <>
              <p>
                {w("Your application will be submitted for manual review. You cannot accept bookings until your professional status and service scopes are approved.")}
              </p>
              <section className="onboarding-review-panel">
                <h2>{w("Professional details")}</h2>
                <dl>
                  <div><dt>{w("Professional name")}</dt><dd>{answers.name}</dd></div>
                  <div><dt>{w("Credentials & scope")}</dt><dd>{answers.statement}</dd></div>
                  <div><dt>{w("Résumé")}</dt><dd>{w(resumeUploaded?"Resume uploaded for authorized review.":"Not provided")}</dd></div>
                  <div><dt>{w("Clinic affiliations (optional)")}</dt><dd>{answers.affiliations||w("Not provided")}</dd></div>
                </dl>
              </section>
              <section className="onboarding-review-panel">
                <h2>{w("Requested scopes")}</h2>
                <ul>{(answers.requested_services||[]).map(id=><li key={id}><FileText size={22} aria-hidden="true"/><div><strong>{catalog.find(service=>service.id===id)?.label||w("Service details unavailable")}</strong><p>{w("Pending review")}</p></div></li>)}</ul>
                <p className="supporting">{w("Each service needs its own human approval before publication.")}</p>
              </section>
            </>
          )}
          <div className="form-actions" data-tour={step===3&&clinician?"applicant-submit":undefined}>
            {step > 0 && (
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() => void save(steps[position - 1])}
              >
                {w("Back")}
              </Button>
            )}
            {(clinician||step!==3)&&<Button type="submit" loading={busy}>
              {step === 3
                ? clinician
                  ? w("Submit for review")
                  : w("Find care")
                : w("Continue")}
            </Button>}
          </div>
          <Button
            variant="quiet"
            data-tour={clinician?"applicant-save":undefined}
            disabled={busy}
            onClick={() => void save(step)}
          >
            {w("Save for later")}
          </Button>
          {saved && (
            <p role="status">{w("Progress saved. You can return to this step.")}</p>
          )}
        </form>
      )}
    </section>{clinician&&saved&&<WorkspaceTour role="applicant"/>}
    </>
  );
}
