import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  HeartHandshake,
  MessageCircle,
  ShieldCheck,
  Sprout,
} from "lucide-react";

import { rememberCareQuery } from "../care-intent";
import { useLocale } from "../hooks/useLocale";
export default function Homepage() {
  const { w } = useLocale();
  const navigate=useNavigate();
  const [query,setQuery]=useState("");
  const [tool,setTool]=useState("Schedule");
  return (
    <main>
      <section className="dual-care-hero container">
        <header><p className="eyebrow">MENTAL HEALTH & RELATIONSHIP CARE · ETHIOPIA</p><h1>Find support.<br/>Make time for care.</h1><p className="hero-intro">Private voice and video consultations with approved mental health and counseling professionals.</p></header>
        <div className="care-entry-columns">
          <section className="patient-care-entry"><p className="eyebrow">FOR PATIENTS</p><h2>Talk to someone who fits your needs.</h2><p>Choose your clinician, see the fee, and decide what you share. Browse directly or ask eligible clinicians for a private offer.</p>
            <form onSubmit={e=>{e.preventDefault();rememberCareQuery(query);navigate('/patient/discovery');}}><label htmlFor="landing-care-query">What would you like support with?</label><input id="landing-care-query" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Stress, relationships, feeling low…" required/><button className="button primary" type="submit">{w('Find care')}</button></form>
            <div className="care-entry-chips">{['Work stress','Relationships','Anxiety'].map(text=><button type="button" key={text} onClick={()=>setQuery(text)}>{text}</button>)}</div>
            <Link className="text-link" to="/patient/requests">Post a private request</Link><p className="supporting">Free to browse · Pay the agreed session fee · Adults 18+</p>
          </section>
          <section className="clinician-care-entry"><p className="eyebrow">FOR CLINICIANS</p><h2>Your practice. One connected workspace.</h2><p>Bring your patients, publish approved services, manage bookings, and respond to people looking for your expertise.</p>
            <div className="care-tool-preview"><div className="care-entry-chips" aria-label="Explore clinician tools">{['Schedule','Requests','Earnings'].map(value=><button key={value} type="button" aria-pressed={tool===value} onClick={()=>setTool(value)}>{value}</button>)}</div>
            <h3>{tool==='Schedule'?'Set hours that work for you.':tool==='Requests'?'Respond with a private offer.':'Understand every balance.'}</h3><p>{tool==='Schedule'?'Recurring availability and date exceptions help patients book usable times.':tool==='Requests'?'Review eligible requests, propose a fee and time, and track the patient’s response.':'Track pending earnings, available funds and payout requests. Funds release follows completion and dispute rules.'}</p></div>
            <Link className="button primary" to="/sign-in?intent=clinician">Apply as a clinician</Link><Link className="text-link" to="/clinician">Open your workspace</Link><p className="supporting">Credentials and each service scope are reviewed before publication.</p>
          </section>
        </div>
      </section>
      <section className="services-section container">
        <div className="section-heading">
          <p className="eyebrow">START WITH WHAT’S ON YOUR MIND</p>
          <h2>There’s room for all of it.</h2>
          <p>
            Explore the kind of support you’re looking for. Available services
            depend on approved clinician offerings.
          </p>
        </div>
        <div className="category-grid">
          {[
            [
              Sprout,
              "Your wellbeing",
              "Space to talk about stress, difficult feelings and everyday life.",
            ],
            [
              HeartHandshake,
              "Your relationships",
              "Explore connection, communication and changes in your relationships.",
            ],
            [
              MessageCircle,
              "A place to begin",
              "You don’t need to have the perfect words to start a conversation.",
            ],
          ].map(([Icon, title, copy]) => {
            const Mark = Icon as typeof Sprout;
            return (
              <Link key={String(title)} className="category" to="/sign-in">
                <Mark size={28} />
                <h3>{String(title)}</h3>
                <p>{String(copy)}</p>
                <span className="text-link">
                  Explore support <ArrowRight size={18} />
                </span>
              </Link>
            );
          })}
        </div>
      </section>
      <section className="how-section" id="how-it-works">
        <div className="container">
          <p className="eyebrow">YOUR PACE. YOUR CHOICE.</p>
          <h2>A few small steps toward support.</h2>
          <div className="steps-grid">
            {[
              [
                "01",
                "Find your clinician",
                "Explore approved services, session lengths and clear prices.",
              ],
              [
                "02",
                "Choose your time",
                "Pick an available time that works for you.",
              ],
              [
                "03",
                "Decide what to share",
                "Review the information your clinician will see before you confirm.",
              ],
            ].map(([number, title, copy]) => (
              <div key={number}>
                <span className="step-number">{number}</span>
                <h3>{title}</h3>
                <p>{copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="privacy-section container">
        <div className="privacy-mark">
          <ShieldCheck size={64} strokeWidth={1.2} />
        </div>
        <div>
          <p className="eyebrow">A THOUGHTFUL START</p>
          <h2>Your story. Your sharing choices.</h2>
          <p>
            Use a preferred name or alias. Before booking, see exactly what
            you’ll share with your clinician. You can change your choices for
            each request.
          </p>
          <Link className="text-link" to="/sign-in">
            Take the first step <ArrowRight size={18} />
          </Link>
        </div>
      </section>
      <section className="clinician-invite container">
        <div>
          <p className="eyebrow">FOR CLINICIANS</p>
          <h2>Make space for meaningful care.</h2>
          <p>
            Apply to offer your services on TeleTena. Applications and service
            scopes are reviewed before you can accept bookings.
          </p>
        </div>
        <Link className="button secondary" to="/for-clinicians">
          Explore clinician access <ArrowRight size={20} />
        </Link>
      </section>
    </main>
  );
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
