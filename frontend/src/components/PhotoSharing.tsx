import {useEffect,useState} from 'react';
import {api} from '../api';
import {Checkbox,Button,InlineNotice} from './ui';
import {useLocale} from '../hooks/useLocale';
export default function PhotoSharing(){
 const {w}=useLocale();const [value,setValue]=useState<boolean|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function load(){try{const r=await api<{share_photo:boolean}>('tele_tena.api.profile_photos.sharing');setValue(r.share_photo);setError('');}catch{setError('Photo sharing preferences could not be loaded.');}}
 useEffect(()=>{void load();},[]);
 return <section className="settings-section" onChange={event=>event.stopPropagation()}><h2>{w('Profile Photo Sharing')}</h2><p>{w('Share your current photo only with clinicians authorized to treat you in an appointment. It is not shown to other clinicians, partners or public visitors. A recognizable photo may identify you even when your name is masked.')}</p>{value===null?<p role="status">{w('Loading Preferences…')}</p>:<Checkbox variant="card" label={w('Share My Profile Photo With My Clinicians')} checked={value} disabled={busy} onChange={async event=>{const selected=event.target.checked;setBusy(true);setError('');try{const r=await api<{share_photo:boolean}>('tele_tena.api.profile_photos.set_sharing',{share_photo:selected?1:0},true);setValue(r.share_photo);}catch{setError('Your photo sharing preference could not be saved. Try again.');}finally{setBusy(false);}}}/>}<p className="supporting">{w('Changes apply to future photo requests, including existing appointments. Turning sharing off does not recall images already viewed or change historical disclosure records. Your name, history and individual file choices stay separate.')}</p>{busy&&<p role="status">{w('Saving…')}</p>}{error&&<InlineNotice tone="danger">{w(error)}{value===null&&<Button variant="secondary" onClick={()=>void load()}>{w('Retry')}</Button>}</InlineNotice>}</section>;
}
