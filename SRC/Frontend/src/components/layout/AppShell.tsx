import {
  BarChart3,
  Building2,
  CalendarDays,
  CalendarPlus,
  LogOut,
  Mail,
  Package,
  Palette,
  Search,
  Shield,
  User,
  UserCog,
  UserPlus,
  UserRoundCheck,
  Users,
} from "lucide-react"
import { type FormEvent, useEffect, useState } from "react"
import { Link, NavLink, Outlet, useLocation, useNavigate, useSearchParams } from "react-router-dom"

import { useAuth } from "../../auth/useAuth"
import { DEFAULT_FEATURE_FLAGS, loadFeatureFlags } from "../../lib/featureFlags"
import { Button } from "../ui/Button"

function AppointmentSearchBar() {
  const navigate = useNavigate()
  const location = useLocation()
  const [params] = useSearchParams()
  const [draft, setDraft] = useState("")

  useEffect(() => {
    const qParam = params.get("q") ?? ""
    if (location.pathname === "/") {
      setDraft(qParam)
    }
  }, [location.pathname, params])

  function apply(event?: FormEvent) {
    event?.preventDefault()
    const q = draft.trim()
    if (location.pathname === "/") {
      navigate(q ? `/?q=${encodeURIComponent(q)}` : "/", { replace: true })
    } else {
      navigate(q ? `/?q=${encodeURIComponent(q)}` : "/")
    }
  }

  return (
    <form
      onSubmit={(e) => apply(e)}
      className="order-3 flex min-w-[200px] w-full items-center gap-2 md:order-none md:max-w-md md:flex-1"
      role="search"
    >
      <label htmlFor="nav-appointment-search" className="sr-only">
        Search appointments
      </label>
      <div className="relative min-w-0 flex-1">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500"
          aria-hidden
        />
        <input
          id="nav-appointment-search"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Search services…"
          className="focus-ring h-10 w-full rounded-md border border-line bg-white pl-10 pr-3 text-sm text-ink placeholder:text-neutral-500"
        />
      </div>
      <Button type="submit" variant="secondary" className="shrink-0 px-3 md:px-4">
        Search
      </Button>
    </form>
  )
}

export function AppShell() {
  const { user, logout, hasRole } = useAuth()
  const isAdmin = hasRole("admin")
  const isOrganiser = hasRole("organiser") && !isAdmin
  const isCustomer = Boolean(user) && !isAdmin && !isOrganiser
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3 md:flex-nowrap md:justify-between">
          <Link
            to="/"
            className="order-1 flex shrink-0 items-center gap-3 font-bold tracking-normal text-ink md:order-none"
          >
            <span className="grid h-9 w-9 place-items-center rounded-md bg-odoo-primary text-paper">OC</span>
            <span>OverClocked</span>
          </Link>
          <div className="order-2 ml-auto flex shrink-0 items-center gap-2 md:order-none md:ml-0 md:hidden">
            {user ? (
              <>
                <Link to="/me/profile" className="max-w-[140px] truncate rounded-md px-2 py-1 text-xs font-semibold text-neutral-700">
                  {user.full_name}
                </Link>
                <Button variant="ghost" onClick={logout} title="Log out" className="px-2">
                  <LogOut size={17} />
                </Button>
              </>
            ) : (
              <Link to="/login">
                <Button variant="secondary">Login</Button>
              </Link>
            )}
          </div>

          <nav className="order-4 hidden shrink-0 items-center gap-1 md:order-none md:flex">
            {(!user || isCustomer) && <NavItem to="/">Book</NavItem>}
            {isCustomer && <NavItem to="/me/appointments">My appointments</NavItem>}
            {isOrganiser && <NavItem to="/admin">Dashboard</NavItem>}
            {isOrganiser && <NavItem to="/organiser/types">Types</NavItem>}
            {isOrganiser && <NavItem to="/organiser/bookings">Bookings</NavItem>}
            {isOrganiser && <NavItem to="/organiser/mail-templates">Email Templates</NavItem>}
            {isAdmin && <AdminNavItems />}
          </nav>

          {(!user || isCustomer) && <AppointmentSearchBar />}

          <div className="order-5 hidden shrink-0 items-center gap-2 md:order-none md:flex">
            {user ? (
              <>
                <Link to="/me/profile" className="hidden rounded-md px-2 py-1 text-sm font-semibold text-neutral-700 hover:bg-white sm:inline">
                  {user.full_name}
                </Link>
                <Button variant="ghost" onClick={logout} title="Log out">
                  <LogOut size={17} />
                </Button>
              </>
            ) : (
              <Link to="/login">
                <Button variant="secondary">Login</Button>
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
      <nav className="fixed bottom-0 left-0 right-0 grid grid-cols-4 border-t border-line bg-paper md:hidden">
        {(!user || isCustomer) ? (
          <MobileNav to="/" icon={<CalendarDays size={18} />} label="Book" />
        ) : isOrganiser ? (
          <MobileNav to="/organiser/types" icon={<UserCog size={18} />} label="Types" />
        ) : (
          <MobileNav to="/admin" icon={<Shield size={18} />} label="Admin" />
        )}
        {isCustomer ? (
          <MobileNav to="/me/appointments" icon={<User size={18} />} label="Mine" />
        ) : (
          <MobileNav to="/login" icon={<User size={18} />} label="Login" />
        )}
        {isOrganiser ? (
          <MobileNav to="/organiser/bookings" icon={<CalendarPlus size={18} />} label="Bookings" />
        ) : (
          <MobileNav to="/signup" icon={<UserPlus size={18} />} label="Join" />
        )}
        {isAdmin ? (
          <MobileNav to="/admin" icon={<Shield size={18} />} label="Admin" />
        ) : isOrganiser ? (
          <MobileNav to="/organiser/mail-templates" icon={<Mail size={18} />} label="Emails" />
        ) : user ? (
          <MobileNav to="/me/profile" icon={<User size={18} />} label="Profile" />
        ) : (
          <MobileNav to="/login?intent=staff" icon={<UserCog size={18} />} label="Staff" />
        )}
      </nav>
    </div>
  )
}

function AdminNavItems() {
  const [flags, setFlags] = useState(DEFAULT_FEATURE_FLAGS)

  useEffect(() => {
    loadFeatureFlags().then(setFlags)
  }, [])

  const items = [
    { to: "/admin", label: "Dashboard", icon: <Shield size={15} /> },
    flags.ENABLE_APPOINTMENT_ANALYTICS && { to: "/admin/analytics", label: "Analytics", icon: <BarChart3 size={15} /> },
    flags.ENABLE_WAITLIST && { to: "/admin/waitlist", label: "Waitlist", icon: <UserRoundCheck size={15} /> },
    flags.ENABLE_ADMIN_MANUAL_BOOKING && { to: "/admin/manual-booking", label: "Manual booking", icon: <CalendarPlus size={15} /> },
    flags.ENABLE_RECURRING_BOOKINGS && { to: "/admin/packages", label: "Packages", icon: <Package size={15} /> },
    flags.ENABLE_THEME_CUSTOMIZATION && { to: "/admin/theme", label: "Theme", icon: <Palette size={15} /> },
    { to: "/admin/users", label: "Users", icon: <Users size={15} /> },
    { to: "/admin/organizations", label: "Organizations", icon: <Building2 size={15} /> },
  ].filter((item): item is { to: string; label: string; icon: JSX.Element } => Boolean(item))

  return (
    <>
      {items.map(({ to, label, icon }) => (
        <NavItem key={to} to={to}>{icon}{label}</NavItem>
      ))}
    </>
  )
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-semibold ${isActive ? "bg-odoo-primary text-paper" : "text-ink hover:bg-white"}`
      }
    >
      {children}
    </NavLink>
  )
}

function MobileNav({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink to={to} className="flex flex-col items-center gap-1 py-2 text-xs font-semibold text-ink">
      {icon}
      {label}
    </NavLink>
  )
}
