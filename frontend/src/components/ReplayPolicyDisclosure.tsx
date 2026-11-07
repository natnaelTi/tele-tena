import {Link} from 'react-router-dom';
import {useLocale} from '../hooks/useLocale';
export type ReplayDisclosure={version:string;review_only:boolean;terms_title:string;terms:string[];privacy_title:string;privacy:string[];guest_acceptance_available:boolean};
export function ReplayPolicyDisclosure({value,privacy=false}:{value:ReplayDisclosure;privacy?:boolean}){
 const{w}=useLocale();
 return <section id={privacy?"policy-replay-privacy":"policy-replay-terms"} className="policy-replay-disclosure" aria-label={w(privacy?value.privacy_title:value.terms_title)}>
 <h3>{w(privacy?value.privacy_title:value.terms_title)}</h3>
 {(privacy?value.privacy:value.terms).map(text=><p key={text}>{w(text)}</p>)}
 {!privacy&&<Link to="/policies#policy-replay-privacy" target="_blank" rel="noopener noreferrer">{w('Read Replay Provider and Retention Details in the Privacy Notice')}</Link>}
 <p className="supporting">{w('Review Draft')} · {value.version}</p>
 </section>;
}
