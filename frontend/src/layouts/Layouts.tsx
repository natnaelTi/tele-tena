import "./ProductShell.css";
import { Link, Navigate, NavLink, Outlet, useLocation } from "react-router-dom";
import { useCallback, useEffect, useRef, useState } from "react";
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
  MoreHorizontal,
  HeartHandshake,
} from "lucide-react";
import { Brand } from "../components/Brand";
import { Button, Dialog, InlineNotice, Skeleton } from "../components/ui";
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

export function MedicalLeadLayout(){
  const {session,refresh}=useSession();const {w}=useLocale();
  if(!session?.roles.includes('Tele Tena Medical Lead'))return <main className="container"><InlineNotice tone="danger">{w('You do not have access to clinical rubric governance.')}</InlineNotice></main>;
  return <div className="workspace"><aside className="sidebar"><Brand/><div className="workspace-label">{w('Clinical standards')}</div><nav className="workspace-nav" aria-label={w('Clinical standards')}>
    <NavLink to="/admin/rubrics"><ClipboardCheck size={20}/><span>{w('Rubric versions')}</span></NavLink>
    {session.roles.includes('Tele Tena Approver')&&<NavLink to="/admin/vetting"><Stethoscope size={20}/><span>{w('Service-scope vetting')}</span></NavLink>}
  </nav><div className="sidebar-bottom"><TranslationNote/><Button variant="quiet" onClick={()=>void journeyApi.logout().then(refresh).catch(()=>undefined)}><LogOut size={20}/>{w('Sign out')}</Button></div></aside>
    <div className="workspace-body"><DemoBar/><header className="workspace-header"><span>{w('Clinical standards')}</span><LanguageSelect/></header><main className="workspace-main" id="main-content"><Outlet/></main></div></div>;
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
    no_immediate_capacity:{label:"Review availability",to:"/clinician/availability"},
  };
  const pausedMessage = data?.reasons?.includes("no_immediate_capacity")
    ? `${w("No full session can start within")} ${data.immediate_window_minutes || 30} ${w("minutes. Your published hours can still be used for scheduled requests.")}`
    : "Complete setup before receiving requests.";
  return <section className="request-presence-shell" aria-label={w("Request availability")}>
    <div><strong>{w(data?.ready ? "Available for requests" : "Requests paused")}</strong>
      <span>{w(failureMessage || (data?.ready ? "Ready status expires if this session disconnects." : pausedMessage))}</span>
      {data?.reasons?.includes("immediate_policy_required") && <span>{w("A reviewer must enable immediate requests for this service. Service-scope approval alone does not enable this. This does not guarantee a request or match.")}</span>}
      {!!data?.reasons?.length && <nav className="request-readiness-actions" aria-label={w("Setup needed")}>{data.reasons.filter((reason: string)=>reason!=="immediate_policy_required").map((reason: string) => {const item=guidance[reason];return item?<Link key={reason} to={item.to}>{w(item.label)}</Link>:<span key={reason}>{w("Complete setup before receiving requests.")}</span>;})}</nav>}
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
      <header className="public-header reference-public-header">
        <Brand />
        <nav aria-label="Main navigation">
          <Link to="/patient/discovery">{w("Find care")}</Link>
          <a href={(import.meta.env.PROD ? "/teletena/" : "/") + "#how-it-works"}>{w("How it works")}</a>
          <Link to="/for-clinicians">{w("For clinicians")}</Link>
          <LanguageSelect />
          <Link className="button secondary" to="/sign-in">
            {w("Sign in")}
          </Link>
        </nav>
      </header>
      <Outlet />
      <footer className="public-footer reference-public-footer">
        <Brand />
        <p>{w("Personal care, connected. Adults 18+ · Not an emergency service.")}</p>
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
  return session ? <Outlet /> : <Navigate to={`/sign-in?next=${encodeURIComponent(location.pathname)}`} state={location.state} replace />;
}
const patientNav = [
  ["/patient", "Home", Home],
  ["/patient/discovery", "Find care", Search],
  ["/patient/appointments", "Appointments", CalendarDays],
  ["/patient/requests", "My requests", ClipboardCheck],
  ["/patient/account", "Account", Settings2],
  ["/patient/clinic-access", "Clinic access", Building2],
  ["/patient/relationships", "Shared care", HeartHandshake],
] as const;
const clinicianNav = [
  ["/clinician", "Today", Home],
  ["/clinician/appointments", "Appointments", CalendarDays],
  ["/clinician/requests", "Requests", ClipboardCheck],
  ["/clinician/offers", "Your offers", ClipboardCheck],
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
  ["/admin", "Overview", Home],
  ["/admin/applications", "Applications", ClipboardCheck],
  ["/admin/scopes", "Service scopes", Stethoscope],
  ["/admin/services", "Service catalog", Stethoscope],
  ["/admin/vetting", "Scope vetting", ClipboardCheck],
  ["/admin/clinics", "Clinics", Building2],
  ["/admin/financial-disputes", "Financial disputes", Wallet],
  ["/admin/exceptions", "Exceptions", Settings2],
] as const;
const clinicHomeNav = [["/clinic", "Clinic workspace", Building2]] as const;
const clinicNav = [
  ["/clinic", "Clinic workspace", Building2],
  ["/clinic/calendar", "Clinic calendar", CalendarDays],
] as const;
export function WorkspaceLayout({
  kind,
}: {
  kind: "patient" | "clinician" | "admin" | "clinic";
}) {
  const location = useLocation();
  const { session, refresh } = useSession();
  const { w } = useLocale();
  const [moreOpen, setMoreOpen] = useState(false);
  const [signoutBusy,setSignoutBusy]=useState(false);
  const [signoutError,setSignoutError]=useState("");
  const signout=async()=>{if(signoutBusy)return;setSignoutBusy(true);setSignoutError("");try{await journeyApi.logout();await refresh();}catch{setSignoutError(w("We could not sign you out. Try again."));}finally{setSignoutBusy(false);}};
  const moreTrigger = useRef<HTMLButtonElement | null>(null);
  const roleItems =
    kind === "patient"
      ? patientNav
      : kind === "clinician"
        ? clinicianNav
        : kind === "clinic"
          ? session?.clinic_schedule_workspace ? clinicNav : clinicHomeNav
          : adminNav;
  const items = kind !== "clinic" && session?.clinic_workspace
    ? [...roleItems, ["/clinic", "Clinic workspace", Building2] as const]
    : roleItems;
  const mobilePrimaryRoutes = kind === "clinician"
    ? ["/clinician", "/clinician/requests", "/clinician/availability"]
    : kind === "patient"
      ? ["/patient", "/patient/discovery", "/patient/appointments"]
      : kind === "admin"
        ? ["/admin", "/admin/applications", "/admin/scopes"]
        : ["/clinic"];
  const mobilePrimary = items.filter(([to]) => mobilePrimaryRoutes.includes(to));
  const mobileMore = items.filter(([to]) => !mobilePrimaryRoutes.includes(to));
  const tourTargets: Record<string, string> = {
    "/patient": "patient-home", "/patient/discovery": "patient-discovery",
    "/patient/appointments": "patient-appointments", "/patient/account": "patient-account",
    "/clinician": "clinician-today", "/clinician/availability": "clinician-availability",
    "/clinician/appointments": "clinician-appointments", "/clinician/care": "clinician-care",
    "/clinician/account": "clinician-account", "/clinician/vetting": "clinician-professional-review",
    "/admin": "reviewer-overview", "/admin/applications": "reviewer-applications", "/admin/scopes": "reviewer-scopes",
  };
  const renderNavLink = (item: (typeof items)[number], closeMore = false) => {
    const [to, label, Icon] = item;
    return <NavLink key={to} to={to} end data-tour={tourTargets[to]} onClick={closeMore ? () => setMoreOpen(false) : undefined}>
      <Icon size={20} /><span>{w(label)}</span>
    </NavLink>;
  };
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
  if (kind === "patient" || kind === "clinician") return <div className="reference-workspace">
    <DemoBar />
    <header className="product-header"><Brand /><nav className="product-desktop-nav" aria-label={w("Workspace")}>{mobilePrimary.map(item => renderNavLink(item))}<Button variant="quiet" onClick={event => { moreTrigger.current = event.currentTarget; setMoreOpen(true); }}><MoreHorizontal size={20} />{w("More")}</Button></nav><div className="product-user"><LanguageSelect /><span>{session?.profile?.display_name}</span><Button variant="quiet" aria-label={w("Sign out")} title={w("Sign out")} loading={signoutBusy} onClick={()=>void signout()}><LogOut size={20} /></Button></div></header>
    {signoutError&&<InlineNotice tone="danger">{signoutError}</InlineNotice>}
    {kind === "clinician" && session?.roles.includes("Tele Tena Clinician") && <ClinicianRequestAvailability />}
    <main className={`reference-workspace-main ${location.pathname.includes('/discovery') || location.pathname.includes('/availability') ? 'workspace-wide' : ''}`} id="main-content"><WorkspaceTour role={kind} /><Outlet /></main>
    <nav className="product-mobile-nav" aria-label={w("Mobile workspace")}>{mobilePrimary.map(item => renderNavLink(item))}<Button variant="quiet" onClick={event => { moreTrigger.current = event.currentTarget; setMoreOpen(true); }}><MoreHorizontal size={20} /><span>{w("More")}</span></Button></nav>
    <Dialog open={moreOpen} onOpenChange={open => { setMoreOpen(open); if (!open) requestAnimationFrame(() => moreTrigger.current?.focus()); }} title={w("More workspace links")} description={w("Choose another area of your workspace.")} drawer><nav className="workspace-more-links" aria-label={w("Additional workspace links")}>{mobileMore.map(item => renderNavLink(item, true))}</nav><TranslationNote /></Dialog>
  </div>;
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
          {items.map((item) => renderNavLink(item))}
        </nav>
        <nav className="workspace-mobile-nav" aria-label={w("Mobile workspace")}>
          {mobilePrimary.map((item) => renderNavLink(item))}
          {mobileMore.length > 0 && <Button variant="quiet" className="mobile-nav-more" onClick={(event) => { moreTrigger.current = event.currentTarget; setMoreOpen(true); }}>
            <MoreHorizontal size={20} /><span>{w("More")}</span>
          </Button>}
        </nav>
        <div className="sidebar-bottom">
          <TranslationNote />
          <Button
            variant="quiet"
            loading={signoutBusy}
            onClick={()=>void signout()}
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

        {signoutError&&<InlineNotice tone="danger">{signoutError}</InlineNotice>}
        {kind !== "clinic" && <WorkspaceTour role={kind} />}
        <main className="workspace-main" id="main-content">
          <Outlet />
        </main>
      </div>
      {mobileMore.length > 0 && <Dialog open={moreOpen} onOpenChange={(open) => {
        setMoreOpen(open);
        if (!open) window.requestAnimationFrame(() => moreTrigger.current?.focus());
      }} title={w("More workspace links")} description={w("Choose another area of your workspace.")} drawer>
        <nav className="workspace-more-links" aria-label={w("Additional workspace links")}>
          {mobileMore.map((item) => renderNavLink(item, true))}
        </nav>
      </Dialog>}
    </div>
  );
}
