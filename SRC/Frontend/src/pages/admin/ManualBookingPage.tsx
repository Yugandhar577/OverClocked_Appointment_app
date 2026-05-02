import { useState, type FormEvent } from "react"

import { createManualBooking } from "../../api/advanced"
import { errorMessage } from "../../api/client"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"

export function ManualBookingPage() {
  const [form, setForm] = useState({ customer_id: "", appointment_type_id: "", slot_id: "", people_count: 1, resource_id: "", payment_status: "unpaid", internal_notes: "" })
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  function update(key: string, value: string | number) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError("")
    setMessage("")
    try {
      await createManualBooking({
        ...form,
        resource_id: form.resource_id || undefined,
      })
      setMessage("Manual booking created and checked against existing slot capacity.")
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <section className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Manual Booking</h1>
        <p className="text-sm text-neutral-600">Create an admin-side booking using the same conflict checks as customer booking.</p>
      </div>
      {message && <Notice tone="success">{message}</Notice>}
      {error && <Notice tone="error">{error}</Notice>}
      <form onSubmit={submit} className="odoo-surface grid gap-3 p-4 md:grid-cols-2">
        <input className="h-10 rounded border border-line px-3" placeholder="Customer ID" value={form.customer_id} onChange={(event) => update("customer_id", event.target.value)} required />
        <input className="h-10 rounded border border-line px-3" placeholder="Appointment type ID" value={form.appointment_type_id} onChange={(event) => update("appointment_type_id", event.target.value)} required />
        <input className="h-10 rounded border border-line px-3" placeholder="Slot ID" value={form.slot_id} onChange={(event) => update("slot_id", event.target.value)} required />
        <input className="h-10 rounded border border-line px-3" placeholder="Resource ID optional" value={form.resource_id} onChange={(event) => update("resource_id", event.target.value)} />
        <input className="h-10 rounded border border-line px-3" type="number" min={1} value={form.people_count} onChange={(event) => update("people_count", Number(event.target.value))} />
        <select className="h-10 rounded border border-line bg-white px-3" value={form.payment_status} onChange={(event) => update("payment_status", event.target.value)}>
          <option value="unpaid">Unpaid</option>
          <option value="deposit_due">Deposit due</option>
          <option value="paid">Paid</option>
        </select>
        <textarea className="rounded border border-line px-3 py-2 md:col-span-2" placeholder="Internal notes" value={form.internal_notes} onChange={(event) => update("internal_notes", event.target.value)} />
        <Button className="md:col-span-2" type="submit">Create booking</Button>
      </form>
    </section>
  )
}
