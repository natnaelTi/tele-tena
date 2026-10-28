import {useEffect,useId,useRef,useState} from 'react';
import type {InputHTMLAttributes} from 'react';
import {getCountries,getCountryCallingCode,parsePhoneNumberFromString} from 'libphonenumber-js';
import type {CountryCode} from 'libphonenumber-js';
import {api} from '../api';
import {useLocale} from '../hooks/useLocale';
import {ChevronDown} from 'lucide-react';
import {CountryFlag} from './CountryFlag';
import {Button,Dialog,TextField} from './ui';
import './PhoneField.css';
export function PhoneField({label,error,onValueChange,...props}:Omit<InputHTMLAttributes<HTMLInputElement>,'onChange'>&{label:string;hint?:string;error?:string;onValueChange?:(value:string)=>void}){
 const id=useId(),{w,locale}=useLocale(),[country,setCountry]=useState<CountryCode>('ET'),[source,setSource]=useState(false),[open,setOpen]=useState(false),[search,setSearch]=useState(''),trigger=useRef<HTMLButtonElement|null>(null),touched=useRef(false);
 const [raw,setRaw]=useState(typeof props.value==='string'?props.value:'');
 useEffect(()=>{if(!props.value)setRaw('');},[props.value]);
 useEffect(()=>{let active=true;void api<{country:CountryCode|null;source:string|null}>('tele_tena.api.country.suggestion').then(value=>{if(active&&!touched.current&&!props.value&&value.country&&getCountries().includes(value.country)){setCountry(value.country);setSource(!!value.source);}}).catch(()=>{});return()=>{active=false;};},[]);
 const names=new Intl.DisplayNames([locale==='am'?'am':locale==='om'?'om':'en'],{type:'region'});
 const selected=(raw.startsWith('+')?parsePhoneNumberFromString(raw)?.country:null)||country;
 return <div className="field phone-field"><label htmlFor={props.id||id}>{label}{props.required&&<span className="required-marker" title="Required" aria-hidden="true"> *</span>}</label><div className="phone-entry">
  <Button variant="secondary" className="phone-country-trigger" aria-label={w('Country code')} aria-haspopup="dialog" aria-expanded={open} title={`${names.of(selected)||selected} +${getCountryCallingCode(selected)}`} disabled={props.disabled} onClick={event=>{trigger.current=event.currentTarget;setSearch('');setOpen(true);}}><CountryFlag country={selected}/><span>+{getCountryCallingCode(selected)}</span><ChevronDown size={14} aria-hidden="true"/></Button>
  <Dialog open={open} onOpenChange={value=>{setOpen(value);if(!value)requestAnimationFrame(()=>trigger.current?.focus());}} title={w('Choose a Country')} description={w('Search by country name or calling code. SMS sign-in currently supports Ethiopian mobile numbers only.')} className="country-picker-dialog"><TextField label={w('Search Countries')} type="search" placeholder={w('Country name or calling code')} value={search} onChange={e=>setSearch(e.target.value)} onKeyDown={e=>{if(e.key==='ArrowDown'){e.preventDefault();document.getElementById(id+'-country-options')?.querySelector<HTMLButtonElement>('button')?.focus();}}}/><ul className="country-picker-options" id={id+'-country-options'}>{getCountries().map(code=>({code,name:names.of(code)||code,calling:getCountryCallingCode(code)})).filter(c=>!search.trim()||[c.name,c.code,'+'+c.calling].some(v=>v.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()))).sort((a,b)=>a.name.localeCompare(b.name)).map(c=><li key={c.code}><Button variant="quiet" className="country-option" aria-pressed={selected===c.code} onClick={()=>{
   touched.current=true;setSource(false);const prefix='+'+getCountryCallingCode(selected);const national=raw.startsWith(prefix)?raw.slice(prefix.length):raw;
   setCountry(c.code);setRaw(national);onValueChange?.(national?'+'+c.calling+national.replace(/^0/,''):'');setOpen(false);requestAnimationFrame(()=>trigger.current?.focus());
  }}><CountryFlag country={c.code}/><span>{c.name}</span><span>+{c.calling}</span></Button></li>)}</ul>{!getCountries().some(code=>[names.of(code)||code,code,'+'+getCountryCallingCode(code)].some(value=>value.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())))&&<p role="status">{w('No Countries Found')}</p>}</Dialog>
  <input {...props} aria-label={props["aria-label"]||label} value={raw} id={props.id||id} type="tel" autoComplete="tel-national" inputMode="tel" placeholder={selected==='ET'?'09…':w('Phone number')} aria-invalid={!!error} aria-describedby={id+'-help'} onChange={event=>{
   touched.current=true;const next=event.target.value;setRaw(next);
   onValueChange?.(!next?'':next.startsWith('+')?next:next.startsWith('00')?'+'+next.slice(2):'+'+getCountryCallingCode(selected)+next.replace(/^0/,''));
  }}/></div>
  <p id={id+'-help'} className={error?'field-error':'supporting'}>{error||w('SMS sign-in currently supports Ethiopian mobile numbers. For other countries, use email.')}</p>
  {source&&<p className="supporting">{w('Country suggested from your connection. You can change it.')} <a href="https://db-ip.com" target="_blank" rel="noreferrer">IP Geolocation by DB-IP</a></p>}
 </div>;
}
