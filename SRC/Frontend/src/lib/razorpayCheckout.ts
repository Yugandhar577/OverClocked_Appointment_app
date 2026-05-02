import { verifyPayment } from "../api/payments"
import type { PaymentInitiateResponse } from "../api/types"

/** Matches `--odoo-primary` in `src/styles/theme.css` */
const RAZORPAY_CHECKOUT_ACCENT = "#714b67"

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void }
  }
}

let razorpayScriptPromise: Promise<void> | null = null

export function loadRazorpayScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.reject(new Error("No window"))
  if (window.Razorpay) return Promise.resolve()
  if (!razorpayScriptPromise) {
    razorpayScriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script")
      script.src = "https://checkout.razorpay.com/v1/checkout.js"
      script.async = true
      script.onload = () => resolve()
      script.onerror = () => reject(new Error("Failed to load Razorpay checkout script."))
      document.body.appendChild(script)
    })
  }
  return razorpayScriptPromise
}

export type CheckoutResult =
  | { ok: true; data: Awaited<ReturnType<typeof verifyPayment>> }
  | { ok: false; message: string }

export async function openRazorpayCheckout(
  data: PaymentInitiateResponse,
  appointmentId: string,
  onUpdate: (msg: string) => void,
): Promise<CheckoutResult> {
  await loadRazorpayScript()

  return new Promise((resolve) => {
    if (!window.Razorpay) {
      resolve({ ok: false, message: "Razorpay script failed to load. Check your network." })
      return
    }

    let settled = false
    const finish = (result: CheckoutResult) => {
      if (settled) return
      settled = true
      resolve(result)
    }

    // Docs use amount as a string in subunits; `order_id` ties to the server order (must be same key/account).
    const options: Record<string, unknown> = {
      key: data.key_id,
      amount: String(data.amount_paise),
      currency: data.currency,
      order_id: data.order_id,
      name: "OverClocked",
      description: data.description,
      image: "https://razorpay.com/assets/razorpay-glyph.svg",
      prefill: {
        name: (data.prefill_name ?? "Customer").trim() || "Customer",
        email: (data.customer_email ?? "").trim() || "test.customer@example.com",
        contact: (data.prefill_contact ?? "").trim() || "+919999999999",
      },
      notes: { appointment_id: appointmentId },
      theme: { color: RAZORPAY_CHECKOUT_ACCENT },
    }

    if (data.display_config && Object.keys(data.display_config).length > 0) {
      options.config = data.display_config
    }

    Object.assign(options, {
      handler: async (response: {
        razorpay_payment_id: string
        razorpay_order_id: string
        razorpay_signature: string
      }) => {
        onUpdate("Verifying payment on server…")
        try {
          const verified = await verifyPayment({
            appointment_id: appointmentId,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          })
          finish({ ok: true, data: verified })
        } catch (e) {
          finish({ ok: false, message: e instanceof Error ? e.message : String(e) })
        }
      },
      modal: {
        ondismiss: () => {
          finish({ ok: false, message: "Checkout closed." })
        },
      },
    })

    try {
      const rzp = new window.Razorpay(options)
      rzp.open()
    } catch (e) {
      finish({ ok: false, message: e instanceof Error ? e.message : String(e) })
    }
  })
}
