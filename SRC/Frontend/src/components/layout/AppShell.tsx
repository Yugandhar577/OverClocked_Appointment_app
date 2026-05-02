import { BarChart3, Building2, CalendarDays, CalendarPlus, ChevronDown, LayoutDashboard, LogOut, Package, Palette, Shield, User, UserCog, UserRoundCheck, Users } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { Link, NavLink, Outlet } from "react-router-dom"

import { useAuth } from "../../auth/useAuth"
import { DEFAULT_FEATURE_FLAGS, loadFeatureFlags } from "../../lib/featureFlags"
import { Button } from "../ui/Button"

export function AppShell() {
  const { user, logout, hasRole } = useAuth()
  const isAdmin = hasRole("admin")
  const isOrganiser = hasRole("organiser") && !isAdmin
  const isCustomer = Boolean(user) && !isAdmin && !isOrganiser
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-3 font-bold tracking-normal text-ink">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-ink text-paper">OC</span>
            <span>OverClocked</span>
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {(!user || isCustomer) && <NavItem to="/">Book</NavItem>}
            {isCustomer && <NavItem to="/me/appointments">My appointments</NavItem>}
            {isOrganiser && <NavItem to="/admin">Dashboard</NavItem>}
            {isOrganiser && <NavItem to="/organiser/types">Types</NavItem>}
            {isOrganiser && <NavItem to="/organiser/bookings">Bookings</NavItem>}
            {isAdmin && <AdminDropdown />}
          </nav>
          <div className="flex items-center gap-2">
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
          <MobileNav to="/organiser/bookings" icon={<LayoutDashboard size={18} />} label="Org" />
        ) : (
          <MobileNav to="/organiser/types" icon={<UserCog size={18} />} label="Org" />
        )}
        {isAdmin ? (
          <MobileNav to="/admin" icon={<Shield size={18} />} label="Admin" />
        ) : (
          <MobileNav to="/me/profile" icon={<Shield size={18} />} label="Profile" />
        )}
      </nav>
    </div>
  )
}

function AdminDropdown() {
  const [open, setOpen] = useState(false)
  const [flags, setFlags] = useState(DEFAULT_FEATURE_FLAGS)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadFeatureFlags().then(setFlags)
  }, [])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [])

  const items = [
    { to: "/admin", label: "Dashboard", icon: <LayoutDashboard size={15} /> },
    flags.ENABLE_APPOINTMENT_ANALYTICS && { to: "/admin/analytics", label: "Analytics", icon: <BarChart3 size={15} /> },
    flags.ENABLE_WAITLIST && { to: "/admin/waitlist", label: "Waitlist", icon: <UserRoundCheck size={15} /> },
    flags.ENABLE_ADMIN_MANUAL_BOOKING && { to: "/admin/manual-booking", label: "Manual booking", icon: <CalendarPlus size={15} /> },
    flags.ENABLE_RECURRING_BOOKINGS && { to: "/admin/packages", label: "Packages", icon: <Package size={15} /> },
    flags.ENABLE_THEME_CUSTOMIZATION && { to: "/admin/theme", label: "Theme", icon: <Palette size={15} /> },
    { to: "/admin/users", label: "Users", icon: <Users size={15} /> },
    { to: "/admin/organizations", label: "Organizations", icon: <Building2 size={15} /> },
  ].filter((item): item is { to: string; label: string; icon: JSX.Element } => Boolean(item))

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="inline-flex h-9 items-center gap-1.5 rounded-md px-3 text-sm font-semibold text-ink transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-signal focus:ring-offset-2 focus:ring-offset-paper"
      >
        <Shield size={15} />
        Admin
        <ChevronDown size={13} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute right-0 top-full z-50 mt-1.5 w-48 overflow-hidden rounded-xl border border-line bg-white py-1 shadow-panel">
          {items.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/admin"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                [
                  "flex items-center gap-2.5 px-3 py-2 text-sm font-semibold transition",
                  isActive ? "bg-ink text-paper" : "text-ink hover:bg-paper",
                ].join(" ")
              }
            >
              {icon}
              {label}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `rounded-md px-3 py-2 text-sm font-semibold ${isActive ? "bg-ink text-paper" : "text-ink hover:bg-white"}`
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
