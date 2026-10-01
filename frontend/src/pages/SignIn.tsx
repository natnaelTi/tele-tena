import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, LockKeyhole } from "lucide-react";
import { api, phoneAuth, setCsrf, signIn } from "../api";
import {
  Button,
  InlineNotice,
  OTPInput,
  PhoneField,
  TextField,
} from "../components/ui";
import { destination, useSession } from "../hooks/useSession";
import { useLocale } from "../hooks/useLocale";
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
    } catch {
      setError(
        "We couldn’t complete that step. Check your details and try again. Codes expire after five minutes.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function request() {
    await run(async () => {
      const result = await api<{
        challenge_id: string;
        delivery_state: string;
        message: string;
      }>(
        "tele_tena.api.contact_auth.request_code",
        { channel, contact, request_id: crypto.randomUUID() },
        true,
      );
      setChallenge(result.challenge_id);
      setCooldown(60);
      setNotice(
        "If delivery is available, a code will arrive shortly. Wait one minute before requesting another.",
      );
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
            onChange={(e) => setContact(e.target.value)}
            hint="Ethiopia (+251). You can also enter a number starting with 09 or 07."
            required
          />
        ) : (
          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            value={contact}
            onChange={(e) => setContact(e.target.value)}
            required
          />
        )}
        {!challenge && passwordMode && (
          <TextField
            label="Password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        )}
        <Button type="submit" loading={busy} className="full">
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
              {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend code"}
            </Button>
          </div>
        </>
      ) : (
        <div className="auth-secondary vertical">
          <Button
            variant="quiet"
            onClick={() => {
              setChannel(channel === "phone" ? "email" : "phone");
              setPasswordMode(false);
              setContact("");
              setError("");
            }}
          >
            {channel === "phone" ? w("Use email instead") : "Use phone instead"}
          </Button>
          {channel === "email" && (
            <Button
              variant="quiet"
              onClick={() => setPasswordMode(!passwordMode)}
            >
              {passwordMode
                ? "Use an email code instead"
                : "Use password instead"}
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
