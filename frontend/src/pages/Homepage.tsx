import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, CalendarDays, LockKeyhole, MessageCircle, Search, ShieldCheck, UserRound, Users } from "lucide-react";
import { rememberCareQuery } from "../care-intent";
import { useLocale } from "../hooks/useLocale";
import "./Homepage.css";

const tools = {
  Schedule: ["Set hours that work for you.", "Recurring availability and date exceptions help patients book usable times.", "Preview availability", "/clinician/availability"],
  Requests: ["Respond with a private offer.", "Review eligible requests, propose a fee and time, and track the patient’s response.", "Explore requests", "/clinician/requests"],
  Earnings: ["Understand every balance.", "Track pending earnings, available funds and payout requests. Funds release follows completion and dispute rules.", "Explore earnings", "/clinician/earnings"],
} as const;
export default function Homepage() {
  const { w } = useLocale();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [tool, setTool] = useState<keyof typeof tools>("Schedule");
  const preview = tools[tool];
  return <main className="landing-page">
    <section className="landing-hero">
      <header className="landing-intro">
        <p className="eyebrow">{w("MENTAL HEALTH & RELATIONSHIP CARE · ETHIOPIA")}</p>
        <h1>{w("Find support.")}<br />{w("Make time for care.")}</h1>
        <p>{w("Private voice and video consultations with approved mental health and counseling professionals.")}</p>
      </header>
      <div className="landing-entries">
        <section className="landing-patient">
          <span className="landing-role"><UserRound size={18} />{w("For patients")}</span>
          <h2>{w("Talk to someone")}<br />{w("who fits your needs.")}</h2>
          <p>{w("Choose your clinician, see the fee, and decide what you share. Browse directly or ask eligible clinicians for a private offer.")}</p>
          <form className="landing-search" onSubmit={e => { e.preventDefault(); rememberCareQuery(query); navigate('/patient/discovery'); }}>
            <label htmlFor="landing-care-query">{w("What would you like support with?")}</label>
            <div><Search size={20} /><input id="landing-care-query" value={query} onChange={e => setQuery(e.target.value)} placeholder={w("Stress, relationships, feeling low…")} required /></div>
            <button className="button full" type="submit">{w("Find my care")}<ArrowRight size={18} /></button>
          </form>
          <div className="landing-chips" aria-label={w("Ideas to get started")}>{['Work stress', 'Relationships', 'Anxiety'].map(text => <button type="button" key={text} onClick={() => setQuery(w(text))}>{w(text)}</button>)}</div>
          <Link className="text-link" to="/patient/requests">{w("Prefer clinicians to respond? Post a private request")}<ArrowRight size={16} /></Link>
          <Link className="text-link landing-signup" to="/sign-in?intent=patient&mode=register">{w("Create an account")}</Link>
          <p className="landing-note"><LockKeyhole size={16} />{w("Free to browse · Pay the agreed session fee · Adults 18+")}</p>
        </section>
        <section className="landing-clinician">
          <span className="landing-role"><Users size={18} />{w("For clinicians")}</span>
          <h2>{w("Your practice.")}<br />{w("One connected workspace.")}</h2>
          <p>{w("Bring your patients, publish approved services, manage bookings, and respond to people looking for your expertise.")}</p>
          <div className="landing-practice">
            <div className="landing-preview-heading"><strong>{w("Practice preview")}</strong><span>{w("Clinician")}</span></div>
            <div className="landing-chips" aria-label={w("Explore clinician tools")}>{(Object.keys(tools) as (keyof typeof tools)[]).map(value => <button key={value} type="button" aria-pressed={tool === value} onClick={() => setTool(value)}>{w(value)}</button>)}</div>
            <div role="region" aria-live="polite" aria-label={w("Practice preview")}><h3>{w(preview[0])}</h3><p>{w(preview[1])}</p><Link className="button secondary" to={preview[3]}>{w(preview[2])}<ArrowRight size={16} /></Link></div>
          </div>
          <Link className="button" to="/sign-in?intent=clinician&mode=register">{w("Apply as a clinician")}<ArrowRight size={18} /></Link>
          <Link className="text-link" to="/clinician">{w("Already approved? Explore your workspace")}<ArrowRight size={16} /></Link>
          <p className="landing-note"><ShieldCheck size={16} />{w("Credentials and each service scope are reviewed before publication.")}</p>
        </section>
      </div>
    </section>
    <section className="landing-principles" id="how-it-works" aria-label={w("How it works")}>
      {[[CalendarDays, "Clear choices", "See the session fee, length and available times before you book."], [ShieldCheck, "Your disclosure, your choice", "Preview exactly what you share with your clinician."], [MessageCircle, "A real conversation", "Join a private voice or video consultation at your agreed time."]].map(([Icon, title, copy]) => {
        const Mark = Icon as typeof CalendarDays;
        return <div key={String(title)}><Mark size={27} /><section><h3>{w(String(title))}</h3><p>{w(String(copy))}</p></section></div>;
      })}
    </section>
  </main>;
}
export function ClinicianInvitation() {
  return (
    <main className="container editorial">
      <p className="eyebrow">FOR CLINICIANS</p>
      <h1>Care starts with a thoughtful connection.</h1>
      <p className="hero-intro">
        Bring your professional experience to TeleTena. Set your availability,
        publish approved services and meet patients with clear sharing choices.
      </p>
      <ol className="plain-steps">
        <li>Verify your contact.</li>
        <li>
          Share your professional identity, credentials and requested service
          scope.
        </li>
        <li>
          Submit for manual review. Approval is required before offering care.
        </li>
      </ol>
      <Link className="button primary" to="/sign-in?intent=clinician">
        Start your application <ArrowRight size={20} />
      </Link>
    </main>
  );
}
