import { useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"

import { errorMessage } from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

const demoAccounts = [
  { label: "Customer", email: "cust1@test.local", password: "Customer123!" },
  { label: "Organiser", email: "org1@test.local", password: "Organiser123!" },
  { label: "Admin", email: "admin@test.local", password: "Admin123!" },
]

function defaultRouteForRoles(roles: string[]) {
  if (roles.includes("admin")) return "/admin"
  if (roles.includes("organiser")) return "/organiser/types"
  return "/"
}

function canUseRequestedRoute(roles: string[], route?: string) {
  if (!route) return false
  if (roles.includes("admin")) return route.startsWith("/admin")
  if (roles.includes("organiser")) return route.startsWith("/organiser") || route === "/admin"
  return !route.startsWith("/admin") && !route.startsWith("/organiser")
}

export function LoginPage() {
  const [email, setEmail] = useState("cust1@test.local")
  const [password, setPassword] = useState("Customer123!")
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError("")
    try {
      const user = await auth.login(email, password)
      const requestedRoute = (location.state as { from?: string } | null)?.from
      navigate(canUseRequestedRoute(user.roles, requestedRoute) ? requestedRoute! : defaultRouteForRoles(user.roles))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="grid gap-4" onSubmit={submit}>
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-neutral-500">Welcome back</p>
        <h2 className="mt-2 text-3xl font-black text-ink">Sign in to your desk</h2>
        <p className="mt-2 text-sm text-neutral-600">Choose a demo role or use your account credentials.</p>
      </div>
      {error && <Notice tone="error">{error}</Notice>}
      <div className="grid grid-cols-3 gap-2">
        {demoAccounts.map((account) => (
          <button
            key={account.label}
            type="button"
            onClick={() => {
              setEmail(account.email)
              setPassword(account.password)
              setError("")
            }}
            className={`focus-ring rounded-md border px-3 py-2 text-xs font-bold transition ${
              email === account.email ? "border-[var(--odoo-primary)] bg-[#f5efe3] text-ink" : "border-line bg-white text-ink hover:border-ink"
            }`}
          >
            {account.label}
          </button>
        ))}
      </div>
      <Field label="Email">
        <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" />
      </Field>
      <Field label="Password">
        <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" />
      </Field>
      <Button className="h-11" disabled={saving}>{saving ? "Logging in" : "Login"}</Button>
      <div className="grid gap-2 rounded-lg border border-line bg-[#fbf7ef] p-3 text-sm text-neutral-700">
        <div className="flex items-center justify-between"><span>Customer booking</span><strong>Slots + confirmations</strong></div>
        <div className="flex items-center justify-between"><span>Organiser console</span><strong>Types + resources</strong></div>
        <div className="flex items-center justify-between"><span>Admin tools</span><strong>Analytics + theme</strong></div>
      </div>
      <p className="text-sm text-neutral-700">
        New here?{" "}
        <Link className="font-semibold text-signal" to="/signup">
          Create an account
        </Link>
      </p>
    </form>
  )
}
