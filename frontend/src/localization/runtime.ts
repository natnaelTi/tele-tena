import dictionary from './reviewed.json';
type Entry={english:string;source_hash:string;amharic?:string;afaan_oromo?:string};
const entries=Object.values(dictionary) as Entry[];
// Only the validated, reviewed import is bundled. Existing provisional fallbacks
// stay in use until a translator explicitly marks a row reviewed.
export function reviewedCopy(english:string,locale:string,key?:string):string|undefined {
 if(locale==='en')return english;
 const entry=key?(dictionary as Record<string,Entry>)[key]:entries.find(e=>e.english===english);
 if(!entry||entry.english!==english)return undefined;
 return locale==='am'?entry.amharic:locale==='om'?entry.afaan_oromo:undefined;
}
