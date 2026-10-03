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
  Earnings: ["ገቢዎች", "Galii"],
  Pending: ["በመጠባበቅ ላይ", "Eegaa jira"],
  Available: ["ያለ", "Argama"],
  "Payout requested": ["የክፍያ ጥያቄ ተጠይቋል", "Gaaffiin kaffaltii dhiyaate"],
  "Request a payout": ["ክፍያ ይጠይቁ", "Kaffaltii gaafadhu"],
  "Amount (ETB)": ["መጠን (ብር)", "Hamma (ETB)"],
  "Request payout": ["ክፍያ ጠይቅ", "Kaffaltii gaafadhu"],
  "No external transfer occurs here.": ["እዚህ ውጫዊ የገንዘብ ማስተላለፍ አይካሄድም።", "As irratti dabarsi maallaqaa alaa hin raawwatamu."],
  "Payout request recorded.": ["የክፍያ ጥያቄው ተመዝግቧል።", "Gaaffiin kaffaltii galmaa'eera."],
  "Consultation earnings": ["ከምክክር የተገኘ ገቢ", "Galii marii"],
  "No finalized consultations yet.": ["ገና የተጠናቀቁ ምክክሮች የሉም።", "Ammaaf mariin xumurame hin jiru."],
  "Payout requests": ["የክፍያ ጥያቄዎች", "Gaaffii kaffaltii"],
  "No payout requests.": ["የክፍያ ጥያቄ የለም።", "Gaaffiin kaffaltii hin jiru."],
  "Cancel request": ["ጥያቄውን ሰርዝ", "Gaaffii haqi"],
  "Payout request cancelled; the reservation was released.": ["የክፍያ ጥያቄው ተሰርዟል፤ የተያዘው መጠን ተመልሷል።", "Gaaffiin haqameera; maallaqni qabame bilisa ta'eera."],
  "Financial disputes": ["የገንዘብ ክርክሮች", "Waldhabdee maallaqaa"],
  "Release after review": ["ከግምገማ በኋላ ክፈት", "Gamaaggama booda gadhiisi"],
  "Refund patient": ["ለታካሚው መልስ", "Dhukkubsataaf deebisi"],
  "Request payment review": ["የክፍያ ግምገማ ጠይቅ", "Gamaaggama kaffaltii gaafadhu"],
  "Payment review requested. The related simulated earnings are on hold.": ["የክፍያ ግምገማ ተጠይቋል። ተያያዥ የሙከራ ገቢ ታግዷል።", "Gamaaggamni kaffaltii gaafatameera. Galiin fakkeeffame walqabatu dhaabbateera."],
  "Refund recorded in the demonstration ledger.": ["ተመላሽ በሙከራ የገንዘብ መዝገብ ተመዝግቧል።", "Deebiin galmee maallaqaa agarsiisaa keessatti galmaa'eera."],
  "No open financial disputes.": ["ክፍት የገንዘብ ክርክር የለም።", "Waldhabdeen maallaqaa banamaan hin jiru."],
  "Pending earnings become available after the recorded dispute window. No external transfer occurs here.": ["የሚጠባበቀው ገቢ ከተመዘገበው የክርክር ጊዜ በኋላ ይገኛል። እዚህ ውጫዊ ማስተላለፍ አይካሄድም።", "Galiin eegaa jiru yeroo waldhabdee galmaa'e booda argama. Asitti dabarsi alaa hin jiru."],
  "Held for the agreed demonstration review window or an open dispute.": ["ለሙከራ የግምገማ ጊዜ ወይም ለክፍት ክርክር ተይዟል።", "Yeroo gamaaggama agarsiisaa ykn waldhabdee banaadhaaf qabame."],
  "Reserved while a request is open. No external transfer.": ["ጥያቄው ክፍት እስከሆነ ድረስ ተይዟል። ውጫዊ ማስተላለፍ የለም።", "Gaaffiin hanga banamutti qabameera. Dabarsi alaa hin jiru."],
  "Requested amounts are reserved from available earnings. No external transfer occurs here.": ["የተጠየቀው መጠን ከሚገኘው ገቢ ይያዛል። እዚህ ውጫዊ ማስተላለፍ አይካሄድም።", "Hamma gaafatame galii argamu keessaa qabama. Asitti dabarsi alaa hin jiru."],
  Consultation: ["ምክክር", "Mari"],
  "On hold": ["ታግዷል", "Dhaabbateera"],
  "Expected release": ["የሚጠበቀው መለቀቅ", "Yeroo gadhiifamuu eegamu"],
  "Subject to the saved dispute window.": ["በተመዘገበው የክርክር ጊዜ መሠረት።", "Yeroo waldhabdee galmaa'e irratti hundaa'a."],
  "Release is paused while an authorized reviewer resolves the dispute.": ["የተፈቀደለት ገምጋሚ ክርክሩን እስኪፈታ ድረስ መለቀቁ ቆሟል።", "Gamaaggamaan hayyamame hanga waldhabdee furutti gadhiifamuun dhaabbateera."],
  "Historical balance preserved for authorized review; no automatic settlement.": ["የቀድሞ ቀሪ ሂሳብ ለተፈቀደ ግምገማ ተጠብቋል፤ በራስ-ሰር አይከፈልም።", "Hafteen durii gamaaggama hayyamameef eegameera; ofumaan hin xumuramu."],
  "Requested on": ["የተጠየቀበት", "Yeroo gaafatame"],
  "Financial disputes review only payment concerns. No clinical note access is included.": ["የገንዘብ ክርክሮች የክፍያ ጉዳዮችን ብቻ ይመለከታሉ። የምክክር ማስታወሻ መዳረሻ አይሰጥም።", "Waldhabdeen maallaqaa dhimma kaffaltii qofa ilaala. Yaadannoo marii argachuun hin dabalamu."],
  "Opened": ["ተከፍቷል", "Banameera"],
  "Resolution record": ["የውሳኔ መዝገብ", "Galmee murtii"],
  "Record a short reason. This does not add or change clinical documentation.": ["አጭር ምክንያት ይመዝግቡ። ይህ የምክክር ሰነድን አይጨምርም ወይም አይቀይርም።", "Sababa gabaabaa galmeessi. Kun galmee yaalaa hin jijjiiru ykn hin dabalu."],
  "Hold resolved. Eligible release will run through the scheduled process.": ["እገዳው ተፈቷል። ብቁ መለቀቅ በታቀደው ሂደት ይከናወናል።", "Dhaabbannoon furameera. Gadhiifamuun ulaagaa guute adeemsa saganteeffameen raawwatama."],
  Requested: ["ተጠይቋል", "Gaafatameera"],
  Cancelled: ["ተሰርዟል", "Haqameera"],
  Released: ["ተለቋል", "Gadhiifameera"],
  Refunded: ["ተመላሽ ተደርጓል", "Deebi'eera"],
  LegacyHold: ["የቀድሞ ገቢ ታግዷል", "Galiin durii dhaabbateera"],
  Gross: ["ጠቅላላ", "Waliigala"],
  Fee: ["ክፍያ", "Kaffaltii"],
  Net: ["ቀሪ", "Haftee"],
  "No external transfer has occurred.": ["ውጫዊ የገንዘብ ማስተላለፍ አልተካሄደም።", "Dabarsi maallaqaa alaa hin raawwatamne."],
  Disputed: ["በክርክር ላይ", "Waldhabdee keessa jira"],
  "Patient’s dispute reason": ["የታካሚው የክርክር ምክንያት", "Sababa waldhabdee dhukkubsataa"],
  "Opened on": ["የተከፈተበት", "Yeroo baname"],
  "Payment concern": ["የክፍያ ጉዳይ", "Dhimma kaffaltii"],
  "Calendar edit mode": ["የቀን መቁጠሪያ ማስተካከያ ሁኔታ", "Haala gulaallii kalandarii"],
  "Recurring weekly": ["በየሳምንቱ የሚደገም", "Torban torbaniin irra deddeebi'u"],
  "This date only": ["በዚህ ቀን ብቻ", "Guyyaa kana qofa"],
  "Weekly availability": ["ሳምንታዊ የስራ ሰዓት", "Yeroo hojii torbanii"],
  "Edit weekly interval": ["ሳምንታዊ ሰዓትን ያስተካክሉ", "Yeroo torbanii gulaali"],
  "Close interval editor": ["የሰዓት ማስተካከያውን ዝጋ", "Gulaallii yeroo cufi"],
  "Repeats every week": ["በየሳምንቱ ይደገማል", "Torban torbaniin irra deddeebi'a"],
  "Interval starts": ["የሚጀምርበት ሰዓት", "Yeroo jalqabaa"],
  "Interval ends": ["የሚያበቃበት ሰዓት", "Yeroo xumuraa"],
  "Remove interval": ["ይህን ሰዓት አስወግድ", "Yeroo kana haqi"],
  "Copy availability to other days": ["የስራ ሰዓትን ወደ ሌሎች ቀናት ቅዳ", "Yeroo hojii gara guyyaa biraatti garagalchi"],
  "Choose a time to add a weekly interval.": ["ሳምንታዊ ሰዓት ለመጨመር ጊዜ ይምረጡ።", "Yeroo torbanii dabaluuf sa'aatii filadhu."],
  "Choose a time to prepare a date-specific replacement. Confirm it in Date exceptions before saving. Existing appointments remain unchanged.": ["ለተመረጠው ቀን የሚተካ ሰዓት ይምረጡ። ከማስቀመጥዎ በፊት በቀን ልዩነቶች ውስጥ ያረጋግጡ። ያሉ ቀጠሮዎች አይቀየሩም።", "Guyyaa filatameef yeroo bakka bu'u filadhu. Olkaa'uu dura addaddummaa guyyaa keessatti mirkaneessi. Beellamoonni jiran hin jijjiiraman."],
  "Time-field editor and keyboard alternative": ["የሰዓት መስኮች እና የቁልፍ ሰሌዳ አማራጭ", "Dirree sa'aatii fi filannoo kiiboordii"],
  "Date exceptions and breaks": ["የቀን ልዩነቶች እና እረፍቶች", "Addaddummaa guyyaa fi boqonnaa"],
  "Earnings activity": ["የገቢ እንቅስቃሴ", "Sochii galii"],
  "No earnings activity yet.": ["እስካሁን የገቢ እንቅስቃሴ የለም።", "Hanga ammaatti sochiin galii hin jiru."],
  "Consultation completed": ["ምክክሩ ተጠናቋል", "Mariin xumurameera"],
  "Earnings released": ["ገቢው ተለቋል", "Galiin gadhiifameera"],
  "Payout request cancelled": ["የክፍያ ጥያቄ ተሰርዟል", "Gaaffiin kaffaltii haqameera"],
  "Refund recorded": ["ተመላሽ ተመዝግቧል", "Deebiin galmaa'eera"],
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
