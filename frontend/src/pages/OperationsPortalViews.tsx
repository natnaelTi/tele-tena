import { eventLabel, operationsTime } from "../components/operationsLabels";
import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  Clock3,
  AlertTriangle,
  Activity,
} from "lucide-react";
import { api } from "../api";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";
import {
  Button,
  InlineNotice,
  Select,
  Skeleton,
  TextField,
} from "../components/ui";
const prefix = "tele_tena.api.operations.";
export function humanBytes(n: number | null | undefined) {
  if (n === null || n === undefined) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (n >= 1024 && i < 3) {
    n /= 1024;
    i++;
  }
  return `${n.toLocaleString(undefined, { maximumFractionDigits: i ? 1 : 0 })} ${units[i]}`;
}
export function OpsState({ value }: { value: string }) {
  const { w } = useLocale();
  const label =
    (
      {
        "No Eligible Data": w("No Eligible Data"),
        "Insufficient Sample": w("Insufficient Sample"),
        Observed: w("Observed"),
      } as Record<string, string>
    )[value] || w(value);
  return (
    <span
      className={
        "ops-state " +
        (["Ready", "Current", "Resolved", "Verified", "Completed"].includes(
          value,
        )
          ? "is-current"
          : ["Failed", "Stale", "Error", "Critical"].includes(value)
            ? "is-danger"
            : "is-neutral")
      }
    >
      {label}
    </span>
  );
}
export function DecisionOverview({
  data,
  refresh,
}: {
  data: any;
  refresh: () => Promise<void>;
}) {
  const { w } = useLocale();
  const queues = [
    [
      "Professional Applications Awaiting Review",
      data.applications,
      "/admin/applications",
      CheckCircle2,
    ],
    [
      "Service Applications Awaiting Review",
      Number.isFinite(data.scope_pending)
        ? data.scope_pending + data.scope_replies
        : null,
      "/admin/vetting",
      Clock3,
    ],
    [
      "Payments Awaiting Verification",
      data.payment_reviews,
      "/admin/operations/health#payment-review",
      Activity,
    ],
    [
      "Unresolved Support Reports",
      data.support_open,
      "/admin/support",
      AlertTriangle,
    ],
  ] as const;
  return (
    <>
      <div className="ops-overview-context">
        <span>
          {w("Window")}: <strong>{w("Current Queues")}</strong>
        </span>
        <span>
          {w("Processing Freshness")}:{" "}
          <OpsState value={data.health.freshness} />
        </span>
      </div>
      <section className="ops-section-intro">
        <div>
          <h2>{w("What Needs Attention")}</h2>
          <p>
            {w(
              "Open a queue to make a decision. Counts reflect this site, not the provider test project.",
            )}
          </p>
        </div>
        <Button variant="secondary" onClick={() => void refresh()}>
          {w("Refresh Queues")}
        </Button>
      </section>
      <div className="ops-metrics">
        {queues.map(([label, n, path, Icon]) => (
          <Link key={label} className="ops-metric" to={path}>
            <span>
              <Icon size={20} />
              {w(label)}
            </span>
            <strong>{n ?? "—"}</strong>
            {label === "Service Applications Awaiting Review" && (
              <small>
                {w("Clarification Replies")}: {data.scope_replies}
              </small>
            )}
            <small>
              {w(n === 0 ? "No Items Awaiting Action" : "Open Queue")}
              <ArrowRight size={16} />
            </small>
          </Link>
        ))}
      </div>
      {data.assistance_requests > 0 && (
        <InlineNotice>
          <Link to="/admin/applications">
            {w("Open Email-Assistance Requests")}: {data.assistance_requests} →
          </Link>
        </InlineNotice>
      )}
      <section className="ops-panel">
        <div className="ops-section-intro">
          <div>
            <h2>{w("Operational Attention")}</h2>
            <p>
              {w(
                "Observed incidents are separate from clinical decisions and support reports.",
              )}
            </p>
          </div>
          <Link to="/admin/operations/health">{w("Open System Health")}</Link>
        </div>
        {data.incidents.length ? (
          data.incidents.map((x: any) => (
            <article className="ops-incident" key={x.id}>
              <div>
                <OpsState value={x.state} />
                <strong>{x.code.replaceAll("_", " ")}</strong>
                <p>
                  {w(x.severity)} · {w("Occurrences")}: {x.n}
                </p>
              </div>
              {!x.acknowledged_at && x.state === "Open" && (
                <Button
                  variant="secondary"
                  onClick={() =>
                    void api(prefix + "acknowledge", { id: x.id }, true).then(
                      refresh,
                    )
                  }
                >
                  {w("Acknowledge")}
                </Button>
              )}
            </article>
          ))
        ) : (
          <div className="ops-empty">
            <CheckCircle2 />
            <h3>{w("No Incidents Recorded")}</h3>
            <p>
              {w(
                "This does not prove all systems are healthy. Check collection and job freshness.",
              )}
            </p>
          </div>
        )}
      </section>
      <div className="ops-grid">
        <section className="ops-panel">
          <h2>{w("Processing Freshness")}</h2>
          <OpsState value={data.health.freshness} />
          <p>
            {w(
              "Based on observed scheduler and operations worker completion, not process presence.",
            )}
          </p>
          <Link to="/admin/operations/health">
            {w("Inspect Execution and Queues")} →
          </Link>
        </section>
        <section className="ops-panel">
          <h2>{w("Collection and Coverage")}</h2>
          <OpsState
            value={
              data.collection.native_events
                ? "Native Collection Enabled"
                : "Disabled"
            }
          />
          <p>
            {w(
              "Synthetic activity is excluded by default. Missing collection is not zero demand.",
            )}
          </p>
          <Link to="/admin/operations/insights">
            {w("Explore Journey Evidence")} →
          </Link>
        </section>
      </div>
    </>
  );
}
export function IntegrationCards() {
  const { w } = useLocale(),
    load = useCallback(() => api<any>(prefix + "integration_status"), []),
    r = useResource(load);
  return (
    <section className="ops-panel">
      <h2>{w("Integrations: Configuration and Evidence")}</h2>
      <p>
        {w(
          "A successful isolated test does not configure this site or establish current health. No connectivity test runs when this page opens.",
        )}
      </p>
      {r.error ? (
        <InlineNotice tone="danger">
          {w("Integration status could not be loaded.")}
          <Button onClick={() => void r.refresh()}>{w("Retry")}</Button>
        </InlineNotice>
      ) : !r.data ? (
        <Skeleton />
      ) : (
        <>
          <p>
            {w("Site Configuration Binding")}:{" "}
            <strong>
              {w(r.data.site_binding_present ? "Present" : "Not Bound")}
            </strong>{" "}
            · {w("Private Configuration Loaded")}:{" "}
            {w(r.data.private_configuration_loaded ? "Yes" : "No")}
          </p>
          <div className="ops-integration-grid">
            {r.data.items.map((x: any) => (
              <article className="ops-integration" key={x.key}>
                <h3>
                  {w(
                    (
                      {
                        posthog: "PostHog",
                        bugsink: "Bugsink",
                        mobile: "Mobile Alerts",
                        archive: "Replay Archive",
                        source_maps: "Private Source Maps",
                      } as any
                    )[x.key],
                  )}
                </h3>
                <dl>
                  <dt>{w("Site Configuration")}</dt>
                  <dd>
                    <OpsState value={x.configuration_state} />
                  </dd>
                  <dt>{w("Saved Enablement")}</dt>
                  <dd>{w(x.enabled ? "Enabled" : "Disabled")}</dd>
                  <dt>{w("Effective Runtime")}</dt>
                  <dd>
                    {w(x.effective ? "Eligible; Check Outcomes" : "Inactive")}
                  </dd>
                  <dt>{w("Measured Health")}</dt>
                  <dd>{w(x.health)}</dd>
                  <dt>{w("Current Build Verification")}</dt>
                  <dd>
                    {w(
                      x.current_build_verified
                        ? "Verified"
                        : "Not Verified for This Build",
                    )}
                  </dd>
                  <dt>{w("Last Verification")}</dt>
                  <dd>
                    {w(x.last_verified.status)} · {x.last_verified.verified_on}
                  </dd>
                </dl>
                <p>{w(x.last_verified.scope)}</p>
                <details>
                  <summary>{w("Next Operator Action")}</summary>
                  <p>{w(x.next_action)}</p>
                  <p>
                    {w(
                      "Keep production collection disabled until separately approved. Provider acceptance is not confirmed receipt.",
                    )}
                  </p>
                  {x.observed.length > 0 && (
                    <ul>
                      {x.observed.map((v: any) => (
                        <li key={v.state}>
                          {w(v.state)}: {v.n}
                        </li>
                      ))}
                    </ul>
                  )}
                </details>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
export function HealthOverview({ data }: { data: any }) {
  const { w } = useLocale();
  return (
    <>
      <div className="ops-health-cards">
        <section className="ops-panel">
          <h2>{w("Database Readiness")}</h2>
          <OpsState value={data.database} />
          <p>
            {w(
              "The current authorized query completed. This is not a restore or load test.",
            )}
          </p>
        </section>
        <section className="ops-panel">
          <h2>{w("Observed Job Execution")}</h2>
          <OpsState value={data.freshness} />
          <p>
            {w(
              "Inspect last completion before interpreting an empty queue as healthy.",
            )}
          </p>
        </section>
        <section className="ops-panel">
          <h2>{w("Backup Freshness")}</h2>
          <OpsState value={data.backup} />
          <p>
            {w(
              data.backup_details?.reason ||
                "No verified backup source configured",
            )}
          </p>
        </section>
      </div>
      <section className="ops-panel">
        <h2>{w("Processing and Delivery")}</h2>
        <dl className="ops-facts">
          <dt>{w("Operations Queue")}</dt>
          <dd>
            {w(data.queue.state)} · {w("Pending")}: {data.queue.pending ?? "—"}
          </dd>
          <dt>{w("Oldest Queued Job Age")}</dt>
          <dd>
            {data.queue.oldest_age_seconds === null
              ? w(
                  data.queue.state === "Observed" && data.queue.pending === 0
                    ? "No Queued Jobs"
                    : "Unknown",
                )
              : `${data.queue.oldest_age_seconds} ${w("Seconds")}`}
          </dd>
        </dl>
        <div className="ops-table-wrap">
          <table>
            <caption>{w("Observed Job Execution")}</caption>
            <thead>
              <tr>
                <th>{w("Job")}</th>
                <th>{w("Last Observed")}</th>
                <th>{w("Age in Seconds")}</th>
                <th>{w("State")}</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.beats).map(([name, x]: any) => (
                <tr key={name}>
                  <td>{name.replaceAll("_", " ")}</td>
                  <td>{operationsTime(x.at)}</td>
                  <td>{x.age_seconds}</td>
                  <td>
                    <OpsState
                      value={x.age_seconds > 240 ? "Stale" : "Current"}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!Object.keys(data.beats).length && (
          <p>{w("No Job Completion Observed")}</p>
        )}
        <section id="payment-review">
          <h3>{w("Payment Verification Queue")}</h3>
          <p>
            {w(
              "Receipt verification belongs to the receiving clinician. Operations can follow up without access to private receipts or payment-account details.",
            )}
          </p>
          {data.payment_queue?.length ? (
            <ul>
              {data.payment_queue.map((x: any) => (
                <li key={x.state}>
                  {w(x.state)}: {x.n} · {w("Oldest")}: {String(x.oldest)}
                </li>
              ))}
            </ul>
          ) : (
            <p>{w("No Payments Awaiting Verification")}</p>
          )}
        </section>
        <h3>{w("Appointment Notification Outcomes")}</h3>
        <p>
          {w(
            "ProviderAccepted means accepted for processing, not delivered. Unknown outcomes require investigation; do not resend blindly.",
          )}
        </p>
        {data.notification_states.length ? (
          <ul className="ops-chip-list">
            {data.notification_states.map((x: any) => (
              <li key={x.state}>
                {w(x.state)}: {x.n}
              </li>
            ))}
          </ul>
        ) : (
          <p>{w("No Delivery Outcomes Observed")}</p>
        )}
        <details>
          <summary>{w("Release and Technical Details")}</summary>
          <p className="ops-code">{data.release}</p>
          <p>
            {w("Backup verification timestamp")}:{" "}
            {String(data.backup_details?.verified_at || w("Unavailable"))}
          </p>
          <Link to="/admin/operations/archive">
            {w("Inspect Archive Health")}
          </Link>
        </details>
      </section>
      <IntegrationCards />
    </>
  );
}
function JourneyControls({ synthetic }: { synthetic: boolean }) {
  const { w } = useLocale(),
    [filters, setFilters] = useState({
      family: "application",
      days: "7",
      locale: "all",
      device: "all",
      payment_mode: "all",
      source: "all",
      include_synthetic: synthetic ? "1" : "0",
    });
  const controls = [
    [
      "family",
      "Journey",
      [
        ["application", "Clinician Applications"],
        ["booking", "Scheduled Booking"],
        ["request", "Immediate Requests"],
        ["consultation", "Consultations"],
      ],
    ],
    [
      "days",
      "Time Window",
      [
        ["1", "Last 24 Hours"],
        ["7", "Last 7 Days"],
        ["30", "Last 30 Days"],
        ["90", "Last 90 Days"],
      ],
    ],
    [
      "include_synthetic",
      "Data Scope",
      [
        ["0", "Exclude Synthetic and Staff"],
        ["1", "Include Labelled Synthetic and Staff"],
      ],
    ],
    [
      "locale",
      "Interface Locale",
      [
        ["all", "All Locales"],
        ["en", "English"],
        ["am", "Amharic"],
        ["om", "Afaan Oromo"],
      ],
    ],
    [
      "device",
      "Device",
      [
        ["all", "All Devices"],
        ["mobile", "Mobile"],
        ["tablet", "Tablet"],
        ["desktop", "Desktop"],
        ["unknown", "Unknown"],
      ],
    ],
    [
      "payment_mode",
      "Payment Mode",
      [
        ["all", "All Modes"],
        ["Offline", "Offline Direct Payment"],
        ["Wallet", "Wallet / Integrated Flow"],
      ],
    ],
    [
      "source",
      "Event Source",
      [
        ["all", "All Sources"],
        ["server", "Server-Confirmed Outcomes"],
        ["browser", "Browser Interactions"],
      ],
    ],
  ] as const;
  const control = ([key, label, options]: (typeof controls)[number]) => (
    <Select
      key={key}
      label={w(label)}
      value={filters[key]}
      onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}
    >
      {options.map(([v, l]) => (
        <option key={v} value={v}>
          {w(l)}
        </option>
      ))}
    </Select>
  );
  return (
    <>
      <section className="ops-panel ops-filters">
        <h2>{w("Explore a Journey")}</h2>
        <div className="ops-filter-grid">
          {controls.slice(0, 3).map(control)}
        </div>
        <details>
          <summary>{w("Advanced Filters")}</summary>
          <div className="ops-filter-grid">
            {controls.slice(3).map(control)}
          </div>
        </details>
      </section>
      <JourneyResults key={JSON.stringify(filters)} filters={filters} />
    </>
  );
}
function JourneyResults({ filters }: { filters: Record<string, string> }) {
  const { w } = useLocale(),
    load = useCallback(
      () => api<any>(prefix + "journey_insights", filters),
      [filters],
    ),
    r = useResource(load);
  if (r.error)
    return (
      <InlineNotice tone="danger">
        {w("Journey data could not be loaded. Your filters remain selected.")}
        <Button onClick={() => void r.refresh()}>{w("Retry")}</Button>
      </InlineNotice>
    );
  if (!r.data) return <Skeleton />;
  const d = r.data;
  return (
    <>
      {d.include_synthetic && (
        <InlineNotice>
          {w("Synthetic and Staff Activity Included")} ·{" "}
          {w("Exclude this scope from production conclusions.")}
        </InlineNotice>
      )}
      <section className="ops-panel">
        <div className="ops-section-intro">
          <h2>{w("Attempt Outcomes")}</h2>
          <OpsState value={d.sample_state} />
        </div>
        <p>
          {w(
            (
              {
                application:
                  "Completion means professional application submission. Reviewer approval and individual scope or language decisions are separate.",
                booking:
                  "Completion means a confirmed booking, not a click or an unverified payment claim.",
                request:
                  "Completion means a request converted to an appointment. Payment verification, confirmation and permission to join remain separate.",
                consultation:
                  "Completion means documentation recorded. Connection, leaving and clinician End are separate outcomes.",
              } as Record<string, string>
            )[d.family] ||
              "Completion follows the versioned journey definition.",
          )}
        </p>
        <p>
          {w("Sample Size")}: {d.observed_attempts} {w("Observed Attempts")}
        </p>
        <p>
          {w("Cohort starts")}: {operationsTime(d.since)} →{" "}
          {operationsTime(d.through)} · Africa/Nairobi
        </p>
        <div className="ops-metrics">
          <div className="ops-metric">
            <span>{w("Observed Attempts")}</span>
            <strong>{d.observed_attempts}</strong>
          </div>
          <div className="ops-metric">
            <span>{w("Completed Within 24 Hours")}</span>
            <strong>
              {d.completed_in_window} / {d.observed_attempts}
            </strong>
          </div>
          <div className="ops-metric">
            <span>{w("Completion Rate")}</span>
            <strong>
              {d.completion_percent === null ? "—" : `${d.completion_percent}%`}
            </strong>
            <small>{w("Of Observed Attempts")}</small>
          </div>
          <div className="ops-metric">
            <span>{w("Interrupted Beyond 24 Hours")}</span>
            <strong>{d.interrupted}</strong>
          </div>
        </div>
        {!d.observed_attempts ? (
          <div className="ops-empty">
            <h3>{w("No Eligible Attempts in This Window")}</h3>
            <p>
              {w(
                "No completion percentage is available. Check the time window, filters and collection coverage.",
              )}
            </p>
          </div>
        ) : (
          <div className="ops-outcomes">
            {d.attempts.map((x: any) => (
              <div key={x.state}>
                <div>
                  <strong>{w(x.state)}</strong>
                  <span>
                    {x.n} / {d.observed_attempts}
                  </span>
                </div>
                <progress
                  aria-label={w(x.state)}
                  value={x.n}
                  max={d.observed_attempts}
                />
              </div>
            ))}
          </div>
        )}
        <p>
          {w("Completed After the Window")}: {d.completed_later}
        </p>
        <p>
          {w(
            "Saved, resumed and interrupted attempts do not establish abandonment or user frustration. Small samples are descriptive, not reliable comparisons.",
          )}
        </p>
      </section>
      <section className="ops-panel">
        <h2>{w("Journey Progression Events")}</h2>
        <p>
          {w(
            "Independent stage counts, not a conversion funnel. Browser clicks do not establish successful business outcomes.",
          )}
        </p>
        <div className="ops-table-wrap">
          <table>
            <thead>
              <tr>
                <th>{w("Stage or Outcome")}</th>
                <th>{w("Evidence Source")}</th>
                <th>{w("Events")}</th>
              </tr>
            </thead>
            <tbody>
              {d.events.map((x: any) => (
                <tr key={x.name + x.source}>
                  <td>{w(eventLabel(x.name))}</td>
                  <td>
                    {w(
                      x.source === "server"
                        ? "Server-Confirmed Outcome"
                        : "Browser Interaction",
                    )}
                  </td>
                  <td>{x.n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!d.events.length && (
          <p>{w("No Eligible Journey Events in This Window")}</p>
        )}
        <p>
          {w("Daily Aggregates")}: {d.daily_start} → {d.daily_end} ·
          Africa/Nairobi
        </p>
      </section>
      <section className="ops-panel">
        <h2>{w("Coverage and Interpretation")}</h2>
        <OpsState
          value={
            d.native_collection_enabled
              ? "Native Collection Enabled"
              : "Disabled"
          }
        />
        <p>{w(d.correlation_note)}</p>
        <p>{w(d.coverage_scope)}</p>
        {d.coverage.length ? (
          <ul>
            {d.coverage.map((x: any) => (
              <li key={x.kind}>
                {x.kind.replaceAll("_", " ")}: {x.n}
              </li>
            ))}
          </ul>
        ) : (
          <p>
            {w(
              "Coverage Is Not Yet Available. This Does Not Establish Zero Traffic.",
            )}
          </p>
        )}
        <details>
          <summary>{w("Public-Route Heatmaps")}</summary>
          <p>
            {w(
              "Unavailable: no approved public interaction coordinates have been collected. Private screens are excluded. No heatmap is fabricated from journey event counts.",
            )}
          </p>
        </details>
      </section>
    </>
  );
}
export function QuarterlyReader({
  items,
  refresh,
}: {
  items: any[];
  refresh: () => Promise<void>;
}) {
  const { w } = useLocale(),
    [period, setPeriod] = useState(() => {
      const d = new Date();
      return d.getFullYear() + "-Q" + (Math.floor(d.getMonth() / 3) + 1);
    }),
    [selected, setSelected] = useState<any>(null),
    [compare, setCompare] = useState<any>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [note, setNote] = useState("");
  const metadata = useResource(
    useCallback(() => api<any>(prefix + "integration_status"), []),
  );
  const open = async (id: string, comparison = false) => {
    setError("");
    try {
      const d = await api<any>(prefix + "report_detail", { id }, true);
      if (comparison) setCompare(d);
      else {
        setSelected(d);
        setNote("");
      }
    } catch {
      setError("The report could not be opened. Try again.");
    }
  };
  return (
    <>
      <section className="ops-panel">
        <h2>{w("Report Library")}</h2>
        <p>
          {w(
            "Calendar quarters use Africa/Nairobi. A partial quarter is not directly comparable with a complete quarter.",
          )}
        </p>
        <div className="ops-filter-grid">
          <TextField
            label={w("Calendar Quarter in Africa/Nairobi")}
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            placeholder="2026-Q4"
          />
          <Button
            loading={busy}
            onClick={() => {
              setBusy(true);
              setError("");
              void api(prefix + "report_compile", { period }, true)
                .then(refresh)
                .catch(() =>
                  setError(
                    "The quarterly report could not be generated. Check the period.",
                  ),
                )
                .finally(() => setBusy(false));
            }}
          >
            {w("Generate or Refresh Report")}
          </Button>
          {metadata.data?.scenario && (
            <Button
              variant="secondary"
              onClick={() =>
                void api(
                  prefix + "report_compile",
                  { period, include_synthetic: 1 },
                  true,
                )
                  .then(refresh)
                  .catch(() =>
                    setError("The synthetic report could not be generated."),
                  )
              }
            >
              {w("Generate Synthetic Review Report")}
            </Button>
          )}
        </div>
        {error && <InlineNotice tone="danger">{w(error)}</InlineNotice>}
        {!items.length ? (
          <div className="ops-empty">
            <h3>{w("No Quarterly Reports Yet")}</h3>
            <p>
              {w(
                "Generate a supported quarter to inspect measured data and its coverage limitations.",
              )}
            </p>
          </div>
        ) : (
          <div className="ops-report-library">
            {items.map((x) => (
              <Button
                key={x.id}
                data-report-id={x.id}
                variant={selected?.id === x.id ? "primary" : "secondary"}
                onClick={() => void open(x.id)}
              >
                {x.period} · {w("Version")} {x.version}
              </Button>
            ))}
          </div>
        )}
      </section>
      {selected && (
        <article className="ops-panel ops-report">
          <header className="ops-section-intro">
            <div>
              <h2>{selected.data.period}</h2>
              <OpsState
                value={
                  selected.data.incomplete_period
                    ? "Partial Quarter"
                    : "Completed Quarter"
                }
              />
              <p>
                {w("Version")}: {selected.version} · {w("Timezone")}:
                Africa/Nairobi
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() =>
                void (async () => {
                  try {
                    const detail = await api(
                        prefix + "report_export",
                        { id: selected.id },
                        true,
                      ),
                      blob = new Blob([JSON.stringify(detail, null, 2)], {
                        type: "application/json",
                      }),
                      url = URL.createObjectURL(blob),
                      a = document.createElement("a");
                    a.href = url;
                    a.download = "teletena-quarter-report.json";
                    a.click();
                    setTimeout(() => URL.revokeObjectURL(url), 1000);
                  } catch {
                    setError("The report could not be exported. Try again.");
                  }
                })()
              }
            >
              {w("Export Report")}
            </Button>
          </header>
          {selected.data.data_scope && (
            <InlineNotice>
              {w("Isolated Synthetic Review Report")} ·{" "}
              {w("Not Production Metrics")}
            </InlineNotice>
          )}
          <p>
            {w("Covered Dates")}: {operationsTime(selected.data.start_utc)} →{" "}
            {operationsTime(selected.data.generated_through_utc)} ·
            Africa/Nairobi
          </p>
          <p>
            {w("Quarter End, Exclusive")}:{" "}
            {operationsTime(selected.data.end_utc_exclusive)} · Africa/Nairobi
          </p>
          <div className="ops-metrics">
            <div className="ops-metric">
              <span>{w("Measured Events")}</span>
              <strong>{selected.data.sample_size}</strong>
            </div>
            <div className="ops-metric">
              <span>{w("Excluded Synthetic and Staff")}</span>
              <strong>{selected.data.excluded_synthetic_events}</strong>
            </div>
          </div>
          <h3>{w("Measured Findings")}</h3>
          {Object.keys(selected.data.events).length ? (
            <div className="ops-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{w("Event")}</th>
                    <th>{w("Count")}</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(selected.data.events).map(([k, n]: any) => (
                    <tr key={k}>
                      <td>{w(eventLabel(k))}</td>
                      <td>{n}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>
              {w(
                "No Eligible Measured Events. This Does Not Establish Zero Activity.",
              )}
            </p>
          )}
          <h3>{w("Journey Attempt Summary")}</h3>
          {selected.data.attempts?.length ? (
            <div className="ops-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{w("Journey")}</th>
                    <th>{w("State")}</th>
                    <th>{w("Attempts")}</th>
                    <th>{w("Completed Within 24 Hours")}</th>
                    <th>{w("Completed Later")}</th>
                    <th>{w("Mean Completion Time")}</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.data.attempts.map((x: any, i: number) => (
                    <tr key={i}>
                      <td>
                        {w(
                          (
                            {
                              application:
                                "Professional Application Submission",
                              booking: "Booking Confirmation",
                              request: "Request Converted to Appointment",
                              consultation: "Consultation Documentation",
                            } as Record<string, string>
                          )[x.family] || x.family,
                        )}
                      </td>
                      <td>{w(x.state)}</td>
                      <td>{x.n}</td>
                      <td>{x.completed_in_window}</td>
                      <td>{x.completed_later}</td>
                      <td>
                        {x.seconds === null
                          ? w("Unavailable")
                          : `${Math.round(Number(x.seconds) / 60)} ${w("Minutes")}`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>
              {w(
                "No Eligible Attempt Summaries in This Report. This Is Not Zero Activity.",
              )}
            </p>
          )}
          <h3>{w("Coverage Limitations")}</h3>
          <p>{w(selected.data.notes)}</p>
          <p>{w(selected.data.attempt_segmentation_limit)}</p>
          <p>
            {w(
              "Counters are site-wide and may include synthetic activity. Missing collection and short samples limit comparisons.",
            )}
          </p>
          <details>
            <summary>{w("Collection and Archive Coverage")}</summary>
            <ul>
              {selected.data.coverage.map((x: any, i: number) => (
                <li key={i}>
                  {String(x.day)} · {x.kind}: {x.n}
                </li>
              ))}
            </ul>
            <ul>
              {selected.data.archive.map((x: any) => (
                <li key={x.state}>
                  {w(x.state)}: {x.n} · {humanBytes(x.bytes)}
                </li>
              ))}
            </ul>
          </details>
          <h3>{w("Support Resolution")}</h3>
          {selected.data.support_resolution.length ? (
            <div className="ops-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{w("Category")}</th>
                    <th>{w("Reports")}</th>
                    <th>{w("Mean Resolution Time")}</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.data.support_resolution.map((x: any) => (
                    <tr key={x.category}>
                      <td>{w(x.category)}</td>
                      <td>{x.n}</td>
                      <td>
                        {x.seconds === null
                          ? w("Not Yet Resolved")
                          : `${Math.round(x.seconds / 60)} ${w("Minutes")}`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>{w("No Support Reports in This Period")}</p>
          )}
          <h3>{w("Compare a Supported Report")}</h3>
          <Select
            label={w("Comparison Report")}
            value={compare?.id || ""}
            onChange={(e) => {
              if (e.target.value) void open(e.target.value, true);
              else setCompare(null);
            }}
          >
            <option value="">{w("Choose a Report")}</option>
            {items
              .filter((x) => x.id !== selected.id)
              .map((x) => (
                <option key={x.id} value={x.id}>
                  {x.period} · {w("Version")} {x.version}
                </option>
              ))}
          </Select>
          {compare && (
            <div className="ops-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{w("Period")}</th>
                    <th>{w("Coverage State")}</th>
                    <th>{w("Measured Events")}</th>
                  </tr>
                </thead>
                <tbody>
                  {[selected, compare].map((x) => (
                    <tr key={x.id}>
                      <td>
                        {x.data.period} v{x.version}
                      </td>
                      <td>
                        {w(
                          x.data.incomplete_period
                            ? "Partial Quarter"
                            : "Completed Quarter",
                        )}
                      </td>
                      <td>{x.data.sample_size}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p>
                {w(
                  "Different coverage and partial periods prevent an automatic improvement claim.",
                )}
              </p>
            </div>
          )}
          <h3>{w("Reviewer Annotations")}</h3>
          <p>
            {w(
              "Human interpretation is separate from measured evidence. Do not include clinical or identity details.",
            )}
          </p>
          {JSON.parse(selected.annotation || "[]").map((x: any, i: number) => (
            <article className="ops-reply" key={i}>
              <p className="prewrap">{x.note}</p>
              <time>{x.at}</time>
            </article>
          ))}
          <label className="field">
            <span>
              {w("Reviewer Interpretation and Recommended Follow-Up")}
            </span>
            <textarea
              rows={4}
              maxLength={3000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <Button
            disabled={!note.trim()}
            onClick={() =>
              void api(
                prefix + "report_annotate",
                { id: selected.id, note },
                true,
              )
                .then(() => open(selected.id))
                .catch(() =>
                  setError(
                    "The annotation was not saved. Your text remains here.",
                  ),
                )
            }
          >
            {w("Save Annotation")}
          </Button>
        </article>
      )}
    </>
  );
}

export function JourneyExplorer() {
  const { w } = useLocale(),
    load = useCallback(() => api<any>(prefix + "integration_status"), []),
    r = useResource(load);
  if (r.error)
    return (
      <InlineNotice tone="danger">
        {w("Journey context could not be loaded.")}
        <Button onClick={() => void r.refresh()}>{w("Retry")}</Button>
      </InlineNotice>
    );
  if (!r.data) return <Skeleton />;
  return <JourneyControls synthetic={!!r.data.scenario} />;
}
