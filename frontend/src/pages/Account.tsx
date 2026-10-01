import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageTitle, money } from "../components/Domain";
import { Button, Checkbox, InlineNotice, TextField } from "../components/ui";
import { journeyApi } from "../journey-api";
import { useSession } from "../hooks/useSession";
import { useAction } from "../hooks/useAction";
import { useLocale } from "../hooks/useLocale";
import { useResource } from "../hooks/useResource";

const tabs=["Personal profile","Contact & sign-in","Language & timezone","Privacy & sharing"] as const;
export default function Account() {
  const { session, refresh } = useSession();
  const profile = session!.profile!;
  const {locale,setLocale}=useLocale();
  const [tab,setTab]=useState<(typeof tabs)[number]>("Personal profile");
  const [name, setName] = useState(profile.display_name);
  const [history, setHistory] = useState(profile.history);
  const [shareName, setShareName] = useState(!!profile.share_name);
  const [shareHistory, setShareHistory] = useState(!!profile.share_history);
  const [preferredLocale,setPreferredLocale]=useState(locale);
  const [zone,setZone]=useState("Africa/Addis_Ababa");
  const [resume,setResume]=useState(false);const [resumeBusy,setResumeBusy]=useState(false);
  const [dirty,setDirty]=useState(false);
  const [installPrompt,setInstallPrompt]=useState<any>(null);
  const action = useAction();
  const prefs=useResource(journeyApi.preferences);
  const wallet=useResource(journeyApi.wallet);
  useEffect(()=>{if(prefs.data){setPreferredLocale(prefs.data.locale as typeof locale);setZone(prefs.data.timezone||"Africa/Addis_Ababa");setLocale(prefs.data.locale as typeof locale);}},[prefs.data]);
  useEffect(()=>{if(profile.kind==="clinician")void journeyApi.resumeStatus().then(value=>setResume(value.uploaded)).catch(()=>undefined);},[profile.kind]);
  useEffect(()=>{const receive=(event:Event)=>{event.preventDefault();setInstallPrompt(event);};window.addEventListener("beforeinstallprompt",receive);return()=>window.removeEventListener("beforeinstallprompt",receive);},[]);
  const saveProfile=()=>void action.run(async()=>{await journeyApi.saveProfile({kind:profile.kind,display_name:name,adult:1,history,share_name:shareName,share_history:shareHistory});await refresh();setDirty(false);},"Your profile and privacy defaults are saved.");
  return <>
    <PageTitle title="Account" description="Manage your personal details, sign-in, language and privacy choices." />
    <nav className="account-tabs" aria-label="Account settings">{tabs.map(label=><button type="button" key={label} className={tab===label?"selected":""} onClick={()=>setTab(label)}>{label}</button>)}</nav>
    <div className="account-sections" data-tour-unsaved={dirty?"true":"false"} onChange={()=>setDirty(true)}>
    {tab==="Personal profile"&&<section className="settings-section"><h2>Personal profile</h2><p>Your preferred name is used in your account. Sharing it with a clinician is decided for each appointment.</p><TextField label={profile.kind==="clinician"?"Professional name":"Preferred name or alias"} value={name} maxLength={120} onChange={e=>setName(e.target.value)} required/>{profile.kind==="patient"&&<><details className="settings-disclosure"><summary>Optional saved history</summary><label className="field">Information you may choose to share<textarea rows={5} maxLength={4000} value={history} onChange={e=>setHistory(e.target.value)}/></label><p className="supporting">Your saved history is not shared unless you choose it for an appointment.</p></details></>}<Button loading={action.busy} onClick={saveProfile}>Save profile</Button></section>}
    {tab==="Contact & sign-in"&&<section className="settings-section"><h2>Contact and sign-in</h2><p>Your sign-in contact is verified before it is used. Contact changes are not available from this screen yet.</p><div className="settings-summary"><strong>Sign-in method</strong><span>Verified phone or email sign-in</span></div><Link to="/sign-in" className="text-link">Sign out and choose another sign-in method</Link></section>}
    {tab==="Language & timezone"&&<section className="settings-section"><h2>Language and timezone</h2><label className="field">Language<select value={preferredLocale} onChange={e=>{const value=e.target.value as typeof locale;setPreferredLocale(value);setLocale(value);}}><option value="en">English</option><option value="am">አማርኛ</option><option value="om">Afaan Oromo</option></select></label><label className="field">Timezone<select value={zone} onChange={e=>setZone(e.target.value)}><option value="Africa/Addis_Ababa">Addis Ababa (EAT)</option><option value="Africa/Nairobi">Nairobi (EAT)</option><option value="UTC">UTC</option></select></label><Button loading={action.busy} onClick={()=>void action.run(async()=>{await journeyApi.savePreferences(preferredLocale,zone);setLocale(preferredLocale);setDirty(false);},"Language and timezone saved.")}>Save preferences</Button><p className="supporting">Appointment times also show the timezone saved with each booking.</p></section>}
    {tab==="Privacy & sharing"&&<section className="settings-section"><h2>Privacy and sharing defaults</h2><p>Defaults help start a booking. You can change sharing for each appointment without changing these preferences.</p>{profile.kind==="patient"&&<><Checkbox label="Share my preferred name by default" checked={shareName} onChange={e=>setShareName(e.target.checked)}/><Checkbox label="Share my saved history by default" checked={shareHistory} onChange={e=>setShareHistory(e.target.checked)}/></>}<Button loading={action.busy} onClick={saveProfile}>Save privacy defaults</Button><p className="supporting">Changes do not alter information already shared with a clinician.</p></section>}
    {action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}{action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
    {profile.kind==="patient"&&<section className="settings-summary-panel"><h2>Balance</h2>{wallet.data?<p><strong>ETB {money(wallet.data.available)}</strong> available · ETB {money(wallet.data.reserved)} reserved</p>:wallet.error?<InlineNotice tone="danger">Balance could not be loaded.</InlineNotice>:<p>Loading balance…</p>}<Link className="button secondary" to="/patient/payments">Payments and activity</Link></section>}
    {profile.kind==="clinician"&&<section className="settings-summary-panel"><h2>Professional profile and practice</h2><p>Approval and each service scope are reviewed by an administrator.</p><Link className="button secondary" to="/clinician/services">Services and pricing</Link> <Link className="button secondary" to="/clinician/availability">Availability</Link><label className="field">Resume (PDF, up to 5 MB)<input type="file" accept="application/pdf,.pdf" disabled={resumeBusy} onChange={async e=>{const file=e.target.files?.[0];if(!file)return;if(file.size>5*1024*1024)return;setResumeBusy(true);try{const data=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(",")[1]||"");reader.onerror=()=>reject(new Error());reader.readAsDataURL(file);});await journeyApi.uploadResume(file.name,data);setResume(true);}catch{window.alert("Resume upload failed. Check that this is a PDF no larger than 5 MB.");}finally{setResumeBusy(false);e.target.value="";}}}/>{resume&&<><span>Resume securely stored for authorized review.</span><Button variant="quiet" onClick={()=>void journeyApi.removeResume().then(()=>setResume(false)).catch(()=>window.alert("Submitted evidence cannot be removed here."))}>Remove resume</Button></>}</label></section>}
    <section className="settings-summary-panel"><h2>Notifications</h2><p>Notification preferences are not available yet.</p></section>
    <section className="settings-summary-panel"><h2>Install TeleTena</h2>{installPrompt?<Button variant="secondary" onClick={async()=>{await installPrompt.prompt();setInstallPrompt(null);}}>Install app</Button>:<details><summary>Installation help</summary><p>On Android or desktop, use your browser’s Install app or Add to Home Screen menu. On iPhone or iPad, open the Share menu in Safari and choose Add to Home Screen. Installation requires a secure HTTPS site.</p></details>}<p className="supporting">The app stores only public files for offline access. Bookings, notes and payments require a connection.</p></section>
    </div>
  </>;
}
