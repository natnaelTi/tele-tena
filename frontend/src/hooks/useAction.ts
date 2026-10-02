import { useState } from "react";
import { ApiError } from "../api";
const messages: Record<string, string> = {
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
