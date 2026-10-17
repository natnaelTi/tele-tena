import { Link } from 'react-router-dom';
import { CalendarDays, MessageCircle, Users, Video } from 'lucide-react';
import { Card, InlineNotice } from '../components/ui';
import { useLocale } from '../hooks/useLocale';
import './PublicJourneys.css';

/** A02/A03 source compositions; public explanation, never fictional live records. */
export default function PublicJourney({clinician=false}:{clinician?:boolean}) {
  const {w}=useLocale();
  const steps=clinician?[
    [CalendarDays,'Availability','Recurring hours and date exceptions'],
    [Video,'Appointments','Voice and video consultations'],
  ]:[
    [MessageCircle,'Tell us what you need','A few words are enough.'],
    [Users,'Choose your clinician','See scope, experience, price and availability.'],
    [Video,'Meet in your own space','Join a private voice or video consultation.'],
  ];
  const cards=clinician?[
    ['Set your rhythm','Recurring hours, date exceptions, and booking rules that fit your practice.'],
    ['Build credible trust','Verified scope and transparent service information. Patient experience and booking reliability stay distinct.'],
    ['Know your earnings','See pending and available earnings, release dates, and payout requests.'],
  ]:[
    ['Your privacy, visible','Preview exactly what your clinician will see. Use an alias when you prefer.'],
    ['Know the price','A defined session length and a clear price before you book. Extensions need your agreement.'],
    ['Stay connected','Find shared summaries, follow-ups, and your previous clinicians in one place.'],
  ];
  return <div className="public-journey-surface"><main className="public-journey">
    <section className="public-journey-hero"><div><p className="eyebrow">{w(clinician?'FOR CLINICIANS':'CARE ON YOUR TERMS')}</p><h1>{w(clinician?'Your practice.':'From a question')}<br/>{w(clinician?'More connected.':'to a conversation.')}</h1><p>{w(clinician?'Bring your patients, publish your availability, and meet people looking for your expertise.':'Choose the person, time, and privacy that feel right for you.')}</p><Link className="button primary" to={clinician?'/sign-in?intent=clinician&mode=register':'/care'}>{w(clinician?'Apply as a clinician':'Find your care')}</Link></div>
    <aside className="public-journey-preview" aria-label={w(clinician?'Practice preview':'How it works')}>{clinician&&<><span className="supporting">{w('Practice preview')}</span><h2>{w('Space for good care.')}</h2></>}{steps.map(([Icon,title,copy])=>{const Mark=Icon as typeof CalendarDays;return <div className="public-journey-step" key={String(title)}><span aria-hidden="true"><Mark size={22}/></span><div><strong>{w(String(title))}</strong><p>{w(String(copy))}</p></div></div>;})}</aside></section>
    <section className="public-journey-grid">{cards.map(([title,copy])=><Card key={title}><h2>{w(title)}</h2><p>{w(copy)}</p></Card>)}</section>
    {clinician&&<InlineNotice>{w('Applications are reviewed by a person. Approval is granted separately for each requested service scope.')}</InlineNotice>}
    <nav className="public-journey-next" aria-label={w('Next steps')}><Link to="/">{w('Back to home')}</Link><Link to={clinician?'/sign-in?intent=clinician':'/sign-in?intent=patient&mode=register'}>{w(clinician?'Sign in':'Create an account')}</Link></nav>
  </main></div>;
}
