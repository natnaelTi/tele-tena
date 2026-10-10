import { Link } from "react-router-dom";
import { useLocale } from "../hooks/useLocale";
import { money } from "./Domain";
/** One financial source; no calculated or fabricated totals. */
export function WalletSummary({ available, reserved, href = "/patient/payments" }: { available: number; reserved: number; href?: string }) {
  const { w } = useLocale();
  return <section className="reference-wallet"><span>{w("Available balance")}</span><strong>ETB {money(available)}</strong><p>{w("Reserved for appointments")} · ETB {money(reserved)}</p><Link className="button secondary" to={href}>{w("View wallet")}</Link></section>;
}
