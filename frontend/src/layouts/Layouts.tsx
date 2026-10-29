import {PublicMotion} from '../components/PublicMotion';
import {RequestPresenceProvider} from '../components/RequestPresence';
import {UserNotifications} from '../components/UserNotifications';
import {AccountMenu} from "../components/AccountMenu";
import "./ProductShell.css";
import { ClinicianNotifications } from "../components/ClinicianNotifications";
import { Link, Navigate, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
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
  Menu,
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
  return <div className="reference-workspace workspace-role-medical-lead"><DemoBar/>
    <header className="product-header site-masthead"><Brand bilingual/><nav className="product-desktop-nav" aria-label={w('Clinical standards')}><NavLink to="/admin/rubrics"><ClipboardCheck size={20}/><span>{w('Rubric versions')}</span></NavLink>{session.roles.includes('Tele Tena Approver')&&<NavLink to="/admin/vetting"><Stethoscope size={20}/><span>{w('Service-scope vetting')}</span></NavLink>}</nav><div className="product-user"><LanguageSelect/><AccountMenu accountPath={session.roles.includes('Tele Tena Approver')?'/admin/account':'/admin/rubrics/account'} onSignout={()=>void signout()} busy={busy}/></div></header>
    {error&&<InlineNotice tone="danger">{w('We could not sign you out. Try again.')}</InlineNotice>}
    <nav className="product-mobile-nav" aria-label={w('Clinical standards')}><NavLink to="/admin/rubrics"><ClipboardCheck size={20}/><span>{w('Rubric versions')}</span></NavLink>{session.roles.includes('Tele Tena Approver')&&<NavLink to="/admin/vetting"><Stethoscope size={20}/><span>{w('Service-scope vetting')}</span></NavLink>}</nav>
    <main className="reference-workspace-main" id="main-content"><Outlet/></main>
  </div>;
}

export function PublicLayout() {
  const { w } = useLocale();
  const {session,refresh,error:sessionError}=useSession(),navigate=useNavigate();
  const [signingOut,setSigningOut]=useState(false),[signoutError,setSignoutError]=useState(false);
  const home=destination(session);
  const isReviewer=!!session?.roles.some(role=>['Tele Tena Approver','Tele Tena Medical Lead'].includes(role));
  const links=!session?[]:isReviewer?[[home,'Home'],...(session.roles.includes('Tele Tena Approver')?[['/admin/applications','Applications'],['/admin/vetting','Service scopes'],['/admin/services','Services']]:[])]:session.profile?.kind==='patient'?[[home,'Home'],['/care','Find care'],['/patient/appointments','Appointments'],['/patient/requests','My requests'],['/patient/couples','Shared care']]:session.profile?.kind==='clinician'?[[home,'Home'],...(session.roles.includes('Tele Tena Clinician')?[['/clinician/appointments','Appointments'],['/clinician/requests','Requests']]:[['/clinician/vetting','Professional review']])]:[[home,'Continue']];
  const accountPath=isReviewer?(session?.roles.includes('Tele Tena Approver')?'/admin/account':'/admin/rubrics/account'):session?.profile?'/'+session.profile.kind+'/account':home;
  const signout=async()=>{setSigningOut(true);setSignoutError(false);try{await journeyApi.logout();await refresh();navigate('/sign-in');}catch{setSignoutError(true);}finally{setSigningOut(false);}};
  const location=useLocation();
  const informationPage=["/how-it-works","/for-clinicians"].includes(location.pathname);
  useEffect(()=>{if(!location.hash)window.scrollTo({top:0,left:0,behavior:"instant"});},[location.pathname]);
  const [menuOpen,setMenuOpen]=useState(false);
  const menuTrigger=useRef<HTMLButtonElement|null>(null);
  useEffect(()=>{if(["#how-it-works","#public-faq","#clinician-application","#product-tour"].includes(location.hash)){const tick=requestAnimationFrame(()=>document.getElementById(location.hash.slice(1))?.scrollIntoView());return()=>cancelAnimationFrame(tick);}},[location.pathname,location.hash]);
  const publicLinks=[["/care","Find care"],["/how-it-works","How it works"],["/contact","Contact"]];
  const heroRoute=location.pathname==='/'||location.pathname==='/for-clinicians';
  const [headerVisible,setHeaderVisible]=useState(!heroRoute);
  useEffect(()=>{const update=()=>{const hero=document.querySelector('.public-audience-hero');setHeaderVisible(!heroRoute||!!sessionError||!!hero&&scrollY>=hero.getBoundingClientRect().height*.75);};update();window.addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);return()=>{window.removeEventListener('scroll',update);window.removeEventListener('resize',update);};},[heroRoute,location.pathname,sessionError]);
  return (
    <div className={`public-experience-shell ${heroRoute&&!sessionError?"has-immersive-hero":""}`}>
      <PublicMotion/>
      <DemoBar />
      <header className={`public-header reference-public-header site-masthead ${informationPage?"reference-information-header":""} ${headerVisible?"is-revealed":"is-concealed"}`} inert={!headerVisible}>
        <Brand bilingual />
        <nav aria-label={w(session?"Workspace":"Main navigation")}>
          {session?links.map(([to,label])=><Link key={to} className={"public-desktop-link "+(to===home?"button secondary":"")} to={to}>{w(label)}</Link>):<>
            {publicLinks.map(([to,label])=><Link className="public-desktop-link" aria-current={location.pathname===to?"page":undefined} key={to} to={to}>{w(label)}</Link>)}
          </>}
          {session?.profile?.kind==='patient'&&<UserNotifications/>}
          <LanguageSelect />
          <button type="button" className="public-menu-button" ref={menuTrigger} aria-label={w("Open navigation")} aria-haspopup="dialog" onClick={()=>setMenuOpen(true)}><Menu size={22}/></button>
          {session?<AccountMenu accountPath={accountPath} onSignout={()=>void signout()} busy={signingOut}/>:<Link className="button secondary" to="/sign-in">{w("Sign in")}</Link>}
        </nav>
      </header>
      {signoutError&&<InlineNotice tone="danger">{w("We could not sign you out. Try again.")}</InlineNotice>}
      <div id="main-content" tabIndex={-1}><Outlet /></div>
      <footer className="public-footer reference-public-footer">
        <div className="public-footer-brand"><Brand bilingual/><p>{w("Personal care, connected. Adults 18+ · Not an emergency service.")}</p></div>
        <nav aria-label={w("Care")}><h2>{w("Care")}</h2><Link to="/care">{w("Clinicians & services")}</Link><Link to="/request">{w("Request a Consultation")}</Link></nav>
        <nav aria-label={w("For clinicians")}><h2>{w("For Clinicians")}</h2><Link to="/for-clinicians">{w("Explore the practice tools")}</Link><Link to="/sign-in?intent=clinician&mode=register">{w("Apply as a clinician")}</Link></nav>
        <nav aria-label={w("Information")}><h2>{w("Information")}</h2><Link to="/contact">{w("Contact")}</Link><Link to="/how-it-works#public-faq">{w("Help & FAQ")}</Link><Link to="/policies">{w("Terms & Privacy")}</Link><TranslationNote/></nav>
      </footer>
      <Dialog open={menuOpen} onOpenChange={setMenuOpen} title={w("Navigation")} description={w("Choose where to go next.")} focusReturnTarget={menuTrigger.current} className="public-mobile-menu"><nav aria-label={w("Main navigation")}>{(session?links:publicLinks).map(([to,label])=><Link key={to} to={to} onClick={()=>setMenuOpen(false)}>{w(label)}</Link>)}</nav><LanguageSelect/></Dialog>
    </div>
  );
}
export function AuthLayout() {
  return (
    <div className="auth-layout">
      <DemoBar />
      <header className="auth-header site-masthead">
        <Brand bilingual />
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
  return session ? <Outlet key={session.user}/> : <Navigate to={`/sign-in?next=${encodeURIComponent(location.pathname)}`} state={location.state} replace />;
}
const patientNav = [
  ["/patient", "Home", Home],
  ["/patient/discovery", "Find care", Search],
  ["/patient/appointments", "Appointments", CalendarDays],
  ["/patient/requests", "My requests", ClipboardCheck],
  ["/patient/account", "Account", Settings2],
  ["/patient/payments", "Balance", Wallet],
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
      ? ["/patient", "/patient/discovery", "/patient/appointments", "/patient/requests", "/patient/couples"]
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
      <Icon size={20} /><span>{w(session?.payment_mode==='Offline'?(to==='/patient/payments'?'Expenses Ledger':to==='/clinician/earnings'?'Revenue Ledger':label):label)}</span>
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
  return <div className={"reference-workspace workspace-role-"+kind}>
    <DemoBar />
    <header className="product-header site-masthead"><Brand bilingual /><nav className="product-desktop-nav" aria-label={w("Workspace")}>{mobilePrimary.map(item => renderNavLink(item))}{mobileMore.length > 0 && <Button variant="quiet" onClick={event => { moreTrigger.current = event.currentTarget; setMoreOpen(true); }}><MoreHorizontal size={20} />{w("More")}</Button>}</nav><div className="product-user">{kind==='patient'&&<UserNotifications/>}{kind==="clinician"&&session?.roles.includes("Tele Tena Clinician")&&<ClinicianNotifications/>}<LanguageSelect /><AccountMenu accountPath={'/'+kind+'/account'} onSignout={()=>void signout()} busy={signoutBusy}/></div></header>
    {signoutError&&<InlineNotice tone="danger">{signoutError}</InlineNotice>}
    <RequestPresenceProvider enabled={kind === "clinician" && !!session?.roles.includes("Tele Tena Clinician")}><main className={`reference-workspace-main ${location.pathname.includes('/discovery') || location.pathname.includes('/availability') || kind==='admin' ? 'workspace-wide' : ''}`} id="main-content"><Outlet /></main></RequestPresenceProvider>
    <nav className="product-mobile-nav" aria-label={w("Mobile workspace")}>{mobilePrimary.map(item => renderNavLink(item))}{mobileMore.length > 0 && <Button variant="quiet" onClick={event => { moreTrigger.current = event.currentTarget; setMoreOpen(true); }}><MoreHorizontal size={20} /><span>{w("More")}</span></Button>}</nav>
    <Dialog open={moreOpen} onOpenChange={open => { setMoreOpen(open); if (!open) requestAnimationFrame(() => moreTrigger.current?.focus()); }} title={w("More Workspace Links")} description={w("Choose another area of your workspace.")} drawer>{groupedMore}<TranslationNote /></Dialog>
  </div>;
}
