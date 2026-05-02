import { Outlet } from "react-router-dom"

export function AuthShell() {
  return (
    <div className="grid min-h-screen place-items-center bg-[#fbf7ef] px-4 py-10">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-xl border border-line bg-white shadow-panel lg:grid-cols-[0.95fr_1.05fr]">
        <section className="hidden bg-[#f5efe3] p-8 lg:block">
          <div className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-lg bg-primary text-lg font-bold text-paper">OC</span>
            <div>
              <h1 className="text-2xl font-bold text-ink">OverClocked</h1>
              <p className="text-sm text-neutral-600">Appointment workspace</p>
            </div>
          </div>
          <div className="mt-10">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-neutral-500">Odoo style scheduling</p>
            <h2 className="mt-3 text-4xl font-black leading-tight text-ink">Manage appointments from one calm workspace.</h2>
            <p className="mt-4 text-base leading-7 text-neutral-700">
              Sign in as a customer, organiser, or admin and continue with the right tools for your role.
            </p>
          </div>
          <div className="mt-10 rounded-lg border border-line bg-white/70 p-5 text-sm leading-7 text-neutral-700">
            Role-aware navigation keeps booking, organiser setup, and admin controls separated.
          </div>
        </section>
        <section className="p-6 md:p-8">
          <div className="mb-7 flex items-center gap-3 lg:hidden">
            <span className="grid h-10 w-10 place-items-center rounded-md bg-primary text-paper">OC</span>
            <div>
              <h1 className="text-xl font-bold text-ink">OverClocked</h1>
              <p className="text-sm text-neutral-600">Appointment workspace</p>
            </div>
          </div>
          <Outlet />
        </section>
      </div>
    </div>
  )
}
