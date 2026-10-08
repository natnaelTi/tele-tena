import { useState } from "react";
import { ApiError } from "../api";
const messages: Record<string, string> = {
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
  session_required: "Your session has expired. Sign in again to save this schedule.",
  permission_denied: "You don’t have permission to change this schedule.",
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
            ? "The schedule could not be saved. Review the time fields and schedule requirements."
            : "We couldn’t save this change. Check your connection and inputs, then try again.");
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, success, run };
}
