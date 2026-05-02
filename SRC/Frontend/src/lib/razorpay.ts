import { verifyPayment } from "../api/payments"
import type { PaymentInitiateResponse } from "../api/types"
import { openRazorpayStandardCheckout } from "../paymentGateway/razorpayStandardCheckout"

export type CheckoutResult =
  | { ok: true; data: Awaited<ReturnType<typeof verifyPayment>> }
  | { ok: false; message: string }

export type OpenCheckoutOptions = {
  /** Selected tile on our gateway panel (maps to Razorpay behaviour). */
  selectedMethod?: string
  upiVpa?: string
}

/**
 * Opens Razorpay Standard Checkout (hosted modal) after server initiate.
 * For `mock_checkout`, callers should verify server-side without opening this.
 */
export async function openRazorpayCheckout(
  data: PaymentInitiateResponse,
  appointmentId: string,
  onUpdate: (msg: string) => void,
  options?: OpenCheckoutOptions,
): Promise<CheckoutResult> {
  if (data.mock_checkout) {
    return { ok: false, message: "Mock checkout: use server verify or Demo success on this page." }
  }

  const method = options?.selectedMethod ?? "upi_pay"
  const vpa = (options?.upiVpa ?? "").trim()
  const useUpiIntent = method === "upi_pay" && Boolean(vpa)

  return openRazorpayStandardCheckout({
    init: data,
    appointmentId,
    mode: useUpiIntent ? "upi_intent" : "all_methods",
    upiVpa: useUpiIntent ? vpa : undefined,
    onStatus: onUpdate,
  })
}
