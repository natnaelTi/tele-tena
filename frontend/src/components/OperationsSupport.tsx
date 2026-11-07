import { operationsTime } from "./operationsLabels";
import { useCallback, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useLocale } from "../hooks/useLocale";
import { useSession } from "../hooks/useSession";
import { useResource } from "../hooks/useResource";
import { api, ApiError } from "../api";
import { Select, Button, InlineNotice, Skeleton } from "./ui";
import { AttachmentPreview } from "./AttachmentPreview";
import { OpsState } from "../pages/OperationsPortalViews";
const prefix = "tele_tena.api.operations.";
const STATES = [
  "New",
  "Triaged",
  "In Progress",
  "Waiting for User",
  "Resolved",
  "Closed",
];
function age(value: string) {
  const minutes = Math.max(
    0,
    Math.floor(
      (Date.now() - new Date(value.replace(" ", "T") + "Z").getTime()) / 60000,
    ),
  );
  return minutes < 60
    ? `${minutes}m`
    : minutes < 1440
      ? `${Math.floor(minutes / 60)}h`
      : `${Math.floor(minutes / 1440)}d`;
}
export function ReviewerSupportQueue() {
  const { w } = useLocale(),
    [filters, setFilters] = useState({
      state: "all",
      priority: "all",
      ownership: "all",
      offset: 0,
    });
  return (
    <>
      <section className="ops-panel">
        <h2>{w("Find Reports")}</h2>
        <div className="ops-filter-grid">
          <Select
            label={w("Report Status")}
            value={filters.state}
            onChange={(e) =>
              setFilters({ ...filters, state: e.target.value, offset: 0 })
            }
          >
            {["all", ...STATES].map((x) => (
              <option key={x} value={x}>
                {w(x === "all" ? "All Statuses" : x)}
              </option>
            ))}
          </Select>
          <Select
            label={w("Priority")}
            value={filters.priority}
            onChange={(e) =>
              setFilters({ ...filters, priority: e.target.value, offset: 0 })
            }
          >
            {["all", "Critical", "High", "Normal", "Low"].map((x) => (
              <option key={x} value={x}>
                {w(x === "all" ? "All Priorities" : x)}
              </option>
            ))}
          </Select>
          <Select
            label={w("Ownership")}
            value={filters.ownership}
            onChange={(e) =>
              setFilters({ ...filters, ownership: e.target.value, offset: 0 })
            }
          >
            {[
              ["all", "All Reviewers"],
              ["mine", "Assigned to Me"],
              ["unassigned", "Unassigned"],
            ].map(([v, l]) => (
              <option key={v} value={v}>
                {w(l)}
              </option>
            ))}
          </Select>
        </div>
      </section>
      <QueueRows
        key={JSON.stringify(filters)}
        filters={filters}
        onPage={(offset) => setFilters({ ...filters, offset })}
      />
    </>
  );
}
function QueueRows({
  filters,
  onPage,
}: {
  filters: Record<string, string | number>;
  onPage: (n: number) => void;
}) {
  const { w } = useLocale(),
    load = useCallback(
      () => api<any>(prefix + "support_queue", filters),
      [filters],
    ),
    r = useResource(load);
  if (r.error)
    return (
      <InlineNotice tone="danger">
        {w("Support queue could not be loaded. Your filters remain selected.")}
        <Button onClick={() => void r.refresh()}>{w("Retry")}</Button>
      </InlineNotice>
    );
  if (!r.data) return <Skeleton />;
  const d = r.data;
  return (
    <section className="ops-panel ops-list">
      <div className="ops-section-intro">
        <h2>{w("Support Queue")}</h2>
        <span>
          {d.total} {w("Reports")}
        </span>
      </div>
      {d.items.length ? (
        <div className="ops-table-wrap">
          <table>
            <thead>
              <tr>
                <th>{w("Report")}</th>
                <th>{w("Status")}</th>
                <th>{w("Priority")}</th>
                <th>{w("Assigned Reviewer")}</th>
                <th>{w("Age")}</th>
              </tr>
            </thead>
            <tbody>
              {d.items.map((x: any) => (
                <tr key={x.id}>
                  <td>
                    <Link to={"/admin/support/" + x.id}>
                      {w(x.category)} · {x.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td>
                    <OpsState value={x.state} />
                  </td>
                  <td>{w(x.priority)}</td>
                  <td>{x.assignee_name || w("Unassigned")}</td>
                  <td>
                    <time
                      title={operationsTime(x.created) + " · Africa/Nairobi"}
                    >
                      {age(String(x.created))}
                    </time>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="ops-empty">
          <h3>{w("No Problem Reports")}</h3>
          <p>
            {w(
              "No reports match these filters. Change the filters to check another queue.",
            )}
          </p>
        </div>
      )}
      <div className="actions">
        <Button
          variant="secondary"
          disabled={!d.offset}
          onClick={() => onPage(Math.max(0, d.offset - d.page_size))}
        >
          {w("Previous Page")}
        </Button>
        <span>
          {d.total ? d.offset + 1 : 0}–{d.offset + d.items.length} / {d.total}
        </span>
        <Button
          variant="secondary"
          disabled={d.offset + d.page_size >= d.total}
          onClick={() => onPage(d.offset + d.page_size)}
        >
          {w("Next Page")}
        </Button>
      </div>
    </section>
  );
}
export function SupportRecord({
  id,
  reviewer,
}: {
  id?: string;
  reviewer: boolean;
}) {
  const latest = useRef<any>(null);
  const { w } = useLocale(),
    { session } = useSession(),
    load = useCallback(async () => {
      const next = await api<any>(
        prefix + (id ? "support_detail" : "support_list"),
        id ? { id } : {},
        !!id,
      );
      if (!id) return next;
      if (
        latest.current &&
        String(latest.current.modified) > String(next.modified)
      )
        return latest.current;
      latest.current = next;
      return next;
    }, [id]),
    r = useResource(load),
    [body, setBody] = useState(""),
    [audience, setAudience] = useState("Internal"),
    [key, setKey] = useState(() => crypto.randomUUID()),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const base = reviewer ? "/admin/support" : "/support";
  if (r.error)
    return (
      <InlineNotice tone="danger">
        {w("This Support Report Is Unavailable")}
        <Button onClick={() => void r.refresh()}>{w("Retry")}</Button>
      </InlineNotice>
    );
  if (!r.data) return <Skeleton />;
  if (!id)
    return (
      <div className="ops-list">
        {r.data.length ? (
          r.data.map((x: any) => (
            <Link key={x.id} to={base + "/" + x.id}>
              <strong>{w(x.category)}</strong>
              <OpsState value={x.state} />
              <time>{String(x.modified)}</time>
            </Link>
          ))
        ) : (
          <p>{w("No Problem Reports")}</p>
        )}
      </div>
    );
  const d = r.data;
  return (
    <>
      <Link to={base}>← {w("Back to Reports")}</Link>
      <section className="ops-panel">
        <div className="ops-section-intro">
          <h2>{w(d.category)}</h2>
          <OpsState value={d.state} />
        </div>
        <p className="ops-code">
          {w("Reference")}: {id}
        </p>
        <p className="prewrap">{d.description}</p>
        <div className="ops-chip-list">
          <span>{w(d.priority)}</span>
          <span>
            {w("Created")}: {operationsTime(d.created)} · Africa/Nairobi
          </span>
        </div>
        {d.attachments.map((f: any) => (
          <p key={f.id}>
            {f.filename}{" "}
            <AttachmentPreview
              source="support"
              id={f.id}
              filename={f.filename}
              purpose="Support Screenshot"
            />
          </p>
        ))}
      </section>
      {reviewer && <Assignment key={d.id} data={d} refresh={r.refresh} />}
      <section className="ops-panel">
        <h2>{w("Response History")}</h2>
        {!d.replies.length && <p>{w("No Responses Yet")}</p>}
        {d.replies.map((x: any) => (
          <article
            className={
              "ops-reply " + (x.audience === "Internal" ? "ops-internal" : "")
            }
            key={x.id}
          >
            <strong>
              {w(
                x.audience === "Internal"
                  ? "Private Reviewer Note"
                  : "Reply Visible to the Reporter",
              )}
            </strong>
            <p className="prewrap">{x.body}</p>
            <time>{operationsTime(x.created)} · Africa/Nairobi</time>
          </article>
        ))}
      </section>
      <section className="ops-panel">
        <h2>{w("Add a Response")}</h2>
        {reviewer && (
          <Select
            label={w("Response Visibility")}
            value={audience}
            onChange={(e) => setAudience(e.target.value)}
          >
            <option value="Internal">{w("Private Reviewer Note")}</option>
            <option value="User">{w("Reply Visible to the Reporter")}</option>
          </Select>
        )}
        <InlineNotice>
          {w(
            reviewer && audience === "Internal"
              ? "Only authorized reviewers can read this note. It is not sent to the reporter."
              : "This reply is visible to the reporter. Follow-up notifications respect the existing permission and communication settings.",
          )}
        </InlineNotice>
        <label className="field">
          <span>
            {w("Response")}
            <span className="required-marker" aria-hidden="true">
              {" "}
              *
            </span>
          </span>
          <textarea
            required
            rows={4}
            maxLength={3000}
            value={body}
            onChange={(e) => {
              setBody(e.target.value);
              setKey(crypto.randomUUID());
            }}
          />
        </label>
        {error && <InlineNotice tone="danger">{w(error)}</InlineNotice>}
        <Button
          disabled={busy || !body.trim()}
          loading={busy}
          onClick={() =>
            void (async () => {
              setBusy(true);
              setError("");
              try {
                await api(
                  prefix + "support_reply",
                  {
                    id,
                    body,
                    audience: reviewer ? audience : "User",
                    retry_key: key,
                    ...(reviewer
                      ? {
                          preserve_triage: true,
                        }
                      : {}),
                  },
                  true,
                );
                setBody("");
                setKey(crypto.randomUUID());
                await r.refresh();
              } catch {
                setError("The response was not saved. Your text remains here.");
              } finally {
                setBusy(false);
              }
            })()
          }
        >
          {w(
            reviewer && audience === "Internal"
              ? "Save Private Note"
              : "Send Reply",
          )}
        </Button>
        <small>{session ? w("Access and changes are audited.") : ""}</small>
      </section>
    </>
  );
}
function Assignment({
  data,
  refresh,
}: {
  data: any;
  refresh: () => Promise<void>;
}) {
  const { w } = useLocale(),
    [state, setState] = useState(data.state),
    [priority, setPriority] = useState(data.priority),
    [assignee, setAssignee] = useState(data.assignee || ""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    load = useCallback(() => api<any>(prefix + "support_queue"), []),
    r = useResource(load);
  return (
    <section className="ops-panel">
      <h2>{w("Triage and Ownership")}</h2>
      <div className="ops-filter-grid">
        <Select
          label={w("Report Status")}
          value={state}
          onChange={(e) => setState(e.target.value)}
        >
          {STATES.map((x) => (
            <option key={x} value={x}>
              {w(x)}
            </option>
          ))}
        </Select>
        <Select
          label={w("Priority")}
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          {["Low", "Normal", "High", "Critical"].map((x) => (
            <option key={x} value={x}>
              {w(x)}
            </option>
          ))}
        </Select>
        <Select
          label={w("Assigned Reviewer")}
          value={assignee}
          onChange={(e) => setAssignee(e.target.value)}
        >
          <option value="">{w("Unassigned")}</option>
          {r.data?.reviewers.map((x: any) => (
            <option key={x.id} value={x.id}>
              {x.label}
            </option>
          ))}
        </Select>
      </div>
      {error && <InlineNotice tone="danger">{w(error)}</InlineNotice>}
      {notice && <InlineNotice tone="success">{w(notice)}</InlineNotice>}
      <Button
        variant="secondary"
        loading={busy}
        onClick={() => {
          setBusy(true);
          setError("");
          void api(
            prefix + "support_assign",
            {
              id: data.id,
              state,
              priority,
              assignee: assignee || null,
              expected: {
                state: data.state,
                priority: data.priority,
                assignee: data.assignee || null,
              },
            },
            true,
          )
            .then(async () => {
              await refresh();
              setNotice("Triage Updated");
            })
            .catch((error) =>
              setError(
                error instanceof ApiError &&
                  error.code === "operations_conflict"
                  ? "This report was changed by another reviewer. Reload saved triage before applying your changes."
                  : "Assignment could not be saved. Your choices remain here.",
              ),
            )
            .finally(() => setBusy(false));
        }}
      >
        {w("Save Triage")}
      </Button>
      <Button
        variant="quiet"
        disabled={busy}
        onClick={() =>
          void api<any>(prefix + "support_detail", { id: data.id }, true)
            .then(async (next) => {
              setState(next.state);
              setPriority(next.priority);
              setAssignee(next.assignee || "");
              setError("");
              setNotice("Saved Triage Reloaded");
              await refresh();
            })
            .catch(() =>
              setError(
                "Saved triage could not be reloaded. Your choices remain here.",
              ),
            )
        }
      >
        {w("Reload Saved Triage")}
      </Button>
      <p>
        {w(
          "Reloading saved triage replaces unsaved triage choices. Your response draft remains here.",
        )}
      </p>
      <p>
        {w(
          "Triage changes do not send the private report or notes to an external provider. Use a visible reply when the reporter needs an update.",
        )}
      </p>
    </section>
  );
}
