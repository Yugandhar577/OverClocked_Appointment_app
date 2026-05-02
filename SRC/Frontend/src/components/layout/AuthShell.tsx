import { Outlet } from "react-router-dom"

export function AuthShell() {
  return (
    <div className="grid min-h-screen place-items-center px-4 py-10">
      <div className="w-full max-w-md rounded-md border border-line bg-paper p-6 shadow-panel">
        <div className="mb-6 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-ink text-paper">OC</span>
          <div>
            <h1 className="text-xl font-bold text-ink">OverClocked</h1>
            <p className="text-sm text-neutral-600">Appointment workspace</p>
          </div>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
