import { useState } from "react"

import { updateMe } from "../../api/auth"
import { errorMessage } from "../../api/client"
import { useAuth } from "../../auth/useAuth"
import { Button } from "../../components/ui/Button"
import { Field, Input } from "../../components/ui/Field"
import { Notice } from "../../components/ui/Notice"

export function ProfilePage() {
  const auth = useAuth()
  const [fullName, setFullName] = useState(auth.user?.full_name ?? "")
  const [phone, setPhone] = useState(auth.user?.phone ?? "")
  const [message, setMessage] = useState("")

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    try {
      await updateMe({ full_name: fullName, phone })
      await auth.refresh()
      setMessage("Saved.")
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <form className="mx-auto grid max-w-xl gap-4" onSubmit={submit}>
      <h1 className="text-3xl font-bold text-ink">Profile</h1>
      {message && <Notice>{message}</Notice>}
      <Field label="Full name">
        <Input value={fullName} onChange={(event) => setFullName(event.target.value)} />
      </Field>
      <Field label="Phone">
        <Input value={phone} onChange={(event) => setPhone(event.target.value)} />
      </Field>
      <Button>Save</Button>
    </form>
  )
}
