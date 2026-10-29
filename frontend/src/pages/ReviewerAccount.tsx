import ReferencePriority from '../components/ReferencePriority';
import {Link} from 'react-router-dom';
import {usePaymentCapabilities} from '../components/DirectPayments';
import PublicContentEditor from '../components/PublicContentEditor';
import {useSession} from '../hooks/useSession';
import {PageTitle} from '../components/Domain';
import ProfilePhoto from '../components/ProfilePhoto';
import {useLocale} from '../hooks/useLocale';
export default function ReviewerAccount(){const {w}=useLocale();const {session}=useSession();const payment=usePaymentCapabilities();return <><PageTitle title={w('Account')}/><ProfilePhoto/>{payment.data?.can_configure&&<Link className="button secondary" to="/financial-configuration">{w("Payment Mode and Timing")}</Link>}{session?.roles.includes("Tele Tena Medical Lead")&&<ReferencePriority/>}{session?.roles.includes("Tele Tena Approver")&&<PublicContentEditor/>}</>;}
