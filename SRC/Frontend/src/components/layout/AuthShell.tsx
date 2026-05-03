import { LogIn, UserPlus } from "lucide-react"
import type { MouseEvent } from "react"
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom"

export function AuthShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const isSignup = location.pathname === "/signup"
  const mode = isSignup ? "signup" : "login"

  function switchMode(event: MouseEvent<HTMLAnchorElement>, to: string) {
    event.preventDefault()
    if (location.pathname !== to) navigate(to)
  }

  return (
    <div className="grid min-h-screen place-items-center bg-[#fbf7ef] px-4 py-10">
      <div className={`auth-shell-card auth-mode-${mode} grid w-full max-w-5xl overflow-hidden rounded-xl border border-line bg-white shadow-panel lg:grid-cols-2`}>
        <section className="auth-panel-left hidden bg-[#f5efe3] p-8 lg:block">
          <div className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-lg bg-odoo-primary text-lg font-bold text-paper">OC</span>
            <div>
              <h1 className="text-2xl font-bold text-ink">OverClocked</h1>
              <p className="text-sm text-neutral-600">Appointment workspace</p>
            </div>
          </div>
          <div className="mt-8 grid grid-cols-2 gap-2 rounded-lg border border-line bg-white/70 p-1">
            <Link
              to="/login"
              aria-current={!isSignup ? "page" : undefined}
              onClick={(event) => switchMode(event, "/login")}
              className={`inline-flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-bold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal ${
                !isSignup ? "bg-odoo-primary text-paper shadow-sm" : "text-ink hover:bg-white"
              }`}
            >
              <LogIn size={16} />
              Login
            </Link>
            <Link
              to="/signup"
              aria-current={isSignup ? "page" : undefined}
              onClick={(event) => switchMode(event, "/signup")}
              className={`inline-flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-bold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal ${
                isSignup ? "bg-odoo-primary text-paper shadow-sm" : "text-ink hover:bg-white"
              }`}
            >
              <UserPlus size={16} />
              Sign up
            </Link>
          </div>
          <div className="mt-10">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-neutral-500">Odoo style scheduling</p>
            <h2 className="mt-3 text-4xl font-black leading-tight text-ink">
              {isSignup ? "Build your appointment workspace in minutes." : "Manage appointments from one calm workspace."}
            </h2>
            <p className="mt-4 text-base leading-7 text-neutral-700">
              {isSignup
                ? "Create one account, verify it, and start setting up booking flows for your team."
                : "Sign in as a customer, organiser, or admin and continue with the right tools for your role."}
            </p>
          </div>
          <div className="mt-10 rounded-lg border border-line bg-white/70 p-5 text-sm leading-7 text-neutral-700">
            {isSignup
              ? "Create your profile once, then manage booking pages, confirmations, and customer details from the same workspace."
              : "Role-aware navigation keeps booking, organiser setup, and admin controls separated."}
          </div>
        </section>
        <section className="auth-panel-right p-6 md:p-8">
          <div className="mb-7 flex items-center gap-3 lg:hidden">
            <span className="grid h-10 w-10 place-items-center rounded-md bg-odoo-primary text-paper">OC</span>
            <div>
              <h1 className="text-xl font-bold text-ink">OverClocked</h1>
              <p className="text-sm text-neutral-600">Appointment workspace</p>
            </div>
          </div>
          <div key={mode} className="auth-form-frame">
            <Outlet />
          </div>
        </section>
      </div>
    </div>
  )
}
