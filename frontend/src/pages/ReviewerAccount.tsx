import PublicContentEditor from '../components/PublicContentEditor';
import {useSession} from '../hooks/useSession';
import {PageTitle} from '../components/Domain';
import ProfilePhoto from '../components/ProfilePhoto';
import {useLocale} from '../hooks/useLocale';
export default function ReviewerAccount(){const {w}=useLocale();const {session}=useSession();return <><PageTitle title={w('Account')}/><ProfilePhoto/>{session?.roles.includes("Tele Tena Approver")&&<PublicContentEditor/>}</>;}
