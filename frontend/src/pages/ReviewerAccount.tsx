import {PageTitle} from '../components/Domain';
import ProfilePhoto from '../components/ProfilePhoto';
import {useLocale} from '../hooks/useLocale';
export default function ReviewerAccount(){const {w}=useLocale();return <><PageTitle title={w('Account')}/><ProfilePhoto/></>;}
