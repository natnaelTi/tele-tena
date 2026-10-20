import {useId,useEffect,useRef} from 'react';
import {useLocale} from '../hooks/useLocale';

const scene=import.meta.env.BASE_URL+'public-experience/connected-practice-stage-v4.webp';
// Coordinates belong to the1448×1086 stage asset. SVG scaling keeps every overlay
// inside its screen at all responsive sizes. No live room, media or audio APIs.
const screens=[
 {key:'upper',points:'687,164 845,179 844,278 687,272',origin:'766px 260px',wave:'translate(815 190) rotate(5)'},
 {key:'left',points:'623,286 751,296 750,369 623,364',origin:'688px 357px',wave:'translate(721 303) rotate(5)'},
 {key:'right',points:'802,291 907,282 907,380 802,380',origin:'857px 370px',wave:'translate(877 299) rotate(-5)'},
 {key:'phone',points:'689,404 741,408 731,456 675,451',origin:'708px 444px',wave:'translate(724 414) rotate(9) scale(.4)'},
];
export default function ClinicianHeroScene(){
 const{w}=useLocale();const id=useId().replaceAll(':',''),ref=useRef<SVGSVGElement>(null);
 useEffect(()=>{ref.current?.querySelectorAll<SVGElement>('.scene-audio-bar').forEach((bar,index)=>{bar.style.setProperty('--bar-duration',`${.8+Math.random()*1.4}s`);bar.style.setProperty('--bar-delay',`${-Math.random()*3}s`);bar.style.setProperty('--bar-min',`${.15+(index%3)*.1}`);});},[]);
 return <div className="clinician-stage"><img src={scene} width="1448" height="1086" fetchPriority="high" alt={w('A clinician on a complete floating office stage, with a TeleTena phone consultation and illustrative patient screens.')}/>
 <svg ref={ref} viewBox="0 0 1448 1086" aria-hidden="true" className="scene-activity">
  <defs>{screens.map(screen=><clipPath key={screen.key} id={id+'-'+screen.key}><polygon points={screen.points}/></clipPath>)}<clipPath id={id+'-clinician'}><path d="M457 277 Q514 246 558 266 Q607 278 604 328 L585 370 L627 401 L657 462 L432 462 L447 403 L466 380 Q434 335 457 277Z"/></clipPath></defs>
  <g clipPath={'url(#'+id+'-clinician)'}><image href={scene} width="1448" height="1086" className="scene-person clinician-person" style={{transformOrigin:'526px 395px'}}/></g>
  {screens.map((screen,index)=><g key={screen.key} className={'scene-screen scene-screen-'+screen.key}>
   <g clipPath={'url(#'+id+'-'+screen.key+')'}><image href={scene} width="1448" height="1086" className="scene-person" style={{transformOrigin:screen.origin,animationDelay:`-${index*1.7}s`,animationDuration:`${5+index*1.3}s`}}/></g>
   <g transform={screen.wave} className="scene-waveform"><rect x="-3" y="-4" width="31" height="20" rx="5" fill="#123f48" opacity=".82"/>{[0,1,2,3,4].map(i=><rect key={i} x={i*5} y="0" width="2.4" height="12" rx="1.2" className="scene-audio-bar" fill="#a8f2e7"/>)}</g>
  </g>)}
  <g transform="translate(699 394) rotate(8)"><rect x="-3" y="-5" width="43" height="13" rx="4" fill="#123f48"/><text x="1" y="6" fill="#e8fbf8" fontFamily="Inter,sans-serif" fontSize="7" fontWeight="600">TeleTena</text></g>
 </svg></div>;
}
