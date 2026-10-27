import {TelebirrPayeeSettings,usePaymentCapabilities,DirectLedgerSummary} from '../components/DirectPayments';
import {CareLanguageEditor,PreferredCareLanguage} from '../components/CareLanguages';
import {ProfessionalEditor} from '../components/ProfessionalReview';
import {EncounterFileHistory} from '../components/EncounterFiles';
import {NotificationPreferences} from '../components/BookingNotices';
import HistoryDocuments from "../components/HistoryDocuments";
import "./Account.css";
import ProfilePhoto, {Avatar} from "../components/ProfilePhoto";
import { api } from "../api";
import { WalletSummary } from "../components/WalletSummary";
import { useNavigate } from "react-router-dom";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, ShieldCheck, Users, Layers, CalendarDays, WalletCards, UserRound, Bell, Globe, LockKeyhole, HelpCircle, LayoutDashboard, HeartPulse } from "lucide-react";
import { Link } from "react-router-dom";
import { PageTitle } from "../components/Domain";
import { Button, Checkbox, InlineNotice, Select, TextField } from "../components/ui";
import { journeyApi } from "../journey-api";
import { useSession } from "../hooks/useSession";
import { useAction } from "../hooks/useAction";
import { useLocale } from "../hooks/useLocale";
import { useResource } from "../hooks/useResource";

export default function Account() {
  const { session, refresh } = useSession();
  const profile = session!.profile!;
  const canManagePractice = session!.roles.includes("Tele Tena Clinician");
  const {locale,setLocale,w}=useLocale();
  const navigate = useNavigate();
  const sections=profile.kind==="clinician"?["Personal profile","Professional profile & practice","Language & timezone","Notifications","Contact & sign-in","Help & installation"]:["Personal profile","Medical history","Privacy & sharing","Language & timezone","Notifications","Contact & sign-in","Help & installation"];
  const tabs = ["Overview", ...sections];
  const sectionIcon=(label:string)=>label==='Overview'?LayoutDashboard:label==='Personal profile'?UserRound:label==='Medical history'?HeartPulse:label==='Privacy & sharing'?ShieldCheck:label==='Language & timezone'?Globe:label==='Notifications'?Bell:label==='Contact & sign-in'?LockKeyhole:label==='Help & installation'?HelpCircle:ShieldCheck;
  const [tab,setTab]=useState("Overview");
  const sectionNavigation = useRef<HTMLElement>(null);
  useEffect(() => {
    const navigation = sectionNavigation.current;
    const selected = navigation?.querySelector<HTMLElement>('[aria-current="page"]');
    if (!navigation || !selected) return;
    const boundary = navigation.getBoundingClientRect();
    const item = selected.getBoundingClientRect();
    // Reveal only within the horizontal strip; never move the page vertically.
    if (item.left < boundary.left) navigation.scrollLeft += item.left - boundary.left;
    else if (item.right > boundary.right) navigation.scrollLeft += item.right - boundary.right;
  }, [tab]);
  const [alias,setAlias]=useState(profile.care_alias||'');
  const [name, setName] = useState(profile.display_name);
  useEffect(()=>{if(profile.kind==="clinician")setName(profile.display_name);},[profile.kind,profile.display_name]);
  const [nameAttempted,setNameAttempted]=useState(false);
  const [history, setHistory] = useState(profile.history);
  const [shareName, setShareName] = useState(!!profile.share_name);
  const [shareHistory, setShareHistory] = useState(!!profile.share_history);
  const [preferredLocale,setPreferredLocale]=useState(locale);
  const [zone,setZone]=useState("Africa/Addis_Ababa");
  const [dirty,setDirty]=useState(false);
  const [installPrompt,setInstallPrompt]=useState<any>(null);
  const action = useAction();
  const prefs=useResource(journeyApi.preferences);
  const loadAccess = useCallback(() => api<{phone_otp:boolean;email_otp:boolean}>("tele_tena.api.contact_auth.sign_in_options"), []);
  const access = useResource(loadAccess);
  const paymentMode=usePaymentCapabilities();
  const loadWallet=useCallback(()=>profile.kind==="patient"?journeyApi.wallet():Promise.resolve(null),[profile.kind]);
  const wallet=useResource(loadWallet);
  useEffect(()=>{if(prefs.data){setPreferredLocale(prefs.data.locale as typeof locale);setZone(prefs.data.timezone||"Africa/Addis_Ababa");setLocale(prefs.data.locale as typeof locale);}},[prefs.data]);
  useEffect(()=>{const receive=(event:Event)=>{event.preventDefault();setInstallPrompt(event);};window.addEventListener("beforeinstallprompt",receive);return()=>window.removeEventListener("beforeinstallprompt",receive);},[]);
  const saveProfile=()=>void action.run(async()=>{await journeyApi.saveProfile({kind:profile.kind,display_name:profile.kind==='clinician'?profile.display_name:name,adult:1,history,...(profile.kind==='patient'?{care_alias:alias}:{}),share_name:shareName,share_history:shareHistory});await refresh();setDirty(false);},profile.kind==="clinician"?"Your professional profile and care languages are saved.":"Your profile and privacy defaults are saved.");
  const title = "Your Account";
  const description = "Your details, preferences and privacy, all in one place.";
  const practiceLinks = [
    ...(canManagePractice ? [
      {label:"Services and pricing",to:"/clinician/services",description:"Approved scopes and tailored offerings",Icon:Layers},
      {label:"Availability",to:"/clinician/availability",description:"Confirmation, buffers and notice",Icon:CalendarDays},
      {label:"Earnings",to:"/clinician/earnings",description:"Balances and payment activity",Icon:WalletCards},
    ] : []),
    {label:"Application & credentials",to:"/clinician/vetting",description:"Profile, languages and evidence",Icon:ShieldCheck},
  ];
  const practiceSettings = <section className="settings-section"><h2>{w("Practice Settings")}</h2>{practiceLinks.map(({label,to,description,Icon})=><Link className="settings-link-row" key={to} to={to} aria-label={w(label)} aria-describedby={"practice-description-"+to.split("/").pop()}><Icon size={20}/><span><strong>{w(label)}</strong><small id={"practice-description-"+to.split("/").pop()}>{w(description)}</small></span><ArrowRight size={18}/></Link>)}</section>;
  const personalEditor = <form className="settings-section" onSubmit={e=>{e.preventDefault();saveProfile();}}><h2>{w("Personal Details")}</h2>{profile.kind==='patient'&&<TextField label={w("Clinician-facing alias")} value={alias} onChange={event=>{setAlias(event.target.value);setDirty(true);}}/>}{tab === "Personal profile" && <p>{w("Your preferred name is used in your account. Sharing it with a clinician is decided for each appointment.")}</p>}<TextField label={w(profile.kind === "clinician" ? "Professional name" : "Preferred name or alias")} value={name} maxLength={120} onChange={e=>{setName(e.target.value);setDirty(true);}} required pattern={String.raw`.*\S.*`} onInvalid={()=>setNameAttempted(true)} error={nameAttempted&&!name.trim()?w(profile.kind === "clinician"?"Enter your professional name.":"Enter a preferred name or alias."):undefined} disabled={action.busy}/><Button type="submit" variant="secondary" loading={action.busy}>{w("Save details")}</Button></form>;
  return <>
    <PageTitle title={w(title)} description={w(description)} />
    <div className="account-mobile-sections"><Select label={w("Account section")} value={tab} onChange={event=>setTab(event.target.value)}>{tabs.map(label=><option key={label} value={label}>{w(label)}</option>)}</Select></div>
    <div className="account-workspace"><nav ref={sectionNavigation} className="account-tabs" aria-label={w("Account settings")}>{tabs.map(label=><button type="button" key={label} className={tab===label?"selected":""} onClick={()=>setTab(label)} aria-current={tab===label?"page":undefined}>{(()=>{const Icon=sectionIcon(label);return <><Icon size={18} aria-hidden="true"/><span>{w(label)}</span></>;})()}</button>)}</nav>
    <div className="account-sections" data-tour-unsaved={dirty?"true":"false"} onChange={()=>setDirty(true)}>
    {tab==="Personal profile"&&<ProfilePhoto/>}
    {action.error&&<InlineNotice tone="danger">{w(action.error)}</InlineNotice>}{action.success&&<InlineNotice tone="success">{w(action.success)}</InlineNotice>}
    {tab === "Overview" && <div className="account-overview"><section className="settings-section account-at-a-glance"><h2>{w("Account Overview")}</h2><dl className="settings-summary"><dt>{w(profile.kind==="clinician"?"Professional name":"Preferred name or alias")}</dt><dd>{name}</dd>{profile.kind==='patient'&&<><dt>{w("Clinician-facing alias")}</dt><dd>{alias||w("Private patient")}</dd></>}<dt>{w("Language")}</dt><dd>{{en:'English',am:'አማርኛ',om:'Afaan Oromo'}[preferredLocale]}</dd><dt>{w("Timezone")}</dt><dd>{zone}</dd></dl><Button variant="secondary" onClick={()=>setTab('Personal profile')}>{w('Edit personal details')}</Button>{profile.kind==='patient'&&<button type="button" className="settings-link-row" onClick={()=>setTab('Privacy & sharing')}><ShieldCheck size={20}/><span><strong>{w('Privacy & sharing')}</strong><small>{w('Defaults and encounter-level control')}</small></span><ArrowRight size={18}/></button>}</section><aside>{profile.kind === "patient" ? <>{paymentMode.data?.mode==='Offline'?<DirectLedgerSummary role="patient"/>:wallet.data ? <WalletSummary available={wallet.data.available} reserved={wallet.data.reserved} /> : wallet.error ? <InlineNotice tone="danger">{w("Balance unavailable.")} <Button variant="secondary" onClick={()=>void wallet.refresh()}>{w("Try again")}</Button></InlineNotice> : <p role="status">{w("Loading balance…")}</p>}<section className="settings-section"><h2>{w("People in Your Care")}</h2><Link className="settings-link-row" to="/patient/couples"><Users size={20}/><span><strong>{w("Shared care")}</strong><small>{w("Manage invitations and consent")}</small></span><ArrowRight size={18}/></Link><p className="supporting">{w("Relationships are private. Being linked never automatically shares records.")}</p></section></> : practiceSettings}</aside></div>}
    {tab==='Medical history'&&profile.kind==='patient'&&<section className="settings-section"><h2>{w('Medical History')}</h2><p>{w("Your saved history is not shared unless you choose it for an appointment.")}</p><form onSubmit={e=>{e.preventDefault();saveProfile();}}><div className="field"><label htmlFor="account-private-history">{w("Information you may choose to share")}</label><textarea id="account-private-history" rows={5} maxLength={4000} value={history} onChange={e=>setHistory(e.target.value)} disabled={action.busy}/></div><Button type="submit" variant="secondary" loading={action.busy}>{w('Save details')}</Button></form><HistoryDocuments/></section>}


    {tab==="Personal profile" && profile.kind==="patient" && personalEditor}
    {tab==="Notifications"&&<NotificationPreferences/>}{tab==="Contact & sign-in"&&<section className="settings-section"><h2>{w("Contact and Sign-in")}</h2><p>{w("Your sign-in contact is verified before it is used. Contact changes are not available from this screen yet.")}</p><dl className="settings-summary"><dt>{w("Email and password")}</dt><dd>{w("Available")}</dd>{access.data && <><dt>{w("Phone code")}</dt><dd>{w(access.data.phone_otp ? "Available" : "Unavailable on this site")}</dd><dt>{w("Email code")}</dt><dd>{w(access.data.email_otp ? "Available" : "Unavailable on this site")}</dd></>}</dl>{access.error ? <InlineNotice tone="danger">{w("Sign-in methods could not be loaded.")} <Button variant="quiet" onClick={() => void access.refresh()}>{w("Try again")}</Button></InlineNotice> : !access.data && <p role="status">{w("Loading sign-in methods…")}</p>}<Button variant="secondary" loading={action.busy} onClick={() => void action.run(async () => { await journeyApi.logout(); await refresh(); navigate("/sign-in"); }, "")}>{w("Sign out and choose another sign-in method")}</Button></section>}
    {profile.kind==='patient'&&tab==='Language & timezone'&&<PreferredCareLanguage/>}{tab==="Language & timezone"&&<form className="settings-section" onSubmit={e=>{e.preventDefault();void action.run(async()=>{await journeyApi.savePreferences(preferredLocale,zone);setLocale(preferredLocale);setDirty(false);},"Language and timezone saved.");}}><h2>{w("Language and Timezone")}</h2><Select label={w("Language")} disabled={action.busy} value={preferredLocale} onChange={e=>{const value=e.target.value as typeof locale;setPreferredLocale(value);setLocale(value);}}><option value="en">English</option><option value="am">አማርኛ</option><option value="om">Afaan Oromo</option></Select><Select label={w("Timezone")} disabled={action.busy} value={zone} onChange={e=>setZone(e.target.value)}><option value="Africa/Addis_Ababa">Addis Ababa (EAT)</option><option value="Africa/Nairobi">Nairobi (EAT)</option><option value="UTC">UTC</option></Select><Button type="submit" variant="secondary" loading={action.busy}>{w("Save preferences")}</Button><p className="supporting">{w("Appointment times also show the timezone saved with each booking.")}</p></form>}
    {tab==="Privacy & sharing"&&<EncounterFileHistory/>}{tab==="Privacy & sharing"&&<div className="account-settings-columns"><form className="settings-section" onSubmit={e=>{e.preventDefault();saveProfile();}}><h2>{w("Default Disclosure")}</h2><p>{w("Defaults help start a booking. You can change sharing for each appointment without changing these preferences.")}</p>{profile.kind==="patient"&&<><TextField label={w("Clinician-facing alias")} value={alias} onChange={event=>setAlias(event.target.value)} disabled={action.busy}/><Checkbox variant="card" label={w("Share my preferred name by default")} checked={shareName} onChange={e=>setShareName(e.target.checked)} disabled={action.busy}/><Checkbox variant="card" label={w("Share my saved history by default")} checked={shareHistory} onChange={e=>setShareHistory(e.target.checked)} disabled={action.busy}/></>}<Button type="submit" loading={action.busy}>{w("Save privacy defaults")}</Button></form><section className="settings-section settings-privacy-preview"><h2>{w("A Preview of Your Defaults")}</h2>{profile.kind === "patient" ? <><div className="settings-preview-identity"><ShieldCheck size={24}/><div><strong>{w(shareName?"Name visible to the clinician":"Clinician-facing alias")}</strong><p>{shareName ? name : alias||w("Private patient")}</p></div></div><dl className="settings-defaults-list"><dt>{w("Saved history")}</dt><dd>{shareHistory ? w("Shared by default") : w("Not shared")}</dd><dt>{w("Request details")}</dt><dd>{w("You choose these when booking or posting a request.")}</dd></dl></> : <p>{w("Patient disclosure is chosen separately for each consultation.")}</p>}<InlineNotice>{w("Existing bookings retain their agreed disclosure snapshot. Changing defaults does not rewrite past consent.")}</InlineNotice></section></div>}

    {profile.kind==="clinician"&&tab==="Professional profile & practice"&&<section className="settings-section account-professional-intro"><div className="professional-profile-summary"><Avatar url={session?.photo?.url} name={profile.display_name}/><div><h2>{w('Professional Profile & Practice')}</h2><p>{profile.display_name}</p></div></div><p>{w('Keep your professional details current, apply for individual service scopes and manage your practice. Your private evidence is never part of your public profile.')}</p><Link className="button secondary" to="/clinician/vetting"><ShieldCheck size={18}/>{w('Service Scope Applications')}</Link></section>}
    {profile.kind==="clinician"&&<ProfessionalEditor accountView accountSection={tab==='Personal profile'?'personal':tab==='Professional profile & practice'?'professional':undefined} onOpenPersonal={()=>setTab('Personal profile')} onOpenProfessional={()=>setTab('Professional profile & practice')}/>}
    {profile.kind==="clinician"&&tab==="Professional profile & practice"&&<div className="account-settings-columns"><div>{canManagePractice&&<TelebirrPayeeSettings/>}<section className="settings-section"><CareLanguageEditor/></section></div><aside>{practiceSettings}<section className="settings-section"><h2>{w('Clinic Affiliation Confirmations')}</h2><p className="supporting">{w('Select claimed affiliations in your professional details above. Verification and clinic confirmation are managed separately.')}</p><Link className="settings-link-row" to="/clinician/affiliations"><Users size={20}/><span>{w('Manage Clinic Affiliations')}</span><ArrowRight size={18}/></Link><p className="supporting">{w('A clinic affiliation does not grant access to patient records.')}</p></section></aside></div>}


    {tab==="Help & installation"&&<section className="settings-section"><h2>{w("Help & Installation")}</h2><p>{w("Use the Help & tours button for guides and walkthroughs.")}</p><details className="settings-help" open><summary>{w("Install TeleTena and Offline Use")}</summary>{installPrompt?<Button variant="secondary" onClick={async()=>{await installPrompt.prompt();setInstallPrompt(null);}}>{w("Install app")}</Button>:<p>{w("On Android or desktop, use your browser’s Install app or Add to Home Screen menu. On iPhone or iPad, use Safari’s Share menu and choose Add to Home Screen. Installation requires HTTPS. Only public files work offline; bookings, notes and payments need a connection.")}</p>}</details></section>}
    </div></div>
  </>;
}
