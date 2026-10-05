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
} from "lucide-react";
import { Brand } from "../components/Brand";
import { Button, InlineNotice, Skeleton } from "../components/ui";
import { LanguageSelect, useLocale } from "../hooks/useLocale";
import { useSession } from "../hooks/useSession";
import { journeyApi } from "../journey-api";
import WorkspaceTour from "../components/WorkspaceTour";
import { useResource } from "../hooks/useResource";
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
  const [connectionFailed, setConnectionFailed] = useState(false);
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (!ready) { void refresh(); return; }
      void journeyApi.setRequestPresence(true)
        .then(() => { setConnectionFailed(false); void refresh(); })
        .catch(() => setConnectionFailed(true));
    }, 30000);
    return () => window.clearInterval(timer);
  }, [ready, refresh]);
  const toggle = async () => {
    setBusy(true);
    try {
      await journeyApi.setRequestPresence(!presence.data?.ready);
      setConnectionFailed(false);
      await presence.refresh();
    } catch {
      setConnectionFailed(true);
    } finally { setBusy(false); }
  };
  const data = presence.data;
  const guidance:Record<string,string>={approval_required:"Approval required",language_required:"Add a care language",offering_required:"Publish an offering",scope_approval_required:"Get approval for a service scope",published_schedule_required:"Publish availability",immediate_policy_required:"Ask a reviewer to enable immediate requests for a service"};
  return <section className="request-presence-shell" aria-label={w("Request availability")}>
    <div><strong>{w(data?.ready ? "Available for requests" : "Requests paused")}</strong>
      <span>{w(connectionFailed ? "Connection lost; availability will expire." : data?.configured ? "Ready status expires if this session disconnects." : "Complete setup before receiving requests.")}</span>
      {!!data?.reasons?.length && <small>{data.reasons.map((reason: string) => w(guidance[reason]||"Complete setup before receiving requests.")).join(" · ")}</small>}
    </div>
    <Button className="compact-button" variant={data?.ready ? "secondary" : "primary"} loading={busy} disabled={!data?.configured && !data?.ready} onClick={() => void toggle()}>{w(data?.ready ? "Pause" : "Go available")}</Button>
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
  return session ? <Outlet /> : <Navigate to={`/sign-in?next=${encodeURIComponent(location.pathname + location.search)}`} replace />;
}
const patientNav = [
  ["/patient", "Home", Home],
  ["/patient/discovery", "Find care", Search],
  ["/patient/appointments", "Appointments", CalendarDays],
  ["/patient/account", "Account", Settings2],
] as const;
const clinicianNav = [
  ["/clinician", "Today", Home],
  ["/clinician/appointments", "Appointments", CalendarDays],
  ["/clinician/requests", "Requests", ClipboardCheck],
  ["/clinician/availability", "Availability", Clock3],
  ["/clinician/services", "Services & pricing", Stethoscope],
  ["/clinician/vetting", "Professional review", ClipboardCheck],
  ["/clinician/care", "Care records", FileHeart],
  ["/clinician/earnings", "Earnings", Wallet],
  ["/clinician/account", "Account", Settings2],
] as const;
const adminNav = [
  ["/admin", "Applications", ClipboardCheck],
  ["/admin/scopes", "Service scopes", Stethoscope],
  ["/admin/vetting", "Scope vetting", ClipboardCheck],
  ["/admin/financial-disputes", "Financial disputes", Wallet],
  ["/admin/exceptions", "Exceptions", Settings2],
] as const;
export function WorkspaceLayout({
  kind,
}: {
  kind: "patient" | "clinician" | "admin";
}) {
  const { session, refresh } = useSession();
  const { w } = useLocale();
  const location = useLocation();
  const items =
    kind === "patient"
      ? patientNav
      : kind === "clinician"
        ? clinicianNav
        : adminNav;
  useEffect(()=>{const revealActive=()=>{if(window.matchMedia("(max-width: 800px)").matches){document.querySelector<HTMLElement>(".workspace-nav a.active")?.scrollIntoView({block:"nearest",inline:"center"});}};revealActive();window.addEventListener("resize",revealActive);return()=>window.removeEventListener("resize",revealActive);},[location.pathname]);
  if (kind === "admin" && !session?.roles.includes("Tele Tena Approver"))
    return (
      <main className="container">
        <InlineNotice tone="danger">
          You don’t have access to this workspace.
        </InlineNotice>
      </main>
    );
  if (kind !== "admin" && session?.profile?.kind !== kind)
    return <Navigate to="/onboarding" replace />;
  return (
    <div className="workspace">
      <aside className="sidebar">
        <Brand />
        <div className="workspace-label">
          {kind === "admin"
            ? "Review workspace"
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
              : session?.profile?.display_name}
          </span>
          <LanguageSelect />
        </header>
        {kind === "clinician" && session?.roles.includes("Tele Tena Clinician") && <ClinicianRequestAvailability />}
        <WorkspaceTour role={kind} />
        <main className="workspace-main" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
