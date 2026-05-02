import type { FormEvent } from "react"
import { useEffect, useId, useRef, useState } from "react"
import { Link, useNavigate } from "react-router-dom"

import { errorMessage } from "../../api/client"
import { defaultRouteForRoles } from "../../lib/postLoginRedirect"
import { useAuth } from "../../auth/useAuth"
import { Button } from "../ui/Button"
import { Field, Input } from "../ui/Field"
import { Notice } from "../ui/Notice"

const CUSTOMER_EMAIL = "cust1@test.local"
const CUSTOMER_PASSWORD = "Customer123!"

export const LANDING_LOGIN_MODAL_STORAGE_KEY = "oc_landing_login_dismissed"

type LandingLoginModalProps = {
  open: boolean
  onDismiss: () => void
}

export function LandingLoginModal({ open, onDismiss }: LandingLoginModalProps) {
  const navigate = useNavigate()
  const auth = useAuth()
  const titleId = useId()
  const descId = useId()
  const firstFieldRef = useRef<HTMLInputElement>(null)
  const [email, setEmail] = useState(CUSTOMER_EMAIL)
  const [password, setPassword] = useState(CUSTOMER_PASSWORD)
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    document.body.style.overflow = "hidden"
    window.setTimeout(() => firstFieldRef.current?.focus(), 0)
    return () => {
      document.body.style.overflow = ""
    }
  }, [open])

  if (!open) return null

  function skip() {
    sessionStorage.setItem(LANDING_LOGIN_MODAL_STORAGE_KEY, "1")
    onDismiss()
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError("")
    try {
      const user = await auth.login(email, password)
      skip()
      navigate(defaultRouteForRoles(user.roles))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center p-4">
      <button
        type="button"
        aria-label="Continue without signing in"
        className="absolute inset-0 bg-ink/50 backdrop-blur-[2px]"
        onClick={skip}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        className="relative z-[101] grid w-full max-w-md gap-4 rounded-xl border border-line bg-paper p-6 shadow-panel"
      >
        <div>
          <h2 id={titleId} className="text-xl font-bold text-ink">
            Welcome to OverClocked
          </h2>
          <p id={descId} className="mt-2 text-sm text-neutral-700">
            You can browse and pick a service without an account — we&apos;ll ask you to sign in when you confirm a booking.
          </p>
        </div>

        <form className="grid gap-4" onSubmit={submit}>
          {error && <Notice tone="error">{error}</Notice>}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-neutral-500">Quick demo (customer)</p>
            <button
              type="button"
              onClick={() => {
                setEmail(CUSTOMER_EMAIL)
                setPassword(CUSTOMER_PASSWORD)
                setError("")
              }}
              className="focus-ring mt-2 rounded-md border border-line bg-white px-3 py-2 text-xs font-bold text-ink hover:border-ink"
            >
              Customer
            </button>
          </div>
          <Field label="Email">
            <Input
              ref={firstFieldRef}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              autoComplete="email"
            />
          </Field>
          <Field label="Password">
            <Input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete="current-password"
            />
          </Field>
          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={saving} className="min-w-[7rem]">
              {saving ? "Signing in..." : "Sign in"}
            </Button>
            <Button type="button" variant="secondary" onClick={skip}>
              Skip — continue browsing
            </Button>
          </div>
          <p className="text-sm text-neutral-700">
            New here?{" "}
            <Link className="font-semibold text-signal" to="/signup" onClick={skip}>
              Create an account
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
