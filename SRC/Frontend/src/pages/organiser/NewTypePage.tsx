import { useState } from "react"

import {
  addResource,
  createAppointmentType,
  publishAppointmentType,
  replaceQuestions,
  replaceWorkingHours,
  updateRules,
} from "../../api/appointmentTypes"
import { errorMessage } from "../../api/client"
import { Button } from "../../components/ui/Button"
import { Field, Input, Select } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri"]

export function NewTypePage() {
  const [title, setTitle] = useState("Team Consultation")
  const [duration, setDuration] = useState(30)
  const [capacity, setCapacity] = useState(4)
  const [resourceName, setResourceName] = useState("Primary consultant")
  const [question, setQuestion] = useState("Phone?")
  const [requiresConfirmation, setRequiresConfirmation] = useState(false)
  const [isPaid, setIsPaid] = useState(false)
  const [message, setMessage] = useState("")

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setMessage("")
    try {
      const created = await createAppointmentType({
        title,
        preset_type: "meeting",
        duration_minutes: duration,
        timezone: "Asia/Kolkata",
        resource_type: "user",
        venue: "Room 201",
      })
      await addResource(created.id, { name: resourceName, capacity, resource_type: "human" })
      await replaceWorkingHours(
        created.id,
        weekDays.map((_day, index) => ({ day_of_week: index, start_time: "09:00:00", end_time: "17:00:00" })),
      )
      await replaceQuestions(created.id, [{ label: question, question_type: "text", required: true }])
      await updateRules(created.id, {
        requires_confirmation: requiresConfirmation,
        manage_capacity: true,
        is_paid: isPaid,
        price: isPaid ? 500 : null,
        advance_payment_required: false,
        cancel_before_minutes: 60,
        reschedule_before_minutes: 60,
        max_per_slot: capacity,
        future_days_limit: 30,
        assignment_method: "auto",
      })
      const published = await publishAppointmentType(created.id)
      setMessage(`Published with ${published.slots_generated} generated slots.`)
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <form className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]" onSubmit={submit}>
      <section className="grid gap-5">
        <h1 className="text-3xl font-bold text-ink">New appointment type</h1>
        {message && <Notice>{message}</Notice>}
        <div className="grid gap-4 rounded-md border border-line bg-paper p-4">
          <Field label="Title">
            <Input value={title} onChange={(event) => setTitle(event.target.value)} />
          </Field>
          <Field label="Duration">
            <Input type="number" value={duration} onChange={(event) => setDuration(Number(event.target.value))} />
          </Field>
          <Field label="Resource">
            <Input value={resourceName} onChange={(event) => setResourceName(event.target.value)} />
          </Field>
          <Field label="Capacity">
            <Input type="number" min={1} value={capacity} onChange={(event) => setCapacity(Number(event.target.value))} />
          </Field>
          <Field label="Required question">
            <Input value={question} onChange={(event) => setQuestion(event.target.value)} />
          </Field>
        </div>
      </section>
      <aside className="h-fit rounded-md border border-line bg-paper p-4 shadow-panel">
        <h2 className="text-lg font-bold">Options</h2>
        <div className="mt-4 grid gap-4">
          <Field label="Confirmation">
            <Select value={String(requiresConfirmation)} onChange={(event) => setRequiresConfirmation(event.target.value === "true")}>
              <option value="false">Auto-confirm</option>
              <option value="true">Manual</option>
            </Select>
          </Field>
          <Field label="Payment">
            <Select value={String(isPaid)} onChange={(event) => setIsPaid(event.target.value === "true")}>
              <option value="false">Free</option>
              <option value="true">Paid</option>
            </Select>
          </Field>
          <Button>Save and publish</Button>
        </div>
      </aside>
    </form>
  )
}
