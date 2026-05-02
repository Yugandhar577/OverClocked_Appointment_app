import { useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"

import { verifyOtp } from "../../api/auth"
import { errorMessage } from "../../api/client"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

export function OtpPage() {
  const [params] = useSearchParams()
  const [email, setEmail] = useState(params.get("email") ?? "")
  const [otp, setOtp] = useState("")
  const [error, setError] = useState("")
  const navigate = useNavigate()

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    try {
      await verifyOtp(email, otp)
      navigate("/login")
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <form className="grid gap-4" onSubmit={submit}>
      {error && <Notice tone="error">{error}</Notice>}
      <Field label="Email">
        <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
      </Field>
      <Field label="OTP">
        <Input value={otp} onChange={(event) => setOtp(event.target.value)} inputMode="numeric" />
      </Field>
      <Button>Verify</Button>
      <Link className="text-sm font-semibold text-signal" to="/login">
        Back to login
      </Link>
    </form>
  )
}
