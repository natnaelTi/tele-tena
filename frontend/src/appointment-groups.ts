import type { Appointment } from './journey-api';
/** Display grouping never changes server lifecycle or financial state. */
export function appointmentGroups(appointments: Appointment[], clinician: boolean, now: number) {
  const groups: Record<string, Appointment[]> = { 'Needs action': [], 'In progress': [], Upcoming: [], Past: [] };
  for (const item of appointments) {
    let group: string;
    if (['Completed', 'Cancelled', 'Expired', 'NoShow'].includes(item.state)) group = 'Past';
    else if (item.state === 'PendingConfirmation') group = 'Needs action';
    else if (item.call_state === 'Ended') group = clinician && item.documentation_state !== 'Finalized' ? 'Needs action' : 'Past';
    else if (item.call_state === 'Open') group = 'In progress';
    else if (item.state === 'Booked' && new Date(item.end).getTime() >= now) group = 'Upcoming';
    else group = 'Past';
    groups[group].push(item);
  }
  for (const [name, rows] of Object.entries(groups)) rows.sort((a, b) => name === 'Past' ? Date.parse(b.start) - Date.parse(a.start) : Date.parse(a.start) - Date.parse(b.start));
  return Object.entries(groups).filter(([, rows]) => rows.length);
}

export type AppointmentView = 'all' | 'upcoming' | 'attention' | 'completed' | 'cancelled';
/** Filters use persisted lifecycle states; elapsed bookings remain historical,
 * never become completed by a display calculation. */
export function appointmentsForView(appointments: Appointment[], view: AppointmentView, clinician: boolean, now: number) {
  return appointments.filter(item => {
    if (view === 'all') return true;
    if (view === 'completed') return item.state === 'Completed';
    if (view === 'cancelled') return item.state === 'Cancelled';
    if (view === 'attention') return item.state === 'PendingConfirmation' ||
      (clinician && item.state === 'Booked' && item.call_state === 'Ended' && item.documentation_state !== 'Finalized');
    return item.state === 'Booked' && item.call_state !== 'Ended' &&
      (item.call_state === 'Open' || Date.parse(item.end) >= now);
  });
}

/** Completed/cancelled reference views group real history by booked local month.
 * Different years stay separate; no clock calculation changes a lifecycle. */
export function appointmentDisplayGroups(appointments: Appointment[], view: AppointmentView, clinician: boolean, now: number, locale: string) {
  if (view !== 'completed' && view !== 'cancelled') return appointmentGroups(appointments, clinician, now);
  const months = new Map<string, Appointment[]>();
  for (const item of [...appointments].sort((a,b)=>Date.parse(b.start)-Date.parse(a.start))) {
    let label = 'Past';
    const instant = new Date(item.start);
    if (Number.isFinite(instant.getTime())) {
      try {
        label = new Intl.DateTimeFormat(locale, { month: 'long', year: 'numeric', timeZone: item.timezone || 'UTC' }).format(instant);
      } catch {
        // Historical invalid timezone cannot hide an otherwise authorized row.
        label = new Intl.DateTimeFormat(locale, { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(instant);
      }
    }
    const group = months.get(label) || [];
    group.push(item);
    months.set(label, group);
  }
  return [...months.entries()];
}
