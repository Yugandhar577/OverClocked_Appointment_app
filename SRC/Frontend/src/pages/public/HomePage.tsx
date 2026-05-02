import { Calendar, CalendarCheck, IndianRupee, Plus, Sparkles, Users } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"

import { listAppointmentTypes } from "../../api/appointmentTypes"
import { errorMessage } from "../../api/client"
import type { AppointmentTypeListItem } from "../../api/types"
import { useAuth } from "../../auth/useAuth"
import {
  LandingLoginModal,
  LANDING_LOGIN_MODAL_STORAGE_KEY,
} from "../../components/public/LandingLoginModal"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { Skeleton, SkeletonText } from "../../components/ui/Skeleton"

export function HomePage() {
  const pageSize = 6
  const [items, setItems] = useState<AppointmentTypeListItem[]>([])
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [landingPromptOpen, setLandingPromptOpen] = useState(false)
  const [searchParams] = useSearchParams()
  const { user, hasRole } = useAuth()

  const query = (searchParams.get("q") ?? "").trim().toLowerCase()

  const visibleItems = useMemo(() => {
    if (!query) return items
    return items.filter((item) => {
      const title = item.title.toLowerCase()
      const org = item.organiser_name?.toLowerCase() ?? ""
      const preset = (item.preset_type ?? "").toLowerCase()
      return title.includes(query) || org.includes(query) || preset.includes(query)
    })
  }, [items, query])

  useEffect(() => {
    listAppointmentTypes(true, 1, pageSize)
      .then((data) => {
        setItems(data.items)
        setPage(data.page)
        setTotal(data.total)
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  async function loadMore() {
    setError("")
    setLoadingMore(true)
    try {
      const data = await listAppointmentTypes(true, page + 1, pageSize)
      setItems((current) => [...current, ...data.items])
      setPage(data.page)
      setTotal(data.total)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoadingMore(false)
    }
  }

  useEffect(() => {
    if (user) return
    if (sessionStorage.getItem(LANDING_LOGIN_MODAL_STORAGE_KEY)) return
    setLandingPromptOpen(true)
  }, [user])

  return (
    <div className="grid gap-6">
      <LandingLoginModal open={landingPromptOpen} onDismiss={() => setLandingPromptOpen(false)} />
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

      <section className="relative overflow-hidden rounded-xl border border-line bg-gradient-to-br from-white via-paper to-slate-100/80 px-5 py-5 shadow-panel md:px-6 md:py-6">
        <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-signal/10 blur-3xl" />
        <div className="relative flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-ink text-paper">
              <Sparkles size={18} />
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-moss">Book with confidence</p>
              <h2 className="mt-1 text-lg font-bold text-ink md:text-xl">Find the right appointment in moments</h2>
              <p className="mt-1 max-w-2xl text-sm text-neutral-700">
                Browse published services below. Signing in is optional until you finalize a reservation — skip the welcome prompt anytime to explore.
              </p>
            </div>
          </div>
        </div>
      </section>

      {loading && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((item) => (
            <article key={item} className="rounded-md border border-line bg-paper p-4 shadow-panel">
              <div className="flex items-start justify-between gap-3">
                <div className="w-full">
                  <Skeleton className="h-5 w-2/3 bg-white" />
                  <Skeleton className="mt-2 h-4 w-1/2 bg-white" />
                </div>
                <Skeleton className="h-7 w-20 bg-white" />
              </div>
              <div className="mt-6">
                <SkeletonText lines={2} />
              </div>
              <Skeleton className="mt-6 h-11 w-full bg-white" />
            </article>
          ))}
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {visibleItems.map((item) => (
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
      {!loading && !error && items.length > 0 && query && visibleItems.length === 0 && (
        <Notice>No services match &ldquo;{searchParams.get("q")?.trim()}&rdquo;. Try another search.</Notice>
      )}
      {!query && items.length < total && (
        <div className="flex justify-center">
          <Button type="button" variant="secondary" onClick={loadMore} disabled={loadingMore}>
            {loadingMore ? "Loading..." : `Load more services (${items.length}/${total})`}
          </Button>
        </div>
      )}
    </div>
  )
}
