import { useState } from "react";
import { ApiError } from "../api";
const messages: Record<string, string> = {
  outside_availability:
    "Choose a time inside an available window, allowing for the full session.",
  appointment_conflict: "That time has just been booked. Choose another time.",
  insufficient_funds: "Your simulated balance is too low for this session.",
  approval_required: "Approval is required before accepting bookings.",
  service_scope_required: "This service needs administrator approval.",
  invalid_availability_window:
    "Choose a future start time and an end within 24 hours.",
  availability_overlap: "This time overlaps an existing availability window.",
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
      setError(
        (e instanceof ApiError && messages[e.code]) ||
          "We couldn’t save this change. Check your connection and inputs, then try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, success, run };
}
