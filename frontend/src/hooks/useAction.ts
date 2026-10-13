import { useState } from "react";
import { ApiError } from "../api";
const messages: Record<string, string> = {
  credential_provenance_required: "Approval needs a license document attached to this scope, a verification source, check date and source reference. Request information if the document is missing.",
  credential_evidence_invalid: "Choose a License or registration document uploaded to this service application.",
  credential_verification_flag_required: "Clear the unfinished credential check before requesting information, or complete it and confirm verification after checking the source.",
  credential_check_date_invalid: "Enter a valid credential check date that is not in the future.",
  vetting_scores_incomplete: "Complete every assessment score and rationale before approving this scope.",
  vetting_mandatory_criterion_failed: "A mandatory assessment has not passed. Request information or decline; scores cannot replace required evidence.",
  catalog_not_approved: "The service definition needs medical-lead approval before a clinician can be approved for it.",
  credential_expired: "The credential has expired. Request current evidence before approval.",
  catalog_booking_rules_invalid: "Choose how appointments can be booked. Consultation, notes and summary requirements belong under Required platform workflows.",
  catalog_duration_range: "Set both session length limits, with the minimum no greater than the maximum.",
  catalog_date_range: "The end date must be on or after the effective date.",
  catalog_invalid_date: "Enter a valid effective date or leave the optional date empty.",
  scope_qualification_required: "Add your professional category, qualification and issuing institution before submission.",
  scope_adult_required: "Confirm that your service application is limited to adult care in the Relevant experience step.",
  scope_approach_invalid: "An approach is no longer available. In Relevant experience, move the unlisted entry to your training description before saving.",
  credential_date_invalid: "Enter a valid credential date.",
  resume_required: "Upload a PDF resume before submitting your application.",
  scope_not_open: "This service is not accepting applications. Your other choices are still here.",
  scope_selection_invalid: "Choose between one and ten different services.",
  scope_application_locked: "This application is awaiting review. Respond to a clarification request to change it.",
  credential_date_range: "The license expiry must be on or after its validity start date.",
  credential_not_current: "This credential is not valid yet and cannot authorize current practice.",
  catalog_requirements_missing: "Complete the professional, credential, consent and jurisdiction requirements before approval.",
  catalog_review_state: "Only a submitted draft definition can receive a clinical review decision.",
  catalog_workflow_unavailable: "This service requires a workflow outside the current adult MVP.",

  note_required: "Enter a consultation note or turn off note sharing.",
  summary_required: "Enter a patient summary before publishing.",
  consultation_close_pending: "Room closure is still pending. Return to the room and retry End for everyone before finalizing. Your draft can be saved.",
  documentation_not_ready: "End the consultation before saving or finalizing notes.",
  adult_required: "Confirm that you are 18 or older before continuing.",
  relationship_retry_changed: "This invitation submission changed. Start a new invitation.",
  relationship_invitation_rate_limited: "You have reached the invitation limit. Try again later.",
  relationship_invitation_expired: "This invitation has expired. Ask the person to send a new one.",
  relationship_invitation_unavailable: "This invitation is no longer available.",
  relationship_self_invite: "You cannot accept your own invitation.",
  relationship_decision_invalid: "Choose whether to accept or decline the invitation.",
  outside_availability:
    "Choose a time inside an available window, allowing for the full session.",
  appointment_conflict: "That time has just been booked. Choose another time.",
  insufficient_funds: "Your balance is too low for this session.",
  approval_required: "Approval is required before accepting bookings.",
  service_scope_required: "This service needs administrator approval.",
  invalid_availability_window:
    "Choose a future start time and an end within 24 hours.",
  availability_overlap: "This time overlaps an existing availability window.",
  schedule_start_invalid: "Enter a valid start time in hours and minutes.",
  schedule_end_invalid: "Enter a valid end time in hours and minutes.",
  schedule_interval_order: "Each end time must be after its start time.",
  schedule_interval_overlap: "Times on the same day cannot overlap.",
  schedule_times_required: "Add at least one available time before publishing.",
  schedule_timezone_invalid: "Choose a valid timezone, such as Africa/Addis_Ababa.",
  schedule_data_invalid: "Review the schedule times and date exceptions.",
  schedule_interval_invalid: "Check the start and end fields for each interval.",
  schedule_intervals_limit: "This schedule has too many intervals. Remove some times and save again.",
  schedule_exception_start_invalid: "Enter a valid exception start time.",
  schedule_exception_end_invalid: "Enter a valid exception end time.",
  schedule_exception_order: "An exception must end after it starts.",
  session_required: "Your session has expired. Sign in again before continuing.",
  permission_denied: "You don’t have permission to make this change.",
  preview_changed: "Your profile changed. Review your sharing choices again.",
  offering_changed:
    "The price or duration changed. Review this offering again.",
  request_active_limit: "Close an existing request before publishing another.",
  request_rate_limit: "Please wait before publishing another care request.",
  request_time_range_invalid: "Choose a future appointment window of up to 90 days.",
  request_languages_required: "Choose the languages you can provide care in first.",
  request_schedule_required: "Publish an approved service schedule before becoming available for requests.",
  request_presence_stale: "Your available-now status has expired. Turn it on again before offering.",
  request_eligibility_changed: "You are no longer eligible for this request. Review your approved services and care languages.",
  request_price_limit: "Your total quote is above the patient’s stated price limit.",
  request_offer_exists: "Withdraw your current offer before sending another.",
  request_offer_limit: "This request has reached its response limit.",
  request_offer_expired: "This offer is no longer available. Choose another offer or browse clinicians.",
  request_offer_changed: "The service or price changed. Ask for a new offer.",
  request_disclosure_changed: "Review the exact information that will be shared before accepting.",
  request_matched: "This request has already been matched.",
  request_retry_changed: "This retry differs from the request already sent. Start a new request to change it.",
  reschedule_unavailable: "This appointment can no longer be changed. Contact support if you need help.",
  reschedule_pending: "A time-change request is already waiting for a response.",
  reschedule_resolved: "This time-change request is no longer active.",
  reschedule_service_changed: "The booked service has changed and needs support review before rescheduling.",
  slot_unavailable: "That time is no longer available. Choose another time.",
};
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  async function run(action: () => Promise<unknown>, message = "Saved.") {
    if (busy) return;
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      await action();
      setSuccess(message);
    } catch (e) {
      setError(e instanceof ApiError && messages[e.code]
        ? messages[e.code]
        : e instanceof ApiError && e.status >= 500
          ? "The service is temporarily unavailable. Your changes are still here; try saving again."
          : e instanceof ApiError && e.status === 417
            ? "Some details need your attention. Review your inputs and try again."
            : "We couldn’t save this change. Check your connection and inputs, then try again.");
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, success, run };
}
