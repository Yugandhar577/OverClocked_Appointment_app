import { Calendar, CalendarCheck, IndianRupee, Plus, Users } from "lucide-react"
import { useEffect, useState } from "react"
import { Link } from "react-router-dom"

import { listAppointmentTypes } from "../../api/appointmentTypes"
import { errorMessage } from "../../api/client"
import type { AppointmentTypeListItem } from "../../api/types"
import { useAuth } from "../../auth/useAuth"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"

export function HomePage() {
  const [items, setItems] = useState<AppointmentTypeListItem[]>([])
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const { user, hasRole } = useAuth()

  useEffect(() => {
    listAppointmentTypes(true)
      .then((data) => setItems(data.items))
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="grid gap-6">
      <div className="flex flex-col justify-between gap-4 border-b border-line pb-5 md:flex-row md:items-end">
        <div>
          <h1 className="text-3xl font-bold text-ink">Book an appointment</h1>
          <p className="mt-2 max-w-2xl text-sm text-neutral-700">
            {user ? `Signed in as ${user.full_name}.` : "Pick a service first, then sign in when you confirm."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {user && (
            <Link to="/me/appointments">
              <Button variant="secondary">
                <CalendarCheck size={17} />
                My appointments
              </Button>
            </Link>
          )}
          {hasRole("organiser", "admin") ? (
            <Link to="/organiser/types">
              <Button variant="secondary">
                <Users size={17} />
                Organiser console
              </Button>
            </Link>
          ) : (
            <Link to="/login">
              <Button variant="secondary">
                <Users size={17} />
                Staff login
              </Button>
            </Link>
          )}
        </div>
      </div>
      {hasRole("organiser", "admin") && (
        <div className="grid gap-3 rounded-md border border-line bg-paper p-4 md:grid-cols-[1fr_auto_auto] md:items-center">
          <div>
            <h2 className="font-bold text-ink">Organiser workspace</h2>
            <p className="text-sm text-neutral-700">Manage services, generated slots, and incoming bookings.</p>
          </div>
          <Link to="/organiser/bookings">
            <Button variant="secondary" className="w-full md:w-auto">
              <CalendarCheck size={17} />
              Bookings
            </Button>
          </Link>
          <Link to="/organiser/types/new">
            <Button className="w-full md:w-auto">
              <Plus size={17} />
              New type
            </Button>
          </Link>
        </div>
      )}
      {error && <Notice tone="error">{error}</Notice>}
      {loading && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((item) => (
            <div key={item} className="h-40 animate-pulse rounded-md border border-line bg-white" />
          ))}
        </div>
      )}
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <article key={item.id} className="rounded-md border border-line bg-paper p-4 shadow-panel">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-ink">{item.title}</h2>
                <p className="text-sm text-neutral-700">{item.organiser_name}</p>
              </div>
              <span className="rounded-md border border-line bg-white px-2 py-1 text-xs font-semibold capitalize">{item.preset_type ?? "meeting"}</span>
            </div>
            <div className="mt-5 flex items-center gap-4 text-sm text-neutral-700">
              <span className="flex items-center gap-1">
                <Calendar size={16} />
                {item.duration_minutes} min
              </span>
              <span className="flex items-center gap-1">
                <IndianRupee size={16} />
                {item.is_paid ? item.price : "Free"}
              </span>
            </div>
            <Link className="mt-5 block" to={`/book/${item.id}`}>
              <Button className="w-full">Book</Button>
            </Link>
          </article>
        ))}
      </div>
      {!loading && !error && items.length === 0 && <Notice>No published appointment types yet.</Notice>}
    </div>
  )
}
