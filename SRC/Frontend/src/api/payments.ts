import { api } from "./client"
import type { PaymentInitiateResponse, PaymentStatusResponse, PaymentVerifyResponse } from "./types"

export async function initiatePayment(appointmentId: string): Promise<PaymentInitiateResponse> {
  const res = await api.post<PaymentInitiateResponse>("/payments/initiate", { appointment_id: appointmentId })
  return res.data
}

export async function verifyPayment(payload: {
  appointment_id: string
  razorpay_order_id: string
  razorpay_payment_id: string
  razorpay_signature: string
}): Promise<PaymentVerifyResponse> {
  const res = await api.post<PaymentVerifyResponse>("/payments/verify", payload)
  return res.data
}

export async function getPaymentStatus(appointmentId: string): Promise<PaymentStatusResponse> {
  const res = await api.get<PaymentStatusResponse>(`/payments/status/${appointmentId}`)
  return res.data
}
