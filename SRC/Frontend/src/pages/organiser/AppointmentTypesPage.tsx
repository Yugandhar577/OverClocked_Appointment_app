import { Copy, Plus } from "lucide-react"
import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

import { listAppointmentTypes, shareLink } from "../../api/appointmentTypes"
import { errorMessage } from "../../api/client"
import type { AppointmentTypeListItem } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"

export function AppointmentTypesPage() {
  const [items, setItems] = useState<Array<AppointmentTypeListItem & { published: boolean }>>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState("")

  useEffect(() => {
    Promise.all([listAppointmentTypes(true), listAppointmentTypes(false)])
      .then(([published, drafts]) =>
        setItems([
          ...published.items.map((item) => ({ ...item, published: true })),
          ...drafts.items.map((item) => ({ ...item, published: false })),
        ]),
      )
      .catch((err) => setMessage(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  async function copyLink(id: string) {
    try {
      const res = await shareLink(id)
      await navigator.clipboard.writeText(res.url)
      setMessage("Share URL copied.")
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <div className="grid gap-5">
      <div className="flex items-center justify-between border-b border-line pb-4">
        <h1 className="text-3xl font-bold text-ink">Appointment types</h1>
        <Link to="/organiser/types/new">
          <Button>
            <Plus size={17} />
            New
          </Button>
        </Link>
      </div>
      {message && <Notice>{message}</Notice>}
      <div className="grid gap-3 md:grid-cols-3">
        <Metric label="Total" value={items.length} />
        <Metric label="Published" value={items.filter((item) => item.published).length} />
        <Metric label="Drafts" value={items.filter((item) => !item.published).length} />
      </div>
      {loading && <Notice>Loading appointment types...</Notice>}
      <div className="grid gap-3">
        {items.map((item) => (
          <div key={item.id} className="flex flex-col justify-between gap-3 rounded-md border border-line bg-paper p-4 md:flex-row md:items-center">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-bold text-ink">{item.title}</h2>
                <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${item.published ? "border-green-200 bg-green-50 text-moss" : "border-amber-200 bg-amber-50 text-amber-800"}`}>
                  {item.published ? "Published" : "Draft"}
                </span>
              </div>
              <p className="text-sm text-neutral-700">
                {item.duration_minutes} min - {item.is_paid ? `INR ${item.price}` : "Free"}
              </p>
            </div>
            <div className="flex gap-2">
              <Link to={`/book/${item.id}`}>
                <Button variant="secondary">Open</Button>
              </Link>
              <Button variant="secondary" onClick={() => copyLink(item.id)}>
                <Copy size={16} />
              </Button>
            </div>
          </div>
        ))}
      </div>
      {!loading && items.length === 0 && <Notice>No appointment types yet.</Notice>}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="text-xs font-semibold uppercase text-neutral-600">{label}</div>
      <div className="mt-1 text-2xl font-bold text-ink">{value}</div>
    </div>
  )
}
