import {discardGuestDraft} from '../guest-intent';
import {clearCareQuery} from '../care-intent';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  useRef,
} from "react";
import type { ReactNode } from "react";
import { api, setCsrf } from "../api";
import type { Session } from "../journey-api";
type State = {
  session: Session | null;
  loading: boolean;
  error: boolean;
  refresh: () => Promise<Session | null>;
};
const Context = createContext<State | null>(null);
export function SessionProvider({ children }: { children: ReactNode }) {
  const previousActor=useRef<string|null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const refresh = useCallback(async () => {
    setError(false);
    try {
      const result = await api<Session & { authenticated: boolean }>(
        "tele_tena.api.contact_auth.session",
      );
      const current = result.authenticated ? result : null;
      if(previousActor.current&&previousActor.current!==current?.user){discardGuestDraft();clearCareQuery();}
      previousActor.current=current?.user||null;
      setSession(current);
      if (current) setCsrf(current.csrf_token);
      return current;
    } catch {
      setError(true);
      throw new Error("Session unavailable");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [refresh]);
  useEffect(()=>{
    const hide=()=>{if(previousActor.current)document.documentElement.dataset.sessionHidden='true';};
    const show=(event:PageTransitionEvent)=>{if(!event.persisted)return;setLoading(true);void refresh().catch(()=>undefined).finally(()=>requestAnimationFrame(()=>{delete document.documentElement.dataset.sessionHidden;}));};
    const timer=setInterval(()=>{if(previousActor.current&&document.visibilityState==='visible')void refresh().catch(()=>undefined);},30000);
    window.addEventListener('pagehide',hide);window.addEventListener('pageshow',show);
    return()=>{clearInterval(timer);window.removeEventListener('pagehide',hide);window.removeEventListener('pageshow',show);};
  },[refresh]);
  return (
    <Context.Provider value={{ session, loading, error, refresh }}>
      {children}
    </Context.Provider>
  );
}
export function useSession() {
  const value = useContext(Context);
  if (!value) throw new Error("Missing session provider");
  return value;
}
export function destination(session: Session | null) {
  return !session
    ? "/sign-in"
    : session.roles.includes("Tele Tena Medical Lead")
      ? "/admin/rubrics"
    : session.roles.includes("Tele Tena Approver")
      ? "/admin"
      : session.clinic_workspace && !session.profile
        ? "/clinic"
      : session.profile?.kind === "clinician"
        ? "/clinician"
        : session.profile
          ? "/patient"
          : "/onboarding";
}
