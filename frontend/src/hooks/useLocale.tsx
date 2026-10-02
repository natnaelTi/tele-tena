import { createContext, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { locales } from "../i18n";
import type { Key } from "../i18n";
import { useSession } from "./useSession";
import { journeyApi } from "../journey-api";
type Locale = keyof typeof locales;
const words: Record<string, [string, string]> = {
  "Find care": ["እንክብካቤ ያግኙ", "Tajaajila barbaadi"],
  Home: ["መነሻ", "Mana"],
  Appointments: ["ቀጠሮዎች", "Beellamoota"],
  Account: ["መለያ", "Herrega"],
  Today: ["ዛሬ", "Harʼa"],
  Continue: ["ቀጥል", "Itti fufi"],
  "Sign in": ["ግባ", "Seeni"],
  "Sign out": ["ውጣ", "Baʼi"],
  "Phone number": ["ስልክ ቁጥር", "Lakkoofsa bilbilaa"],
  "Use email instead": ["ኢሜይል ይጠቀሙ", "Imeelii fayyadami"],
  "Use phone instead": ["በስልክ ይጠቀሙ", "Bilbila fayyadami"],
  "Use password instead": ["በይለፍ ቃል ይጠቀሙ", "Jecha darbii fayyadami"],
  "Use an email code instead": ["በኢሜይል ኮድ ይጠቀሙ", "Koodii imeelii fayyadami"],
  "Resend code": ["ኮድ እንደገና ላክ", "Koodii irra deebi'ii ergi"],
  Email: ["ኢሜይል", "Imeelii"],
  Password: ["ይለፍ ቃል", "Jecha darbii"],
  "Verify and continue": ["አረጋግጠው ይቀጥሉ", "Mirkaneessiitii itti fufi"],
  "Change number": ["ቁጥር ቀይር", "Lakkoofsa jijjiiri"],
  "Verification code": ["የማረጋገጫ ኮድ", "Koodii mirkaneessaa"],
  Availability: ["የሚገኙበት ጊዜ", "Yeroo argamtu"],
  "Services & pricing": ["አገልግሎት እና ዋጋ", "Tajaajilaa fi gatii"],
  "Profile & privacy": ["መገለጫ እና ግላዊነት", "Ibsaa fi iccitii"],
  Back: ["ተመለስ", "Deebiʼi"],
  "Save changes": ["ለውጦችን አስቀምጥ", "Jijjiirama olkaaʼi"],
  "Demo environment": ["የሙከራ አካባቢ", "Naannoo agarsiisaa"],
  "Simulated balance": ["የሙከራ ቀሪ ሂሳብ", "Haftee fakkeeffame"],
  "Choose a time": ["ጊዜ ይምረጡ", "Yeroo filadhu"],
  "What you’ll share": ["የሚያጋሩት መረጃ", "Waan qooddu"],
  "Join consultation": ["ወደ ምክክር ይግቡ", "Marii seeni"],
  "For clinicians": ["ለባለሙያዎች", "Ogeessotaaf"],
  "How it works": ["እንዴት ይሰራል", "Akkaataa hojjetu"],
  "Welcome to TeleTena": ["ወደ TeleTena እንኳን ደህና መጡ", "Baga TeleTena dhuftan"],
  "Help & tours": ["እገዛ እና ጉብኝቶች", "Gargaarsa fi daawwannaa"],
  "Quick tour": ["አጭር ጉብኝት", "Daawwannaa gabaabaa"],
  "Want a quick tour of this workspace?": ["የዚህን የስራ ቦታ አጭር ጉብኝት ይፈልጋሉ?", "Bakka hojii kana daawwachuu barbaaddaa?"],
  "Take a quick tour": ["አጭር ጉብኝት ይውሰዱ", "Daawwannaa gabaabaa jalqabi"],
  "Dismiss tour invitation": ["የጉብኝት ግብዣን ዝጋ", "Affeerraa daawwannaa cufi"],
  "Consultations": ["ምክክሮች", "Mariilee"],
  "Balance and privacy": ["ቀሪ ሂሳብ እና ግላዊነት", "Haftee fi iccitii"],
  "Your practice": ["የስራ ልምምድዎ", "Shaakala hojii kee"],
  "Services and schedule": ["አገልግሎቶች እና መርሃ ግብር", "Tajaajilaa fi sagantaa"],
  "Appointments and calls": ["ቀጠሮዎች እና ጥሪዎች", "Beellamoota fi bilbiloota"],
  "Consultation notes": ["የምክክር ማስታወሻዎች", "Yaadannoo marii"],
  "Care records and account": ["የእንክብካቤ መዝገቦች እና መለያ", "Galmee kunuunsaa fi herrega"],
  "Application queue": ["የማመልከቻ ወረፋ", "Tarree iyyannoo"],
  "Review evidence": ["ማስረጃን ይገምግሙ", "Ragaa qoradhu"],
  "Service scopes": ["የአገልግሎት ወሰኖች", "Daangaa tajaajilaa"],
  "QUICK TOUR": ["አጭር ጉብኝት", "DAAWWANNAA GABAABAA"],
  "This feature is not available in the current view. Continue to the next step.": ["ይህ ባህሪ በአሁኑ ገጽ ላይ የለም። ወደ ቀጣዩ ደረጃ ይቀጥሉ።", "Amalli kun fuula ammaa irratti hin jiru. Gara tarkaanfii itti aanuutti ce'i."],
  "Next": ["ቀጣይ", "Itti aanuu"],
  "Finish": ["ጨርስ", "Xumuri"],
  "Skip": ["ዝለል", "Darbi"],
  "Close tour": ["ጉብኝቱን ዝጋ", "Daawwannaa cufi"],
  "Profile and resume": ["መገለጫ እና የስራ ልምድ ሰነድ", "Ibsa dhuunfaa fi CV"],
  "Complete your professional profile and upload evidence for review. Approval is manual.": ["የሙያ መገለጫዎን ያጠናቅቁ እና ለግምገማ ሰነድ ይስቀሉ። ማጽደቅ በእጅ ይከናወናል።", "Ibsa ogummaa guutiitii ragaa gamaaggamaaf olkaa'i. Mirkaneessi harkaan raawwatama."],
  "Care records": ["የእንክብካቤ መዝገቦች", "Galmee kunuunsaa"],
  "Open only the encounters you treated. Clinic affiliation does not grant access.": ["እርስዎ የተከታተሏቸውን ግንኙነቶች ብቻ ይክፈቱ። የክሊኒክ ግንኙነት ፈቃድ አይሰጥም።", "Walgahii ati tajaajilte qofa bani. Walitti dhufeenyi kilinikaa hayyama hin kennu."],
  "Find a clinician": ["ባለሙያ ያግኙ", "Ogeessa barbaadi"],
  "Use the professional display name as the primary identifier.": ["የሙያ ስምን እንደ ዋና መለያ ይጠቀሙ።", "Maqaa ogummaa akka eenyummaa jalqabaatti fayyadami."],
  "Make an application decision": ["በማመልከቻ ላይ ውሳኔ ይስጡ", "Murtii iyyannoo kenni"],
  "Approval is manual and does not automatically approve requested services.": ["ማጽደቅ በእጅ ይከናወናል፤ የተጠየቁ አገልግሎቶችን በራስ-ሰር አያጸድቅም።", "Mirkaneessi harkaan raawwatama; tajaajiloota gaafataman ofumaan hin mirkaneessu."],
  "Professional profile": ["የሙያ መገለጫ", "Ibsa ogummaa"],
  "Enter the professional name that matches your credentials.": ["ከማስረጃዎችዎ ጋር የሚዛመድ የሙያ ስም ያስገቡ።", "Maqaa ogummaa ragaa kee wajjin walsimu galchi."],
  "Request service scopes": ["የአገልግሎት ወሰኖችን ይጠይቁ", "Daangaa tajaajilaa gaafadhu"],
  "Select only the service types you want the reviewers to assess.": ["ገምጋሚዎች እንዲመረምሩ የሚፈልጉትን አገልግሎቶች ብቻ ይምረጡ።", "Tajaajiloota gamaaggamtoonni akka qoratan barbaaddu qofa filadhu."],
  "Upload evidence": ["ማስረጃ ይስቀሉ", "Ragaa olkaa'i"],
  "Add a PDF resume. Receipt does not mean your credentials are verified.": ["የPDF የስራ ልምድ ሰነድ ያክሉ። መቀበሉ ምስክርነትዎ ተረጋግጧል ማለት አይደለም።", "CV PDF dabali. Fudhachuun ragaan kee mirkanaa'e jechuu miti."],
  "Save and resume": ["ያስቀምጡ እና ይቀጥሉ", "Olkaa'iitii itti fufi"],
  "Save your progress before leaving this form.": ["ከዚህ ቅጽ ከመውጣትዎ በፊት እድገትዎን ያስቀምጡ።", "Unka kana keessaa ba'uu dura adeemsa kee olkaa'i."],
  "Manual review": ["በእጅ ግምገማ", "Gamaaggama harkaa"],
  "You cannot accept bookings until your application and each requested scope are approved.": ["ማመልከቻዎ እና የተጠየቁ የአገልግሎት ወሰኖች እስኪጸድቁ ድረስ ቀጠሮ መቀበል አይችሉም።", "Iyyannoon kee fi daangaan tajaajilaa tokkoon tokkoon isaa hanga mirkanaa'anitti beellama fudhachuu hin dandeessu."],
};
const Context = createContext<{
  locale: Locale;
  setLocale: (value: Locale) => void;
  t: (key: Key) => string;
  w: (english: string) => string;
} | null>(null);
export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("en");
  const {session,loading}=useSession();
  const loadedUser=useRef<string|null>(null);
  useEffect(()=>{
    if(loading)return;
    if(!session){loadedUser.current=null;setLocale("en");return;}
    if(loadedUser.current===session.user)return;
    loadedUser.current=session.user;
    let active=true;
    void journeyApi.preferences().then(preference=>{if(active&&["en","am","om"].includes(preference.locale))setLocale(preference.locale as Locale);}).catch(()=>undefined);
    return()=>{active=false;};
  },[session?.user,loading]);
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);
  return (
    <Context.Provider
      value={{
        locale,
        setLocale,
        t: (key) => locales[locale][key],
        w: (english) =>
          locale === "en"
            ? english
            : words[english]?.[locale === "am" ? 0 : 1] || english,
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useLocale() {
  const result = useContext(Context);
  if (!result) throw new Error("Missing locale provider");
  return result;
}
export function LanguageSelect() {
  const { locale, setLocale } = useLocale();
  return (
    <select
      className="language-select"
      aria-label="Language / ቋንቋ / Afaan"
      value={locale}
      onChange={(e) => setLocale(e.target.value as Locale)}
    >
      <option value="en">English</option>
      <option value="am">አማርኛ</option>
      <option value="om">Afaan Oromo</option>
    </select>
  );
}
