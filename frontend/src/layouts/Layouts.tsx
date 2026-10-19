import {RequestPresenceProvider} from '../components/RequestPresence';
import {BookingNotices} from '../components/BookingNotices';
import {AccountMenu} from "../components/AccountMenu";
import "./ProductShell.css";
import { ClinicianNotifications } from "../components/ClinicianNotifications";
import { Link, Navigate, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useRef, useState } from "react";
import {
  CalendarDays,
  ClipboardCheck,
  Home,
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
import { useSession, destination } from "../hooks/useSession";
import { journeyApi } from "../journey-api";

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
  const [busy,setBusy]=useState(false),[error,setError]=useState(false);
  const signout=async()=>{setBusy(true);setError(false);try{await journeyApi.logout();await refresh();}catch{setError(true);}finally{setBusy(false);}};
  if(!session?.roles.includes('Tele Tena Medical Lead'))return <main className="container"><InlineNotice tone="danger">{w('You do not have access to clinical rubric governance.')}</InlineNotice></main>;
  return <div className="workspace workspace-medical-lead"><aside className="sidebar"><Brand/><div className="workspace-label">{w('Clinical standards')}</div><nav className="workspace-nav" aria-label={w('Clinical standards')}>
    <NavLink to="/admin/rubrics"><ClipboardCheck size={20}/><span>{w('Rubric versions')}</span></NavLink>
    {session.roles.includes('Tele Tena Approver')&&<NavLink to="/admin/vetting"><Stethoscope size={20}/><span>{w('Service-scope vetting')}</span></NavLink>}
  </nav><div className="sidebar-bottom"><TranslationNote/></div></aside>
    <div className="workspace-body"><DemoBar/><header className="workspace-header"><span>{w('Clinical standards')}</span><LanguageSelect/><AccountMenu accountPath={session.roles.includes('Tele Tena Approver')?'/admin/account':'/admin/rubrics/account'} onSignout={()=>void signout()} busy={busy}/></header>{error&&<InlineNotice tone="danger">{w('We could not sign you out. Try again.')}</InlineNotice>}<nav className="workspace-mobile-nav" aria-label={w('Clinical standards')}><NavLink to="/admin/rubrics"><ClipboardCheck size={20}/><span>{w('Rubric versions')}</span></NavLink>{session.roles.includes('Tele Tena Approver')&&<NavLink to="/admin/vetting"><Stethoscope size={20}/><span>{w('Service-scope vetting')}</span></NavLink>}</nav><main className="workspace-main" id="main-content"><Outlet/></main></div></div>;
}

export function PublicLayout() {
  const { w } = useLocale();
  const {session,refresh}=useSession(),navigate=useNavigate();
  const [signingOut,setSigningOut]=useState(false),[signoutError,setSignoutError]=useState(false);
  const home=destination(session);
  const isReviewer=!!session?.roles.some(role=>['Tele Tena Approver','Tele Tena Medical Lead'].includes(role));
  const links=!session?[]:isReviewer?[[home,'Home'],...(session.roles.includes('Tele Tena Approver')?[['/admin/applications','Applications'],['/admin/vetting','Service scopes'],['/admin/services','Services']]:[])]:session.profile?.kind==='patient'?[[home,'Home'],['/care','Find care'],['/patient/appointments','Appointments'],['/patient/requests','My requests']]:session.profile?.kind==='clinician'?[[home,'Home'],...(session.roles.includes('Tele Tena Clinician')?[['/clinician/appointments','Appointments'],['/clinician/requests','Requests']]:[['/clinician/vetting','Professional review']])]:[[home,'Continue']];
  const accountPath=isReviewer?(session?.roles.includes('Tele Tena Approver')?'/admin/account':'/admin/rubrics/account'):session?.profile?'/'+session.profile.kind+'/account':home;
  const signout=async()=>{setSigningOut(true);setSignoutError(false);try{await journeyApi.logout();await refresh();navigate('/sign-in');}catch{setSignoutError(true);}finally{setSigningOut(false);}};
  const location=useLocation();
  const informationPage=["/how-it-works","/for-clinicians"].includes(location.pathname);
  return (
    <>
      <DemoBar />
      <header className={`public-header reference-public-header ${informationPage?"reference-information-header":""}`}>
        <Brand />
        <nav aria-label={w(session?"Workspace":"Main navigation")}>
          {session?links.map(([to,label])=><Link key={to} className={to===home?"button secondary":""} to={to}>{w(label)}</Link>):<>
            {!informationPage&&<Link to="/care">{w("Find care")}</Link>}
            <Link to="/how-it-works">{w("How it works")}</Link>
            <Link to="/for-clinicians">{w("For clinicians")}</Link>
          </>}
          <LanguageSelect />
          {session?<AccountMenu accountPath={accountPath} onSignout={()=>void signout()} busy={signingOut}/>:<Link className="button secondary" to="/sign-in">{w("Sign in")}</Link>}
        </nav>
      </header>
      {signoutError&&<InlineNotice tone="danger">{w("We could not sign you out. Try again.")}</InlineNotice>}
      <Outlet />
      <footer className="public-footer reference-public-footer">
        <Brand />
        <p>{w("Personal care, connected. Adults 18+ · Not an emergency service.")}</p>
        <Link to="/care">{w("Find care")}</Link>
        <TranslationNote />
      </footer>
    </>
  );
}
export function AuthLayout() {
  return (
    <div className="auth-layout">
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
    </div>
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
  ["/patient/couples", "Shared care", HeartHandshake],
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
// Applicants can continue profile/review work, without approved-only workspace links.
const applicantNav = [
  ["/clinician", "Your application", Home],
  ["/clinician/vetting", "Professional review", ClipboardCheck],
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
  ["/admin/matching", "Matching operations", Settings2],
  ["/admin/exceptions", "Exceptions", Settings2],
  ["/admin/account", "Account", Settings2],
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
        ? session?.roles.includes("Tele Tena Clinician") ? clinicianNav : applicantNav
        : kind === "clinic"
          ? session?.clinic_schedule_workspace ? clinicNav : clinicHomeNav
          : adminNav;
  const items = kind !== "clinic" && session?.clinic_workspace
    ? [...roleItems, ["/clinic", "Clinic workspace", Building2] as const]
    : roleItems;
  const mobilePrimaryRoutes = kind === "clinician"
    ? session?.roles.includes("Tele Tena Clinician")
      ? ["/clinician", "/clinician/requests", "/clinician/availability"]
      : ["/clinician", "/clinician/vetting", "/clinician/account"]
    : kind === "patient"
      ? ["/patient", "/patient/discovery", "/patient/appointments"]
      : kind === "admin"
        ? ["/admin", "/admin/applications"]
        : ["/clinic"];
  const mobilePrimary = items.filter(([to]) => mobilePrimaryRoutes.includes(to));
  const mobileMore = items.filter(([to]) => !mobilePrimaryRoutes.includes(to) && !to.endsWith("/account"));
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
    return <NavLink key={to} to={to} end={to === "/"+kind} data-tour={tourTargets[to]} onClick={closeMore ? () => setMoreOpen(false) : undefined}>
      <Icon size={20} /><span>{w(label)}</span>
    </NavLink>;
  };
  const groups = [
    {name:kind === "admin"?"Applications & approval":"Care & appointments", items:mobileMore.filter(([to])=> /appointments|care$|requests$|offers$|couples$|applications|scopes$|vetting$/.test(to))},
    {name:kind === "admin"?"Services & operations":"Practice & affiliations", items:mobileMore.filter(([to])=> /availability$|services$|affiliations$|clinics$|clinic-access$|matching$|exceptions$|clinic$|calendar$/.test(to))},
    {name:"Payments",items:mobileMore.filter(([to])=> /payments$|earnings$|financial-disputes$/.test(to))},
  ];
  const groupedMore = <nav className="workspace-more-links" aria-label={w("Additional workspace links")}>{groups.filter(group=>group.items.length).map(group=><section key={group.name} className="workspace-more-group"><h3>{w(group.name)}</h3>{group.items.map(item=>renderNavLink(item,true))}</section>)}</nav>;
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
    <header className="product-header"><Brand /><nav className="product-desktop-nav" aria-label={w("Workspace")}>{mobilePrimary.map(item => renderNavLink(item))}{mobileMore.length > 0 && <Button variant="quiet" onClick={event => { moreTrigger.current = event.currentTarget; setMoreOpen(true); }}><MoreHorizontal size={20} />{w("More")}</Button>}</nav><div className="product-user">{kind==='patient'&&<BookingNotices/>}{kind==="clinician"&&session?.roles.includes("Tele Tena Clinician")&&<ClinicianNotifications/>}<LanguageSelect /><AccountMenu accountPath={'/'+kind+'/account'} onSignout={()=>void signout()} busy={signoutBusy}/></div></header>
    {signoutError&&<InlineNotice tone="danger">{signoutError}</InlineNotice>}
    <RequestPresenceProvider enabled={kind === "clinician" && !!session?.roles.includes("Tele Tena Clinician")}><main className={`reference-workspace-main ${location.pathname.includes('/discovery') || location.pathname.includes('/availability') ? 'workspace-wide' : ''}`} id="main-content"><Outlet /></main></RequestPresenceProvider>
    <nav className="product-mobile-nav" aria-label={w("Mobile workspace")}>{mobilePrimary.map(item => renderNavLink(item))}{mobileMore.length > 0 && <Button variant="quiet" onClick={event => { moreTrigger.current = event.currentTarget; setMoreOpen(true); }}><MoreHorizontal size={20} /><span>{w("More")}</span></Button>}</nav>
    <Dialog open={moreOpen} onOpenChange={open => { setMoreOpen(open); if (!open) requestAnimationFrame(() => moreTrigger.current?.focus()); }} title={w("More workspace links")} description={w("Choose another area of your workspace.")} drawer>{groupedMore}<TranslationNote /></Dialog>
  </div>;
  return (
    <div className={`workspace workspace-${kind}`}>
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
          <AccountMenu accountPath={"/"+kind+"/account"} onSignout={()=>void signout()} busy={signoutBusy}/>
        </header>

        {signoutError&&<InlineNotice tone="danger">{signoutError}</InlineNotice>}

        <main className="workspace-main" id="main-content">
          <Outlet />
        </main>
      </div>
      {mobileMore.length > 0 && <Dialog open={moreOpen} onOpenChange={(open) => {
        setMoreOpen(open);
        if (!open) window.requestAnimationFrame(() => moreTrigger.current?.focus());
      }} title={w("More workspace links")} description={w("Choose another area of your workspace.")} drawer>
        {groupedMore}
      </Dialog>}
    </div>
  );
}
