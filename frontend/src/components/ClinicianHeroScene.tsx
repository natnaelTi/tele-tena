import {useId,useEffect,useRef} from 'react';
import {useLocale} from '../hooks/useLocale';

const scene=import.meta.env.BASE_URL+'public-experience/connected-practice-stage-v3.webp';
// Coordinates belong to the1536×1024 stage asset. SVG scaling keeps every overlay
// inside its screen at all responsive sizes. No live room, media or audio APIs.
const screens=[
 {key:'upper',points:'776,132 958,147 958,266 775,255',origin:'864px 248px',wave:'translate(922 158) rotate(5)'},
 {key:'left',points:'689,271 844,287 843,370 688,358',origin:'772px 354px',wave:'translate(811 295) rotate(5)'},
 {key:'right',points:'910,279 1034,268 1033,384 910,383',origin:'968px 374px',wave:'translate(1004 285) rotate(-4)'},
 {key:'phone',points:'764,418 819,422 805,483 746,477',origin:'784px 470px',wave:'translate(801 427) rotate(9) scale(.42)'},
];
export default function ClinicianHeroScene(){
 const{w}=useLocale();const id=useId().replaceAll(':',''),ref=useRef<SVGSVGElement>(null);
 useEffect(()=>{ref.current?.querySelectorAll<SVGElement>('.scene-audio-bar').forEach((bar,index)=>{bar.style.setProperty('--bar-duration',`${.8+Math.random()*1.4}s`);bar.style.setProperty('--bar-delay',`${-Math.random()*3}s`);bar.style.setProperty('--bar-min',`${.15+(index%3)*.1}`);});},[]);
 return <div className="clinician-stage"><img src={scene} width="1536" height="1024" fetchPriority="high" alt={w('A clinician on a complete floating office stage, with a TeleTena phone consultation and illustrative patient screens.')}/>
 <svg ref={ref} viewBox="0 0 1536 1024" aria-hidden="true" className="scene-activity">
  <defs>{screens.map(screen=><clipPath key={screen.key} id={id+'-'+screen.key}><polygon points={screen.points}/></clipPath>)}<clipPath id={id+'-clinician'}><path d="M434 245 Q508 206 579 238 Q647 265 635 327 L620 367 L679 411 L711 471 L419 474 L438 408 L463 377 Q419 328 434 245Z"/></clipPath></defs>
  <g clipPath={'url(#'+id+'-clinician)'}><image href={scene} width="1536" height="1024" className="scene-person clinician-person" style={{transformOrigin:'545px 405px'}}/></g>
  {screens.map((screen,index)=><g key={screen.key} className={'scene-screen scene-screen-'+screen.key}>
   <g clipPath={'url(#'+id+'-'+screen.key+')'}><image href={scene} width="1536" height="1024" className="scene-person" style={{transformOrigin:screen.origin,animationDelay:`-${index*1.7}s`,animationDuration:`${5+index*1.3}s`}}/></g>
   <g transform={screen.wave} className="scene-waveform"><rect x="-3" y="-4" width="31" height="20" rx="5" fill="#123f48" opacity=".82"/>{[0,1,2,3,4].map(i=><rect key={i} x={i*5} y="0" width="2.4" height="12" rx="1.2" className="scene-audio-bar" fill="#a8f2e7"/>)}</g>
  </g>)}
  <g transform="translate(766 403) rotate(8)"><rect x="-3" y="-5" width="61" height="16" rx="4" fill="#123f48"/><text x="1" y="6" fill="#e8fbf8" fontFamily="Inter,sans-serif" fontSize="9" fontWeight="600">TeleTena</text></g>
 </svg></div>;
}
