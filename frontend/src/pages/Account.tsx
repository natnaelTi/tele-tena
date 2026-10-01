import { useState } from "react";
import { Link } from "react-router-dom";
import { PageTitle } from "../components/Domain";
import { Button, Checkbox, InlineNotice, TextField } from "../components/ui";
import { journeyApi } from "../journey-api";
import { useSession } from "../hooks/useSession";
import { useAction } from "../hooks/useAction";
export default function Account() {
  const { session, refresh } = useSession();
  const profile = session!.profile!;
  const [name, setName] = useState(profile.display_name);
  const [history, setHistory] = useState(profile.history);
  const [shareName, setShareName] = useState(!!profile.share_name);
  const [shareHistory, setShareHistory] = useState(!!profile.share_history);
  const action = useAction();
  return (
    <>
      <PageTitle
        title="Profile & privacy"
        description="Your defaults are a starting point. You decide what to share for each booking."
      />
      <div className="two-column">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void action.run(async () => {
              await journeyApi.saveProfile({
                kind: profile.kind,
                display_name: name,
                adult: 1,
                history,
                share_name: shareName,
                share_history: shareHistory,
              });
              await refresh();
            }, "Your profile defaults are saved.");
          }}
        >
          <TextField
            label="Preferred name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            maxLength={120}
          />
          {profile.kind === "patient" && (
            <>
              <label className="field">
                Saved history (optional)
                <textarea
                  value={history}
                  onChange={(e) => setHistory(e.target.value)}
                  rows={4}
                  maxLength={4000}
                />
              </label>
              <p className="supporting">
                Use synthetic information only in this demo. Saved history is
                shared only when you choose to include it.
              </p>
              <h2>Default sharing choices</h2>
              <Checkbox
                label="Share my preferred name by default"
                checked={shareName}
                onChange={(e) => setShareName(e.target.checked)}
              />
              <Checkbox
                label="Share my saved history by default"
                checked={shareHistory}
                onChange={(e) => setShareHistory(e.target.checked)}
              />
            </>
          )}
          <Button type="submit" loading={action.busy}>
            Save changes
          </Button>
          {action.error && (
            <InlineNotice tone="danger">{action.error}</InlineNotice>
          )}
          {action.success && (
            <InlineNotice tone="success">{action.success}</InlineNotice>
          )}
        </form>
        <aside>
          <h2>Your account</h2>
          {profile.kind === "patient" && (
            <Link className="account-link" to="/patient/payments">
              Payments & simulated balance
            </Link>
          )}
          <p className="supporting">
            Changing a default does not change the information already shared in
            an existing booking.
          </p>
        </aside>
      </div>
    </>
  );
}
