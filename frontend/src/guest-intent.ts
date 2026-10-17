/** Only opaque navigation intent is durable; clinical draft text stays in memory. */
export type ReturnIntent = {kind:'offering';ref:string}|{kind:'request'};
const key='teletena-return-v1';
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
export function rememberReturn(value:ReturnIntent){if(value.kind==='request'||value.kind==='offering'&&uuid.test(value.ref))sessionStorage.setItem(key,JSON.stringify(value));}
export function returnIntent():ReturnIntent|null{try{const value=JSON.parse(sessionStorage.getItem(key)||'null');return value?.kind==='request'?{kind:'request'}:value?.kind==='offering'&&uuid.test(value.ref)?{kind:'offering',ref:value.ref}:null;}catch{return null;}}
export function clearReturn(){sessionStorage.removeItem(key);}
export function returnPath(){const value=returnIntent();return value?.kind==='offering'?'/patient/book/'+value.ref:value?.kind==='request'?'/patient/requests':'';}
export type RequestDraft={request_text:string;service?:string;service_label?:string;language?:string;format?:'video'|'audio';urgency?:'immediate'|'scheduled'};
let draft:RequestDraft|null=null;
export function rememberGuestDraft(value:RequestDraft){draft={...value,request_text:value.request_text.slice(0,2000)};}
export function guestDraft(){return draft;}
export function discardGuestDraft(){draft=null;clearReturn();}
