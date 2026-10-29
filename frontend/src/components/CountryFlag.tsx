import {Globe} from 'lucide-react';
import './CountryFlag.css';
// Local SVGs work even when the platform font renders emoji as country letters.
export function CountryFlag({country}:{country?:string|null}){return country&&/^[A-Za-z]{2}$/.test(country)?<img className="country-flag" src={(import.meta.env.PROD?'/assets/tele_tena/review':'')+'/flags/'+country.toLowerCase()+'.svg'} loading="lazy" decoding="async" alt="" aria-hidden="true" width="24" height="18"/>:<Globe className="country-flag" size={20} aria-hidden="true"/>;}
