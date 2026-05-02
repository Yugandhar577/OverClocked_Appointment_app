export type SeedResponse = {
  organiser_id: string;
  customer_id: string;
  appointment_type_id: string;
  slot_id: string;
  appointment_id: string;
  message: string;
};

export type InitiateResponse = {
  key_id: string;
  order_id: string;
  amount_paise: number;
  currency: string;
  appointment_id: string;
  description: string;
  customer_email: string | null;
  customer_contact: string | null;
  prefill_name: string | null;
  prefill_contact: string;
  display_config: Record<string, unknown> | null;
};

export type VerifyResponse = {
  payment_id: string;
  status: string;
  razorpay_payment_id: string;
  appointment_status: string;
};

export type PaymentStatusResponse = {
  appointment_id: string;
  payment_status: string | null;
  amount: string | null;
  currency: string | null;
  paid_at: string | null;
  payment_gateway_ref: string | null;
  last_error?: string | null;
};

export type ApiError = { detail?: string | { msg: string }[] };
