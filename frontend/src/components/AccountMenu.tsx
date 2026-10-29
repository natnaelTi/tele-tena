import {useEffect,useId,useRef,useState} from 'react';
import {Link,useLocation} from 'react-router-dom';
import {ChevronDown,LogOut,Settings2} from 'lucide-react';
import {Avatar} from './ProfilePhoto';
import {useSession} from '../hooks/useSession';
import {useLocale} from '../hooks/useLocale';
import './WorkspaceControls.css';

export function AccountMenu({accountPath,onSignout,busy}:{accountPath:string;onSignout:()=>void;busy:boolean}){
 const {session}=useSession(),{w}=useLocale(),location=useLocation();
 const [open,setOpen]=useState(false),id=useId(),root=useRef<HTMLDivElement>(null),trigger=useRef<HTMLButtonElement>(null);
 const name=session?.profile?.display_name||session?.display_name||w('Your account');
 useEffect(()=>setOpen(false),[location.pathname]);
 useEffect(()=>{if(!open)return;const dismiss=(event:PointerEvent)=>{if(!root.current?.contains(event.target as Node))setOpen(false);};document.addEventListener('pointerdown',dismiss);return()=>document.removeEventListener('pointerdown',dismiss);},[open]);
 function close(){setOpen(false);trigger.current?.focus();}
 return <div className="account-menu" ref={root} onBlur={event=>{if(!event.currentTarget.contains(event.relatedTarget as Node))setOpen(false);}} onKeyDown={event=>{if(event.key==='Escape'&&open){event.preventDefault();event.stopPropagation();close();}if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){event.preventDefault();if(!open){setOpen(true);requestAnimationFrame(()=>root.current?.querySelector<HTMLElement>('.account-menu-panel a')?.focus());return;}const controls=[...root.current!.querySelectorAll<HTMLElement>('.account-menu-panel a,.account-menu-panel button')];const index=controls.indexOf(document.activeElement as HTMLElement);controls[event.key==='Home'?0:event.key==='End'?controls.length-1:(index+(event.key==='ArrowUp'?-1:1)+controls.length)%controls.length]?.focus();}}}>
 <button type="button" className="account-menu-trigger" data-tour={accountPath.startsWith('/patient')?'patient-account':accountPath.startsWith('/clinician')?'clinician-account':undefined} ref={trigger} aria-expanded={open} aria-controls={id} aria-label={w('Account menu')+': '+name} onClick={()=>setOpen(!open)}><Avatar url={session?.photo?.url} name={name}/><span>{name}</span><ChevronDown size={18} aria-hidden="true"/></button>
 {open&&<nav className="account-menu-panel" id={id} aria-label={w('Account menu')}><Link to={accountPath} aria-current={location.pathname.startsWith(accountPath)?"page":undefined} onClick={()=>setOpen(false)}><Settings2 size={20}/>{w('Account')}</Link>{(session?.user==='Administrator'||session?.roles.includes('Tele Tena Financial Configuration'))&&<Link to="/financial-configuration" onClick={()=>setOpen(false)}><Settings2 size={20}/>{w('Payment Mode')}</Link>}<button type="button" disabled={busy} aria-busy={busy||undefined} onClick={()=>{onSignout();}}><LogOut size={20}/>{w(busy?'Signing out…':'Sign out')}</button></nav>}
 </div>;
}
