import { operationsTime } from "./operationsLabels";
import { useCallback, type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Select } from "./ui";
import { ClipboardCheck, Files, ArrowUpRight, ShieldCheck } from "lucide-react";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";
import { api } from "../api";
import { OperationsNavigation } from "./OperationsNavigation";
import "../pages/Operations.css";
export function OperationsFrame({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  const location = useLocation(),
    navigate = useNavigate();
  const active = location.pathname.startsWith("/admin/support")
    ? "/admin/support"
    : location.pathname;
  const { w } = useLocale(),
    load = useCallback(
      () => api<any>("tele_tena.api.operations.integration_status"),
      [],
    ),
    r = useResource(load);
  return (
    <div className="operations-page operations-portal ph-no-capture">
      <aside className="ops-sidebar">
        <div className="ops-sidebar-heading">
          <ShieldCheck size={23} />
          <div>
            <strong>{w("Operations")}</strong>
            <small>{w("Reviewer Workspace")}</small>
          </div>
        </div>
        <p className="ops-nav-group">{w("Manage and Understand")}</p>
        <div className="ops-mobile-section">
          <Select
            label={w("Operations Sections")}
            value={active}
            onChange={(e) => navigate(e.target.value)}
          >
            {[
              ["/admin/operations", "Overview"],
              ["/admin/operations/insights", "Journey Insights"],
              ["/admin/operations/health", "System Health"],
              ["/admin/operations/archive", "Replay Archive"],
              ["/admin/operations/reports", "Quarterly Reports"],
              ["/admin/operations/settings", "Operational Settings"],
              ["/admin/support", "User Support"],
            ].map(([path, label]) => (
              <option key={path} value={path}>
                {w(label)}
              </option>
            ))}
          </Select>
        </div>
        <OperationsNavigation />
        <p className="ops-nav-group">{w("Review Applications")}</p>
        <nav className="ops-review-links" aria-label={w("Application Queues")}>
          <Link to="/admin/applications">
            <ClipboardCheck size={19} />
            {w("Applications")}
            <ArrowUpRight size={15} />
          </Link>
          <Link to="/admin/vetting">
            <Files size={19} />
            {w("Service Applications")}
            <ArrowUpRight size={15} />
          </Link>
        </nav>
        <p className="ops-sidebar-note">
          {w(
            "Operational access does not grant access to clinical records or private identity evidence.",
          )}
        </p>
      </aside>
      <div className="ops-content">
        <header className="ops-page-heading">
          <p className="eyebrow">{w("TeleTena Operations")}</p>
          <h1>{w(title)}</h1>
          <p>{w(description)}</p>
          <div className="ops-context">
            <span>
              {w("Environment")}: {r.data?.environment || w("Unknown")}
            </span>
            <span>
              {w("Observed")}:{" "}
              {r.data?.observed_at
                ? operationsTime(r.data.observed_at)
                : w("Unavailable")}{" "}
              · Africa/Nairobi
            </span>
            <span>{w("Current Database")}</span>
          </div>
          {r.data?.scenario && (
            <div role="status" className="ops-scenario">
              {w("Isolated Synthetic Review Scenario")} ·{" "}
              {w("No provider traffic, real care or production metrics.")}
            </div>
          )}
        </header>
        {children}
      </div>
    </div>
  );
}
