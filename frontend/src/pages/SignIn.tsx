import {journeyApi} from '../journey-api';
import {returnPath,rememberReturn,startAuthTiming} from '../guest-intent';
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, LockKeyhole } from "lucide-react";
import { ApiError, api, phoneAuth, setCsrf, signIn } from "../api";
import {
  Button,
  InlineNotice,
  OTPInput,
  PhoneField,
  TextField,
} from "../components/ui";
import { pendingCareQuery } from "../care-intent";
import { destination, useSession } from "../hooks/useSession";
import { useLocale } from "../hooks/useLocale";
type SignInOptions = { phone_otp: boolean; email_otp: boolean; patient_registration: boolean; clinician_registration: boolean };
export default function SignIn() {
  const { refresh, session } = useSession();
  const { w, t } = useLocale();
  const navigate = useNavigate();
  const routeLocation=useLocation();
  const [params] = useSearchParams();
  const [channel, setChannel] = useState<"phone" | "email">("phone");
  const [contact, setContact] = useState("");
  const [passwordMode, setPasswordMode] = useState(false);
  const [password, setPassword] = useState("");
  const [challenge, setChallenge] = useState("");
  const [code, setCode] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [resendAt, setResendAt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [options, setOptions] = useState<SignInOptions | null>(null);
  const [optionsError, setOptionsError] = useState(false);
  const requestKey = useRef("");
  useEffect(()=>{startAuthTiming();},[]);
  useEffect(() => {
    let active = true;
    void api<SignInOptions>("tele_tena.api.contact_auth.sign_in_options")
      .then((value) => {
        if (!active) return;
        setOptions(value);
      })
      .catch(() => { if (active) setOptionsError(true); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!resendAt) return;
    // A decrementing counter can diverge from server time through suspension,
    // clock corrections or background throttling. Recompute from the deadline.
    const update = () => setCooldown(Math.max(0, Math.ceil((resendAt-Date.now())/1000)));
    update();
    const timer = setInterval(update, 250);
    return () => clearInterval(timer);
  }, [resendAt]);
  async function run(task: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const csrf = await phoneAuth<{ csrf_token: string }>("csrf_token", {});
      setCsrf(csrf.csrf_token);
      await task();
    } catch (error) {
      const code = error instanceof ApiError ? error.code : "";
      if (code === "resend_cooldown") { setCooldown(60); setResendAt(Date.now()+60000); }
      const key = code === "review_password_required" ? "phoneAccessUnavailable"
        : code === "sms_budget_exhausted" ? "smsTemporarilyUnavailable"
        : code === "resend_cooldown" ? "resendCooldown"
        : code === "registration_unavailable" ? "registrationUnavailable"
        : code === "otp_invalid" ? "otpInvalidExpired"
        : code === "invalid_contact" ? "contactInvalid"
        : code === "credentials_invalid" || code === "login_failed" ? "credentialsInvalid"
        : code === "network_error" ? "networkTryAgain"
        : code === "service_unavailable" ? "serviceUnavailable"
        : "stepCouldNotComplete";
      setError(t(key));
    } finally {
      setBusy(false);
    }
  }
  async function request() {
    if(channel==='phone'&&!/^\+251[79][0-9]{8}$/.test(contact.replace(/[\s().-]/g,''))){setError(w('SMS sign-in currently supports Ethiopian mobile numbers. For other countries, use email.'));return;}
    await run(async () => {
      if (!requestKey.current) requestKey.current = crypto.randomUUID();
      const result = await api<{
        challenge_id: string;
        delivery_state: string;
        message: string;
        resend_after: number;
      }>(
        "tele_tena.api.contact_auth.request_code",
        { channel, contact, request_id: requestKey.current },
        true,
      );
      requestKey.current = "";
      if (result.delivery_state === "rejected") {
        setError("The provider could not send a code. Check your contact or use another sign-in option.");
        setCooldown(60);
        setResendAt(Date.now()+60000);
        return;
      }
      setChallenge(result.challenge_id);
      setCooldown(Math.max(60,result.resend_after||60));
      setResendAt(Date.now()+Math.max(60,result.resend_after||60)*1000);
      setNotice(result.delivery_state === "accepted"
        ? "The provider accepted the request. Check your messages; delivery is not yet confirmed."
        : "Delivery could not be confirmed. If a code arrives, enter it here. Wait one minute before resending.");
    });
  }
  async function proceed() {
    const directNext=params.get('next')||'';
    const selected=/^\/patient\/book\/([a-f0-9-]{36})$/.exec(directNext);
    if(selected)rememberReturn({kind:'offering',ref:selected[1]});
    const linked=/^\/patient\/book-link\/([a-f0-9]{64})$/.exec(directNext);if(linked)rememberReturn({kind:'booking-link',ref:linked[1]});
    const state=routeLocation.state as {coupleInvitationToken?:string;relationshipInvitationToken?:string}|null;
    const explicitInvitation=(directNext==='/couple-invitation'&&/^[A-Za-z0-9_-]{40,64}$/.test(state?.coupleInvitationToken||''))||(directNext==='/relationship-invitation'&&/^[A-Za-z0-9_-]{40,64}$/.test(state?.relationshipInvitationToken||''));
    const current = await refresh();
    const pending=returnPath();
    if(pending&&!explicitInvitation&&params.get("intent")!=="clinician"){
      if(current?.profile?.kind==='patient'){navigate(pending,{replace:true});return;}
      if(!current?.profile&&!current?.roles.some(role=>['Tele Tena Approver','Tele Tena Medical Lead','Tele Tena Clinician'].includes(role))){navigate('/onboarding?intent=patient',{replace:true});return;}
      setError(w('You are signed in to a professional workspace. Use a patient account to continue; no patient role has been added.'));return;
    }
    if(params.get('intent')==='clinician'&&current?.profile?.kind==='patient'){
      setError(w('This account has a patient profile. Use your professional account to apply; your existing profile and permissions are unchanged.'));return;
    }
    const next = params.get("next") || "";
    const inviteToken = (routeLocation.state as {relationshipInvitationToken?:string}|null)?.relationshipInvitationToken || "";
    const coupleToken=(routeLocation.state as {coupleInvitationToken?:string}|null)?.coupleInvitationToken||"";
    const safeCoupleReturn=next==="/couple-invitation"&&/^[A-Za-z0-9_-]{40,64}$/.test(coupleToken);
    if(safeCoupleReturn){navigate(current?.profile?.kind==="patient"?next:"/onboarding?intent=patient",{replace:true,state:{coupleInvitationToken:coupleToken}});return;}
    const safeBookingReturn = /^\/patient\/book-link\/[a-f0-9]{64}$/.test(next);
    const safeRelationshipReturn = next === "/relationship-invitation" && /^[A-Za-z0-9_-]{40,64}$/.test(inviteToken);
    if (inviteToken && !current?.profile) {
      navigate("/onboarding?intent=patient", { replace:true, state:{relationshipInvitationToken:inviteToken} });
      return;
    }
    navigate(
      (safeBookingReturn || safeRelationshipReturn || (next === "/patient/discovery" && current?.profile?.kind === "patient")) ? next : !current?.profile && ["patient", "clinician"].includes(params.get("intent") || "")
        ? "/onboarding?intent=" + params.get("intent")
        : current?.profile?.kind === "patient" && pendingCareQuery()
          ? "/patient/discovery" : destination(current),
      { replace: true, state: routeLocation.state },
    );
  }
  const masked =
    channel === "phone"
      ? "•••• " + contact.slice(-4)
      : contact.slice(0, 1) + "•••@" + (contact.split("@")[1] || "");
  return (
    <section className="auth-panel">
      <p className="eyebrow">A SPACE FOR YOU</p>
      <h1>
        {challenge
          ? "Check your " + (channel === "phone" ? "phone" : "email")
          : w(channel === "phone" ? "What’s your number?" : "Sign in with email")}
      </h1>
      <p className="auth-description">
        {challenge
          ? "Enter the six-digit code sent to " + masked + "."
        : passwordMode
            ? t("emailPasswordPrompt")
            : w("We’ll send a code to sign you in or get you started.")}
      </p>
      {session && (
        <p>
          <Link to={destination(session)}>{w("Return to your workspace")}</Link><Button variant="quiet" onClick={()=>void run(async()=>{await journeyApi.logout();await refresh();})}>{w("Sign out and use another account")}</Button>
        </p>
      )}
      {error && <InlineNotice tone="danger">{error}</InlineNotice>}
      {optionsError && <InlineNotice tone="danger">{t("authOptionsUnavailable")}</InlineNotice>}
      {!options && !error && !optionsError ? <p role="status">Checking sign-in options…</p> : null}
      {options && channel === "phone" && !options.phone_otp && !error && (
        <InlineNotice tone="info">{t("phoneAccessUnavailable")}</InlineNotice>
      )}
      {options && channel === "email" && !passwordMode && !options.email_otp && <InlineNotice tone="info">{w("Email codes are unavailable on this site. Choose password sign-in if you already have an account.")}</InlineNotice>}
      {params.get("mode") === "register" && options && !(params.get("intent") === "clinician" ? options.clinician_registration : options.patient_registration) && <InlineNotice tone="info">{w("New registration is unavailable on this site. Existing invited users can still sign in.")}</InlineNotice>}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (challenge)
            void run(async () => {
              await api(
                "tele_tena.api.contact_auth.verify_code",
                { channel, contact, challenge_id: challenge, code },
                true,
              );
              await proceed();
            });
          else if (passwordMode)
            void run(async () => {
              await signIn(contact, password);
              await proceed();
            });
          else void request();
        }}
      >
        {challenge ? (
          <OTPInput
            label={w("Verification code")}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            required
            autoFocus
          />
        ) : channel === "phone" ? (
          <PhoneField
            label={w("Phone number")}
            value={contact}
            onValueChange={(value) => { setContact(value); requestKey.current = ""; }}
            required
          />
        ) : (
          <TextField
            label={w("Email")}
            type="email"
            autoComplete="email"
            value={contact}
            onChange={(e) => { setContact(e.target.value); requestKey.current = ""; }}
            required
          />
        )}
        {!challenge && passwordMode && (
          <TextField
            label={w("Password")}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        )}
        <Button type="submit" loading={busy} disabled={!options || (channel === "phone" && !options.phone_otp) || (channel === "email" && !passwordMode && !options.email_otp)} className="full">
          {challenge
            ? w("Verify and continue")
            : passwordMode
              ? w("Sign in")
              : w("Continue")}
          <ArrowRight size={20} />
        </Button>
      </form>
      {challenge ? (
        <>
          <p className="supporting" role="status">
            {notice}
          </p>
          <div className="auth-secondary">
            <Button
              variant="quiet"
              onClick={() => {
                setChallenge("");
                setCode("");
                setError("");
                requestKey.current = "";
              }}
            >
              <ArrowLeft size={18} />
              {channel === "phone" ? w("Change number") : "Change email"}
            </Button>
            <Button
              variant="quiet"
              disabled={cooldown > 0 || busy}
              onClick={() => void request()}
            >
              {cooldown > 0 ? t("resendInSeconds").replace("{seconds}",String(cooldown)) : w("Resend code")}
            </Button>
          </div>
        </>
      ) : (
        <div className="auth-secondary vertical">
          {options?.phone_otp && channel === "email" && <Button
            variant="quiet"
            onClick={() => {
              setChannel("phone");
              setPasswordMode(false);
              setContact("");
              setPassword("");
              setError("");
              requestKey.current = "";
            }}
          >
            {w("Use phone instead")}
          </Button>}
          {channel === "phone" && <Button
            variant="quiet"
            onClick={() => {
              setChannel("email");
              setPasswordMode(false);
              setContact("");
              setPassword("");
              setError("");
              requestKey.current = "";
            }}
          >
            {w("Use email instead")}
          </Button>}
          {channel === "email" && (
            <Button
              variant="quiet"
              onClick={() => setPasswordMode(!passwordMode)}
            >
              {passwordMode
                ? w("Use an email code instead")
                : w("Use password instead")}
            </Button>
          )}
        </div>
      )}
      {!challenge && <div className="auth-registration">
        <p>{w("New to TeleTena?")}</p>
        {options?.patient_registration?<Link to="/sign-in?intent=patient&mode=register">{w("Create an account")}</Link>:<span aria-disabled="true">{w("Patient registration is unavailable on this site.")}</span>}
        {options?.clinician_registration?<Link to="/sign-in?intent=clinician&mode=register">{w("Apply as a clinician")}</Link>:<span aria-disabled="true">{w("Clinician applications are unavailable on this site.")}</span>}
      </div>}
      <p className="auth-privacy">
        <LockKeyhole size={16} />
        Your contact is verified before you set up your profile.
      </p>
    </section>
  );
}
