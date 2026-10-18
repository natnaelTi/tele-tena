import {returnPath} from '../guest-intent';
import {FileUpload} from "../components/FileUpload";
import HistoryDocuments from "../components/HistoryDocuments";
import { useEffect, useState } from "react";
import { Link,Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
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
import { FileText, ShieldCheck } from "lucide-react";
import "./Onboarding.css";
type Answers = {
  professional?: {competencies?:string; certifications?:string; credential_valid_from?:string; professional_category?:string; qualification?:string; issuing_institution?:string; registration_number?:string; issuing_authority?:string; jurisdiction?:string; credential_expiry?:string; experience_years?:number};
  care_languages?: string[];
  introduction?: string;
  name?: string;care_alias?:string;terms_accepted?:boolean;privacy_acknowledged?:boolean;terms_version?:string;privacy_version?:string;marketing?:boolean;
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
  const [, setAccess] = useState<{patient_registration:boolean;clinician_registration:boolean}|null>(null);
  useEffect(() => {
    api<{ kind: string; step: number; answers: Answers }>(
      "tele_tena.api.contact_auth.onboarding",
    )
      .then((draft) => {
        setKind(
          params.get("intent") === "clinician" ? "clinician" : draft.kind,
        );
        setStep(draft.step);
        setAnswers(Object.keys(draft.answers).length?draft.answers:{share_name:false,share_history:true});
        setReady(true);
        void api<{terms_version:string;privacy_version:string}>('tele_tena.api.policies.current').then(policy=>setAnswers(previous=>({...previous,terms_version:policy.terms_version,privacy_version:policy.privacy_version})));
      })
      .catch(() =>
        setError(
          "Your saved progress could not be loaded. Reload to try again.",
        ),
      );
    void api<{patient_registration:boolean;clinician_registration:boolean}>("tele_tena.api.contact_auth.sign_in_options")
      .then(setAccess).catch(() => setError("Your saved progress could not be loaded. Reload to try again."));
    void api<{id:string;label:string}[]>("tele_tena.api.contact_auth.application_services").then(setCatalog).catch(()=>undefined);
    void journeyApi.resumeStatus().then(value=>setResumeUploaded(value.uploaded)).catch(()=>undefined);
  }, [params]);
  if (session?.profile) return <Navigate to={session.profile.kind === "patient" && returnPath() ? returnPath() : destination(session)} replace />;
  const clinician = kind === "clinician";
  // Retain stored step 3 as the ready screen for existing saved journeys.
  // Patient-only step 4 is inserted before it without reinterpreting old drafts.
  const steps = clinician ? [0, 1, 2, 5, 3] : [0, 1, 2, 4, 3];
  const position = Math.max(0, steps.indexOf(step));
  const titles = clinician
    ? [
        "Your professional profile",
        "Qualifications & résumé",
        "Clinic affiliations",
        "Review your application",
        "",
        "Choose your service scopes",
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
    if(complete&&(!answers.terms_accepted||!answers.privacy_acknowledged)){setError(w('Review and accept Terms and acknowledge Privacy separately.'));return;}
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
        if(current?.profile?.kind==='patient'&&returnPath()){navigate(returnPath(),{replace:true});return;}
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
        : code === "professional_required"
          ? "Complete your profession, qualification, institution and care languages before submission."
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
            if (clinician && step === 5 && !(answers.requested_services || []).length) {
              setError("Choose at least one service for review.");
              return;
            }
            if (clinician && step === 0 && !(answers.care_languages||[]).length) {setError("Choose at least one consultation language.");return;}
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
                label={w(clinician ? "Full professional name" : "Preferred name or alias")}
                value={answers.name || ""}
                maxLength={120}
                required
                onChange={(e) => update({ name: e.target.value })}
              /></div>
              {clinician && <>
                <Select label={w("Profession")} value={answers.professional?.professional_category || ""} required onChange={e=>update({professional:{...answers.professional,professional_category:e.target.value}})}>
                  <option value="">{w("Choose your profession")}</option>
                  {["Counseling psychologist","Psychiatrist","Clinical psychologist","Counselor","Other"].map(value=><option key={value} value={value}>{w(value)}</option>)}
                </Select>
                <TextField label={w("Years of practice")} type="number" min={0} max={60} value={answers.professional?.experience_years ?? ""} onChange={e=>update({professional:{...answers.professional,experience_years:Number(e.target.value)}})}/>
                <div className="field"><label htmlFor="onboarding-introduction">{w("Professional introduction")}</label><textarea id="onboarding-introduction" rows={4} maxLength={2000} value={answers.introduction||""} onChange={e=>update({introduction:e.target.value})}/><p className="field-hint">{w("This introduction may appear on your approved public profile. Keep credential identifiers in the private application fields.")}</p></div>
                <fieldset className="onboarding-language-options"><legend>{w("Consultation languages")}</legend>{[["en","English"],["am","Amharic"],["om","Afaan Oromo"]].map(([code,label])=><Checkbox key={code} variant="card" description={w("Consultation language")} label={w(label)} checked={(answers.care_languages||[]).includes(code)} onChange={e=>update({care_languages:e.target.checked?[...(answers.care_languages||[]),code]:(answers.care_languages||[]).filter(value=>value!==code)})}/>)}</fieldset>
              </>}
            </>
          )}
          {step === 1 && !clinician && <p className="supporting">{w("For a shared session, every participating adult completes their own registration and consent.")}</p>}
          {step === 1 &&
            (clinician ? (
              <>
                <p className="supporting">{w("Documents and credential identifiers are private to you and authorized reviewers.")}</p>
                {([["qualification","Primary qualification",180,true],["issuing_institution","Issuing institution",180,true],["issuing_authority","Licensing authority",180,false],["registration_number","License number",100,false]] as const).map(([key,label,maximum,required])=><TextField key={key} label={w(label)} required={required} maxLength={maximum} value={answers.professional?.[key]||""} onChange={e=>update({professional:{...answers.professional,[key]:e.target.value}})}/>)}
                <TextField label={w("License valid from")} type="date" value={answers.professional?.credential_valid_from||""} onChange={e=>update({professional:{...answers.professional,credential_valid_from:e.target.value}})}/>
                <TextField label={w("Professional competencies")} maxLength={2000} value={answers.professional?.competencies||""} onChange={e=>update({professional:{...answers.professional,competencies:e.target.value}})}/>
                <TextField label={w("Certifications")} maxLength={2000} value={answers.professional?.certifications||""} onChange={e=>update({professional:{...answers.professional,certifications:e.target.value}})}/>
                <TextField label={w("License expiry")} type="date" value={answers.professional?.credential_expiry||""} onChange={e=>update({professional:{...answers.professional,credential_expiry:e.target.value}})}/>
                <details className="onboarding-optional-credentials"><summary>{w("Additional application details (optional)")}</summary>
                <TextField label={w("Credential jurisdiction")} maxLength={120} value={answers.professional?.jurisdiction||""} onChange={e=>update({professional:{...answers.professional,jurisdiction:e.target.value}})}/>
                <div className="field">
                  <label htmlFor="onboarding-credentials">{w("Qualifications and experience")}</label>
                  <textarea
                    id="onboarding-credentials"
                    maxLength={2000}
                    rows={3}
                    value={answers.statement || ""}
                    onChange={(e) => update({ statement: e.target.value })}
                  />
                </div>
                </details>
                <p className="supporting">{w("Receipt does not mean your credentials are verified. Each requested scope is reviewed separately.")}</p>
                <div className="field" data-tour="applicant-resume">{w("Resume (PDF, up to 5 MB)")}<FileUpload label={w("Upload file")} accept="application/pdf,.pdf" disabled={resumeBusy} onFiles={async files=>{const file=files[0];if(!file)return;if(file.size>5*1024*1024){setError("Choose a PDF no larger than 5 MB.");return;}setResumeBusy(true);setError("");try{const base64=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(",")[1]||"");reader.onerror=()=>reject(new Error("Read failed"));reader.readAsDataURL(file);});await journeyApi.uploadResume(file.name,base64);setResumeUploaded(true);}catch{setError("The resume could not be uploaded. Choose a valid PDF and try again.");}finally{setResumeBusy(false);}}}/>{resumeUploaded&&<span role="status">{w("Resume uploaded for authorized review.")} <button type="button" className="text-button" onClick={()=>void journeyApi.removeResume().then(()=>setResumeUploaded(false)).catch(()=>setError("Resume could not be removed."))}>{w("Remove")}</button></span>}</div>
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
          {step === 5 && clinician && <>
            <p>{w("Select each service you are qualified to provide. Each is reviewed separately.")}</p>
                <fieldset className="scope-picker onboarding-scope-picker" aria-label={w("Services requested for approval")} data-tour="applicant-scopes">
                  <TextField label={w("Search services")} type="search" value={scopeSearch} onChange={e=>setScopeSearch(e.target.value)}/>
                  <div className="onboarding-scope-options" role="group" aria-label={w("Services requested for approval")}>
                    {catalog.filter(service=>service.label.toLocaleLowerCase().includes(scopeSearch.trim().toLocaleLowerCase())).map(service=><Checkbox key={service.id} variant="card" description={w("Evidence and approved scope are required.")} label={service.label} checked={(answers.requested_services||[]).includes(service.id)} onChange={e=>update({requested_services:e.target.checked?[...(answers.requested_services||[]),service.id]:(answers.requested_services||[]).filter(x=>x!==service.id)})}/>)}
                    {!catalog.some(service=>service.label.toLocaleLowerCase().includes(scopeSearch.trim().toLocaleLowerCase()))&&<p role="status">{w("No services match this search. Try another term.")}</p>}
                  </div>
                  <p className="supporting" role="status">{w("Selected services")}: {(answers.requested_services||[]).length}</p>
                </fieldset>
          </>}
          {step === 4 && !clinician && <>
            <p id="onboarding-background-help">{w("Only add what you’re comfortable sharing. This step is optional.")}</p>
            <div className="field">
              <label htmlFor="onboarding-background">{w("Anything you’d like your clinician to know?")}</label>
              <textarea id="onboarding-background" rows={4} maxLength={4000}
                value={answers.history || ""} aria-describedby="onboarding-background-help"
                onChange={e => update({ history: e.target.value })} />
            </div>
            <HistoryDocuments/><Checkbox variant="card" label={w("I’ll decide what to share for each consultation")}
              checked={!answers.share_history} onChange={e => update({ share_history: !e.target.checked })}
              description={w(answers.share_history
                ? "Your background is included in your default disclosure. Preview before every booking."
                : "This background is not included in your default disclosure. Preview before every booking.")} />
            {!answers.history && <Button variant="quiet" disabled={busy} onClick={() => void save(3)}>{w("Skip for now")}</Button>}
          </>}
          {step === 3 && !clinician && <section className="onboarding-ready-hero"><div><h2>{w("Choose your next step")}</h2><p>{w("Browse clinicians and services, or post a private request.")}</p></div><aside><ShieldCheck size={26}/><h2>{w("Your choices come with you.")}</h2><dl><dt>{w("Display name")}</dt><dd>{answers.name}</dd><dt>{w("Care language")}</dt><dd>{{en:"English",am:"አማርኛ",om:"Afaan Oromo"}[answers.language as "en"|"am"|"om"]||"English"}</dd><dt>{w("Sharing")}</dt><dd>{w("Preview before every booking")}</dd></dl></aside></section>}
          {step === 3 && clinician && (
            <>
              <p>
                {w("Your application will be submitted for manual review. You cannot accept bookings until your professional status and service scopes are approved.")}
              </p>
              <section className="onboarding-review-panel">
                <h2>{w("Professional details")}</h2>
                <dl>
                  <div><dt>{w("Professional name")}</dt><dd>{answers.name}</dd></div>
                  <div><dt>{w("Profession")}</dt><dd>{w(answers.professional?.professional_category||"Not provided")}</dd></div>
                  <div><dt>{w("Primary qualification")}</dt><dd>{answers.professional?.qualification||w("Not provided")}</dd></div>
                  <div><dt>{w("Issuing institution")}</dt><dd>{answers.professional?.issuing_institution||w("Not provided")}</dd></div>
                  <div><dt>{w("Consultation languages")}</dt><dd>{(answers.care_languages||[]).map(code=>w(code==="en"?"English":code==="am"?"Amharic":"Afaan Oromo")).join(", ")||w("Not provided")}</dd></div>
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
          {!clinician&&step===0&&<TextField label={w('Your clinician-facing alias')} value={answers.care_alias||''} placeholder={w('Choose an alias')} onChange={event=>update({care_alias:event.target.value})}/>}
          {step===3&&<section className="onboarding-review-panel"><h2>{w('Terms,privacy and consent')}</h2><p>{w('Review-only policy content;approved production policies are still pending.')}</p><Link to="/policies" target="_blank">{w('Read Terms and Privacy review versions')}</Link><Checkbox label={w('I accept the displayed review Terms version')} checked={!!answers.terms_accepted} onChange={event=>update({terms_accepted:event.target.checked})}/><Checkbox label={w('I acknowledge the displayed Privacy version')} checked={!!answers.privacy_acknowledged} onChange={event=>update({privacy_acknowledged:event.target.checked})}/><p>{w('Your earlier care consent is separate. Each encounter has its own sharing preview;global preferences do not share records with unknown recipients.')}</p><Checkbox label={w('Optional marketing updates')} checked={!!answers.marketing} onChange={event=>update({marketing:event.target.checked})}/></section>}
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
            <Button type="submit" loading={busy}>
              {step === 3
                ? clinician
                  ? w("Submit for review")
                  : w("Find care")
                : w(step === 5 ? "Review application" : step === 4 ? "Save and continue" : "Continue")}
            </Button>
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
    </section>
    </>
  );
}
