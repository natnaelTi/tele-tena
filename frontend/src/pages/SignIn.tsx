import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, LockKeyhole } from "lucide-react";
import { ApiError, api, phoneAuth, setCsrf, signIn } from "../api";
import {
  Button,
  InlineNotice,
  OTPInput,
  PhoneField,
  TextField,
} from "../components/ui";
import { destination, useSession } from "../hooks/useSession";
import { useLocale } from "../hooks/useLocale";
type SignInOptions = { phone_otp: boolean; email_otp: boolean; patient_registration: boolean; clinician_registration: boolean };
export default function SignIn() {
  const { refresh, session } = useSession();
  const { w } = useLocale();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [channel, setChannel] = useState<"phone" | "email">("phone");
  const [contact, setContact] = useState("");
  const [passwordMode, setPasswordMode] = useState(false);
  const [password, setPassword] = useState("");
  const [challenge, setChallenge] = useState("");
  const [code, setCode] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [options, setOptions] = useState<SignInOptions | null>(null);
  const requestKey = useRef("");
  useEffect(() => {
    let active = true;
    void api<SignInOptions>("tele_tena.api.contact_auth.sign_in_options")
      .then((value) => {
        if (!active) return;
        setOptions(value);
        if (!value.phone_otp) {
          setChannel("email");
          setPasswordMode(!value.email_otp);
        }
      })
      .catch(() => { if (active) setError("Sign-in options are unavailable. Reload to try again."); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!cooldown) return;
    const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);
  async function run(task: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const csrf = await phoneAuth<{ csrf_token: string }>("csrf_token", {});
      setCsrf(csrf.csrf_token);
      await task();
    } catch (error) {
      setError(
        error instanceof ApiError && error.code === "review_password_required" ? "Phone verification is unavailable here. Use email and password." :
        error instanceof ApiError && error.code === "sms_budget_exhausted" ? "Code sending is temporarily unavailable. Try again later or use email." :
        error instanceof ApiError && error.code === "resend_cooldown" ? "Please wait before requesting another code." :
        error instanceof ApiError && error.code === "registration_unavailable" ? "New registrations are paused here. Existing verified accounts can still sign in." :
        "We couldn’t complete that step. Check your details and try again. Codes expire after five minutes.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function request() {
    await run(async () => {
      if (!requestKey.current) requestKey.current = crypto.randomUUID();
      const result = await api<{
        challenge_id: string;
        delivery_state: string;
        message: string;
      }>(
        "tele_tena.api.contact_auth.request_code",
        { channel, contact, request_id: requestKey.current },
        true,
      );
      requestKey.current = "";
      if (result.delivery_state === "rejected") {
        setError("The provider could not send a code. Check your contact or use another sign-in option.");
        setCooldown(60);
        return;
      }
      setChallenge(result.challenge_id);
      setCooldown(60);
      setNotice(result.delivery_state === "accepted"
        ? "The provider accepted the request. Check your messages; delivery is not yet confirmed."
        : "Delivery could not be confirmed. If a code arrives, enter it here. Wait one minute before resending.");
    });
  }
  async function proceed() {
    const current = await refresh();
    navigate(
      !current?.profile && params.get("intent") === "clinician"
        ? "/onboarding?intent=clinician"
        : destination(current),
      { replace: true },
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
          : w("Welcome to TeleTena")}
      </h1>
      <p className="auth-description">
        {challenge
          ? "Enter the six-digit code sent to " + masked + "."
          : passwordMode
            ? "Use your email and password to continue."
            : "A small step toward the support you’re looking for."}
      </p>
      {session && (
        <p>
          <a href={destination(session)}>Return to your workspace</a>
        </p>
      )}
      {error && <InlineNotice tone="danger">{error}</InlineNotice>}
      {!options && !error ? <p role="status">Checking sign-in options…</p> : null}
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
            onChange={(e) => { setContact(e.target.value); requestKey.current = ""; }}
            hint="Ethiopia (+251). You can also enter a number starting with 09 or 07."
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
              {cooldown > 0 ? `Resend in ${cooldown}s` : w("Resend code")}
            </Button>
          </div>
        </>
      ) : (
        <div className="auth-secondary vertical">
          {options?.phone_otp && <Button
            variant="quiet"
            onClick={() => {
              setChannel(channel === "phone" ? "email" : "phone");
              setPasswordMode(channel === "phone" && !options.email_otp);
              setContact("");
              setError("");
              requestKey.current = "";
            }}
          >
            {channel === "phone" ? w("Use email instead") : w("Use phone instead")}
          </Button>}
          {channel === "email" && options?.email_otp && (
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
      <p className="auth-privacy">
        <LockKeyhole size={16} />
        Your contact is verified before you set up your profile.
      </p>
    </section>
  );
}
