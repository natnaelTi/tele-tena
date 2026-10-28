import {CareLanguageEditor} from '../components/CareLanguages';
import type {CareLanguageHandle} from '../components/CareLanguages';
import {RequiredFieldsNotice} from '../components/ui';
import {ProfessionalStep,professionalError} from '../components/ProfessionalApplication';
import type {ApplicationState,ProfessionalClaims} from '../components/ProfessionalApplication';
import {returnPath,discardGuestDraft} from '../guest-intent';
import HistoryDocuments from "../components/HistoryDocuments";
import { useEffect, useState, useRef } from "react";
import { Link,Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { pendingCareQuery } from "../care-intent";
import { api, ApiError } from "../api";
import {
  Button,
  Dialog,
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
  const { w,setLocale } = useLocale();
  const navigate = useNavigate();
  const routeLocation = useLocation();
  const [params] = useSearchParams();
  const careLanguageEditor=useRef<CareLanguageHandle>(null);
  const [step, setStep] = useState(0);
  const [kind, setKind] = useState("patient");
  const [resumeKind,setResumeKind]=useState("");
  const [answers, setAnswers] = useState<Answers>({});
  const [professional,setProfessional]=useState<ProfessionalClaims>({});
  const [professionalState,setProfessionalState]=useState<ApplicationState|null>(null);
  async function refreshProfessional(){const state=await api<ApplicationState>('tele_tena.api.professional.application');setProfessionalState(state);}
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [signingOut,setSigningOut]=useState(false);
  const [signOutOpen,setSignOutOpen]=useState(false);
  const [signOutError,setSignOutError]=useState("");
  const [catalog, setCatalog] = useState<{id:string;label:string}[]>([]);
  const [resumeUploaded, setResumeUploaded] = useState(false);
  const [scopeSearch, setScopeSearch] = useState("");
  const [access, setAccess] = useState<{patient_registration:boolean;clinician_registration:boolean}|null>(null);
  useEffect(() => {
    api<{ kind: string; step: number; answers: Answers }>(
      "tele_tena.api.contact_auth.onboarding",
    )
      .then((draft) => {
        const requested=params.get('intent');
        setResumeKind(Object.keys(draft.answers).length&&requested&&requested!==draft.kind?draft.kind:'');
        setKind(
          params.get("intent") === "clinician" ? "clinician" : draft.kind,
        );
        setStep(draft.step);
        setAnswers({share_name:true,share_history:true,...draft.answers});
        if(params.get('intent')==='clinician'||draft.kind==='clinician'){void api<ApplicationState>('tele_tena.api.professional.application').then(state=>{setProfessionalState(state);setProfessional(state.payload);}).catch(()=>setError('Your professional application could not be loaded. Reload before editing.'));}
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
  const inviteState=routeLocation.state as {coupleInvitationToken?:string;relationshipInvitationToken?:string}|null;
  const invitationPath=/^[A-Za-z0-9_-]{40,64}$/.test(inviteState?.coupleInvitationToken||'')?'/couple-invitation':/^[A-Za-z0-9_-]{40,64}$/.test(inviteState?.relationshipInvitationToken||'')?'/relationship-invitation':'';
  if(session?.profile)return <Navigate to={session.profile.kind==='patient'?(invitationPath||returnPath()||destination(session)):destination(session)} state={routeLocation.state} replace/>;
  const clinician = kind === "clinician";
  if(ready&&resumeKind)return <section className="guided-panel"><h1>{w('Your Saved Registration Is a Different Journey')}</h1><InlineNotice>{w('Your existing draft is retained. Resume it, or sign in with the account you want to use. No roles or profile details have changed.')}</InlineNotice><Link className="button" to={'/onboarding?intent='+resumeKind}>{w('Resume saved registration')}</Link><Link className="text-link" to="/sign-in">{w('Use another account')}</Link></section>;
  if(ready&&access&&!(clinician?access.clinician_registration:access.patient_registration))return <section className="guided-panel"><h1>{w('Registration Is Unavailable on This Site.')}</h1><InlineNotice>{w('Your saved progress is retained and has not been submitted. Existing invited accounts can still sign in.')}</InlineNotice><Link to="/sign-in">{w('Return to sign in')}</Link></section>;
  // Retain stored step 3 as the ready screen for existing saved journeys.
  // Patient-only step 4 is inserted before it without reinterpreting old drafts.
  const steps = clinician ? [0, 1, 6, 7, 2, 5, 3] : [0, 1, 2, 4, 3];
  const position = Math.max(0, steps.indexOf(step));
  const titles = clinician
    ? [
        "Your Professional Profile",
        "Qualifications and Credentials",
        "Clinic Affiliations and Declaration",
        "Review Your Application",
        "",
        "Choose Your Service Scopes",
        "Professional License",
        "Competency Domains",
      ]
    : [
        "A Little about You",
        "Adult Eligibility",
        "Your Privacy Defaults",
        "You’re Ready",
        "Care Background",
      ];
  const update = (value: Partial<Answers>) => {
    setAnswers({ ...answers, ...value });
    setSaved(false);
  };
  async function save(next: number, complete = false) {
    if(complete&&(!answers.terms_accepted||!answers.privacy_acknowledged)){setError(w('Review and accept Terms and acknowledge Privacy separately.'));return;}
    if (complete && clinician && (!(resumeUploaded||(professional.cv_files||[]).length) || !(answers.requested_services||[]).length)) {
      setError("Upload a CV and select at least one service to request before submitting.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if(clinician&&careLanguageEditor.current)await careLanguageEditor.current.save();
      if(clinician){if(!professionalState)throw new Error('Professional application is not loaded');const state=await api<ApplicationState>('tele_tena.api.professional.save',{payload:professional,revision:professionalState.revision},true);setProfessionalState(state);}
      await api(
        "tele_tena.api.contact_auth.save_onboarding",
        { kind, step: next, answers, complete: complete ? 1 : 0 },
        true,
      );
      setStep(next);
      setSaved(true);
      if (complete) {
        if(kind==='patient')setLocale((answers.language||'en') as 'en'|'am'|'om');
        const current = await refresh();
        const coupleToken=(routeLocation.state as {coupleInvitationToken?:string}|null)?.coupleInvitationToken;
        if(coupleToken&&kind==="patient"){navigate("/couple-invitation",{replace:true,state:{coupleInvitationToken:coupleToken}});return;}
        const invitationToken=(routeLocation.state as {relationshipInvitationToken?:string}|null)?.relationshipInvitationToken;
        if(current?.profile?.kind==='patient'&&!invitationToken&&returnPath()){navigate(returnPath(),{replace:true});return;}
        navigate(invitationToken && current?.profile?.kind==='patient' ? '/relationship-invitation' : current?.profile?.kind === 'patient' && pendingCareQuery() ? '/patient/discovery' : destination(current),
          { replace:true, state: invitationToken ? {relationshipInvitationToken:invitationToken} : undefined });
      }
      return true;
    } catch (failure) {
      const code = failure instanceof ApiError ? failure.code : "network_error";
      setError(failure instanceof ApiError && failure.message && ["bio_word_limit","professional_required","declaration_required","competency_rating_required","credential_date_range","reference_other_required","issuer_country_required"].includes(code)?professionalError(failure):code === "adult_required"
        ? "Please check this step and try again. Adult eligibility and consent are required to finish."
        : code === "care_language_assessment_required"
          ? "Return to Your Professional Profile, choose your care languages and select a self-assessment level for each. Your saved details are retained."
        : code === "professional_required"
          ? "Complete your profession, qualification, institution and care languages before submission."
        : code === "resume_required"
          ? "Upload a CV and select at least one service to request before submitting."
          : code === "session_required" || code === "contact_required"
            ? "Your session has expired. Sign in again to continue your saved registration."
            : code === "registration_unavailable"
              ? "Registration is unavailable on this site. Your saved progress has not been submitted."
              : "We couldn’t save this step. Your entries are still here; check your connection and try again.");
      return false;
    } finally {
      setBusy(false);
    }
  }
  async function signOut(saveFirst:boolean){
    setSignOutError('');
    if(saveFirst&&document.querySelector('.onboarding-guided .upload-dropzone[aria-busy="true"]')){setSignOutError('Wait for the upload to finish before saving, or explicitly discard unsaved changes and sign out.');return;}
    if(saveFirst&&!(await save(step))){setSignOutError('Your draft could not be saved. Retry, or explicitly discard unsaved changes and sign out.');return;}
    setSigningOut(true);
    try{await journeyApi.logout();discardGuestDraft();setAnswers({});setProfessional({});setProfessionalState(null);window.location.replace('/teletena/sign-in?intent='+kind);}
    catch{setSigningOut(false);setSignOutError('Sign-out could not finish. Try again; your entries remain here.');}
  }
  return (
    <>
    <div className="onboarding-session-actions"><Button variant="quiet" onClick={()=>setSignOutOpen(true)}>{w('Sign Out')}</Button></div>
    <Dialog open={signOutOpen} onOpenChange={setSignOutOpen} title={w('Sign Out of Onboarding')} description={w('Saved progress stays with your account. Unsaved text and selections will be discarded unless you save first. An upload that already finished remains private.')}>
      {signOutError&&<InlineNotice tone="danger">{w(signOutError)}</InlineNotice>}
      <div className="actions"><Button loading={busy||signingOut} onClick={()=>void signOut(true)}>{w('Save and Sign Out')}</Button><Button variant="secondary" disabled={signingOut} onClick={()=>void signOut(false)}>{w('Discard Unsaved Changes and Sign Out')}</Button><Button variant="quiet" disabled={signingOut} onClick={()=>setSignOutOpen(false)}>{w('Keep Editing')}</Button></div>
    </Dialog>
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
      <h1>{w(titles[step])}</h1><RequiredFieldsNotice/>
      {error && <InlineNotice tone="danger">{w(error)}</InlineNotice>}
      {!ready||!access||(clinician&&!professionalState) ? (
        <Skeleton />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (clinician && step === 5 && !(answers.requested_services || []).length) {
              setError("Choose at least one service for review.");
              return;
            }
            if(clinician&&step===0&&(!professional.profession||!professional.first_name?.trim()||!professional.last_name?.trim())){setError('Complete First Name, Last Name and Profession before continuing.');return;}
            if(clinician&&step===1&&(!professional.issuer||!professional.qualification_title?.trim())){setError('Complete the awarded qualification and issuing institution before continuing.');return;}
            if (clinician && step === 0 && !(answers.care_languages||[]).length) {setError("Choose at least one consultation language.");return;}
            void save(steps[Math.min(position + 1, steps.length - 1)], step === 3);
          }}
        >
          {clinician&&[0,1,2,6,7].includes(step)&&<ProfessionalStep step={step===6?2:step===7?3:step===2?4:step} value={professional} onChange={change=>{setProfessional(change);setSaved(false);setError('');}} evidence={professionalState?.evidence||[]} legacyCV={professionalState?.legacy_cv} onEvidence={refreshProfessional}/> }
          {step === 0 && !clinician && (
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
            </>
          )}
          {clinician&&step===0&&<CareLanguageEditor ref={careLanguageEditor} onboarding onChange={codes=>setAnswers(previous=>({...previous,care_languages:codes}))}/>}
          {step === 1 && !clinician && <p className="supporting">{w("For a shared session, every participating adult completes their own registration and consent.")}</p>}
          {step === 1 &&
            (clinician ? (
              null
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
              <Checkbox label={w('I consent to storing these details for manual application review.')} checked={!!answers.consent} required onChange={e=>update({consent:e.target.checked})}/>
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
                  {w("Choose your sharing defaults. You can change these for each booking.")}
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
          {step === 3 && !clinician && <section className="onboarding-ready-hero"><div><h2>{w("Choose Your Next Step")}</h2><p>{w("Browse clinicians and services, or post a private request.")}</p></div><aside><ShieldCheck size={26}/><h2>{w("Your Choices Come with You.")}</h2><dl><dt>{w("Display name")}</dt><dd>{[professional.prefix==='Other'?professional.prefix_other:professional.prefix,professional.first_name,professional.last_name].filter(Boolean).join(' ')||w('Not Provided')}</dd><dt>{w("Care language")}</dt><dd>{{en:"English",am:"አማርኛ",om:"Afaan Oromo"}[answers.language as "en"|"am"|"om"]||"English"}</dd><dt>{w("Sharing")}</dt><dd>{w("Preview before every booking")}</dd></dl></aside></section>}
          {step === 3 && clinician && (
            <>
              <p>
                {w("Your application will be submitted for manual review. You cannot accept bookings until your professional status and service scopes are approved.")}
              </p>
              <section className="onboarding-review-panel">
                <h2>{w("Professional Details")}</h2>
                <dl>
                  <div><dt>{w("Professional name")}</dt><dd>{[professional.prefix==='Other'?professional.prefix_other:professional.prefix,professional.first_name,professional.last_name].filter(Boolean).join(' ')||w('Not Provided')}</dd></div>
                  <div><dt>{w("Profession")}</dt><dd>{(professional.profession==='Other'?professional.profession_other:professionalState?.reference_labels?.[professional.profession||''])||w('Selected Profession')}</dd></div>
                  <div><dt>{w("Primary qualification")}</dt><dd>{professional.qualification_title||w('Not Provided')}</dd></div>
                  <div><dt>{w("Issuing institution")}</dt><dd>{(professional.issuer==='Other'?professional.issuer_other:professionalState?.reference_labels?.[professional.issuer||''])||w('Selected Institution')}</dd></div>
                  <div><dt>{w("Consultation languages")}</dt><dd>{(answers.care_languages||[]).map(code=>w(code==="en"?"English":code==="am"?"Amharic":"Afaan Oromo")).join(", ")||w("Not provided")}</dd></div>
                  <div><dt>{w("Credentials & scope")}</dt><dd>{answers.statement}</dd></div>
                  <div><dt>{w("CV")}</dt><dd>{w(resumeUploaded||(professional.cv_files||[]).length?"CV uploaded for authorized review.":"Not provided")}</dd></div>
                  <div><dt>{w("Clinic affiliations (optional)")}</dt><dd>{answers.affiliations||w("Not provided")}</dd></div>
                </dl>
              </section>
              <section className="onboarding-review-panel">
                <h2>{w("Requested Scopes")}</h2>
                <ul>{(answers.requested_services||[]).map(id=><li key={id}><FileText size={22} aria-hidden="true"/><div><strong>{catalog.find(service=>service.id===id)?.label||w("Service details unavailable")}</strong><p>{w("Pending review")}</p></div></li>)}</ul>
                <p className="supporting">{w("Each service needs its own human approval before publication.")}</p>
              </section>
            </>
          )}
          {!clinician&&step===0&&<TextField label={w('Your clinician-facing alias')} value={answers.care_alias||''} placeholder={w('Choose an alias')} onChange={event=>update({care_alias:event.target.value})}/>}
          {step===3&&<section className="onboarding-review-panel"><h2>{w('Terms,privacy and Consent')}</h2><p>{w('Review-only policy content;approved production policies are still pending.')}</p><Link to="/policies" target="_blank">{w('Read Terms and Privacy review versions')}</Link><Checkbox label={w('I accept the displayed review Terms version')} required checked={!!answers.terms_accepted} onChange={event=>update({terms_accepted:event.target.checked})}/><Checkbox label={w('I acknowledge the displayed Privacy version')} required checked={!!answers.privacy_acknowledged} onChange={event=>update({privacy_acknowledged:event.target.checked})}/><p>{w('Your earlier care consent is separate. Each encounter has its own sharing preview;global preferences do not share records with unknown recipients.')}</p><Checkbox label={w('Optional marketing updates')} checked={!!answers.marketing} onChange={event=>update({marketing:event.target.checked})}/></section>}
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
