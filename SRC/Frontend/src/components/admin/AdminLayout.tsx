import { Building2, LayoutDashboard, Users } from "lucide-react"
import type { ReactNode } from "react"
import { NavLink, Outlet } from "react-router-dom"

function AdminNavLink({ to, label, icon }: { to: string; label: string; icon: ReactNode }) {
  return (
    <NavLink
      to={to}
      end={to === "/admin"}
      className={({ isActive }) =>
        clsxNav(isActive)
      }
    >
      <span className="text-neutral-500">{icon}</span>
      {label}
    </NavLink>
  )
}

function clsxNav(isActive: boolean) {
  return [
    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition",
    isActive ? "bg-ink text-paper shadow-panel" : "text-ink hover:bg-white",
  ].join(" ")
}

export function AdminLayout() {
  return (
    <div className="flex flex-col gap-6 md:flex-row md:gap-8">
      <aside className="md:w-56 md:shrink-0">
        <div className="md:sticky md:top-6">
          <div className="mb-2 hidden text-xs font-bold uppercase tracking-wider text-neutral-500 md:block">Console</div>
          <nav className="flex gap-1 overflow-x-auto pb-1 md:flex-col md:gap-1 md:overflow-visible md:rounded-xl md:border md:border-line md:bg-white md:p-2 md:shadow-panel">
            <AdminNavLink to="/admin" label="Dashboard" icon={<LayoutDashboard size={18} />} />
            <AdminNavLink to="/admin/users" label="Users" icon={<Users size={18} />} />
            <AdminNavLink to="/admin/organizations" label="Organizations" icon={<Building2 size={18} />} />
          </nav>
        </div>
      </aside>
      <div className="min-w-0 flex-1 pb-20 md:pb-6">
        <Outlet />
      </div>
    </div>
  )
}
