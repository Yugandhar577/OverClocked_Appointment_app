import { api } from "./client"

export interface InitiatePaymentResponse {
  key_id: string
  order_id: string
  amount_paise: number
  currency: string
  appointment_id: string
  description: string
  customer_email?: string | null
  customer_contact?: string | null
  prefill_name?: string | null
  prefill_contact: string
  display_config?: Record<string, unknown> | null
}

export interface VerifyPaymentResponse {
  payment_id: string
  status: string
  razorpay_payment_id: string
  appointment_status: string
}

export interface PaymentStatusResponse {
  appointment_id: string
  payment_status?: string | null
  amount?: string | null
  currency?: string | null
  paid_at?: string | null
  payment_gateway_ref?: string | null
  last_error?: string | null
}

export async function initiatePayment(appointmentId: string) {
  const res = await api.post<InitiatePaymentResponse>("/payments/initiate", { appointment_id: appointmentId })
  return res.data
}

export async function verifyPayment(payload: {
  appointment_id: string
  razorpay_order_id: string
  razorpay_payment_id: string
  razorpay_signature: string
}) {
  const res = await api.post<VerifyPaymentResponse>("/payments/verify", payload)
  return res.data
}

export async function demoCompletePayment(payload: {
  appointment_id: string
  razorpay_order_id?: string | null
  payment_method?: string
}) {
  const res = await api.post<VerifyPaymentResponse>("/payments/demo-complete", payload)
  return res.data
}

export async function paymentStatus(appointmentId: string) {
  const res = await api.get<PaymentStatusResponse>(`/payments/status/${appointmentId}`)
  return res.data
}
