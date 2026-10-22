import {useId} from 'react';
import {useLocale} from '../hooks/useLocale';
import {Button} from './ui';
const definitions=['Training or introductory exposure','Practice with supervision','Independent practice within professional scope','Advanced practice with substantial relevant experience','Supervises or trains others within professional scope'];
export default function CompetencyRating({value,onChange}:{value:number;onChange:(value:number)=>void}){
 const id=useId(),{w}=useLocale();
 const describe=(level:number)=>`${level} — ${w(definitions[level-1])}`;
 return <fieldset className="competency-rating"><legend>{w('Your Self-Assessment')} <span className="required-marker" aria-hidden="true">*</span><span className="sr-only"> {w('Required')}</span></legend>
  <p id={id+'-description'} className="competency-rating-description" aria-live="polite">{value?describe(value):w('Choose a Level')}</p>
  <label className="sr-only" htmlFor={id}>{w('Your Self-Assessment')}</label>
  <input id={id} type="range" min={1} max={5} step={1} value={value||1} aria-valuetext={value?describe(value):w('Choose a Level')} aria-describedby={id+'-description'} onChange={e=>onChange(Number(e.target.value))} onPointerUp={e=>onChange(Number(e.currentTarget.value))} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onChange(Number(e.currentTarget.value));}}}/>
  <div className="competency-rating-levels" aria-label={w('Choose a Level')}>{definitions.map((_,i)=><Button key={i} variant={value===i+1?'primary':'quiet'} aria-label={describe(i+1)} aria-pressed={value===i+1} onClick={()=>onChange(i+1)}>{i+1}</Button>)}</div>
 </fieldset>;
}
