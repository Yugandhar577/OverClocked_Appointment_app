import { useCallback, useEffect, useMemo, useState } from "react";
import { getHealth, getPaymentStatus, initiatePayment, resetAndSeed } from "./api";
import { openRazorpayCheckout } from "./razorpay";
import type { InitiateResponse, PaymentStatusResponse, SeedResponse } from "./types";

function formatMoney(currency: string, amountPaise: number): string {
  const major = amountPaise / 100;
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(major);
  } catch {
    return `${currency} ${major.toFixed(2)}`;
  }
}

function Badge({ children, tone }: { children: React.ReactNode; tone: "ok" | "warn" | "neutral" }) {
  const cls =
    tone === "ok"
      ? "bg-emerald-500/15 text-emerald-800 ring-emerald-500/25"
      : tone === "warn"
        ? "bg-amber-500/15 text-amber-900 ring-amber-500/25"
        : "bg-zinc-500/10 text-zinc-700 ring-zinc-500/15";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${cls}`}>
      {children}
    </span>
  );
}

function Card({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-zinc-200/80 bg-white/70 p-6 shadow-sm shadow-zinc-900/5 backdrop-blur-md">
      <div className="mb-5">
        <h2 className="text-lg font-semibold tracking-tight text-zinc-900">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-zinc-600">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">{label}</p>
      <div className="mt-1 flex items-center gap-2">
        <code className="font-mono text-sm text-zinc-800">{value}</code>
        <button
          type="button"
          className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
          onClick={async () => {
            await navigator.clipboard.writeText(value);
            setCopied(true);
            window.setTimeout(() => setCopied(false), 1600);
          }}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [seed, setSeed] = useState<SeedResponse | null>(null);
  const [status, setStatus] = useState<PaymentStatusResponse | null>(null);
  const [lastInit, setLastInit] = useState<InitiateResponse | null>(null);
  const [busy, setBusy] = useState<null | "seed" | "pay">(null);
  const [banner, setBanner] = useState<null | { tone: "error" | "info"; text: string }>(null);
  const [checkoutHint, setCheckoutHint] = useState("");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const h = await getHealth();
        if (!cancelled) setApiOk(h.status === "ok");
      } catch {
        if (!cancelled) setApiOk(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshStatus = useCallback(async (appointmentId: string) => {
    try {
      const s = await getPaymentStatus(appointmentId);
      setStatus(s);
    } catch {
      setStatus(null);
    }
  }, []);

  useEffect(() => {
    if (!seed?.appointment_id) return;
    void refreshStatus(seed.appointment_id);
    const t = window.setInterval(() => void refreshStatus(seed.appointment_id), 5000);
    return () => window.clearInterval(t);
  }, [seed?.appointment_id, refreshStatus]);

  const stepIndex = useMemo(() => {
    if (status?.payment_status === "success") return 3;
    if (busy === "pay" || lastInit) return 2;
    if (seed) return 2;
    return 1;
  }, [status?.payment_status, busy, lastInit, seed]);

  async function onSeed() {
    setBanner(null);
    setBusy("seed");
    setLastInit(null);
    try {
      const s = await resetAndSeed();
      setSeed(s);
      await refreshStatus(s.appointment_id);
    } catch (e) {
      setBanner({ tone: "error", text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(null);
    }
  }

  async function onPay() {
    if (!seed) return;
    setBanner(null);
    setBusy("pay");
    setCheckoutHint("");
    try {
      const init = await initiatePayment(seed.appointment_id);
      setLastInit(init);
      const result = await openRazorpayCheckout(init, seed.appointment_id, setCheckoutHint);
      if (result.ok) {
        setBanner({ tone: "info", text: `Payment verified. Appointment is now ${result.data.appointment_status}.` });
        await refreshStatus(seed.appointment_id);
      } else {
        if (result.message !== "Checkout closed.") {
          setBanner({ tone: "error", text: result.message });
        }
      }
    } catch (e) {
      setBanner({ tone: "error", text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(null);
      setCheckoutHint("");
    }
  }

  const amountLabel = lastInit
    ? formatMoney(lastInit.currency, lastInit.amount_paise)
    : seed
      ? "₹10.00 (demo)"
      : "—";

  return (
    <div className="mx-auto max-w-5xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-violet-700">Appointment payments</p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-zinc-900 sm:text-4xl">
            Secure checkout demo
          </h1>
          <p className="mt-3 max-w-xl text-pretty text-base text-zinc-600">
            Server-created Razorpay orders, Standard Checkout, and signature verification — backed by PostgreSQL
            records matching your schema design.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {apiOk === null ? (
            <Badge tone="neutral">Checking API…</Badge>
          ) : apiOk ? (
            <Badge tone="ok">API online</Badge>
          ) : (
            <Badge tone="warn">API offline — start backend on :8000</Badge>
          )}
          {status?.payment_status ? <Badge tone="neutral">Payment: {status.payment_status}</Badge> : null}
        </div>
      </header>

      <ol className="mt-10 grid gap-3 sm:grid-cols-3">
        {[
          { n: 1, t: "Prepare", d: "Seed a paid appointment" },
          { n: 2, t: "Pay", d: "Open Razorpay checkout" },
          { n: 3, t: "Done", d: "Verify & confirm booking" },
        ].map((s) => {
          const active = stepIndex >= s.n;
          return (
            <li
              key={s.n}
              className={`rounded-2xl border px-4 py-3 ${
                active
                  ? "border-violet-200 bg-violet-50/60"
                  : "border-zinc-200/80 bg-white/40"
              }`}
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Step {s.n}</p>
              <p className="mt-0.5 font-semibold text-zinc-900">{s.t}</p>
              <p className="text-sm text-zinc-600">{s.d}</p>
            </li>
          );
        })}
      </ol>

      {banner ? (
        <div
          className={`mt-8 rounded-2xl border px-4 py-3 text-sm ${
            banner.tone === "error"
              ? "border-red-200 bg-red-50 text-red-900"
              : "border-emerald-200 bg-emerald-50 text-emerald-900"
          }`}
        >
          {banner.text}
        </div>
      ) : null}

      <div className="mt-8 grid gap-6 lg:grid-cols-5">
        <div className="space-y-6 lg:col-span-2">
          <Card
            title="Order summary"
            subtitle="Demo uses a fixed ₹10 advance on a pending appointment."
          >
            <dl className="space-y-3 text-sm">
              <div className="flex items-center justify-between gap-3">
                <dt className="text-zinc-600">Service</dt>
                <dd className="font-medium text-zinc-900">Paid consultation (demo)</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-zinc-600">Amount</dt>
                <dd className="font-semibold text-zinc-900">{amountLabel}</dd>
              </div>
              <div className="flex items-center justify-between gap-3">
                <dt className="text-zinc-600">Gateway</dt>
                <dd className="font-medium text-zinc-900">Razorpay (test)</dd>
              </div>
            </dl>
            <div className="mt-6 rounded-xl bg-zinc-50 p-4 text-xs text-zinc-600">
              <p className="font-medium text-zinc-800">Razorpay test mode</p>
              <p className="mt-1">
                Checkout uses dashboard defaults (UPI, cards, netbanking, wallets). For UPI, use test VPAs such as{" "}
                <span className="font-mono text-zinc-800">success@razorpay</span>. Cards and netbanking: see the{" "}
                <a
                  className="font-medium text-violet-700 underline decoration-violet-300 underline-offset-2 hover:text-violet-900"
                  href="https://razorpay.com/docs/payments/payments/test-card-upi-details/"
                  target="_blank"
                  rel="noreferrer"
                >
                  official test details
                </a>
                . Phone prefill is sent as E.164 (+91…) per Razorpay integration guidance.
              </p>
            </div>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-3">
          <Card
            title="1. Prepare environment"
            subtitle="Wipes payment tables and inserts organiser, customer, slot, and one pending paid appointment."
          >
            <button
              type="button"
              disabled={busy !== null}
              onClick={() => void onSeed()}
              className="inline-flex w-full items-center justify-center rounded-xl bg-zinc-900 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
            >
              {busy === "seed" ? "Preparing…" : "Reset & seed database"}
            </button>
            {seed ? (
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <CopyField label="Appointment ID" value={seed.appointment_id} />
                <CopyField label="Customer ID" value={seed.customer_id} />
              </div>
            ) : (
              <p className="mt-4 text-sm text-zinc-600">Run seed to generate IDs for this session.</p>
            )}
          </Card>

          <Card
            title="2. Pay with Razorpay"
            subtitle="Creates an order on the server, opens Standard Checkout, then verifies the signature."
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <button
                type="button"
                disabled={!seed || busy !== null}
                onClick={() => void onPay()}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border border-zinc-300 bg-white px-4 py-3 text-sm font-semibold text-zinc-900 shadow-sm hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M12 3v18M5 10h14M8 7H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2M16 7h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
                Open checkout
              </button>
              {checkoutHint ? (
                <p className="text-sm text-violet-700 sm:flex-1">{checkoutHint}</p>
              ) : (
                <p className="text-sm text-zinc-600 sm:flex-1">{busy === "pay" ? "Contacting gateway…" : " "}</p>
              )}
            </div>
            {lastInit ? (
              <div className="mt-5 grid gap-4 rounded-xl border border-zinc-100 bg-zinc-50/80 p-4 sm:grid-cols-2">
                <CopyField label="Razorpay order_id" value={lastInit.order_id} />
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Checkout prefill</p>
                  <p className="mt-1 font-mono text-sm text-zinc-800 break-all">
                    {(lastInit.prefill_name ?? "—") +
                      " · " +
                      (lastInit.customer_email ?? "—") +
                      " · " +
                      lastInit.prefill_contact}
                  </p>
                </div>
              </div>
            ) : null}
          </Card>

          {status?.payment_status ? (
            <Card title="Payment record" subtitle="Read from GET /api/payments/status/{appointment_id}">
              <dl className="grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-zinc-600">Status</dt>
                  <dd className="mt-0.5 font-medium capitalize text-zinc-900">{status.payment_status}</dd>
                </div>
                <div>
                  <dt className="text-zinc-600">Amount</dt>
                  <dd className="mt-0.5 font-medium text-zinc-900">
                    {status.amount != null && status.currency
                      ? `${status.currency} ${status.amount}`
                      : "—"}
                  </dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-zinc-600">Gateway ref</dt>
                  <dd className="mt-0.5 font-mono text-xs text-zinc-800 break-all">
                    {status.payment_gateway_ref ?? "—"}
                  </dd>
                </div>
                {status.last_error ? (
                  <div className="sm:col-span-2 rounded-lg border border-red-100 bg-red-50/80 p-3">
                    <dt className="text-xs font-medium uppercase tracking-wide text-red-800">Last verify error</dt>
                    <dd className="mt-1 text-sm text-red-900">{status.last_error}</dd>
                  </div>
                ) : null}
              </dl>
            </Card>
          ) : null}
        </div>
      </div>

      <footer className="mt-12 border-t border-zinc-200/80 pt-6 text-center text-xs text-zinc-500">
        FastAPI · SQLAlchemy · Alembic · PostgreSQL · Vite · React · Tailwind
      </footer>
    </div>
  );
}
