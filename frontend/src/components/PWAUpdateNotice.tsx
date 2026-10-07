import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { RefreshCw, X } from "lucide-react";
import { useLocale } from "../hooks/useLocale";
import { Button } from "./ui";

export default function PWAUpdateNotice() {
  const { pathname } = useLocation();
  const { w } = useLocale();
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const activateOnChange = useRef(false);

  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    let active = true;
    let registration: ServiceWorkerRegistration | undefined;

    const offerWaitingWorker = (current: ServiceWorkerRegistration) => {
      if (active && current.waiting && navigator.serviceWorker.controller) {
        setWaitingWorker(current.waiting);
        setDismissed(false);
      }
    };
    const onControllerChange = () => {
      if (activateOnChange.current) window.location.reload();
    };

    navigator.serviceWorker.addEventListener("controllerchange", onControllerChange);
    const script = import.meta.env.PROD ? "/teletena/sw.js" : "/sw.js";
    const scope = import.meta.env.PROD ? "/teletena/" : "/";
    void navigator.serviceWorker.register(script, { scope }).then((current) => {
      if (!active) return;
      registration = current;
      offerWaitingWorker(current);
      current.addEventListener("updatefound", () => {
        const installing = current.installing;
        installing?.addEventListener("statechange", () => offerWaitingWorker(current));
      });
      void current.update().catch(() => undefined);
    }).catch(() => undefined);

    const poll = window.setInterval(() => {
      void registration?.update().catch(() => undefined);
    }, 5 * 60 * 1000);
    return () => {
      active = false;
      window.clearInterval(poll);
      navigator.serviceWorker.removeEventListener("controllerchange", onControllerChange);
    };
  }, []);

  const protectedWorkflow = pathname === "/sign-in" || pathname === "/onboarding" ||
    pathname.startsWith("/consultation/") || pathname.includes("/consultations/");
  if (!waitingWorker || dismissed || protectedWorkflow) return null;

  return (
    <aside className="pwa-update-notice" role="status" aria-live="polite">
      <p>{w("A TeleTena update is ready. Refresh when you have finished what you’re doing.")}</p>
      <Button loading={refreshing} onClick={() => {
        activateOnChange.current = true;
        setRefreshing(true);
        waitingWorker.postMessage("SKIP_WAITING");
      }}>
        <RefreshCw size={18} /> {w("Refresh to update")}
      </Button>
      <Button variant="quiet" aria-label={w("Dismiss update notice")} onClick={() => setDismissed(true)}>
        <X size={18} /> <span>{w("Later")}</span>
      </Button>
    </aside>
  );
}
