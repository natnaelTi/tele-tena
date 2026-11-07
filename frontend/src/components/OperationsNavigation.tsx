import {NavLink} from 'react-router-dom';
import {useLocale} from '../hooks/useLocale';
export function OperationsNavigation(){
 const{w}=useLocale();
 return <nav className="ops-tabs" aria-label={w('Operations Sections')}>
 {([['','Overview'],['insights','Journey Insights'],['health','System Health'],['archive','Replay Archive'],['reports','Quarterly Reports'],['settings','Operational Settings']] as const).map(([path,label])=><NavLink end key={path} to={'/admin/operations'+(path?'/'+path:'')} className={({isActive})=>isActive?'active':''}>{w(label)}</NavLink>)}
 <NavLink to="/admin/support" className={({isActive})=>isActive?'active':''}>{w('User Support')}</NavLink>
 </nav>;
}
