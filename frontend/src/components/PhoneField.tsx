import {useEffect,useId,useRef,useState} from 'react';
import type {InputHTMLAttributes} from 'react';
import {getCountries,getCountryCallingCode,parsePhoneNumberFromString} from 'libphonenumber-js';
import type {CountryCode} from 'libphonenumber-js';
import {api} from '../api';
import {useLocale} from '../hooks/useLocale';
import './PhoneField.css';
export function PhoneField({label,error,onValueChange,...props}:Omit<InputHTMLAttributes<HTMLInputElement>,'onChange'>&{label:string;hint?:string;error?:string;onValueChange?:(value:string)=>void}){
 const id=useId(),{w,locale}=useLocale(),[country,setCountry]=useState<CountryCode>('ET'),[source,setSource]=useState(false),touched=useRef(false);
 const [raw,setRaw]=useState(typeof props.value==='string'?props.value:'');
 useEffect(()=>{if(!props.value)setRaw('');},[props.value]);
 useEffect(()=>{let active=true;void api<{country:CountryCode|null;source:string|null}>('tele_tena.api.country.suggestion').then(value=>{if(active&&!touched.current&&!props.value&&value.country&&getCountries().includes(value.country)){setCountry(value.country);setSource(!!value.source);}}).catch(()=>{});return()=>{active=false;};},[]);
 const names=new Intl.DisplayNames([locale==='am'?'am':locale==='om'?'om':'en'],{type:'region'});
 const selected=(raw.startsWith('+')?parsePhoneNumberFromString(raw)?.country:null)||country;
 return <div className="field phone-field"><label htmlFor={props.id||id}>{label}</label><div className="phone-entry">
  <label className="sr-only" htmlFor={id+'-country'}>{w('Country code')}</label>
  <select id={id+'-country'} aria-label={w('Country code')} value={selected} disabled={props.disabled} onChange={event=>{
   touched.current=true;setSource(false);const next=event.target.value as CountryCode;
   const prefix='+'+getCountryCallingCode(selected);const national=raw.startsWith(prefix)?raw.slice(prefix.length):raw;
   setCountry(next);setRaw(national);onValueChange?.(national?'+'+getCountryCallingCode(next)+national.replace(/^0/,''):'');
  }}>{getCountries().map(code=><option key={code} value={code}>+{getCountryCallingCode(code)} · {names.of(code)||code}</option>)}</select>
  <input {...props} value={raw} id={props.id||id} type="tel" autoComplete="tel-national" inputMode="tel" placeholder={selected==='ET'?'09…':w('Phone number')} aria-invalid={!!error} aria-describedby={id+'-help'} onChange={event=>{
   touched.current=true;const next=event.target.value;setRaw(next);
   onValueChange?.(!next?'':next.startsWith('+')?next:next.startsWith('00')?'+'+next.slice(2):'+'+getCountryCallingCode(selected)+next.replace(/^0/,''));
  }}/></div>
  <p id={id+'-help'} className={error?'field-error':'supporting'}>{error||w('SMS sign-in currently supports Ethiopian mobile numbers. For other countries, use email.')}</p>
  {source&&<p className="supporting">{w('Country suggested from your connection. You can change it.')} <a href="https://db-ip.com" target="_blank" rel="noreferrer">IP Geolocation by DB-IP</a></p>}
 </div>;
}
