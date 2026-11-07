import { OperationsFrame } from "../components/OperationsFrame";
import { OperationsErrorBoundary } from "../components/OperationsErrorBoundary";
import { OperationsArchiveRecords } from "../components/OperationsArchiveRecords";
import {
  DecisionOverview,
  HealthOverview,
  JourneyExplorer,
  QuarterlyReader,
  IntegrationCards,
  OpsState,
  humanBytes,
} from "./OperationsPortalViews";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";
import { useSession } from "../hooks/useSession";
import { WorkspaceLayout } from "../layouts/Layouts";
import {
  Button,
  Checkbox,
  InlineNotice,
  Select,
  Skeleton,
  TextField,
} from "../components/ui";
import "./Operations.css";
const prefix = "tele_tena.api.operations.";
export function SupportShell() {
  const { session } = useSession();
  return (
    <WorkspaceLayout
      kind={
        session?.roles.includes("Tele Tena Approver")
          ? "admin"
          : session?.roles.includes("Tele Tena Clinician")
            ? "clinician"
            : "patient"
      }
    />
  );
}
export default function Operations() {
  const { section = "" } = useParams(),
    { w } = useLocale(),
    [attempt, setAttempt] = useState(0);
  const method =
    section === "settings"
      ? "configuration"
      : section === "archive"
        ? "archive_list"
        : section === "reports"
          ? "reports_list"
          : section === "health"
            ? "health"
            : section === "insights"
              ? "insights"
              : "overview";
  const title =
    (
      {
        settings: "Operational Settings",
        archive: "Replay Archive",
        reports: "Quarterly Reports",
        health: "System Health",
        insights: "Journey Insights",
      } as any
    )[section] || "Overview";
  return (
    <OperationsFrame
      title={title}
      description="Make decisions, understand journey evidence and keep operational follow-up in one workspace."
    >
      <OperationsErrorBoundary
        key={method + ":" + attempt}
        fallback={
          <InlineNotice tone="danger">
            {w("Operations Could Not Be Loaded")}
            <Button onClick={() => setAttempt((x) => x + 1)}>
              {w("Retry")}
            </Button>
          </InlineNotice>
        }
      >
        {section === "insights" ? (
          <JourneyExplorer />
        ) : (
          <OperationsContent key={method} section={section} method={method} />
        )}
      </OperationsErrorBoundary>
    </OperationsFrame>
  );
}
function OperationsContent({
  section,
  method,
}: {
  section: string;
  method: string;
}) {
  const { w } = useLocale(),
    load = useCallback(() => api<any>(prefix + method), [method]),
    r = useResource(load);
  useEffect(() => {
    const id = setInterval(() => void r.refresh(), 30000);
    return () => clearInterval(id);
  }, [r.refresh]);
  const data =
    r.errorDetail instanceof ApiError &&
    [401, 403].includes(r.errorDetail.status)
      ? null
      : r.data;
  return (
    <>
      {r.error && (
        <InlineNotice tone="danger">
          {w("Operations Could Not Be Loaded")}
          <Button onClick={() => void r.refresh()}>{w("Retry")}</Button>
        </InlineNotice>
      )}
      {!data ? (
        r.error ? null : (
          <Skeleton />
        )
      ) : section === "settings" ? (
        <Settings data={data} refresh={r.refresh} />
      ) : section === "health" ? (
        <HealthOverview data={data} />
      ) : section === "archive" ? (
        <Archive data={data} />
      ) : section === "reports" ? (
        <QuarterlyReader items={data} refresh={r.refresh} />
      ) : (
        <DecisionOverview data={data} refresh={r.refresh} />
      )}
    </>
  );
}
function Archive({ data }: { data: any }) {
  const { w } = useLocale();
  const bytes = (n: any) => humanBytes(n);
  return (
    <section className="ops-panel">
      <h2>{w("Replay Readiness")}</h2>
      <OpsState
        value={
          !data.site_capture_enabled
            ? "Disabled"
            : !data.project_proof_verified
              ? "Awaiting Verification"
              : data.available
                ? "Ready"
                : "Unavailable"
        }
      />
      <p>
        {w(
          "Configured rolling retention is not a claim of operational 90-day archive availability.",
        )}
      </p>
      <InlineNotice>{w(data.reason)}</InlineNotice>
      <dl className="ops-facts">
        <dt>{w("Private Storage Used")}</dt>
        <dd>
          {bytes(data.used_bytes)} / {bytes(data.limit_bytes)}
        </dd>
        <dt>{w("Available Archive Capacity")}</dt>
        <dd>{bytes(data.available_bytes)}</dd>
        <dt>{w("Storage Status")}</dt>
        <dd>{w(data.storage_state || "Unavailable")}</dd>
        <dt>{w("Replay Index Entries")}</dt>
        <dd>
          {data.index_entries} / {data.index_limit}
        </dd>
        <dt>{w("Raw Replay Retention")}</dt>
        <dd>
          {data.raw_retention_days} {w("Days From Original Capture")}
        </dd>
        <dt>{w("Oldest Unarchived Recording")}</dt>
        <dd>
          {data.oldest_unarchived
            ? String(data.oldest_unarchived)
            : w("No Unarchived Recordings Observed")}
        </dd>
        <dt>{w("Last Successful Retention Run")}</dt>
        <dd>
          {data.last_retention?.[0]?.at
            ? String(data.last_retention[0].at)
            : w("No Successful Run Observed")}
        </dd>
      </dl>
      {data.export_warning && (
        <InlineNotice tone="danger">
          {w(
            "An export has been waiting more than seven days. Investigate before provider retention expires.",
          )}
        </InlineNotice>
      )}
      <p>{w(data.capacity_note)}</p>
      {data.capacity_estimate && (
        <div>
          <p>
            {w("Measured Archive Samples")}:{" "}
            {data.capacity_estimate.sample_size} · {w("Median Bytes")}:{" "}
            {bytes(data.capacity_estimate.median_bytes)} ·{" "}
            {w("95th Percentile Bytes")}:{" "}
            {bytes(data.capacity_estimate.p95_bytes)}
          </p>
          <p>
            {w("Configured Daily-Limit Scenario Over 90 Days")}:{" "}
            {bytes(data.capacity_estimate.configured_daily_limit_90_day_bytes)}
          </p>
          <p>
            {w(
              "Short or synthetic samples do not establish production storage needs. Spool, support and metadata overhead also use capacity.",
            )}
          </p>
        </div>
      )}
      <details>
        <summary>{w("Capture Coverage and Processing States")}</summary>
        <p>
          {w(
            "Locally recorded, provider-accepted and independently verified are separate states. Dropped collection is not zero traffic.",
          )}
        </p>
        <div className="ops-table-wrap">
          <table>
            <thead>
              <tr>
                <th>{w("Stage")}</th>
                <th>{w("State")}</th>
                <th>{w("Count")}</th>
              </tr>
            </thead>
            <tbody>
              {[
                ...(data.states || []).map((x: any) => ({
                  ...x,
                  stage: "Archive",
                })),
                ...(data.chunks || []).map((x: any) => ({
                  ...x,
                  stage: "Capture Chunks",
                })),
              ].map((x: any, i: number) => (
                <tr key={i}>
                  <td>{w(x.stage)}</td>
                  <td>{w(x.state)}</td>
                  <td>{x.n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ul>
          {(data.capture_counters || []).map((x: any, i: number) => (
            <li key={i}>
              <span className="ops-code">{x.kind}</span>: {x.n} ·{" "}
              {String(x.day)}
            </li>
          ))}
        </ul>
      </details>
      <OperationsArchiveRecords metadata={data} />
    </section>
  );
}
function Settings({
  data,
  refresh,
}: {
  data: any;
  refresh: () => Promise<void>;
}) {
  const { w } = useLocale(),
    [value, setValue] = useState(data.config),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(false),
    [busy, setBusy] = useState(false),
    [revision, setRevision] = useState(data.config.revision);
  const toggle = (k: string, label: string, description: string) => (
    <div className="ops-setting" key={k}>
      <Checkbox
        label={w(label)}
        checked={!!value[k]}
        disabled={
          (k === "replay" && !value[k] && !data.replay_capability) ||
          (k === "archive" && !value[k] && !data.archive_capability)
        }
        onChange={(e) => {
          setValue({ ...value, [k]: e.target.checked });
          setSaved(false);
        }}
      />
      <p>{w(description)}</p>
    </div>
  );
  return (
    <>
      <section className="ops-panel">
        <h2>{w("Collection Preferences")}</h2>
        <p>
          {w(
            "Saved preferences do not prove effective collection. Missing credentials, verification, consent or quotas can keep a saved capability inactive.",
          )}
        </p>
        {toggle(
          "native_events",
          "Native Journey Events",
          "Safe native outcomes and eligible browser interactions. This does not transmit clinical content.",
        )}
        {toggle(
          "analytics",
          "External Product Analytics",
          "Permits delivery through the configured analytics adapter; individual preferences and limits still apply.",
        )}
        {toggle(
          "errors",
          "Error Reporting",
          "Unexpected TeleTena failures only, filtered before transmission.",
        )}
        {toggle(
          "replay",
          "Masked Session Replay",
          "Requires verified archive capability and separate user choice. Guests without a Terms acceptance point remain unrecorded.",
        )}
        {!data.replay_capability && (
          <InlineNotice>
            {w(
              "Replay prerequisites remain incomplete. Keep production collection disabled.",
            )}
          </InlineNotice>
        )}
        <Select
          label={w("Collection Environment")}
          value={value.environment}
          onChange={(e) => setValue({ ...value, environment: e.target.value })}
        >
          {["review", "staging", "production"].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </Select>
      </section>
      <section className="ops-panel">
        <h2>{w("Owner Alerts")}</h2>
        {toggle(
          "alerts",
          "Owner Operational Alerts",
          "Critical and deduplicated operational alerts are separate from patient and clinician notifications. No live test is sent when saving.",
        )}
        <div className="ops-grid">
          <TextField
            label={w("Owner Alert Email")}
            type="email"
            value={value.alert_email || ""}
            onChange={(e) =>
              setValue({ ...value, alert_email: e.target.value })
            }
          />
          <TextField
            label={w("Owner Alert Recipient — Account Reference")}
            value={value.owner}
            onChange={(e) => setValue({ ...value, owner: e.target.value })}
          />
        </div>
        <p>
          {w(
            "Leave the account reference empty for an unlinked owner subscription. A private recipient may already be configured; do not associate a demo reviewer.",
          )}
        </p>
        <Select
          label={w("Mobile Alert Channel")}
          value={value.mobile_channel}
          onChange={(e) =>
            setValue({ ...value, mobile_channel: e.target.value })
          }
        >
          <option value="Disabled">{w("Disabled")}</option>
          <option value="Telegram">Telegram</option>
        </Select>
      </section>
      <section className="ops-panel">
        <h2>{w("Storage and Retention")}</h2>
        {toggle(
          "archive",
          "Replay Archive Exports",
          "Requires selected-project settled proof, independent playback and private storage. A configured policy alone does not establish 90-day availability.",
        )}
        <p>
          {w(
            "Private storage paths and provider secrets are configured by the operator outside this UI.",
          )}
        </p>
        <dl className="ops-facts">
          <dt>{w("Archive Capacity")}</dt>
          <dd>
            {humanBytes(data.archive.used_bytes)} /{" "}
            {humanBytes(data.archive.limit_bytes)}
          </dd>
          <dt>{w("Raw Retention Policy")}</dt>
          <dd>90 {w("Days From Original Capture")}</dd>
        </dl>
        <details>
          <summary>{w("Advanced Limits and Safeguards")}</summary>
          <p>
            {w(
              "Limits bound collection and storage without changing clinical, payment or access rules.",
            )}
          </p>
          <div className="ops-grid">
            {[
              ["replay_index_limit", "Replay Index Entry Limit"],
              ["replay_chunks_per_day", "Daily Replay Chunk Limit"],
              ["replay_pending_chunks", "Pending Replay Chunk Limit"],
              ["replay_chunks_per_record", "Per-Recording Chunk Limit"],
              ["event_total_limit", "Total Native Event Limit"],
              ["alert_messages_per_day", "Daily Alert Message Limit"],
              ["events_per_day", "Daily Event Limit"],
              ["errors_per_day", "Daily Error Limit"],
              ["replays_per_day", "Daily Replay Limit"],
              ["archive_bytes", "Private Archive Byte Limit"],
              ["recording_bytes", "Per-Recording Byte Limit"],
              ["export_queue", "Export Queue Limit"],
              ["retry_budget", "Retry Budget"],
              ["sample_percent", "Eligible Collection Percentage"],
              ["cooldown_minutes", "Alert Cooldown in Minutes"],
            ].map(([k, label]) => (
              <TextField
                key={k}
                label={w(label)}
                type="number"
                value={value[k]}
                onChange={(e) =>
                  setValue({ ...value, [k]: Number(e.target.value) })
                }
              />
            ))}
          </div>
        </details>
      </section>
      {error && <InlineNotice tone="danger">{w(error)}</InlineNotice>}
      {saved && (
        <InlineNotice tone="success">
          {w("Operational Settings Saved")}
        </InlineNotice>
      )}
      <div className="ops-save-bar">
        <Button
          loading={busy}
          onClick={() => {
            const values = Object.fromEntries(
              Object.entries(value).filter(([key]) => key !== "revision"),
            );
            setBusy(true);
            setError("");
            void api(prefix + "configure", { values, revision }, true)
              .then((result: any) => {
                setRevision(result.config.revision);
                setSaved(true);
                return refresh();
              })
              .catch(() =>
                setError(
                  "Settings could not be saved. Check limits, recipient permissions and the current revision.",
                ),
              )
              .finally(() => setBusy(false));
          }}
        >
          {w("Save Operational Settings")}
        </Button>
        <span>{w("Configuration changes are audited.")}</span>
      </div>
      <IntegrationCards />
    </>
  );
}
