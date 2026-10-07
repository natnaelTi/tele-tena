import { Link, Navigate, NavLink, Outlet, useLocation } from "react-router-dom";
import { useCallback, useEffect, useState } from "react";
import {
  CalendarDays,
  ClipboardCheck,
  Home,
  LogOut,
  Search,
  Settings2,
  Stethoscope,
  Wallet,
  Clock3,
  FileHeart,
  Building2,
} from "lucide-react";
import { Brand } from "../components/Brand";
import { Button, InlineNotice, Skeleton } from "../components/ui";
import { LanguageSelect, useLocale } from "../hooks/useLocale";
import { useSession } from "../hooks/useSession";
import { journeyApi } from "../journey-api";
import WorkspaceTour from "../components/WorkspaceTour";
import { useResource } from "../hooks/useResource";
import { ApiError } from "../api";
export function DemoBar() {
  return (
    <div className="demo-bar" role="note" aria-label="Demonstration environment">
      <span className="demo-dot" aria-hidden="true" />
      Demonstration environment — no real payments or clinical care.
    </div>
  );
}
export function TranslationNote() {
  const { t } = useLocale();
  return (
    <details className="translation-note">
      <summary>Language & translation review</summary>
      <p>{t("review")} Some new copy remains in English pending review.</p>
    </details>
  );
}

function ClinicianRequestAvailability() {
  const {w} = useLocale();
  const load = useCallback(() => journeyApi.requestPresence(), []);
  const presence = useResource<any>(load);
  const refresh = presence.refresh;
  const ready = !!presence.data?.ready;
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<"network" | "session" | "permission" | "update" | null>(null);
  const failureMessage = failure === "network"
    ? "Connection interrupted; request availability may expire."
    : failure === "session"
      ? "Your session expired. Sign in again to update request availability."
      : failure === "permission"
        ? "You don’t have permission to change request availability."
        : failure === "update"
          ? "Could not update request availability. Review the setup items and try again."
          : null;
  const recordFailure = useCallback((error: unknown) => {
    if (error instanceof ApiError && error.code === "session_required") setFailure("session");
    else if (error instanceof ApiError && error.code === "permission_denied") setFailure("permission");
    else if (error instanceof TypeError) setFailure("network");
    else setFailure("update");
    void refresh().catch(() => undefined);
  }, [refresh]);
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (!ready) { void refresh(); return; }
      void journeyApi.setRequestPresence(true)
        .then(() => { setFailure(null); void refresh(); })
        .catch(recordFailure);
    }, 30000);
    return () => window.clearInterval(timer);
  }, [ready, refresh, recordFailure]);
  const toggle = async () => {
    setBusy(true);
    try {
      await journeyApi.setRequestPresence(!presence.data?.ready);
      setFailure(null);
      await presence.refresh();
    } catch (error) {
      recordFailure(error);
    } finally { setBusy(false); }
  };
  const data = presence.data;
  const guidance:Record<string,{label:string;to:string}>={
    approval_required:{label:"Approval required",to:"/clinician/vetting"},
    language_required:{label:"Add a care language",to:"/clinician/account"},
    offering_required:{label:"Publish an offering",to:"/clinician/services"},
    scope_approval_required:{label:"Get approval for a service scope",to:"/clinician/vetting"},
    published_schedule_required:{label:"Publish availability",to:"/clinician/availability"},
    immediate_policy_required:{label:"Ask a reviewer to enable immediate requests for a service",to:"/clinician/vetting"},
    no_immediate_capacity:{label:"No complete session fits the next 30 minutes",to:"/clinician/availability"},
  };
  return <section className="request-presence-shell" aria-label={w("Request availability")}>
    <div><strong>{w(data?.ready ? "Available for requests" : "Requests paused")}</strong>
      <span>{w(failureMessage || (data?.ready ? "Ready status expires if this session disconnects." : "Complete setup before receiving requests."))}</span>
      {!!data?.reasons?.length && <nav className="request-readiness-actions" aria-label={w("Setup needed")}>{data.reasons.map((reason: string) => {const item=guidance[reason];return item?<Link key={reason} to={item.to}>{w(item.label)}</Link>:<span key={reason}>{w("Complete setup before receiving requests.")}</span>;})}</nav>}
    </div>
    <Button className="compact-button" variant={data?.ready ? "secondary" : "primary"} loading={busy} disabled={!data?.configured && !data?.ready} onClick={() => void toggle()}>{w(data?.ready ? "Pause" : "Go available")}</Button>
    {failureMessage && <InlineNotice tone="danger">{w(failureMessage)}</InlineNotice>}
  </section>;
}
export function PublicLayout() {
  const { w } = useLocale();
  return (
    <>
      <DemoBar />
      <header className="public-header container">
        <Brand />
        <nav aria-label="Main navigation">
          <a href={(import.meta.env.PROD ? "/teletena/" : "/") + "#how-it-works"}>{w("How it works")}</a>
          <Link to="/for-clinicians">{w("For clinicians")}</Link>
          <LanguageSelect />
          <Link className="button secondary" to="/sign-in">
            {w("Sign in")}
          </Link>
        </nav>
      </header>
      <Outlet />
      <footer className="public-footer container">
        <Brand />
        <p>A little more space for you.</p>
        <Link to="/sign-in">{w("Find care")}</Link>
        <TranslationNote />
      </footer>
    </>
  );
}
export function AuthLayout() {
  return (
    <>
      <DemoBar />
      <header className="auth-header">
        <Brand />
        <LanguageSelect />
      </header>
      <main className="auth-main">
        <Outlet />
      </main>
      <div className="auth-footer">
        <TranslationNote />
      </div>
    </>
  );
}
export function RequireSession() {
  const { session, loading, error, refresh } = useSession();
  const location = useLocation();
  if (loading)
    return (
      <main className="container">
        <Skeleton />
      </main>
    );
  if (error)
    return (
      <main className="container">
        <InlineNotice tone="danger">
          We couldn’t connect.{" "}
          <Button onClick={() => void refresh().catch(() => undefined)}>
            Try again
          </Button>
        </InlineNotice>
      </main>
    );
  return session ? <Outlet /> : <Navigate to={`/sign-in?next=${encodeURIComponent(location.pathname + location.search)}`} state={location.state} replace />;
}
const patientNav = [
  ["/patient", "Home", Home],
  ["/patient/discovery", "Find care", Search],
  ["/patient/appointments", "Appointments", CalendarDays],
  ["/patient/account", "Account", Settings2],
  ["/patient/clinic-access", "Clinic access", Building2],
] as const;
const clinicianNav = [
  ["/clinician", "Today", Home],
  ["/clinician/appointments", "Appointments", CalendarDays],
  ["/clinician/requests", "Requests", ClipboardCheck],
  ["/clinician/availability", "Availability", Clock3],
  ["/clinician/services", "Services & pricing", Stethoscope],
  ["/clinician/vetting", "Professional review", ClipboardCheck],
  ["/clinician/affiliations", "Clinics & affiliations", Building2],
  ["/clinician/clinic-access", "Clinic access", Building2],
  ["/clinician/care", "Care records", FileHeart],
  ["/clinician/earnings", "Earnings", Wallet],
  ["/clinician/account", "Account", Settings2],
] as const;
const adminNav = [
  ["/admin", "Applications", ClipboardCheck],
  ["/admin/scopes", "Service scopes", Stethoscope],
  ["/admin/vetting", "Scope vetting", ClipboardCheck],
  ["/admin/clinics", "Clinics", Building2],
  ["/admin/financial-disputes", "Financial disputes", Wallet],
  ["/admin/exceptions", "Exceptions", Settings2],
] as const;
const clinicNav = [["/clinic", "Clinic workspace", Building2]] as const;
export function WorkspaceLayout({
  kind,
}: {
  kind: "patient" | "clinician" | "admin" | "clinic";
}) {
  const { session, refresh } = useSession();
  const { w } = useLocale();
  const location = useLocation();
  const roleItems =
    kind === "patient"
      ? patientNav
      : kind === "clinician"
        ? clinicianNav
        : kind === "clinic" ? clinicNav : adminNav;
  const items = kind !== "clinic" && session?.clinic_workspace
    ? [...roleItems, ["/clinic", "Clinic workspace", Building2] as const]
    : roleItems;
  useEffect(() => {
    const revealActive = () => {
      if (!window.matchMedia("(max-width: 800px)").matches) return;
      const nav = document.querySelector<HTMLElement>(".workspace-nav");
      const active = nav?.querySelector<HTMLElement>("a.active");
      if (!nav || !active) return;
      const navRect = nav.getBoundingClientRect();
      const itemRect = active.getBoundingClientRect();
      const left = nav.scrollLeft + itemRect.left - navRect.left - (nav.clientWidth - itemRect.width) / 2;
      nav.scrollTo({
        left,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      });
    };
    revealActive();
    window.addEventListener("resize", revealActive);
    return () => window.removeEventListener("resize", revealActive);
  }, [location.pathname]);
  if (kind === "admin" && !session?.roles.includes("Tele Tena Approver"))
    return (
      <main className="container">
        <InlineNotice tone="danger">
          You don’t have access to this workspace.
        </InlineNotice>
      </main>
    );
  if (kind === "clinic" && !session?.clinic_workspace)
    return (
      <main className="container">
        <InlineNotice tone="danger">
          {w("You don’t have access to a clinic workspace.")}
        </InlineNotice>
      </main>
    );
  if (kind !== "admin" && kind !== "clinic" && session?.profile?.kind !== kind)
    return <Navigate to="/onboarding" replace />;
  return (
    <div className="workspace">
      <aside className="sidebar">
        <Brand />
        <div className="workspace-label">
          {kind === "admin"
            ? "Review workspace"
            : kind === "clinic"
              ? w("Clinic workspace")
            : kind === "clinician"
              ? "Clinician workspace"
              : "Your space for care"}
        </div>
        <nav className={`workspace-nav workspace-nav-${kind}`} aria-label="Workspace">
          {items.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end data-tour={to==="/patient"?"patient-home":to==="/patient/discovery"?"patient-discovery":to==="/patient/appointments"?"patient-appointments":to==="/patient/account"?"patient-account":to==="/clinician"?"clinician-today":to==="/clinician/availability"?"clinician-availability":to==="/clinician/appointments"?"clinician-appointments":to==="/clinician/care"?"clinician-care":to==="/admin"?"reviewer-applications":to==="/admin/scopes"?"reviewer-scopes":undefined}>
              <Icon size={20} />
              <span>{w(label)}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <TranslationNote />
          <Button
            variant="quiet"
            onClick={() =>
              void journeyApi
                .logout()
                .then(refresh)
                .catch(() => undefined)
            }
          >
            <LogOut size={20} />
            {w("Sign out")}
          </Button>
        </div>
      </aside>
      <div className="workspace-body">
        <DemoBar />
        <header className="workspace-header">
          <span>
            {kind === "admin"
              ? "Administration"
              : kind === "clinic"
                ? w("Clinic workspace")
                : session?.profile?.display_name}
          </span>
          <LanguageSelect />
        </header>
        {kind === "clinician" && session?.roles.includes("Tele Tena Clinician") && <ClinicianRequestAvailability />}
        {kind !== "clinic" && <WorkspaceTour role={kind} />}
        <main className="workspace-main" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
