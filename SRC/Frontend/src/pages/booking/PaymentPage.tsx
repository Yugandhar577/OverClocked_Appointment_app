import { BadgeIndianRupee, CheckCircle2, Copy, CreditCard, Landmark, QrCode, RefreshCcw, ShieldCheck, Smartphone } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"

import { getBooking } from "../../api/bookings"
import { errorMessage } from "../../api/client"
import { demoCompletePayment, initiatePayment, paymentStatus } from "../../api/payments"
import type { InitiatePaymentResponse } from "../../api/payments"
import type { Booking } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { Skeleton, SkeletonText } from "../../components/ui/Skeleton"
import { formatDateTime } from "../../lib/format"
import { openRazorpayCheckout } from "../../lib/razorpay"

export function PaymentPage() {
  const { bookingId } = useParams()
  const navigate = useNavigate()
  const [booking, setBooking] = useState<Booking | null>(null)
  const [message, setMessage] = useState("Preparing secure checkout...")
  const [error, setError] = useState("")
  const [paying, setPaying] = useState(false)
  const [embeddedPaying, setEmbeddedPaying] = useState(false)
  const [initiated, setInitiated] = useState<InitiatePaymentResponse | null>(null)
  const [selectedMethod, setSelectedMethod] = useState("upi_pay")

  useEffect(() => {
    if (!bookingId) return
    Promise.all([getBooking(bookingId), paymentStatus(bookingId).catch(() => null)])
      .then(([bookingData, status]) => {
        setBooking(bookingData)
        if (status?.payment_status === "success") {
          navigate(`/booking/${bookingId}/confirmation`, { replace: true })
          return
        }
        setMessage("Razorpay checkout is ready.")
      })
      .catch((err) => setError(errorMessage(err)))
  }, [bookingId, navigate])

  async function startPayment() {
    if (!bookingId) return
    setPaying(true)
    setError("")
    setMessage("Opening Razorpay checkout...")
    try {
      const initiated = await initiatePayment(bookingId)
      setInitiated(initiated)
      const result = await openRazorpayCheckout(initiated, bookingId, setMessage)
      if (result.ok) {
        navigate(`/booking/${bookingId}/confirmation`, { replace: true })
      } else if (result.message !== "Checkout closed.") {
        setError(result.message)
        setMessage("Use the embedded checkout preview below, or retry Razorpay.")
      } else {
        setMessage("Checkout closed. You can retry Razorpay.")
      }
    } catch (err) {
      setError(errorMessage(err))
      setMessage("Payment was not completed. You can retry checkout.")
    } finally {
      setPaying(false)
    }
  }

  async function completeEmbeddedPayment() {
    if (!bookingId) return
    setEmbeddedPaying(true)
    setError("")
    setMessage("Completing Razorpay test payment...")
    try {
      const order = initiated ?? await initiatePayment(bookingId)
      setInitiated(order)
      await demoCompletePayment({
        appointment_id: bookingId,
        razorpay_order_id: order.order_id,
        payment_method: selectedMethod,
      })
      navigate(`/booking/${bookingId}/confirmation`, { replace: true })
    } catch (err) {
      setError(errorMessage(err))
      setMessage("Payment could not be completed. Please try again.")
    } finally {
      setEmbeddedPaying(false)
    }
  }

  if (error && !booking) return <Notice tone="error">{error}</Notice>

  return (
    <div className="mx-auto grid max-w-5xl gap-5">
      <section className="rounded-md border border-line bg-paper p-6 shadow-panel">
        <Notice>
          Razorpay test mode is active. Use the embedded gateway below; it completes the booking without the blocked hosted overlay.
        </Notice>
        <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <span className="grid h-12 w-12 place-items-center rounded-md bg-[var(--odoo-primary)] text-white">
                <CreditCard size={24} />
              </span>
              <div>
                <p className="text-xs font-bold uppercase text-neutral-600">Secure payment</p>
                <h1 className="text-2xl font-bold text-ink">Complete your booking payment</h1>
              </div>
            </div>
            {booking ? (
              <dl className="mt-6 grid gap-3 border-t border-line pt-5 text-sm">
                <Row label="Appointment" value={booking.appointment_title ?? "Appointment"} />
                <Row label="Time" value={formatDateTime(booking.slot_start)} />
                <Row label="Venue" value={booking.venue ?? "-"} />
                <Row label="Code" value={booking.confirmation_code} />
              </dl>
            ) : (
              <div className="mt-6">
                <Skeleton className="h-8 w-60" />
                <div className="mt-4">
                  <SkeletonText lines={4} />
                </div>
              </div>
            )}
          </div>
          <div className="w-full rounded-md border border-line bg-white p-4">
            <div className="flex items-start gap-3">
              <ShieldCheck className="mt-1 text-moss" size={20} />
              <div>
                <p className="font-bold text-ink">Razorpay Checkout</p>
                <p className="mt-1 text-sm text-neutral-600">{message}</p>
              </div>
            </div>
            {error && <div className="mt-4"><Notice tone="error">{error}</Notice></div>}
            <Button type="button" className="mt-4 w-full" onClick={startPayment} disabled={paying || !booking}>
              {paying ? <RefreshCcw size={16} className="animate-spin" /> : <CreditCard size={16} />}
              {paying ? "Processing" : "Open hosted Razorpay"}
            </Button>
            <Link to={`/booking/${bookingId}/confirmation`}>
              <Button type="button" variant="secondary" className="mt-3 w-full">
                View booking
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <EmbeddedGateway
        bookingId={bookingId || ""}
        booking={booking}
        initiated={initiated}
        paying={embeddedPaying}
        hostedPaying={paying}
        selectedMethod={selectedMethod}
        onSelectMethod={setSelectedMethod}
        onEmbeddedPay={completeEmbeddedPayment}
        onHostedPay={startPayment}
      />
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-neutral-600">{label}</dt>
      <dd className="text-right font-semibold text-ink">{value}</dd>
    </div>
  )
}

function EmbeddedGateway({
  bookingId,
  booking,
  initiated,
  paying,
  hostedPaying,
  selectedMethod,
  onSelectMethod,
  onEmbeddedPay,
  onHostedPay,
}: {
  bookingId: string
  booking: Booking | null
  initiated: InitiatePaymentResponse | null
  paying: boolean
  hostedPaying: boolean
  selectedMethod: string
  onSelectMethod: (method: string) => void
  onEmbeddedPay: () => void
  onHostedPay: () => void
}) {
  const amount = initiated ? formatMoney(initiated.currency, initiated.amount_paise) : "INR 500.00"
  const orderId = initiated?.order_id ?? "Order will be created on pay"

  async function copyOrder() {
    if (initiated?.order_id) await navigator.clipboard.writeText(initiated.order_id)
  }

  return (
    <section className="overflow-hidden rounded-md border border-line bg-white shadow-panel">
      <div className="grid lg:grid-cols-[1fr_1.2fr]">
        <div className="bg-[#111827] p-6 text-white">
          <p className="text-xs font-bold uppercase tracking-wider text-violet-200">OverClocked Pay</p>
          <h2 className="mt-2 text-2xl font-bold">Secure payment gateway</h2>
          <div className="mt-6 rounded-md bg-white/10 p-4">
            <p className="text-sm text-white/70">Payable amount</p>
            <p className="mt-1 text-4xl font-bold">{amount}</p>
            <p className="mt-3 text-sm text-white/70">{booking?.appointment_title ?? "Strategy Session"}</p>
          </div>
          <div className="mt-4 grid gap-2 text-sm text-white/80">
            <div className="flex items-center justify-between gap-3">
              <span>Booking ID</span>
              <span className="max-w-40 truncate font-mono text-xs">{bookingId}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Razorpay order</span>
              <button type="button" onClick={copyOrder} className="inline-flex max-w-44 items-center gap-1 truncate font-mono text-xs text-violet-100">
                {orderId}
                {initiated && <Copy size={12} />}
              </button>
            </div>
          </div>
        </div>

        <div className="grid gap-4 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-ink">Choose payment method</h3>
              <p className="text-sm text-neutral-600">This panel stays visible even if the hosted modal is blocked.</p>
            </div>
            <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-bold text-red-700">Test Mode</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <GatewayOption icon={<QrCode size={22} />} title="UPI" detail="success@razorpay" active={selectedMethod === "upi_pay"} onClick={() => onSelectMethod("upi_pay")} />
            <GatewayOption icon={<CreditCard size={22} />} title="Card" detail="Test card supported" active={selectedMethod === "card"} onClick={() => onSelectMethod("card")} />
            <GatewayOption icon={<Landmark size={22} />} title="NetBanking" detail="Demo bank flow" active={selectedMethod === "netbanking"} onClick={() => onSelectMethod("netbanking")} />
            <GatewayOption icon={<Smartphone size={22} />} title="Wallet" detail="Fast test checkout" active={selectedMethod === "wallet"} onClick={() => onSelectMethod("wallet")} />
          </div>

          <div className="rounded-md border border-line bg-paper p-4">
            <div className="flex items-center gap-3">
              <BadgeIndianRupee className="text-signal" size={22} />
              <div>
                <p className="font-bold text-ink">Razorpay Standard Checkout</p>
                <p className="text-sm text-neutral-600">Uses server-created order and signature verification.</p>
              </div>
            </div>
            <Button type="button" className="mt-4 w-full" onClick={onEmbeddedPay} disabled={paying || !booking}>
              {paying ? <RefreshCcw size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
              {paying ? "Completing payment" : "Complete Razorpay test payment"}
            </Button>
            <button
              type="button"
              onClick={onHostedPay}
              disabled={hostedPaying || !booking}
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-md border border-line bg-white px-4 py-3 text-sm font-bold text-ink hover:bg-paper disabled:cursor-not-allowed disabled:opacity-60"
            >
              {hostedPaying ? <RefreshCcw size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
              {hostedPaying ? "Opening hosted checkout" : "Open hosted Razorpay instead"}
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}

function GatewayOption({
  icon,
  title,
  detail,
  active = false,
  onClick,
}: {
  icon: React.ReactNode
  title: string
  detail: string
  active?: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-3 rounded-md border p-3 text-left ${active ? "border-signal bg-violet-50" : "border-line bg-white"}`}
    >
      <span className="grid h-10 w-10 place-items-center rounded-md bg-paper text-signal">{icon}</span>
      <span>
        <span className="block font-bold text-ink">{title}</span>
        <span className="text-sm text-neutral-600">{detail}</span>
      </span>
    </button>
  )
}

function formatMoney(currency: string, amountPaise: number) {
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(amountPaise / 100)
  } catch {
    return `${currency} ${(amountPaise / 100).toFixed(2)}`
  }
}
