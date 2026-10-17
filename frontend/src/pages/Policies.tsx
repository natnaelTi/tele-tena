import {useEffect,useState} from 'react';
import {api} from '../api';
import {Card,InlineNotice} from '../components/ui';
export default function Policies(){const [policy,setPolicy]=useState<any>(null);useEffect(()=>{void api('tele_tena.api.policies.current').then(setPolicy);},[]);return <main className="guided-panel"><h1>Terms & Privacy — review environment</h1><InlineNotice>Approved production policy content is pending review. This page does not claim legal approval or compliance.</InlineNotice>{policy&&<Card><h2>Current review versions</h2><p>{policy.terms_version} · {policy.privacy_version}</p><p>{policy.notice}</p><h2>Encounter sharing</h2><p>{policy.sharing_notice}</p></Card>}</main>;}
