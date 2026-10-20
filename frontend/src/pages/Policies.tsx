import {useEffect,useState} from 'react';
import {useLocale} from '../hooks/useLocale';
import {api} from '../api';
import {Card,InlineNotice} from '../components/ui';
export default function Policies(){
 const {w}=useLocale();
 const [error,setError]=useState(false),[policy,setPolicy]=useState<any>(null);
 useEffect(()=>{void api('tele_tena.api.policies.current').then(setPolicy).catch(()=>setError(true));},[]);
 return <main className="guided-panel">
  <h1>{w('Terms & Privacy — review environment')}</h1>
  <InlineNotice>{w('Approved production policy content is pending review. This page does not claim legal approval or compliance.')}</InlineNotice>
  {error&&<p role="alert">{w('Policy versions could not be loaded. Reload to try again.')}</p>}
  {policy&&<Card><h2>{w('Current review versions')}</h2><p>{policy.terms_version} · {policy.privacy_version}</p><p>{w(policy.notice)}</p><h2>{w('Encounter sharing')}</h2><p>{w(policy.sharing_notice)}</p></Card>}
 </main>;
}
