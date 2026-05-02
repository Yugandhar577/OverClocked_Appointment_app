import { ArrowLeft, CreditCard, ShieldCheck } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, useLocation, useNavigate, useParams } from "react-router-dom"

import { getBooking } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import { getPaymentStatus, initiatePayment, verifyPayment } from "../../api/payments"
import type { Booking, PaymentInitiateResponse, PaymentStatusResponse } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { formatDateTime } from "../../lib/format"
import { openRazorpayCheckout } from "../../lib/razorpayCheckout"

type PayLocationState = {
  summary?: {
    title: string
    price?: string | null
    currency: string
    isPaid: boolean
  }
}

function formatMoney(currency: string, amountPaise: number): string {
  const major = amountPaise / 100
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(major)
  } catch {
    return `${currency} ${major.toFixed(2)}`
  }
}

export function PaymentCheckoutPage() {
  const { bookingId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const summary = (location.state as PayLocationState | null)?.summary

  const [booking, setBooking] = useState<Booking | null>(null)
  const [payStatus, setPayStatus] = useState<PaymentStatusResponse | null>(null)
  const [lastInit, setLastInit] = useState<PaymentInitiateResponse | null>(null)
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [hint, setHint] = useState("")

  useEffect(() => {
    if (!bookingId) return
    let cancelled = false
    void (async () => {
      try {
        const [b, s] = await Promise.all([getBooking(bookingId), getPaymentStatus(bookingId)])
        if (cancelled) return
        setBooking(b)
        setPayStatus(s)
        if (s.payment_status === "success" || b.status === "confirmed") {
          navigate(`/booking/${bookingId}/confirmation`, { replace: true })
        }
      } catch (err) {
        if (!cancelled) setError(errorMessage(err))
      }
    })()
    return () => {
      cancelled = true
    }
  }, [bookingId, navigate])

  async function handlePay() {
    if (!bookingId) return
    setError("")
    setHint("")
    setBusy(true)
    try {
      const init = await initiatePayment(bookingId)
      setLastInit(init)
      if (init.mock_checkout) {
        setHint("Completing local demo payment (no Razorpay window)…")
        await verifyPayment({
          appointment_id: bookingId,
          razorpay_order_id: init.order_id,
          razorpay_payment_id: `mock_pay_${bookingId}`,
          razorpay_signature: "mock_sig",
        })
        navigate(`/booking/${bookingId}/confirmation`)
        return
      }
      const result = await openRazorpayCheckout(init, bookingId, setHint)
      if (result.ok) {
        navigate(`/booking/${bookingId}/confirmation`)
        return
      }
      if (result.message !== "Checkout closed.") {
        setError(result.message)
      }
      const s = await getPaymentStatus(bookingId)
      setPayStatus(s)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
      setHint("")
    }
  }

  if (!bookingId) return <Notice tone="error">Missing booking.</Notice>
  if (error && !booking) return <Notice tone="error">{error}</Notice>
  if (!booking) return <Notice>Loading checkout…</Notice>

  const amountLabel = lastInit
    ? formatMoney(lastInit.currency, lastInit.amount_paise)
    : summary?.price
      ? `${summary.currency} ${summary.price}`
      : "—"

  return (
    <div className="mx-auto max-w-lg">
      <Link
        to={`/book/${booking.appointment_type_id}`}
        className="mb-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--odoo-primary)] hover:underline"
      >
        <ArrowLeft size={16} />
        Back to booking
      </Link>

      <div className="rounded-md border border-line bg-paper p-6 shadow-panel">
        <div className="flex items-start gap-3">
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-md bg-[var(--odoo-primary)] text-white">
            <CreditCard size={22} />
          </div>
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-ink">Complete payment</h1>
            <p className="mt-1 text-sm text-neutral-600">
              Complete checkout to confirm booking{" "}
              <span className="font-mono font-semibold text-ink">{booking.confirmation_code}</span>.
            </p>
          </div>
        </div>

        {error ? (
          <div className="mt-4">
            <Notice tone="error">{error}</Notice>
          </div>
        ) : null}
        {payStatus?.last_error ? (
          <div className="mt-4">
            <Notice tone="error">{payStatus.last_error}</Notice>
          </div>
        ) : null}

        <dl className="mt-6 grid gap-3 border-t border-line pt-5 text-sm">
          <div className="flex justify-between gap-3">
            <dt className="text-neutral-600">Service</dt>
            <dd className="text-right font-semibold text-ink">{summary?.title ?? booking.appointment_title ?? "Appointment"}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-neutral-600">Time</dt>
            <dd className="font-semibold text-ink">{booking.slot_start ? formatDateTime(booking.slot_start) : "—"}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-neutral-600">Amount</dt>
            <dd className="font-semibold text-ink">{amountLabel}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-neutral-600">Gateway</dt>
            <dd className="font-medium text-ink">
              {lastInit?.mock_checkout ? "Local demo (no keys)" : "Razorpay"}
            </dd>
          </div>
        </dl>

        <div className="mt-5 flex items-start gap-2 rounded-md border border-line bg-white p-3 text-xs text-neutral-600">
          <ShieldCheck className="mt-0.5 shrink-0 text-[var(--odoo-primary)]" size={16} />
          <p>
            {lastInit?.mock_checkout
              ? "Development mode: payment is simulated on the server so you can test the flow without Razorpay keys. For live checkout, set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in your environment."
              : "Checkout opens in a secure Razorpay window. After payment, we verify the signature on the server and confirm your booking automatically."}
          </p>
        </div>

        {hint && <p className="mt-4 text-sm text-[var(--odoo-primary)]">{hint}</p>}

        <Button type="button" className="mt-5 w-full" disabled={busy} onClick={() => void handlePay()}>
          <CreditCard size={17} />
          {busy ? "Processing…" : "Complete payment"}
        </Button>
      </div>
    </div>
  )
}
