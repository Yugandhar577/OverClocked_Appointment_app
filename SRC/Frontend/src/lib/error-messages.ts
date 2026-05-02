const messages: Record<string, string> = {
  invalid_credentials: "Email or password is incorrect.",
  account_unverified: "Verify the account before logging in.",
  account_disabled: "Account disabled.",
  slot_unavailable: "Slot unavailable.",
  capacity_exceeded: "Selected capacity is no longer available.",
  cancel_window_closed: "Cancellation window closed.",
  reschedule_window_closed: "Reschedule window closed.",
  role_required: "You do not have access to this area.",
}

export function readableError(value: string) {
  return messages[value] ?? value.replaceAll("_", " ")
}
