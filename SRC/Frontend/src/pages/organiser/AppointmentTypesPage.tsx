import { CalendarDays, Copy, Headphones, Link2, Mail, Monitor, Package, Plus, Search, Settings, Share2, Users, Wallet, X } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { Link, useNavigate } from "react-router-dom"

import { listAppointmentTypes, shareLink } from "../../api/appointmentTypes"
import { errorMessage } from "../../api/client"
import type { AppointmentTypeListItem } from "../../api/types"
import { Button } from "../../components/ui/Button"
import { Notice } from "../../components/ui/Notice"
import { Skeleton, SkeletonText } from "../../components/ui/Skeleton"

const presets = [
  {
    id: "meeting",
    title: "Meeting",
    description: "Let others book a meeting in your calendar",
    icon: Users,
  },
  {
    id: "video_call",
    title: "Video Call",
    description: "Schedule a video meeting in a virtual room with participants",
    icon: Headphones,
  },
  {
    id: "table_booking",
    title: "Table Booking",
    description: "Let customers book a table in your restaurant or bar",
    icon: Monitor,
  },
  {
    id: "resource",
    title: "Book a Resource",
    description: "Let customers book a resource such as a room, court, or desk",
    icon: Package,
  },
]

export function AppointmentTypesPage() {
  const navigate = useNavigate()
  const pageSize = 8
  const [items, setItems] = useState<Array<AppointmentTypeListItem & { published: boolean }>>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [message, setMessage] = useState("")
  const [query, setQuery] = useState("")
  const [showPresets, setShowPresets] = useState(false)
  const [publishedPage, setPublishedPage] = useState(1)
  const [draftPage, setDraftPage] = useState(1)
  const [publishedTotal, setPublishedTotal] = useState(0)
  const [draftTotal, setDraftTotal] = useState(0)

  useEffect(() => {
    Promise.all([listAppointmentTypes(true, 1, pageSize), listAppointmentTypes(false, 1, pageSize)])
      .then(([published, drafts]) => {
        setItems([
          ...published.items.map((item) => ({ ...item, published: true })),
          ...drafts.items.map((item) => ({ ...item, published: false })),
        ])
        setPublishedPage(published.page)
        setDraftPage(drafts.page)
        setPublishedTotal(published.total)
        setDraftTotal(drafts.total)
      })
      .catch((err) => setMessage(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  const visibleItems = useMemo(
    () => items.filter((item) => item.title.toLowerCase().includes(query.trim().toLowerCase())),
    [items, query],
  )

  async function copyLink(id: string) {
    try {
      const res = await shareLink(id)
      await navigator.clipboard.writeText(res.url)
      setMessage("Share URL copied.")
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  function startPreset(preset: string) {
    setShowPresets(false)
    navigate(`/organiser/types/new?preset=${preset}`)
  }

  async function loadMore() {
    setMessage("")
    setLoadingMore(true)
    try {
      const publishedCount = items.filter((item) => item.published).length
      const draftCount = items.filter((item) => !item.published).length
      const nextPublished =
        publishedCount < publishedTotal ? await listAppointmentTypes(true, publishedPage + 1, pageSize) : null
      const nextDrafts =
        draftCount < draftTotal ? await listAppointmentTypes(false, draftPage + 1, pageSize) : null
      setItems((current) => [
        ...current,
        ...(nextPublished?.items.map((item) => ({ ...item, published: true })) ?? []),
        ...(nextDrafts?.items.map((item) => ({ ...item, published: false })) ?? []),
      ])
      if (nextPublished) setPublishedPage(nextPublished.page)
      if (nextDrafts) setDraftPage(nextDrafts.page)
    } catch (err) {
      setMessage(errorMessage(err))
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-md border border-line bg-paper">
        <div className="flex flex-col gap-4 border-b border-line p-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" onClick={() => setShowPresets(true)}>
              <Plus size={16} />
              New
            </Button>
            <Button type="button" variant="secondary" onClick={() => visibleItems[0] && copyLink(visibleItems[0].id)} disabled={!visibleItems.length}>
              <Share2 size={16} />
              Share
            </Button>
            <Link to={visibleItems[0] ? `/organiser/types/${visibleItems[0].id}?tab=communication` : "#"}>
              <Button type="button" variant="secondary" disabled={!visibleItems.length}>
                <Mail size={16} />
                Emails
              </Button>
            </Link>
            <Link to={visibleItems[0] ? `/organiser/types/${visibleItems[0].id}?tab=options` : "#"}>
              <Button type="button" variant="secondary" disabled={!visibleItems.length}>
                <Wallet size={16} />
                Payments
              </Button>
            </Link>
            <div>
              <p className="text-sm font-bold text-signal">Appointments</p>
              <h1 className="flex items-center gap-2 text-2xl font-bold text-ink">
                Appointment types
                <Settings size={18} />
              </h1>
            </div>
          </div>
          <label className="focus-within:ring-signal flex h-10 w-full items-center rounded-md border border-line bg-white px-3 focus-within:ring-2 lg:max-w-md">
            <Search size={18} className="text-neutral-500" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search..."
              className="h-full min-w-0 flex-1 border-0 bg-transparent px-3 text-sm outline-none"
            />
          </label>
        </div>

        {message && <div className="p-4"><Notice>{message}</Notice></div>}
        {!loading && visibleItems.length > 0 && (
          <div className="border-b border-line bg-white p-4">
            <div className="grid gap-3 rounded-md border border-line bg-paper p-4 md:grid-cols-[1fr_auto] md:items-center">
              <div>
                <h2 className="font-bold text-ink">Razorpay payments and organiser emails are active</h2>
                <p className="mt-1 text-sm text-neutral-700">
                  Paid appointment types now use Razorpay checkout. Open Emails for confirmation and reminder templates.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link to={`/organiser/types/${visibleItems[0].id}?tab=options`}>
                  <Button type="button" variant="secondary">
                    <Wallet size={16} />
                    Payment setup
                  </Button>
                </Link>
                <Link to={`/organiser/types/${visibleItems[0].id}?tab=communication`}>
                  <Button type="button" variant="secondary">
                    <Mail size={16} />
                    Email setup
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
        {loading && (
          <div className="divide-y divide-line">
            {Array.from({ length: 4 }, (_, index) => (
              <div key={index} className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
                <div>
                  <Skeleton className="h-6 w-56 bg-white" />
                  <div className="mt-3 max-w-sm">
                    <SkeletonText lines={2} />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Skeleton className="h-10 w-24 bg-white" />
                  <Skeleton className="h-10 w-32 bg-white" />
                  <Skeleton className="h-10 w-10 bg-white" />
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="divide-y divide-line">
          {visibleItems.map((item) => (
            <div key={item.id} className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <Link to={`/organiser/types/${item.id}`} className="text-lg font-bold text-ink hover:text-signal">
                    {item.title}
                  </Link>
                  <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${item.published ? "border-green-200 bg-green-50 text-moss" : "border-amber-200 bg-amber-50 text-amber-800"}`}>
                    {item.published ? "Published" : "Draft"}
                  </span>
                </div>
                <p className="mt-1 flex flex-wrap items-center gap-3 text-sm text-neutral-700">
                  <span className="inline-flex items-center gap-1">
                    <CalendarDays size={15} />
                    {item.duration_minutes} min
                  </span>
                  <span>{item.is_paid ? `INR ${item.price}` : "Free"}</span>
                  <span className="capitalize">{(item.preset_type || "meeting").replace("_", " ")}</span>
                  <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${item.is_paid ? "border-indigo-200 bg-indigo-50 text-indigo-800" : "border-neutral-200 bg-neutral-50 text-neutral-700"}`}>
                    {item.is_paid ? "Razorpay enabled" : "No online payment"}
                  </span>
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button type="button" onClick={() => copyLink(item.id)}>
                  <Share2 size={16} />
                  Share
                </Button>
                <Link to={`/organiser/types/${item.id}`}>
                  <Button type="button" variant="secondary">
                    <Settings size={16} />
                    Configure
                  </Button>
                </Link>
                <Link to={`/organiser/types/${item.id}?tab=communication`}>
                  <Button type="button" variant="secondary">
                    <Mail size={16} />
                    Emails
                  </Button>
                </Link>
                <Link to={`/organiser/types/${item.id}?tab=options`}>
                  <Button type="button" variant="secondary">
                    <Wallet size={16} />
                    Payments
                  </Button>
                </Link>
                <Button type="button" variant="ghost" title="Copy link" onClick={() => copyLink(item.id)}>
                  <Copy size={16} />
                </Button>
              </div>
            </div>
          ))}
        </div>

        {!loading && visibleItems.length === 0 && <div className="p-4"><Notice>No appointment types yet.</Notice></div>}
        {!query && items.length < publishedTotal + draftTotal && (
          <div className="border-t border-line p-4 text-center">
            <Button type="button" variant="secondary" onClick={loadMore} disabled={loadingMore}>
              {loadingMore ? "Loading..." : `Load more types (${items.length}/${publishedTotal + draftTotal})`}
            </Button>
          </div>
        )}
      </section>

      <section className="grid gap-3 rounded-md border border-line bg-white p-4 md:grid-cols-[1fr_auto] md:items-center">
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-paper text-signal">
            <Mail size={18} />
          </span>
          <div>
            <h2 className="font-bold text-ink">Email & SMS workflows</h2>
            <p className="mt-1 text-sm text-neutral-700">
              Configure booking emails, cancellation emails, and reminder timing from the organiser type editor.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {visibleItems[0] ? (
            <Link to={`/organiser/types/${visibleItems[0].id}?tab=communication`}>
              <Button type="button" variant="secondary">
                <Mail size={16} />
                Open email section
              </Button>
            </Link>
          ) : (
            <Button type="button" variant="secondary" disabled>
              <Mail size={16} />
              Open email section
            </Button>
          )}
        </div>
      </section>

      <div className="grid gap-3 md:grid-cols-3">
        <Metric label="Shared links" value={items.filter((item) => item.published).length} icon={<Link2 size={18} />} />
        <Metric label="Resources" value={items.length} icon={<Package size={18} />} />
        <Metric label="Appointments" value={items.filter((item) => item.published).length} icon={<CalendarDays size={18} />} />
      </div>

      {showPresets && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-black/35 p-4">
          <section className="w-full max-w-5xl overflow-hidden rounded-md border border-line bg-paper shadow-panel">
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <h2 className="text-xl font-bold text-ink">Choose an appointment preset</h2>
              <button type="button" onClick={() => setShowPresets(false)} className="focus-ring rounded-md p-2 text-neutral-600 hover:bg-white" aria-label="Close">
                <X size={22} />
              </button>
            </div>
            <div className="grid gap-4 p-5 md:grid-cols-3">
              {presets.map((preset) => {
                const Icon = preset.icon
                return (
                  <button
                    type="button"
                    key={preset.id}
                    onClick={() => startPreset(preset.id)}
                    className="focus-ring grid min-h-52 place-items-center rounded-md border border-line bg-white p-5 text-center transition hover:border-signal hover:shadow-panel"
                  >
                    <Icon size={58} className="text-signal" />
                    <span className="mt-4 text-xl font-bold text-ink">{preset.title}</span>
                    <span className="mt-2 max-w-64 text-sm leading-6 text-neutral-700">{preset.description}</span>
                  </button>
                )
              })}
            </div>
            <div className="border-t border-line p-4">
              <Button type="button" onClick={() => setShowPresets(false)}>Close</Button>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

function Metric({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-line bg-white p-3">
      <span className="grid h-10 w-10 place-items-center rounded-md bg-paper text-signal">{icon}</span>
      <div>
        <div className="text-xs font-semibold uppercase text-neutral-600">{label}</div>
        <div className="text-xl font-bold text-ink">{value}</div>
      </div>
    </div>
  )
}
