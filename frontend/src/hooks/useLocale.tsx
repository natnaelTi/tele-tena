import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { locales } from "../i18n";
import type { Key } from "../i18n";
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
};
const Context = createContext<{
  locale: Locale;
  setLocale: (value: Locale) => void;
  t: (key: Key) => string;
  w: (english: string) => string;
} | null>(null);
export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("en");
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
