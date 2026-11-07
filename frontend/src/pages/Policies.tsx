import{useLocation}from'react-router-dom';
import{ReplayPolicyDisclosure}from'../components/ReplayPolicyDisclosure';
import {PolicyText,type PublicDocument} from '../components/PublicContentEditor';
import {useEffect,useState} from 'react';
import {useLocale} from '../hooks/useLocale';
import {api} from '../api';
import {Button,Card,InlineNotice} from '../components/ui';
export default function Policies(){
 const{w,locale}=useLocale();const{hash}=useLocation();const[error,setError]=useState(false),[policy,setPolicy]=useState<any>(null),[retry,setRetry]=useState(0);
 useEffect(()=>{let current=true;setError(false);void api('tele_tena.api.policies.current',{locale}).then(value=>{if(current)setPolicy(value);}).catch(()=>{if(current)setError(true);});return()=>{current=false;};},[retry,locale]);
 useEffect(()=>{if(policy&&hash.startsWith('#policy-'))document.getElementById(hash.slice(1))?.scrollIntoView();},[policy,hash]);
 return <main className="public-policy-page"><p className="eyebrow">{w('Your privacy and choices')}</p><h1>{w('Terms & Privacy')}</h1><InlineNotice>{w('Approved production policy content is pending review. This page does not claim legal approval or compliance.')}</InlineNotice>{error?<InlineNotice tone="danger">{w('Policy versions could not be loaded. Reload to try again.')} <Button variant="quiet" onClick={()=>setRetry(x=>x+1)}>{w('Try again')}</Button></InlineNotice>:!policy?<p role="status">{w('Loading review policy versions…')}</p>:null}{policy&&<Card><h2>{w('Current Review Versions')}</h2><p>{policy.terms_version} · {policy.privacy_version}</p><p>{w(policy.notice)}</p><h2>{w('Encounter Sharing')}</h2><p>{w(policy.sharing_notice)}</p></Card>}{policy?.documents&&<div className="public-policy-library"><nav aria-label={w('Policy Documents')}>{policy.documents.map((doc:PublicDocument)=><a key={doc.key} href={'#policy-'+doc.key}>{doc.title}</a>)}</nav>{policy.documents.map((doc:PublicDocument)=><article key={doc.key} id={'policy-'+doc.key} className="public-policy-document"><h2>{doc.title}</h2><p className="policy-version">{w('Review Draft')} · {doc.key==='terms'?policy.terms_version:doc.key==='privacy'?policy.privacy_version:doc.version}</p><PolicyText body={doc.body}/>{policy.replay_disclosure&&['terms','privacy'].includes(doc.key)&&<ReplayPolicyDisclosure value={policy.replay_disclosure} privacy={doc.key==='privacy'}/>}</article>)}</div>}</main>;
}
