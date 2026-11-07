import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";
import { Button, Select, TextField, InlineNotice, Skeleton } from "./ui";
import { ArchiveReplay } from "./ArchiveReplay";
import { humanBytes, OpsState } from "../pages/OperationsPortalViews";
const prefix = "tele_tena.api.operations.";
export function OperationsArchiveRecords({ metadata }: { metadata: any }) {
  const { w } = useLocale(),
    [state, setState] = useState("all"),
    [reference, setReference] = useState(""),
    [query, setQuery] = useState(""),
    [offset, setOffset] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => {
      setQuery(reference.trim().toLowerCase());
      setOffset(0);
    }, 300);
    return () => clearTimeout(t);
  }, [reference]);
  return (
    <>
      <h3>{w("Find a Recording")}</h3>
      <div className="ops-filter-grid">
        <Select
          label={w("Recording State")}
          value={state}
          onChange={(e) => {
            setState(e.target.value);
            setOffset(0);
          }}
        >
          {[
            "all",
            "Verified",
            "Pending",
            "Capturing",
            "Exporting",
            "Failed",
            "Incomplete",
            "Expired",
          ].map((x) => (
            <option key={x} value={x}>
              {w(x === "all" ? "All States" : x)}
            </option>
          ))}
        </Select>
        <TextField
          label={w("Recording Reference Prefix")}
          placeholder={w("Paste a short recording reference")}
          value={reference}
          onChange={(e) => setReference(e.target.value)}
        />
      </div>
      <RecordRows
        key={state + query + offset}
        state={state}
        reference={query}
        offset={offset}
        onPage={setOffset}
        metadata={metadata}
      />
    </>
  );
}
function RecordRows({
  state,
  reference,
  offset,
  onPage,
  metadata,
}: {
  state: string;
  reference: string;
  offset: number;
  onPage: (n: number) => void;
  metadata: any;
}) {
  const { w } = useLocale(),
    [message, setMessage] = useState(""),
    load = useCallback(
      () => api<any>(prefix + "archive_records", { state, reference, offset }),
      [state, reference, offset],
    ),
    r = useResource(load);
  useEffect(() => {
    const i = setInterval(() => void r.refresh(), 30000);
    return () => clearInterval(i);
  }, [r.refresh]);
  if (r.error)
    return (
      <InlineNotice tone="danger">
        {w("Recordings could not be loaded. Check the reference and retry.")}
        <Button onClick={() => void r.refresh()}>{w("Retry")}</Button>
      </InlineNotice>
    );
  if (!r.data) return <Skeleton />;
  const d = r.data;
  return (
    <>
      {message && <InlineNotice>{w(message)}</InlineNotice>}
      {!d.items.length && (
        <div className="ops-empty">
          <h3>{w("No Recordings Match This State")}</h3>
          <p>
            {w(
              "Check the state or reference. Disabled capture and missing coverage are separate from an empty archive.",
            )}
          </p>
        </div>
      )}
      {d.items.map((x: any) => (
        <article className="ops-reply" key={x.id}>
          <div className="ops-section-intro">
            <div>
              <OpsState value={x.state} />
              <p className="ops-code">
                {w("Reference")}: {x.id.slice(0, 16)}
              </p>
            </div>
            <span>{humanBytes(x.size_bytes)}</span>
          </div>
          <p>
            {w("Captured")}: {String(x.captured)} · {w("Expires")}:{" "}
            {String(x.expires)}
          </p>
          {x.failure_code && (
            <p>
              {x.failure_code} · {w("Attempts")}: {x.tries}
            </p>
          )}
          {metadata.playback_available && x.state === "Verified" ? (
            <ArchiveReplay id={x.id} />
          ) : (
            <p>{w("This recording has no verified playable archive.")}</p>
          )}
          {metadata.site_export_enabled &&
            metadata.project_proof_verified &&
            ["Failed", "Incomplete"].includes(x.state) && (
              <Button
                variant="secondary"
                onClick={() =>
                  void api<any>(prefix + "archive_retry", { id: x.id }, true)
                    .then(() => {
                      setMessage(
                        "Export retry requested within the existing policy window.",
                      );
                      return r.refresh();
                    })
                    .catch(() =>
                      setMessage(
                        "This recording cannot be retried. Check missing data, expiry, permissions and the retry limit.",
                      ),
                    )
                }
              >
                {w("Retry Export")}
              </Button>
            )}
        </article>
      ))}
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
    </>
  );
}
