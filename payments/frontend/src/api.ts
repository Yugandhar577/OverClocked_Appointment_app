import type {
  ApiError,
  InitiateResponse,
  PaymentStatusResponse,
  SeedResponse,
  VerifyResponse,
} from "./types";

async function parseJson<T>(res: Response): Promise<T & ApiError> {
  return (await res.json()) as T & ApiError;
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch("/health");
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return parseJson(res);
}

export async function resetAndSeed(): Promise<SeedResponse> {
  const res = await fetch("/api/demo/reset-and-seed", { method: "POST" });
  const body = await parseJson<SeedResponse>(res);
  if (!res.ok) throw new Error(formatError(body));
  return body;
}

export async function initiatePayment(appointmentId: string): Promise<InitiateResponse> {
  const res = await fetch("/api/payments/initiate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ appointment_id: appointmentId }),
  });
  const body = await parseJson<InitiateResponse>(res);
  if (!res.ok) throw new Error(formatError(body));
  return body;
}

export async function verifyPayment(payload: {
  appointment_id: string;
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}): Promise<VerifyResponse> {
  const res = await fetch("/api/payments/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await parseJson<VerifyResponse>(res);
  if (!res.ok) throw new Error(formatError(body));
  return body;
}

export async function getPaymentStatus(appointmentId: string): Promise<PaymentStatusResponse> {
  const res = await fetch(`/api/payments/status/${appointmentId}`);
  const body = await parseJson<PaymentStatusResponse>(res);
  if (!res.ok) throw new Error(formatError(body));
  return body;
}

function formatError(body: ApiError): string {
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: string }).msg) : JSON.stringify(d)))
      .join("; ");
  }
  return "Request failed";
}
