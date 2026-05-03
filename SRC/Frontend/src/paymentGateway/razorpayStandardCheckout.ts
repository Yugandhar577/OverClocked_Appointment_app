/**
 * Razorpay Standard Checkout — Orders API + server verify.
 * Integer `amount`, E.164 `prefill.contact`; omit `config` unless API sends display_config (keeps full UPI/Card/Netbanking/Wallet UI).
 */
import { verifyPayment } from "../api/payments"
import type { PaymentInitiateResponse } from "../api/types"

const CHECKOUT_SCRIPT = "https://checkout.razorpay.com/v1/checkout.js"
const THEME_COLOR = "#714b67"

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => RazorpayCheckoutInstance
  }
}

let scriptPromise: Promise<void> | null = null

interface RazorpayCheckoutInstance {
  open: () => void
  close?: () => void
  on?: (event: "payment.failed", handler: (response: RazorpayPaymentFailedResponse) => void) => void
}

interface RazorpayPaymentFailedResponse {
  error?: {
    code?: string
    description?: string
    reason?: string
    source?: string
    step?: string
  }
}

export function loadRazorpayCheckoutScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.reject(new Error("No window"))
  if (window.Razorpay) return Promise.resolve()
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script")
      script.src = CHECKOUT_SCRIPT
      script.async = true
      script.onload = () => resolve()
      script.onerror = () => reject(new Error("Failed to load Razorpay checkout script."))
      document.body.appendChild(script)
    })
  }
  return scriptPromise
}

export type StandardCheckoutResult =
  | { ok: true; data: Awaited<ReturnType<typeof verifyPayment>> }
  | { ok: false; message: string }

export type StandardCheckoutMode = "all_methods" | "upi_intent"

export type OpenStandardCheckoutParams = {
  init: PaymentInitiateResponse
  appointmentId: string
  mode: StandardCheckoutMode
  upiVpa?: string
  onStatus: (message: string) => void
}

export async function openRazorpayStandardCheckout(params: OpenStandardCheckoutParams): Promise<StandardCheckoutResult> {
  const { init, appointmentId, mode, onStatus } = params
  await loadRazorpayCheckoutScript()

  return new Promise((resolve) => {
    if (!window.Razorpay) {
      resolve({ ok: false, message: "Razorpay script failed to load. Check your network." })
      return
    }

    let settled = false
    let launchTimer: number | undefined
    const finish = (result: StandardCheckoutResult) => {
      if (settled) return
      settled = true
      if (launchTimer) window.clearTimeout(launchTimer)
      resolve(result)
    }

    const prefill: Record<string, unknown> = {
      name: (init.prefill_name ?? "Customer").trim() || "Customer",
      email: (init.customer_email ?? "").trim() || "customer@example.com",
      contact: (init.prefill_contact ?? "").trim() || "+919999999999",
    }

    if (mode === "upi_intent") {
      const vpa = (params.upiVpa ?? "").trim()
      if (vpa) {
        prefill.method = "upi"
        prefill.vpa = vpa
      }
    }

    const options: Record<string, unknown> = {
      key: init.key_id,
      amount: init.amount_paise,
      currency: init.currency,
      order_id: init.order_id,
      name: "OverClocked",
      description: init.description,
      image: "https://razorpay.com/assets/razorpay-glyph.svg",
      prefill,
      notes: { appointment_id: appointmentId },
      theme: { color: THEME_COLOR },
    }

    if (init.display_config && Object.keys(init.display_config).length > 0) {
      options.config = init.display_config
    }

    Object.assign(options, {
      handler: async (response: {
        razorpay_payment_id: string
        razorpay_order_id: string
        razorpay_signature: string
      }) => {
        onStatus("Verifying payment on server…")
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
      rzp.on?.("payment.failed", (response) => {
        const err = response.error
        const detail = err?.description || err?.reason || err?.code || "Payment failed in Razorpay checkout."
        finish({ ok: false, message: detail })
      })
      launchTimer = window.setTimeout(() => {
        if (!settled) {
          rzp.close?.()
          finish({
            ok: false,
            message:
              "Razorpay checkout did not finish opening. This is usually a blocked checkout frame or a gateway-side load failure. Retry or use Demo success for presentation.",
          })
        }
      }, 15000)
      rzp.open()
      onStatus("Razorpay checkout launched. Complete the payment in the secure window.")
    } catch (e) {
      finish({ ok: false, message: e instanceof Error ? e.message : String(e) })
    }
  })
}
