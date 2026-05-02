import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"

import { signup } from "../../api/auth"
import { errorMessage } from "../../api/client"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

export function SignupPage() {
  const [fullName, setFullName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const navigate = useNavigate()

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setError("")
    try {
      await signup(fullName, email, password)
      navigate(`/otp?email=${encodeURIComponent(email)}`)
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <form className="grid gap-4" onSubmit={submit}>
      {error && <Notice tone="error">{error}</Notice>}
      <Field label="Full name">
        <Input value={fullName} onChange={(event) => setFullName(event.target.value)} />
      </Field>
      <Field label="Email">
        <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
      </Field>
      <Field label="Password">
        <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
      </Field>
      <Button>Create account</Button>
      <Link className="text-sm font-semibold text-signal" to="/login">
        Back to login
      </Link>
    </form>
  )
}
