import PhotoCropDialog, {type PhotoDraft} from './PhotoCropDialog';
import {FileUpload} from "./FileUpload";
import {useEffect, useState,type ReactNode} from 'react';
import {api, ApiError} from '../api';
import {useSession} from '../hooks/useSession';
import {useLocale} from '../hooks/useLocale';
import {Button, Checkbox, InlineNotice} from './ui';
import './ProfilePhoto.css';

type Photo = {url:string|null; published:boolean; can_publish:boolean};
export function Avatar({url,name,className=''}:{url?:string|null;name:string;className?:string}) {
  const [image,setImage]=useState<string|null>(null);
  useEffect(()=>{let active=true,current:string|null=null,loading=false;const abort=new AbortController();setImage(null);
    async function load(){if(loading||!url||!url.startsWith('/api/method/tele_tena.'))return;loading=true;try{const r=await fetch(url,{credentials:'same-origin',cache:'no-store',signal:abort.signal});if(!r.ok||!r.headers.get('Content-Type')?.startsWith('image/'))throw Error();const blob=await r.blob();if(!active)return;const next=URL.createObjectURL(blob);if(current)URL.revokeObjectURL(current);current=next;setImage(next);}catch{if(active){if(current)URL.revokeObjectURL(current);current=null;setImage(null);}}finally{loading=false;}}
    void load();const timer=window.setInterval(()=>{if(document.visibilityState==='visible')void load();},30000);const refresh=()=>{if(document.visibilityState==='visible')void load();};document.addEventListener('visibilitychange',refresh);
    return()=>{active=false;abort.abort();clearInterval(timer);document.removeEventListener('visibilitychange',refresh);if(current)URL.revokeObjectURL(current);};
  },[url]);
  return <span className={'avatar profile-avatar '+className} aria-hidden="true">{image?<img src={image} alt="" onError={()=>setImage(null)}/>:Array.from(name||'?')[0]}</span>;
}
/** An encounter-authorized name and its current permitted photo form one identity. */
export function IdentityName({url,name,children}:{url?:string|null;name:string;children?:ReactNode}){
 return <span className="identity-with-avatar"><span className="identity-name">{children||name}</span><Avatar url={url} name={name}/></span>;
}
export default function ProfilePhoto() {
  const {session,refresh}=useSession(); const {w}=useLocale();
  const [photo,setPhoto]=useState<Photo|null>(null);const [published,setPublished]=useState(false);
  const [draft,setDraft]=useState<PhotoDraft|null>(null);
  useEffect(()=>()=>{if(draft)URL.revokeObjectURL(draft.url);},[draft]);
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [success,setSuccess]=useState('');
  async function load(){try{const result=await api<Photo>('tele_tena.api.profile_photos.status');setPhoto(result);setPublished(result.published);setError('');}catch{setError('Your photo could not be loaded. Try again.');}}
  useEffect(()=>{void load();},[]);
  return <section className="settings-section profile-photo-editor" onChange={event=>event.stopPropagation()}><div><h2>{w('Profile Picture')}</h2><p>{w('JPEG, PNG or WebP. Up to 3 MB.')}</p></div><div className="profile-photo-controls"><Avatar url={photo?.url} name={session?.profile?.display_name||session?.user||''}/><div>{!photo&&<Button variant="secondary" onClick={()=>void load()}>{w('Try again')}</Button>}{photo&&<><div className="field"><FileUpload label={w('Profile Picture')} description={w('JPEG, PNG or WebP. Up to 3 MB.')} actionLabel={w('Select Photo')} accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" disabled={busy} compact onFiles={async files=>{const file=files[0];if(!file)return;setSuccess('');setError('');if(file.size>3*1024*1024||!['image/jpeg','image/png','image/webp'].includes(file.type)){setError('Choose a valid image up to 3 MB.');return;}const url=URL.createObjectURL(file);const image=new Image();try{image.src=url;await image.decode();if(Math.min(image.naturalWidth,image.naturalHeight)<32||Math.max(image.naturalWidth,image.naturalHeight)>4096||image.naturalWidth*image.naturalHeight>16000000)throw new Error();setDraft({url,image});}catch{URL.revokeObjectURL(url);setError('Choose a valid, non-animated JPEG, PNG or WebP image up to 3 MB and 4096 pixels.');}}}/></div>{photo.url&&<Button variant="quiet" disabled={busy} onClick={async()=>{setBusy(true);setError('');setSuccess('');try{const result=await api<Photo>('tele_tena.api.profile_photos.remove',{},true);setPhoto({...photo,...result});setPublished(false);await refresh();setSuccess('Profile picture removed.');}catch{setError('Your photo could not be saved. Try again.');}finally{setBusy(false);}}}>{w('Remove photo')}</Button>}</>}</div></div>{photo?.can_publish?<Checkbox label={w('Show this photo on my approved clinician profile')} checked={published} disabled={busy} onChange={async event=>{const value=event.target.checked;setPublished(value);if(!photo.url)return;setBusy(true);setError('');setSuccess('');try{const result=await api<Photo>('tele_tena.api.profile_photos.set_visibility',{published:value?1:0},true);setPhoto({...photo,...result});await refresh();setSuccess('Photo visibility saved.');}catch{setPublished(photo.published);setError('Your photo could not be saved. Try again.');}finally{setBusy(false);}}}/>:<p className="supporting">{w(session?.profile?.kind==='patient'?'Your photo stays private outside authorized care. Manage sharing with your treating clinicians under Privacy & Sharing.':'Only you can see your photo.')}</p>}{photo?.can_publish&&<p className="supporting">{w('A public photo is visible only while your clinician profile is eligible for discovery.')}</p>}{draft&&<PhotoCropDialog draft={draft} busy={busy} error={error} onCancel={()=>{setDraft(null);setError('');}} onSave={async content=>{if(busy)return;setBusy(true);setError('');try{const result=await api<Photo>('tele_tena.api.profile_photos.upload',{filename:'profile.jpg',content_base64:content,published:published?1:0},true);setPhoto({...photo,...result} as Photo);await refresh();setDraft(null);setSuccess('Profile picture saved.');}catch(e){setError(e instanceof ApiError&&e.code==='photo_invalid'?'Choose a valid image up to 3 MB.':'Your photo could not be saved. Try again.');}finally{setBusy(false);}}}/>} {busy&&<p role="status">{w('Saving photo…')}</p>}{error&&<InlineNotice tone="danger">{w(error)}</InlineNotice>}{success&&<InlineNotice tone="success">{w(success)}</InlineNotice>}</section>;
}
