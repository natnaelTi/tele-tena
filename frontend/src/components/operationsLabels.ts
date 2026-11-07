// Application-owned event labels; never title-case user-authored content.
const labels: Record<string, string> = {
  "application.started": "Application Started",
  "application.resumed": "Application Resumed",
  "application.step_completed": "Application Step Completed",
  "application.saved": "Draft Saved",
  "application.submitted": "Professional Application Submitted",
  "application.scope_created": "Scope Application Created",
  "application.assistance_requested": "Assistance Requested",
  "application.clarification_opened": "Clarification Opened",
  "application.reply_started": "Clarification Reply Started",
  "application.resubmitted": "Additional Information Submitted",
  "application.professional_decision": "Professional Review Decision",
  "application.scope_decision": "Service Scope Decision",
  "application.language_decision": "Care Language Decision",
  "booking.offering_selected": "Offering Selected",
  "booking.auth_returned": "Authentication Return Completed",
  "booking.scheduling_attempted": "Scheduling Attempted",
  "booking.created": "Booking Created",
  "booking.confirmed": "Booking Confirmed",
  "booking.cancelled": "Booking Cancelled",
  "booking.expired": "Booking Expired",
  "payment.submitted": "Payment Claim Submitted",
  "payment.verified": "Payment Receipt Verified",
  "payment.followup": "Payment Follow-Up Requested",
  "request.draft_progressed": "Request Draft Progressed",
  "request.published": "Request Published",
  "request.offer_received": "Offer Received",
  "request.offer_accepted": "Offer Accepted",
  "request.offer_declined": "Offer Declined",
  "request.appointment_created": "Request Appointment Created",
  "request.consultation_handoff": "Consultation Handoff",
  "consultation.join_attempted": "Join Attempted",
  "consultation.join_authorized": "Join Authorized",
  "consultation.connected": "Connection Reported",
  "consultation.quality": "Connection Quality Reported",
  "consultation.connection_failed": "Connection Failed",
  "consultation.left": "Participant Left",
  "consultation.rejoined": "Participant Rejoined",
  "consultation.ended": "Clinician Ended Consultation",
  "consultation.documentation_completed": "Documentation Completed",
  "support.submitted": "Problem Report Submitted",
  "support.acknowledged": "Report Acknowledged",
  "support.triaged": "Report Triaged",
  "support.resolved": "Report Resolved",
  "upload.failed": "Upload Failed",
  "validation.failed": "Validation Failed",
};
export function eventLabel(name: string) {
  return labels[name] || name;
}

export function operationsTime(value: unknown) {
  if (!value) return "—";
  const raw = String(value).replace(" ", "T");
  const date = new Date(/(?:Z|[+-]\d\d:\d\d)$/.test(raw) ? raw : raw + "Z");
  return Number.isNaN(date.getTime())
    ? "—"
    : new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "Africa/Nairobi",
      }).format(date);
}
