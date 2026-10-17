/** Durable allowlisted navigation only. Health text/files never enter Web Storage. */
import {discoveryFilters} from './care-intent';
type Language='en'|'am'|'om';type Format='audio'|'video';
export type ReturnIntent={kind:'offering';ref:string;language?:Language;format?:Format}|{kind:'request';ref?:string};
const key='teletena-return-v1',uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
let memory:ReturnIntent|null=null;
function clean(value:any):ReturnIntent|null{if(value?.kind==='request')return{kind:'request',...(uuid.test(value.ref||'')?{ref:value.ref}:{})};if(value?.kind==='offering'&&uuid.test(value.ref))return{kind:'offering',ref:value.ref,...(['en','am','om'].includes(value.language)?{language:value.language}:{}),...(['audio','video'].includes(value.format)?{format:value.format}:{})};return null;}
export function returnIntent():ReturnIntent|null{try{return clean(JSON.parse(sessionStorage.getItem(key)||'null'))||memory;}catch{return memory;}}
export function rememberReturn(value:ReturnIntent){const filters=discoveryFilters(),prior=returnIntent();memory=clean(value.kind==='offering'?{...value,language:value.language||filters.language||(prior?.kind==='offering'&&prior.ref===value.ref?prior.language:''),format:value.format||filters.format||(prior?.kind==='offering'&&prior.ref===value.ref?prior.format:'')}:value);try{if(memory)sessionStorage.setItem(key,JSON.stringify(memory));}catch{/* Memory-only fallback;no clinical data is persisted. */}}
export function clearReturn(){memory=null;try{sessionStorage.removeItem(key);}catch{}}
export function returnPath(){const value=returnIntent();return value?.kind==='offering'?'/patient/book/'+value.ref:value?.kind==='request'?'/patient/requests'+(value.ref?'/'+value.ref:''):'';}
export type RequestDraft={request_text:string;service?:string;service_label?:string;language?:string;format?:Format;urgency?:'immediate'|'scheduled'};
let draft:RequestDraft|null=null;
export function rememberGuestDraft(value:RequestDraft){draft={...value,request_text:value.request_text.slice(0,2000)};}
export function guestDraft(){return draft;}
export function discardGuestDraft(){draft=null;clearReturn();}
export function clearGuestDraft(){draft=null;}
