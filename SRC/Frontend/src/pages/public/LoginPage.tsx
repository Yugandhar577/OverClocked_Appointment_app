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
      const from = (location.state as { from?: string } | null)?.from ?? defaultRouteForRoles(user.roles)
      navigate(from)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="grid gap-4" onSubmit={submit}>
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
            className="focus-ring rounded-md border border-line bg-white px-3 py-2 text-xs font-bold text-ink hover:border-ink"
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
      <Button disabled={saving}>{saving ? "Logging in" : "Login"}</Button>
      <p className="text-sm text-neutral-700">
        New here?{" "}
        <Link className="font-semibold text-signal" to="/signup">
          Create an account
        </Link>
      </p>
    </form>
  )
}
