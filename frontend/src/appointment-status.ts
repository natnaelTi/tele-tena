/** Presentation only: elapsed time never mutates the persisted outcome. */
export function appointmentStatus(item: { state?: string; status?: string; call_state?: string | null; documentation_state?: string | null; end: string }, clinician: boolean, now = Date.now()) {
  const state = item.state || item.status;
  if (state === 'Completed') return { label: 'Completed', detail: '', tone: 'success' as const };
  if (state === 'Cancelled') return { label: 'Cancelled', detail: '', tone: 'neutral' as const };
  if (state === 'Expired') return { label: 'Expired', detail: '', tone: 'neutral' as const };
  if (state === 'NoShow') return { label: 'No-show recorded', detail: '', tone: 'warning' as const };
  if (state === 'PendingConfirmation') return { label: 'Needs confirmation', detail: '', tone: 'warning' as const };
  if (item.call_state === 'Ended') return { label: 'Call ended', detail: item.documentation_state === 'Finalized' ? '' : clinician ? 'Notes pending' : 'Summary being prepared', tone: 'neutral' as const };
  if (item.call_state === 'Open') return { label: 'In progress', detail: '', tone: 'success' as const };
  if (state === 'Booked') return new Date(item.end).getTime() < now
    ? { label: 'Outcome not recorded', detail: 'The scheduled time has passed.', tone: 'neutral' as const }
    : { label: 'Confirmed', detail: '', tone: 'neutral' as const };
  return { label: 'Status unavailable', detail: '', tone: 'neutral' as const };
}
