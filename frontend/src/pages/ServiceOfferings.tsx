import {useState} from 'react';
import {Link} from 'react-router-dom';
import {api} from '../api';
import {journeyApi} from '../journey-api';
import type {Schedule} from '../journey-api';
import {useLocale} from '../hooks/useLocale';
import {useResource} from '../hooks/useResource';
import {useAction} from '../hooks/useAction';
import {PageTitle,money} from '../components/Domain';
import {Button,Dialog,EmptyState,InlineNotice,Select,Skeleton,StatusBadge,TextField} from '../components/ui';
import './ServiceOfferings.css';
type Offering={id:string;service:string;label:string;title?:string;description?:string;price:number;minutes:number;active:number};
type Practice={offerings:Offering[];approved_services:{id:string;label:string}[];schedules:Schedule[]};
const load=()=>api<Practice>('practice');
export default function ServiceOfferings(){
  const {w}=useLocale();const current=useResource(load);const action=useAction();
  const [open,setOpen]=useState(false),[editing,setEditing]=useState<string>();
  const [scope,setScope]=useState(''),[title,setTitle]=useState(''),[description,setDescription]=useState(''),[price,setPrice]=useState(''),[duration,setDuration]=useState('30');
  const [retryKey,setRetryKey]=useState(()=>crypto.randomUUID());const [errors,setErrors]=useState<Record<string,string>>({});
  const scopes=current.data?.approved_services||[];
  const allowed=scopes.some(item=>item.id===scope);
  const priceValid=/^\d{1,7}(?:\.\d{1,2})?$/.test(price);
  const [whole,fraction='']=priceValid?price.split('.'):['0',''];
  const previewPrice=priceValid?Number(BigInt(whole)*100n+BigInt((fraction+'00').slice(0,2))):null;
  function edit(item?:Offering){setEditing(item?.id);setScope(item?.service||scopes[0]?.id||'');setTitle(item?.title||item?.label||'');setDescription(item?.description||'');setPrice(item?(item.price/100).toFixed(2):'');setDuration(String(item?.minutes||30));setRetryKey(crypto.randomUUID());setErrors({});setOpen(true);}
  function submit(){const fields:Record<string,string>={};if(!allowed)fields.scope=w('Choose a currently approved scope.');if(!title.trim())fields.title=w('Add a public title.');if(!priceValid||!previewPrice||previewPrice>100000000)fields.price=w('Enter a positive amount with at most two decimal places.');if(!/^\d+$/.test(duration)||Number(duration)<5||Number(duration)>240)fields.duration=w('Choose a duration from 5 to 240 minutes.');setErrors(fields);if(Object.keys(fields).length)return;
    void action.run(async()=>{await journeyApi.publish(scope,String(previewPrice),duration,title,description,retryKey,editing);await current.refresh();setOpen(false);},w('Offering saved. Publish availability to make it bookable.'));
  }
  function status(item:Offering){if(!scopes.some(scope=>scope.id===item.service))return 'Scope unavailable';if(!item.active)return 'Inactive';return current.data?.schedules.some(schedule=>schedule.offering===item.id&&schedule.status==='Published')?'Published':'Needs availability';}
  return <><PageTitle title={w('Services & pricing')} description={w('Create tailored offerings within your approved scopes.')} action={<Button disabled={!scopes.length||action.busy} onClick={()=>edit()}>{w('Create offering')}</Button>}/>
    {current.error?<InlineNotice tone="danger">{w('Your offerings could not be loaded.')} <Button variant="secondary" onClick={()=>void current.refresh()}>{w('Retry')}</Button></InlineNotice>:!current.data?<Skeleton/>:<>
      {current.data.offerings.length?<><div className="table-scroll offering-table"><table><thead><tr>{['Offering','Scope','Duration / fee','Status',''].map((label,index)=><th key={index}>{w(label)}</th>)}</tr></thead><tbody>{current.data.offerings.map(item=><tr key={item.id}><td><strong>{item.title||item.label}</strong>{item.description&&<p>{item.description}</p>}</td><td>{scopes.find(scope=>scope.id===item.service)?.label||w('Approval required')}</td><td>{item.minutes} {w('minutes')}<br/>ETB {money(item.price)}</td><td><StatusBadge>{w(status(item))}</StatusBadge></td><td><Button variant="quiet" onClick={()=>edit(item)}>{w('Edit offering')}</Button></td></tr>)}</tbody></table></div><div className="offering-mobile-list">{current.data.offerings.map(item=><article key={item.id}><header><h2>{item.title||item.label}</h2><StatusBadge>{w(status(item))}</StatusBadge></header>{item.description&&<p>{item.description}</p>}<p>{item.minutes} {w('minutes')} · ETB {money(item.price)}</p><Button variant="secondary" onClick={()=>edit(item)}>{w('Edit offering')}</Button></article>)}</div></>:<EmptyState title={w('No offerings yet.')}>{w('Create an offering after its service scope is approved.')}</EmptyState>}
      <section className="offering-scope-help"><h2>{w('Approved scopes')}</h2>{scopes.length?<p>{scopes.map(scope=>scope.label).join(' · ')}</p>:<p>{w('Each service needs its own human approval before publication.')}</p>}<Link className="text-link" to="/clinician/vetting">{w('View scope decisions')}</Link><Link className="text-link" to="/clinician/availability">{w('Set availability')}</Link></section>
    </>}
    {action.success&&<InlineNotice tone="success">{action.success}</InlineNotice>}
    <Dialog size="wide" open={open} onOpenChange={value=>{if(!action.busy)setOpen(value);}} className="offering-editor-dialog" title={w(editing?'Edit offering':'Create offering')} description={w('Patients should know exactly what they are booking.')}><div className="offering-editor-layout"><form onSubmit={event=>{event.preventDefault();submit();}}><h3>{w('Offering details')}</h3><Select label={w('Approved scope')} value={scope} disabled={Boolean(editing)||action.busy} onChange={event=>setScope(event.target.value)}>{!allowed&&<option value={scope}>{w('Approval required')}</option>}{scopes.map(scope=><option key={scope.id} value={scope.id}>{scope.label}</option>)}</Select>{errors.scope&&<InlineNotice tone="danger">{errors.scope}</InlineNotice>}<TextField label={w('Public title')} value={title} maxLength={160} error={errors.title} onChange={event=>setTitle(event.target.value)}/><label className="field">{w('What this session covers')}<textarea rows={4} maxLength={1000} value={description} onChange={event=>setDescription(event.target.value)}/></label><TextField label={w('Duration (minutes)')} inputMode="numeric" value={duration} error={errors.duration} onChange={event=>setDuration(event.target.value)}/><TextField label={w('Session price (ETB)')} inputMode="decimal" value={price} error={errors.price} onChange={event=>setPrice(event.target.value)}/><div className="actions"><Button type="button" variant="secondary" disabled={action.busy} onClick={()=>setOpen(false)}>{w('Cancel')}</Button><Button type="submit" loading={action.busy} disabled={!allowed}>{w('Save offering')}</Button></div>{action.error&&<InlineNotice tone="danger">{action.error}</InlineNotice>}</form><aside><h3>{w('Patient preview')}</h3><h2>{title||w('Public title')}</h2>{description&&<p className="prewrap">{description}</p>}<dl className="summary-list"><dt>{w('Approved scope')}</dt><dd>{scopes.find(item=>item.id===scope)?.label||w('Approval required')}</dd><dt>{w('Duration')}</dt><dd>{duration} {w('minutes')}</dd><dt>{w('Price')}</dt><dd>{previewPrice===null?w('Enter a price'): 'ETB '+money(previewPrice)}</dd></dl><p className="supporting">{w('Format, confirmation and booking rules come from your availability schedule. Saving an offering does not publish available times.')}</p></aside></div></Dialog>
  </>;
}
