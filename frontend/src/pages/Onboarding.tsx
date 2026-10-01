import { useEffect, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
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
type Answers = {
  name?: string;
  adult?: boolean;
  consent?: boolean;
  language?: string;
  share_name?: boolean;
  share_history?: boolean;
  statement?: string;
  affiliations?: string;
};
export default function Onboarding() {
  const { session, refresh } = useSession();
  const { w } = useLocale();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [step, setStep] = useState(0);
  const [kind, setKind] = useState("patient");
  const [answers, setAnswers] = useState<Answers>({});
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
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
  }, [params]);
  if (session?.profile) return <Navigate to={destination(session)} replace />;
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
        navigate(destination(current));
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
              <TextField
                label={
                  clinician ? "Professional name" : "Preferred name or alias"
                }
                value={answers.name || ""}
                maxLength={120}
                required
                onChange={(e) => update({ name: e.target.value })}
              />
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
                  information only; document upload is not available.
                </p>
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
          <div className="form-actions">
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
    </section>
  );
}
