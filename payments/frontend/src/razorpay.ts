import type { InitiateResponse } from "./types";
import { verifyPayment } from "./api";

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void };
  }
}

export type CheckoutResult =
  | { ok: true; data: Awaited<ReturnType<typeof verifyPayment>> }
  | { ok: false; message: string };

export function openRazorpayCheckout(
  data: InitiateResponse,
  appointmentId: string,
  onUpdate: (msg: string) => void,
): Promise<CheckoutResult> {
  return new Promise((resolve) => {
    if (!window.Razorpay) {
      resolve({ ok: false, message: "Razorpay script failed to load. Check your network." });
      return;
    }

    let settled = false;
    const finish = (result: CheckoutResult) => {
      if (settled) return;
      settled = true;
      resolve(result);
    };

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
      notes: {
        appointment_id: appointmentId,
      },
      theme: {
        color: "#4f46e5",
      },
    };

    if (data.display_config && Object.keys(data.display_config).length > 0) {
      options.config = data.display_config;
    }

    Object.assign(options, {
      handler: async (response: {
        razorpay_payment_id: string;
        razorpay_order_id: string;
        razorpay_signature: string;
      }) => {
        onUpdate("Verifying payment on server…");
        try {
          const verified = await verifyPayment({
            appointment_id: appointmentId,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          finish({ ok: true, data: verified });
        } catch (e) {
          finish({ ok: false, message: e instanceof Error ? e.message : String(e) });
        }
      },
      modal: {
        ondismiss: () => {
          if (window.confirm("Close checkout? You can reopen and try again.")) {
            finish({ ok: false, message: "Checkout closed." });
          }
        },
      },
    });

    try {
      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (e) {
      finish({ ok: false, message: e instanceof Error ? e.message : String(e) });
    }
  });
}
