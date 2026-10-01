import { Link } from "react-router-dom";
import {
  ArrowRight,
  HeartHandshake,
  MessageCircle,
  ShieldCheck,
  Sprout,
} from "lucide-react";
import { ConversationArt } from "../components/Brand";
import { useLocale } from "../hooks/useLocale";
export default function Homepage() {
  const { w } = useLocale();
  return (
    <main>
      <section className="hero container">
        <div className="hero-copy">
          <p className="eyebrow">ROOM FOR A REAL CONVERSATION</p>
          <h1>Find someone you feel comfortable talking to.</h1>
          <p className="hero-intro">
            Explore mental health and relationship support. Choose your
            clinician, your time, and what you share.
          </p>
          <div className="actions">
            <Link className="button primary" to="/sign-in">
              {w("Find care")}
              <ArrowRight size={20} />
            </Link>
            <a className="text-link" href="#how-it-works">
              Explore how it works <ArrowRight size={18} />
            </a>
          </div>
          <p className="hero-footnote">
            <ShieldCheck size={18} />
            Your sharing choices stay in your hands.
          </p>
        </div>
        <ConversationArt />
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
