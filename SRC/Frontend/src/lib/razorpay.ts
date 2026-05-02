import type { InitiatePaymentResponse } from "../api/payments"
import { verifyPayment } from "../api/payments"

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void; close?: () => void }
  }
}

let razorpayScriptPromise: Promise<void> | null = null

export function ensureRazorpayScript() {
  if (window.Razorpay) return Promise.resolve()
  if (razorpayScriptPromise) return razorpayScriptPromise
  razorpayScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script")
    script.src = "https://checkout.razorpay.com/v1/checkout.js"
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error("Unable to load Razorpay checkout script."))
    document.body.appendChild(script)
  })
  return razorpayScriptPromise
}

export type CheckoutResult =
  | { ok: true; data: Awaited<ReturnType<typeof verifyPayment>> }
  | { ok: false; message: string }

export async function openRazorpayCheckout(
  data: InitiatePaymentResponse,
  appointmentId: string,
  onUpdate: (message: string) => void,
) {
  await ensureRazorpayScript()
  const RazorpayConstructor = window.Razorpay
  if (!RazorpayConstructor) return { ok: false, message: "Razorpay script failed to load. Check your network." } satisfies CheckoutResult

  return new Promise<CheckoutResult>((resolve) => {
    let done = false
    const finish = (result: CheckoutResult) => {
      if (done) return
      done = true
      resolve(result)
    }

    const options: Record<string, unknown> = {
      key: data.key_id,
      amount: data.amount_paise,
      currency: data.currency,
      order_id: data.order_id,
      name: "Appointment booking",
      description: data.description,
      image: "https://razorpay.com/assets/razorpay-glyph.svg",
      prefill: {
        name: data.prefill_name ?? "Customer",
        email: data.customer_email ?? "customer@demo.local",
        contact: data.prefill_contact,
      },
      notes: { appointment_id: appointmentId },
      theme: { color: "#4f46e5" },
    }

    if (data.display_config && Object.keys(data.display_config).length > 0) {
      options.config = data.display_config
    }

    Object.assign(options, {
      handler: async (response: {
        razorpay_order_id: string
        razorpay_payment_id: string
        razorpay_signature: string
      }) => {
        onUpdate("Verifying payment on server...")
        try {
          const verified = await verifyPayment({
            appointment_id: appointmentId,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          })
          finish({ ok: true, data: verified })
        } catch (error) {
          finish({ ok: false, message: error instanceof Error ? error.message : String(error) })
        }
      },
      modal: {
        ondismiss: () => finish({ ok: false, message: "Checkout closed." }),
      },
    })

    try {
      const razorpay = new RazorpayConstructor(options)
      razorpay.open()
    } catch (error) {
      finish({ ok: false, message: error instanceof Error ? error.message : String(error) })
    }
  })
}
