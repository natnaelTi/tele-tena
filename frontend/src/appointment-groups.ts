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
