import { Link, Navigate, NavLink, Outlet } from "react-router-dom";
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
export function DemoBar() {
  const { w } = useLocale();
  return (
    <div className="demo-bar">
      <span className="demo-dot" />
      {w("Demo environment")}
      <span className="demo-detail">
        Synthetic information · no real payments
      </span>
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
export function PublicLayout() {
  const { w } = useLocale();
  return (
    <>
      <DemoBar />
      <header className="public-header container">
        <Brand />
        <nav aria-label="Main navigation">
          <a href="/#how-it-works">{w("How it works")}</a>
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
  return session ? <Outlet /> : <Navigate to="/sign-in" replace />;
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
  ["/clinician/care", "Care records", FileHeart],
  ["/clinician/earnings", "Earnings", Wallet],
  ["/clinician/account", "Account", Settings2],
] as const;
const adminNav = [
  ["/admin", "Applications", ClipboardCheck],
  ["/admin/scopes", "Service scopes", Stethoscope],
  ["/admin/exceptions", "Exceptions", Settings2],
] as const;
export function WorkspaceLayout({
  kind,
}: {
  kind: "patient" | "clinician" | "admin";
}) {
  const { session, refresh } = useSession();
  const { w } = useLocale();
  const items =
    kind === "patient"
      ? patientNav
      : kind === "clinician"
        ? clinicianNav
        : adminNav;
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
        <nav aria-label="Workspace">
          {items.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end>
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
        <main className="workspace-main" id="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
