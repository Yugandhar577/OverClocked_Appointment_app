import { Outlet } from "react-router-dom"

export function AdminLayout() {
  return (
    <div className="pb-20 md:pb-6">
      <Outlet />
    </div>
  )
}
