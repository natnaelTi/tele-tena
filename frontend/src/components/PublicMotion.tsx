import {useEffect,useRef,useState} from 'react';
import {useLocation} from 'react-router-dom';
import {Stethoscope} from 'lucide-react';

/** A decorative, bounded transition. Never intercepts input or waits on an API. */
export function PublicMotion(){
 const {pathname}=useLocation(),first=useRef(true),[phase,setPhase]=useState<'intro'|'route'|null>('intro');
 const target=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  const intro=first.current;first.current=false;setPhase(intro?'intro':'route');
  const frame=requestAnimationFrame(()=>{const mark=document.querySelector('.hero-brand .brand img, .public-header .brand img');if(mark&&target.current){const r=mark.getBoundingClientRect();target.current.style.setProperty('--mark-x',`${r.left+r.width/2-innerWidth/2}px`);target.current.style.setProperty('--mark-y',`${r.top+r.height/2-innerHeight/2}px`);}});
  const timer=window.setTimeout(()=>setPhase(null),intro?800:420);
  return()=>{cancelAnimationFrame(frame);clearTimeout(timer);};
 },[pathname]);
 return phase?<div className={'public-transition '+phase} aria-hidden="true" ref={target}><div className="transition-mark"><Stethoscope size={68} strokeWidth={1.6}/></div></div>:null;
}

/** Progressive enhancement: content is visible even if observation fails. */
export function usePublicReveals(key:string){
 useEffect(()=>{
  if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const elements=document.querySelectorAll<HTMLElement>('.public-experience .public-section, .public-info-page .tour-workspace');
  if(!('IntersectionObserver' in window))return;
  const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{entry.target.classList.toggle('is-in-view',entry.isIntersecting);}),{threshold:.06});
  elements.forEach(el=>{el.classList.add('motion-section');observer.observe(el);});
  return()=>{observer.disconnect();elements.forEach(el=>el.classList.remove('motion-section','is-in-view'));};
 },[key]);
}
