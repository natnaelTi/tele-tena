import {useLocale} from '../hooks/useLocale';
import type {Availability} from '../pages/PublicDirectory';
export function AvailabilityStatus({value}:{value?:Availability}){const {w}=useLocale();return <span className={'availability-radar '+(value?.available_now?'ready':'')} role="status"><i aria-hidden="true"/>{w(value?.available_now?'Available now':value?.state==='capacity_paused'?'Requests paused — No immediate opening':value?.state==='unpublished'?'No availability published':value?.has_booking_times?'By appointment':'No opening currently available')}</span>;}
