import './Homepage.css';
import {Navigate} from 'react-router-dom';
import {useSession,destination} from '../hooks/useSession';
import {Skeleton,InlineNotice,Button} from '../components/ui';
import {useLocale} from '../hooks/useLocale';
import PublicExperience from '../components/PublicExperience';
export default function Homepage(){
 const{session,loading,error,refresh}=useSession(),{w}=useLocale();
 if(loading)return <Skeleton/>;
 if(error)return <InlineNotice tone="danger">{w('Your session could not be checked. Try again.')} <Button onClick={()=>void refresh().catch(()=>undefined)}>{w('Try again')}</Button></InlineNotice>;
 if(session)return <Navigate to={destination(session)} replace/>;
 return <PublicExperience/>;
}
