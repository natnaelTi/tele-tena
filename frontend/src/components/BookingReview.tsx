import { Link } from "react-router-dom";
import type { Disclosure, Offer } from "../journey-api";
import { useLocale } from "../hooks/useLocale";
import { DisclosurePreview, date, money } from "./Domain";
import { Button, InlineNotice, Skeleton } from "./ui";
import "./BookingReview.css";

/** A price review, not a reservation. The server revalidates at confirmation. */
export function BookingReview({offer,start,zone,format,disclosure,balance,balanceError,onRetry,onConfirm,busy}: {
  offer:Offer; start:string; zone:string; format:string; disclosure:Disclosure;
  balance?:{available:number;reserved:number}|null; balanceError:boolean;
  onRetry:()=>void; onConfirm:()=>void; busy:boolean;
}) {
  const {w}=useLocale();
  const shortfall=balance ? Math.max(0,offer.price-balance.available) : 0;
  return <div className="booking-review-panels">
    <section className="booking-review-panel"><h2>{w("Your consultation")}</h2>
      <div className="booking-review-clinician"><span className="avatar" aria-hidden="true">{offer.display_name.slice(0,1)}</span><div><h3>{offer.display_name}</h3><p>{offer.label}</p></div></div>
      <dl className="summary-list"><dt>{w("When")}</dt><dd>{date(start,zone)}</dd><dt>{w("Timezone")}</dt><dd>{zone}</dd><dt>{w("Duration")}</dt><dd>{offer.minutes} {w("minutes")}</dd><dt>{w("Format")}</dt><dd>{w(format==='audio'?'Audio':'Video')}</dd><dt>{w("Cancellation")}</dt><dd>{w("Cancel before the session starts to release the full reservation.")}</dd></dl>
      <details className="booking-review-disclosure"><summary>{w("What you’ll share")}</summary><DisclosurePreview disclosure={disclosure}/></details>
    </section>
    <section className="booking-review-panel"><h2>{w("Payment summary")}</h2>
      {balanceError ? <InlineNotice tone="danger">{w("Your balance could not be loaded.")} <Button variant="secondary" onClick={onRetry}>{w("Retry")}</Button></InlineNotice> : !balance ? <Skeleton/> : <>
        <dl className="summary-list"><dt>{w("Session price")}</dt><dd>ETB {money(offer.price)}</dd><dt>{w("Available balance")}</dt><dd>ETB {money(balance.available)}</dd><dt>{w("Amount to reserve")}</dt><dd>ETB {money(offer.price)}</dd><dt>{w(shortfall?'Amount to add':'Available after reservation')}</dt><dd>ETB {money(shortfall||balance.available-offer.price)}</dd></dl>
        {shortfall>0 ? <InlineNotice>{w("Add funds before confirming. This time is not held yet.")} <Link to="/patient/payments" target="_blank" rel="noopener">{w("Add funds in a new tab")}</Link><Button variant="secondary" onClick={onRetry}>{w("Check balance again")}</Button></InlineNotice> : <InlineNotice>{w("Funds are reserved when you confirm. Ending the call alone does not release earnings.")}</InlineNotice>}
      </>}
      <Button disabled={busy||!balance||balanceError||shortfall>0} loading={busy} onClick={onConfirm}>{w("Confirm session")} · ETB {money(offer.price)}</Button>
    </section>
  </div>;
}
