import { CalendarDays, LayoutDashboard, LogOut, Shield, User, UserCog } from "lucide-react"
import { Link, NavLink, Outlet } from "react-router-dom"

import { useAuth } from "../../auth/useAuth"
import { Button } from "../ui/Button"

export function AppShell() {
  const { user, logout, hasRole } = useAuth()
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-3 font-bold tracking-normal text-ink">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-ink text-paper">OC</span>
            <span>OverClocked</span>
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            <NavItem to="/">Book</NavItem>
            {user && <NavItem to="/me/appointments">My appointments</NavItem>}
            {hasRole("organiser", "admin") && <NavItem to="/organiser/types">Types</NavItem>}
            {hasRole("organiser", "admin") && <NavItem to="/organiser/bookings">Bookings</NavItem>}
            {hasRole("admin") && <NavItem to="/admin/users">Admin</NavItem>}
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
        <MobileNav to="/" icon={<CalendarDays size={18} />} label="Book" />
        {user ? (
          <MobileNav to="/me/appointments" icon={<User size={18} />} label="Mine" />
        ) : (
          <MobileNav to="/login" icon={<User size={18} />} label="Login" />
        )}
        {hasRole("organiser", "admin") ? (
          <MobileNav to="/organiser/bookings" icon={<LayoutDashboard size={18} />} label="Org" />
        ) : (
          <MobileNav to="/organiser/types" icon={<UserCog size={18} />} label="Org" />
        )}
        {hasRole("admin") ? (
          <MobileNav to="/admin/users" icon={<Shield size={18} />} label="Admin" />
        ) : (
          <MobileNav to="/me/profile" icon={<Shield size={18} />} label="Profile" />
        )}
      </nav>
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
